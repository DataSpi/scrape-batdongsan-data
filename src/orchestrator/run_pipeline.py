"""
Entrypoint for the whole scrape -> dbt pipeline, triggered weekly by a launchd job on
the local machine (see scripts/run_weekly_pipeline.sh + scripts/com.dataspi.
batdongsan-weekly.plist) -- batdongsan.com.vn blocks cloud/CI IPs, so scraping has to
run here; dbt only talks to BigQuery so it runs here too rather than splitting the
pipeline across two machines/schedulers. No standing process needed between runs,
unlike the Airflow DAG kept at dags/pipeline_weekly_dag.py as an optional alternative
(that path needs airflow-scheduler running continuously; see its docstring).

    python -m src.orchestrator.run_pipeline

Steps run strictly in order and the pipeline stops at the first failure (except steps
marked non-fatal, i.e. the observability ones: source freshness + Elementary) -- dbt models
depend on bronze data existing, dbt snapshot depends on dbt run having built this
week's staging tables, and dbt test depends on both having completed.

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
"""

import subprocess
import sys
from pathlib import Path

from src.utils.common_tools import setup_logging

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

DBT_SELECT = ["fct_real_estate+", "fct_real_estate_rent+"]
# vw_real_estate_current/vw_real_estate_rent_current (in DBT_SELECT's downstream graph)
# select from the snp_real_estate/snp_real_estate_rent snapshots, which don't exist yet
# the first time dbt run executes -- dbt snapshot only creates them straight after.
# Building the views is deferred to its own step, after the snapshot exists.
DBT_CURRENT_VIEWS = ["vw_real_estate_current", "vw_real_estate_rent_current"]

STEPS = [
    ("scrape_real_estate_hcm", [sys.executable, "-m", "src._web2br.real_estate", "--mode", "district"]),
    ("scrape_real_estate_hn", [sys.executable, "-m", "src._web2br.real_estate", "--url", HN_REAL_ESTATE_URL]),
    ("scrape_real_estate_rent_hcm", [sys.executable, "-m", "src._web2br.real_estate_rent", "--mode", "district"]),
    ("scrape_real_estate_rent_hn", [sys.executable, "-m", "src._web2br.real_estate_rent", "--url", HN_RENT_URL]),
    ("scrape_projects_hcm", [sys.executable, "-m", "src._web2br.projects"]),
    ("scrape_projects_hn", [sys.executable, "-m", "src._web2br.projects", "--url", HN_PROJECTS_URL]),
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


def run_step(name: str, cmd: list[str]) -> bool:
    logger.info(f"=== Start: {name} ({' '.join(cmd)}) ===")
    process = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    for line in process.stdout:
        logger.info(f"[{name}] {line.rstrip()}")
    process.wait()

    if process.returncode != 0:
        logger.error(f"=== Failed: {name} (exit code {process.returncode}) ===")
        return False
    logger.info(f"=== Done: {name} ===")
    return True


def main() -> int:
    for name, cmd, *rest in STEPS:
        fatal = rest[0] if rest else True
        if not run_step(name, cmd):
            if not fatal:
                logger.warning(f"Non-fatal step failed, continuing: {name}")
                continue
            logger.error(f"Pipeline stopped at step: {name}")
            return 1
    logger.info("Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
