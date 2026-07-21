"""
Manual-trigger only -- rebuild location/project reference lineage.

Replaces the manual steps documented in docs/technical-guides.md (section 3):
districts/wards/projects are near-static reference data, so this only needs
running when it actually changes (e.g. an administrative reform, or after
re-geocoding lat/lng). Not on the weekly schedule -- see dags/pipeline_weekly_dag.py
for that.

Requires GOOGLE_MAPS_API_KEY in .env (Geocoding API key, separate from the BigQuery
service account -- see src/_geocode/geocode_locations.py docstring).
"""
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

REPO_DIR = "/opt/airflow/repo"
DBT_DIR = f"{REPO_DIR}/dbt"
DBT_FLAGS = f"--project-dir {DBT_DIR} --profiles-dir {DBT_DIR}"
LINEAGE_SELECT = "stg_locations_v1+ stg_locations_v2+ stg_projects+"

with DAG(
    dag_id="lineage_rebuild",
    description="Manual: geocode district/ward, reload seeds, rebuild location/project lineage",
    schedule=None,
    start_date=pendulum.datetime(2026, 7, 1, tz="Asia/Ho_Chi_Minh"),
    catchup=False,
    tags=["pipeline", "manual"],
) as dag:

    geocode_locations = BashOperator(
        task_id="geocode_locations",
        bash_command="python -m src._geocode.geocode_locations",
        cwd=REPO_DIR,
    )
    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"dbt seed {DBT_FLAGS} --select district_geo_v1 ward_geo_v2",
        cwd=REPO_DIR,
    )
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"dbt run {DBT_FLAGS} --select {LINEAGE_SELECT}",
        cwd=REPO_DIR,
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"dbt test {DBT_FLAGS} --select {LINEAGE_SELECT}",
        cwd=REPO_DIR,
    )

    geocode_locations >> dbt_seed >> dbt_run >> dbt_test
