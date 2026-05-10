import pandas as pd 
from utils.sqlalchemy_conn import dbConnector as db
from utils.common_tools import setup_logging
logger = setup_logging()

db_conn = db.spyno_sb_conn()

df = db.fetch_to_dataframe(conn=db_conn, query="select * from re_silver.real_estate limit 1000")

df.project.value_counts()