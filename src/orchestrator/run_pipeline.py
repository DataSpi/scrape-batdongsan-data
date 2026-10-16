"""
Entrypoint for the whole scrape -> dbt pipeline, triggered weekly by a launchd job on
the local machine (see scripts/run_weekly_pipeline.sh + scripts/com.dataspi.
batdongsan-weekly.plist) -- batdongsan.com.vn blocks cloud/CI IPs, so scraping has to
run here; dbt only talks to BigQuery so it runs here too rather than splitting the
pipeline across two machines/schedulers. No standing process needed between runs
(an Airflow alternative existed until git tag `airflow-final`; it was removed because the
scrape step needs a headed Chrome and cannot run inside a container).

    python -m src.orchestrator.run_pipeline [--only scrape_]

Steps run strictly in order and the pipeline stops at the first failure (except steps
marked non-fatal, i.e. the scrapes and the observability ones: source freshness + Elementary)
-- dbt models depend on bronze data existing, dbt snapshot depends on dbt run having built this
week's staging tables, and dbt test depends on both having completed.

Scrape steps are non-fatal individually so one blocked city doesn't discard the others, and a
scraper can exit 2 (src/utils/scrape_health.py) meaning "partial": it loaded what it got, some
pages failed. Before the first non-scrape step a gate checks that at least one of the sale/rent
scrapes (the ones dbt builds from) succeeded or was partial; if none did, the run stops there.
A run that got through but with any scrape partial/failed ends as status "partial" (exit 3).

dbt run/snapshot/test are scoped to `fct_real_estate+`/`fct_real_estate_rent+` on purpose:
dim_location_v1/v2 and dim_project are built from near-static reference data
(city/district/ward/project lookups, plus geocoded lat/lng seeds -- see
src/_geocode/geocode_locations.py) that doesn't need rebuilding every week. For the same
reason, scrape_metadata (metadata.py -- re_bronze.dim_city_v2/dim_ward_v2/dim_street_v2/
dim_project_v2, the bronze source for that lineage) isn't a weekly STEP either: scraping it
fresh every week would just sit unused, since dbt never rebuilds those silver dimension
models on the weekly schedule anyway. Refresh both manually, together, when the reference
data actually changes (new city/ward, new project launched, administrative reform):

    python -m src._web2br.metadata
    dbt seed --project-dir dbt --profiles-dir dbt
    dbt run --project-dir dbt --profiles-dir dbt --select dim_location_v1+ dim_location_v2+ dim_project+

Sale ("bán") and rental ("cho thuê") listings are scraped by separate scripts
(real_estate.py vs real_estate_rent.py -- split so a bug in one pipeline can't
affect the other) into separate bronze tables (re_bronze.fct_real_estate vs
re_bronze.fct_real_estate_rent) and built through separate silver/gold models -- rental
prices are monthly rates, not comparable to sale prices, so they never share a table or
a price bound/bin with the sale lineage. See dbt/models/silver/facts/fct_real_estate_rent.sql.

Every run and step is also logged to BigQuery dataset `re_meta` (src/utils/pipeline_log.py):
pipeline_runs, pipeline_step_runs and the summary view vw_pipeline_runs. Logging failures are
swallowed with a warning -- they never affect the pipeline.
"""

import argparse
import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from collections import deque
from pathlib import Path

from src.utils import pipeline_log
from src.utils.common_tools import setup_logging
from src.utils.scrape_health import EXIT_PARTIAL

logger = setup_logging()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"
DBT_FLAGS = ["--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)]

# real_estate.py/real_estate_rent.py default to HCM (--url) when no override is
# passed; projects.py same. HN needs an explicit --url since none of these scripts
# derive a city-level URL from --city-code (--city-code only drives district-mode
# crawling).
HN_REAL_ESTATE_URL = "https://batdongsan.com.vn/ban-can-ho-chung-cu-ha-noi"
HN_PROJECTS_URL = "https://batdongsan.com.vn/du-an-bat-dong-san-ha-noi"
HN_RENT_URL = "https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-ha-noi"

SCRAPE_PREFIX = "scrape_"
# dbt only builds fct_real_estate+/fct_real_estate_rent+, so only these scrapes feed it.
# Projects feed dim_project, which the weekly dbt run doesn't rebuild.
DBT_FEEDING_SCRAPES = {
    "scrape_real_estate_hcm",
    "scrape_real_estate_hn",
    "scrape_real_estate_rent_hcm",
    "scrape_real_estate_rent_hn",
}
EXIT_RUN_PARTIAL = 3  # run finished and dbt ran, but a scrape step was partial or failed

DBT_SELECT = ["fct_real_estate+", "fct_real_estate_rent+"]
# vw_real_estate_current/vw_real_estate_rent_current (in DBT_SELECT's downstream graph)
# select from the snp_real_estate/snp_real_estate_rent snapshots, which don't exist yet
# the first time dbt run executes -- dbt snapshot only creates them straight after.
# Building the views is deferred to its own step, after the snapshot exists.
DBT_CURRENT_VIEWS = ["vw_real_estate_current", "vw_real_estate_rent_current"]

STEPS = [
    # Scrapes are non-fatal (third element False): see the gate in main().
    ("scrape_real_estate_hcm", [sys.executable, "-m", "src._web2br.real_estate", "--mode", "district"], False),
    ("scrape_real_estate_hn", [sys.executable, "-m", "src._web2br.real_estate", "--url", HN_REAL_ESTATE_URL], False),
    (
        "scrape_real_estate_rent_hcm",
        [sys.executable, "-m", "src._web2br.real_estate_rent", "--mode", "district"],
        False,
    ),
    ("scrape_real_estate_rent_hn", [sys.executable, "-m", "src._web2br.real_estate_rent", "--url", HN_RENT_URL], False),
    ("scrape_projects_hcm", [sys.executable, "-m", "src._web2br.projects"], False),
    ("scrape_projects_hn", [sys.executable, "-m", "src._web2br.projects", "--url", HN_PROJECTS_URL], False),
    # Observability steps are non-fatal (third element False): a broken Elementary
    # package or a stale freshness warning must not block the real data pipeline.
    ("dbt_source_freshness", ["dbt", "source", "freshness", *DBT_FLAGS], False),
    ("dbt_run", ["dbt", "run", *DBT_FLAGS, "--select", *DBT_SELECT, "--exclude", *DBT_CURRENT_VIEWS]),
    ("dbt_snapshot", ["dbt", "snapshot", *DBT_FLAGS, "--select", *DBT_SELECT]),
    ("dbt_run_current_views", ["dbt", "run", *DBT_FLAGS, "--select", *DBT_CURRENT_VIEWS]),
    ("dbt_test", ["dbt", "test", *DBT_FLAGS, "--select", *DBT_SELECT]),
    # Elementary: build/refresh its own models, then run the bronze anomaly tests
    # (weekly volume/freshness/null-rate); results land in re_elementary.
    ("dbt_run_elementary", ["dbt", "run", *DBT_FLAGS, "--select", "elementary"], False),
    ("dbt_test_anomalies", ["dbt", "test", *DBT_FLAGS, "--select", "tag:elementary"], False),
]


ROWS_LOADED_RE = re.compile(r"PIPELINE_METRIC rows_loaded=(\d+)")
ERROR_TAIL_LINES = 20
ERROR_TAIL_MAX_CHARS = 4000
# Per-step wall-clock cap. A scrape step takes ~1 min and dbt a few, so an hour only trips on a
# genuine hang (stuck Cloudflare warm-up, dead socket, BigQuery job that never returns).
STEP_TIMEOUT_S = int(os.getenv("PIPELINE_STEP_TIMEOUT_S", "3600"))


def run_step(name: str, cmd: list[str]) -> dict:
    """Run one step; return its outcome (also what gets logged to re_meta.pipeline_step_runs)."""
    logger.info(f"=== Start: {name} ({' '.join(cmd)}) ===")
    started_at = pipeline_log.now_utc()
    t0 = time.monotonic()
    tail = deque(maxlen=ERROR_TAIL_LINES)
    rows_loaded = None
    # Own session/process group, so a timeout (or our own SIGTERM) can kill the step together
    # with everything it spawned (dbt workers, patchright's Chrome) -- not just the direct child.
    process = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
    )
    timed_out = threading.Event()

    def on_timeout():
        timed_out.set()
        _kill_group(process)

    timer = threading.Timer(STEP_TIMEOUT_S, on_timeout)
    timer.start()
    try:
        # Killing the group closes stdout, which ends this loop.
        for line in process.stdout:
            line = line.rstrip()
            logger.info(f"[{name}] {line}")
            tail.append(line)
            if m := ROWS_LOADED_RE.search(line):
                rows_loaded = (rows_loaded or 0) + int(m.group(1))
        process.wait()
    finally:
        timer.cancel()
        if process.poll() is None:  # interrupted (SIGTERM -> SystemExit): don't leave orphans
            _kill_group(process)

    ok = process.returncode == 0
    partial = name.startswith(SCRAPE_PREFIX) and process.returncode == EXIT_PARTIAL
    if timed_out.is_set():
        tail.append(f"TIMEOUT: step killed after {STEP_TIMEOUT_S}s")
        logger.error(f"=== Failed: {name} (timeout after {STEP_TIMEOUT_S}s) ===")
    elif ok:
        logger.info(f"=== Done: {name} ===")
    elif partial:
        logger.warning(f"=== Partial: {name} (exit code {process.returncode}) ===")
    else:
        logger.error(f"=== Failed: {name} (exit code {process.returncode}) ===")
    return {
        "status": "success" if ok else "partial" if partial else "failed",
        "exit_code": process.returncode,
        "started_at": started_at,
        "ended_at": pipeline_log.now_utc(),
        "duration_s": round(time.monotonic() - t0, 1),
        "rows_loaded": rows_loaded,
        "error_tail": None if ok else "\n".join(tail)[-ERROR_TAIL_MAX_CHARS:],
    }


def _kill_group(process: subprocess.Popen) -> None:
    """SIGTERM the step's whole process group, SIGKILL whatever survives 10s."""
    try:
        pgid = os.getpgid(process.pid)
        os.killpg(pgid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _scrape_gate_failure(scrape_status: dict[str, str]) -> str | None:
    """None if at least one dbt-feeding scrape succeeded or was partial; otherwise the first
    scrape step that failed (what the run reports as its failed_step)."""
    if any(scrape_status.get(name) in ("success", "partial") for name in DBT_FEEDING_SCRAPES):
        return None
    failed = [name for name, result in scrape_status.items() if result == "failed"]
    return failed[0] if failed else next(iter(scrape_status))


def main(only: str | None = None) -> int:
    # launchd/shell wrapper stops the job with SIGTERM: turn it into SystemExit so the
    # `finally` below still records the run as interrupted instead of leaving it dangling.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))

    selected = [step for step in STEPS if only is None or step[0].startswith(only)]
    run_id = uuid.uuid4().hex
    t0 = time.monotonic()
    pipeline_log.log_run_event(run_id, "start", status="running", **pipeline_log.run_context())
    logger.info(f"Pipeline run_id={run_id}")

    status, failed_step, steps_total, steps_failed = "interrupted", None, 0, 0
    scrape_status: dict[str, str] = {}
    gate_checked = False
    try:
        for order, (name, cmd, *rest) in enumerate(selected, start=1):
            fatal = rest[0] if rest else True
            if scrape_status and not gate_checked and not name.startswith(SCRAPE_PREFIX):
                gate_checked = True
                if failed_step := _scrape_gate_failure(scrape_status):
                    logger.error(f"Pipeline stopped at step: {failed_step} (no sale/rent scrape produced usable data)")
                    status = "failed"
                    return 1
            result = run_step(name, cmd)
            steps_total += 1
            pipeline_log.log_step(run_id, step_order=order, step_name=name, fatal=fatal, **result)
            if name.startswith(SCRAPE_PREFIX):
                scrape_status[name] = result["status"]
            if result["status"] == "failed":
                steps_failed += 1
                if not fatal:
                    logger.warning(f"Non-fatal step failed, continuing: {name}")
                    continue
                logger.error(f"Pipeline stopped at step: {name}")
                status, failed_step = "failed", name
                return 1
        if scrape_status and not gate_checked:  # --only scrape_: no later step to gate
            if failed_step := _scrape_gate_failure(scrape_status):
                logger.error(f"Pipeline stopped at step: {failed_step} (no sale/rent scrape produced usable data)")
                status = "failed"
                return 1
        if any(result != "success" for result in scrape_status.values()):
            status = "partial"
            logger.warning("Pipeline completed with partial data: see the Partial/Failed scrape steps above")
            return EXIT_RUN_PARTIAL
        status = "success"
        logger.info("Pipeline completed successfully")
        return 0
    finally:
        pipeline_log.log_run_event(
            run_id,
            "end",
            status=status,
            failed_step=failed_step,
            steps_total=steps_total,
            steps_failed=steps_failed,
            duration_s=round(time.monotonic() - t0, 1),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the weekly scrape -> dbt pipeline.")
    parser.add_argument(
        "--only",
        metavar="PREFIX",
        help="Run only steps whose name starts with PREFIX (e.g. 'scrape_', 'dbt_'). Default: all steps.",
    )
    sys.exit(main(parser.parse_args().only))
