"""
Entrypoint for the whole scrape -> dbt pipeline, meant to be triggered by a single
crontab entry on the local machine (batdongsan.com.vn blocks cloud/CI IPs, so scraping
has to run here; dbt only talks to BigQuery so it runs here too rather than splitting
the pipeline across two machines/schedulers).

    python -m src.orchestrator.run_pipeline

Steps run strictly in order and the pipeline stops at the first failure -- dbt models
depend on bronze data existing, and dbt test depends on dbt run having completed.

dbt run/test are scoped to `stg_real_estate+` on purpose: stg_locations_v1/v2 and
stg_projects are built from near-static reference data (city/district/ward/project
lookups, plus geocoded lat/lng seeds -- see src/_geocode/geocode_locations.py) that
doesn't need rebuilding every week. Rebuild that lineage manually when it actually
changes:

    dbt seed --project-dir dbt --profiles-dir dbt
    dbt run --project-dir dbt --profiles-dir dbt --select stg_locations_v1+ stg_locations_v2+ stg_projects+
"""
import subprocess
import sys
from pathlib import Path

from src.utils.common_tools import setup_logging

logger = setup_logging()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"
DBT_FLAGS = ["--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)]

STEPS = [
    ("scrape_real_estate", [sys.executable, "-m", "src._web2br.j_real_estate"]),
    ("scrape_projects", [sys.executable, "-m", "src._web2br.j_projects"]),
    ("scrape_metadata", [sys.executable, "-m", "src._web2br.j_metadata"]),
    ("dbt_run", ["dbt", "run", *DBT_FLAGS, "--select", "stg_real_estate+"]),
    ("dbt_test", ["dbt", "test", *DBT_FLAGS, "--select", "stg_real_estate+"]),
]


def run_step(name: str, cmd: list[str]) -> bool:
    logger.info(f"=== Start: {name} ({' '.join(cmd)}) ===")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if result.stdout:
        logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(f"=== Failed: {name} (exit code {result.returncode}) ===")
        if result.stderr:
            logger.error(result.stderr)
        return False
    logger.info(f"=== Done: {name} ===")
    return True


def main() -> int:
    for name, cmd in STEPS:
        if not run_step(name, cmd):
            logger.error(f"Pipeline stopped at step: {name}")
            return 1
    logger.info("Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
