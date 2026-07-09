import pandas as pd
from utils.sqlalchemy_conn import dbConnector as db


conn = db.spyno_sb_conn()

p1 = db.fetch_to_dataframe(conn, "select * from re_bronze.m_projects")
p2 = db.fetch_to_dataframe(conn, "select * from re_bronze.m_projects_v2")

p_merge = pd.merge(p1, p2[['projectId', 'wardId']], how="outer", on="projectId", suffixes=("_v1", "_v2"))
p_merge.rename(columns={
    'wardId': 'wardId_v2'
}, inplace=True)


db.write_df_to_table(conn, p_merge, schema="re_silver", table="projects", truncate=True)

