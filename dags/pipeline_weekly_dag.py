"""
Weekly scrape -> dbt pipeline, replacing the crontab entry that used to run
`python -m src.orchestrator.run_pipeline` directly on the maintainer's machine.

Runs self-hosted (docker-compose, see repo root) rather than on a managed/cloud
Airflow instance: batdongsan.com.vn blocks cloud/CI IP ranges, so the scrape tasks
below must execute from this machine's residential IP, same as the original
crontab job did.

Same 9 steps, same order, same fail-fast semantics as the old STEPS list in
src/orchestrator/run_pipeline.py (that module is kept as a manual fallback --
see its docstring). dbt run/test are scoped to `stg_real_estate+ stg_real_estate_rent+`
on purpose: stg_locations_v1/v2 and stg_projects are near-static reference data
(city/district/ward/project lookups + geocoded lat/lng seeds) that doesn't need
rebuilding every week -- see dags/lineage_rebuild_dag.py for that manual-trigger DAG.

Sale ("ban") and rental ("cho thue") listings are scraped by separate scripts so a
bug in one can't affect the other -- kept as separate tasks here for the same reason.
"""
from datetime import timedelta

import pendulum
from airflow.operators.bash import BashOperator

from airflow import DAG

REPO_DIR = "/opt/airflow/repo"
DBT_DIR = f"{REPO_DIR}/dbt"
DBT_FLAGS = f"--project-dir {DBT_DIR} --profiles-dir {DBT_DIR}"
DBT_SELECT = "stg_real_estate+ stg_real_estate_rent+"

HN_REAL_ESTATE_URL = "https://batdongsan.com.vn/ban-can-ho-chung-cu-ha-noi"
HN_PROJECTS_URL = "https://batdongsan.com.vn/du-an-bat-dong-san-ha-noi"
HN_RENT_URL = "https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-ha-noi"

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="pipeline_weekly",
    description="Weekly scrape (sale + rent + projects + metadata) then dbt run/test",
    schedule="0 9 * * 1",
    start_date=pendulum.datetime(2026, 7, 1, tz="Asia/Ho_Chi_Minh"),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["pipeline", "weekly"],
) as dag:

    scrape_real_estate_hcm = BashOperator(
        task_id="scrape_real_estate_hcm",
        bash_command="python -m src._web2br.j_real_estate --mode district",
        cwd=REPO_DIR,
    )
    scrape_real_estate_hn = BashOperator(
        task_id="scrape_real_estate_hn",
        bash_command=f"python -m src._web2br.j_real_estate --url {HN_REAL_ESTATE_URL}",
        cwd=REPO_DIR,
    )
    scrape_real_estate_rent_hcm = BashOperator(
        task_id="scrape_real_estate_rent_hcm",
        bash_command="python -m src._web2br.j_real_estate_rent --mode district",
        cwd=REPO_DIR,
    )
    scrape_real_estate_rent_hn = BashOperator(
        task_id="scrape_real_estate_rent_hn",
        bash_command=f"python -m src._web2br.j_real_estate_rent --url {HN_RENT_URL}",
        cwd=REPO_DIR,
    )
    scrape_projects_hcm = BashOperator(
        task_id="scrape_projects_hcm",
        bash_command="python -m src._web2br.j_projects",
        cwd=REPO_DIR,
    )
    scrape_projects_hn = BashOperator(
        task_id="scrape_projects_hn",
        bash_command=f"python -m src._web2br.j_projects --url {HN_PROJECTS_URL}",
        cwd=REPO_DIR,
    )
    scrape_metadata = BashOperator(
        task_id="scrape_metadata",
        bash_command="python -m src._web2br.j_metadata",
        cwd=REPO_DIR,
    )
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"dbt run {DBT_FLAGS} --select {DBT_SELECT}",
        cwd=REPO_DIR,
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"dbt test {DBT_FLAGS} --select {DBT_SELECT}",
        cwd=REPO_DIR,
    )

    (
        scrape_real_estate_hcm
        >> scrape_real_estate_hn
        >> scrape_real_estate_rent_hcm
        >> scrape_real_estate_rent_hn
        >> scrape_projects_hcm
        >> scrape_projects_hn
        >> scrape_metadata
        >> dbt_run
        >> dbt_test
    )
