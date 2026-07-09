from google.cloud import bigquery
import os
import pandas as pd

import json
from google.oauth2 import service_account

def get_bigquery_client():
    credentials_json = os.environ.get("GCP_CREDENTIALS_JSON")
    
    if credentials_json:
        # GitHub Actions: credentials passed as JSON string in env variable
        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        client = bigquery.Client(credentials=credentials, project=credentials_info["project_id"])
    else:
        # Local: use service account file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(base_dir, "gcp_service_account.json")
        client = bigquery.Client()
    
    datasets = list(client.list_datasets())
    if datasets:
        print(f"Kết nối thành công! Đã thấy dataset: {datasets[0].dataset_id}")
    return client

def query_to_df(client, query):
    return client.query(query).to_dataframe()

def execute_query(client, query):
    query_job = client.query(query)
    results = query_job.result()     
    if query_job.statement_type == "SELECT":
        return results.to_dataframe()
    return {
        "statement_type": query_job.statement_type,
        "affected_rows": query_job.num_dml_affected_rows,
        "job_id": query_job.job_id
    }


def upload_df_to_bigquery(
    client,
    df,
    table_id,
    write_disposition="WRITE_APPEND",
    allow_field_addition=False,
):
    from google.cloud.bigquery import LoadJobConfig
    job_config = LoadJobConfig(
        write_disposition=write_disposition,
        autodetect=(write_disposition == "WRITE_TRUNCATE" or allow_field_addition),
    )
    if allow_field_addition and write_disposition != "WRITE_TRUNCATE":
        job_config.schema_update_options = [bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    return job.output_rows


def read_sql_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        sql_query = file.read()
    return sql_query


def get_updated_time(client, schema, table_name):
    query = f"""--sql
    SELECT 
    TIMESTAMP_MILLIS(last_modified_time) AS last_updated
    FROM {schema}.__TABLES__
    WHERE table_id = '{table_name}'
    """
    updated_time = query_to_df(client, query)\
        .iloc[0]['last_updated'].strftime("%Y-%m-%d %H:%M:%S")

    return updated_time