"""
Weekly scrape -> dbt pipeline. Optional path: the live/default scheduler is a launchd
job on the maintainer's machine running `python -m src.orchestrator.run_pipeline`
directly (see that module's docstring) -- no standing process needed between runs. This
DAG is kept for anyone who wants Airflow's UI/retries/backfill instead, at the cost of
airflow-scheduler + its Postgres metadata DB running continuously (~1-1.5GB RAM) just to
fire one job a week.

Runs self-hosted (docker-compose, see repo root) rather than on a managed/cloud
Airflow instance: batdongsan.com.vn blocks cloud/CI IP ranges, so the scrape tasks
below must execute from this machine's residential IP, same constraint run_pipeline.py
has.

Same steps, same order, same fail-fast semantics as the STEPS list in
src/orchestrator/run_pipeline.py -- keep both in sync when one changes. dbt
run/snapshot/test are scoped to `fct_real_estate+ fct_real_estate_rent+` on purpose:
dim_location_v1/v2 and dim_project are near-static reference data (city/district/ward/
project lookups + geocoded lat/lng seeds) that doesn't need rebuilding every week -- see
dags/lineage_rebuild_dag.py for that manual-trigger DAG. For the same reason,
scrape_metadata (metadata.py, the bronze source for that lineage) isn't a task here
either -- run it manually (`python -m src._web2br.metadata`) alongside the lineage
rebuild when reference data actually changes.

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
DBT_SELECT = "fct_real_estate+ fct_real_estate_rent+"
# vw_real_estate_current/vw_real_estate_rent_current (in DBT_SELECT's downstream graph)
# select from the snp_real_estate/snp_real_estate_rent snapshots, which don't exist yet
# the first time dbt run executes -- dbt snapshot only creates them straight after.
# Building the views is deferred to its own task, after the snapshot exists.
DBT_CURRENT_VIEWS = "vw_real_estate_current vw_real_estate_rent_current"

HN_REAL_ESTATE_URL = "https://batdongsan.com.vn/ban-can-ho-chung-cu-ha-noi"
HN_PROJECTS_URL = "https://batdongsan.com.vn/du-an-bat-dong-san-ha-noi"
HN_RENT_URL = "https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-ha-noi"

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="pipeline_weekly",
    description="Weekly scrape (sale + rent + projects) then dbt run/test",
    schedule="0 9 * * 1",
    start_date=pendulum.datetime(2026, 7, 1, tz="Asia/Ho_Chi_Minh"),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["pipeline", "weekly"],
) as dag:
    scrape_real_estate_hcm = BashOperator(
        task_id="scrape_real_estate_hcm",
        bash_command="python -m src._web2br.real_estate --mode district",
        cwd=REPO_DIR,
    )
    scrape_real_estate_hn = BashOperator(
        task_id="scrape_real_estate_hn",
        bash_command=f"python -m src._web2br.real_estate --url {HN_REAL_ESTATE_URL}",
        cwd=REPO_DIR,
    )
    scrape_real_estate_rent_hcm = BashOperator(
        task_id="scrape_real_estate_rent_hcm",
        bash_command="python -m src._web2br.real_estate_rent --mode district",
        cwd=REPO_DIR,
    )
    scrape_real_estate_rent_hn = BashOperator(
        task_id="scrape_real_estate_rent_hn",
        bash_command=f"python -m src._web2br.real_estate_rent --url {HN_RENT_URL}",
        cwd=REPO_DIR,
    )
    scrape_projects_hcm = BashOperator(
        task_id="scrape_projects_hcm",
        bash_command="python -m src._web2br.projects",
        cwd=REPO_DIR,
    )
    scrape_projects_hn = BashOperator(
        task_id="scrape_projects_hn",
        bash_command=f"python -m src._web2br.projects --url {HN_PROJECTS_URL}",
        cwd=REPO_DIR,
    )
    # Observability tasks (source freshness / Elementary) swallow failures with `|| true`,
    # mirroring the non-fatal steps in run_pipeline.py STEPS.
    dbt_source_freshness = BashOperator(
        task_id="dbt_source_freshness",
        bash_command=f"dbt source freshness {DBT_FLAGS} || true",
        cwd=REPO_DIR,
    )
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"dbt run {DBT_FLAGS} --select {DBT_SELECT} --exclude {DBT_CURRENT_VIEWS}",
        cwd=REPO_DIR,
    )
    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command=f"dbt snapshot {DBT_FLAGS} --select {DBT_SELECT}",
        cwd=REPO_DIR,
    )
    dbt_run_current_views = BashOperator(
        task_id="dbt_run_current_views",
        bash_command=f"dbt run {DBT_FLAGS} --select {DBT_CURRENT_VIEWS}",
        cwd=REPO_DIR,
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"dbt test {DBT_FLAGS} --select {DBT_SELECT}",
        cwd=REPO_DIR,
    )
    dbt_run_elementary = BashOperator(
        task_id="dbt_run_elementary",
        bash_command=f"dbt run {DBT_FLAGS} --select elementary || true",
        cwd=REPO_DIR,
    )
    dbt_test_anomalies = BashOperator(
        task_id="dbt_test_anomalies",
        bash_command=f"dbt test {DBT_FLAGS} --select tag:elementary || true",
        cwd=REPO_DIR,
    )

    (
        scrape_real_estate_hcm
        >> scrape_real_estate_hn
        >> scrape_real_estate_rent_hcm
        >> scrape_real_estate_rent_hn
        >> scrape_projects_hcm
        >> scrape_projects_hn
        >> dbt_source_freshness
        >> dbt_run
        >> dbt_snapshot
        >> dbt_run_current_views
        >> dbt_test
        >> dbt_run_elementary
        >> dbt_test_anomalies
    )
