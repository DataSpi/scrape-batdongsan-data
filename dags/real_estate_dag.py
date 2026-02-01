from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator, BranchPythonOperator
from datetime import datetime
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
    dag_id="real_estate_dag",
    start_date=datetime(2026, 1, 29),
    schedule="0 10 * * *",
    catchup=True
) as dag:
    scraping_task = BashOperator(
        task_id="scraping_task",
        bash_command="""
        cd /home/spyno_kiem/scrape-batdongsan-data &&
        source venv/bin/activate &&
        cd src &&
        python3 /home/spyno_kiem/scrape-batdongsan-data/src/main.py"""
    )  


