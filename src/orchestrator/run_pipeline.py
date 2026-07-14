"""
Entrypoint for the whole scrape -> dbt pipeline, meant to be triggered by a single
crontab entry on the local machine (batdongsan.com.vn blocks cloud/CI IPs, so scraping
has to run here; dbt only talks to BigQuery so it runs here too rather than splitting
the pipeline across two machines/schedulers).

    python -m src.orchestrator.run_pipeline

Steps run strictly in order and the pipeline stops at the first failure -- dbt models
depend on bronze data existing, and dbt test depends on dbt run having completed.

dbt run/test are scoped to `stg_real_estate+`/`stg_real_estate_rent+` on purpose:
stg_locations_v1/v2 and stg_projects are built from near-static reference data
(city/district/ward/project lookups, plus geocoded lat/lng seeds -- see
src/_geocode/geocode_locations.py) that doesn't need rebuilding every week. Rebuild that
lineage manually when it actually changes:

    dbt seed --project-dir dbt --profiles-dir dbt
    dbt run --project-dir dbt --profiles-dir dbt --select stg_locations_v1+ stg_locations_v2+ stg_projects+

Sale ("bán") and rental ("cho thuê") listings are scraped by separate scripts
(j_real_estate.py vs j_real_estate_rent.py -- split so a bug in one pipeline can't
affect the other) into separate bronze tables (re_bronze.real_estate vs
re_bronze.real_estate_rent) and built through separate silver/gold models -- rental
prices are monthly rates, not comparable to sale prices, so they never share a table or
a price bound/bin with the sale lineage. See dbt/models/staging/stg_real_estate_rent.sql.
"""
import subprocess
import sys
from pathlib import Path

from src.utils.common_tools import setup_logging

logger = setup_logging()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"
DBT_FLAGS = ["--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)]

# j_real_estate.py/j_real_estate_rent.py default to HCM (--url) when no override is
# passed; j_projects.py same. HN needs an explicit --url since none of these scripts
# derive a city-level URL from --city-code (--city-code only drives district-mode
# crawling).
HN_REAL_ESTATE_URL = "https://batdongsan.com.vn/ban-can-ho-chung-cu-ha-noi"
HN_PROJECTS_URL = "https://batdongsan.com.vn/du-an-bat-dong-san-ha-noi"
HN_RENT_URL = "https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-ha-noi"

DBT_SELECT = ["stg_real_estate+", "stg_real_estate_rent+"]

STEPS = [
    ("scrape_real_estate_hcm", [sys.executable, "-m", "src._web2br.j_real_estate", "--mode", "district"]),
    ("scrape_real_estate_hn", [sys.executable, "-m", "src._web2br.j_real_estate", "--url", HN_REAL_ESTATE_URL]),
    ("scrape_real_estate_rent_hcm", [sys.executable, "-m", "src._web2br.j_real_estate_rent", "--mode", "district"]),
    ("scrape_real_estate_rent_hn", [sys.executable, "-m", "src._web2br.j_real_estate_rent", "--url", HN_RENT_URL]),
    ("scrape_projects_hcm", [sys.executable, "-m", "src._web2br.j_projects"]),
    ("scrape_projects_hn", [sys.executable, "-m", "src._web2br.j_projects", "--url", HN_PROJECTS_URL]),
    ("scrape_metadata", [sys.executable, "-m", "src._web2br.j_metadata"]),
    ("dbt_run", ["dbt", "run", *DBT_FLAGS, "--select", *DBT_SELECT]),
    ("dbt_test", ["dbt", "test", *DBT_FLAGS, "--select", *DBT_SELECT]),
]


def run_step(name: str, cmd: list[str]) -> bool:
    logger.info(f"=== Start: {name} ({' '.join(cmd)}) ===")
    process = subprocess.Popen(
        cmd, cwd=PROJECT_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
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
    for name, cmd in STEPS:
        if not run_step(name, cmd):
            logger.error(f"Pipeline stopped at step: {name}")
            return 1
    logger.info("Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
