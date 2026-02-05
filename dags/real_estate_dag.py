from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator, BranchPythonOperator
from datetime import datetime
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
    dag_id="real_estate_dag",
    start_date=datetime(2026, 1, 29),
    schedule="0 16 * * 5",
    catchup=True
) as dag:
    scraping_task = BashOperator(
        task_id="scraping_task",
        bash_command="""
        cd /home/spyno_kiem/scrape-batdongsan-data &&
        source venv/bin/activate &&
        cd src &&
        python3 /home/spyno_kiem/scrape-batdongsan-data/src/main.py
        """
    )  
    staging_to_project_task = BashOperator(
        task_id="staging_to_project_task",
        bash_command="""
        cd /home/spyno_kiem/scrape-batdongsan-data &&
        source venv/bin/activate &&
        cd src &&
        python3 /home/spyno_kiem/scrape-batdongsan-data/src/staging_to_project.py
        """
    )  
    staging_to_realEstate_type_task = BashOperator(
        task_id="staging_to_realEstate_type_task",
        bash_command="""
        cd /home/spyno_kiem/scrape-batdongsan-data &&
        source venv/bin/activate &&
        cd src &&
        python3 /home/spyno_kiem/scrape-batdongsan-data/src/staging_to_realEstate_type.py
        """
    )
    staging_to_real_estate_task = BashOperator(
        task_id="staging_to_real_estate_task",
        bash_command="""
        cd /home/spyno_kiem/scrape-batdongsan-data &&
        source venv/bin/activate &&
        cd src &&
        python3 /home/spyno_kiem/scrape-batdongsan-data/src/staging_to_real_estate.py
        """
    )
    staging_to_location_task = BashOperator(
        task_id="staging_to_location_task",
        bash_command="""
        cd /home/spyno_kiem/scrape-batdongsan-data &&
        source venv/bin/activate &&
        cd src &&
        python3 /home/spyno_kiem/scrape-batdongsan-data/src/staging_to_location.py
        """
    )
    scraping_task >> [staging_to_project_task, staging_to_realEstate_type_task, staging_to_location_task] >> staging_to_real_estate_task