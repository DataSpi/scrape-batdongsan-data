import pandas as pd
from src.utils.gcp_conn import get_bigquery_client, query_to_df, upload_df_to_bigquery


client = get_bigquery_client()

p1 = query_to_df(client, "select * from re_bronze.m_projects")
p2 = query_to_df(client, "select * from re_bronze.m_projects_v2")

p_merge = pd.merge(p1, p2[['projectId', 'wardId']], how="outer", on="projectId", suffixes=("_v1", "_v2"))
p_merge.rename(columns={
    'wardId': 'wardId_v2'
}, inplace=True)


upload_df_to_bigquery(client, p_merge, f"{client.project}.re_silver.projects", write_disposition="WRITE_TRUNCATE")

