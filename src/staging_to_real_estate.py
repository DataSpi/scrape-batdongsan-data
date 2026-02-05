from utils import dbConnector as db
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
import os
import logging
from psycopg2.extras import execute_batch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "..", "logs", "staging_to_real_estate.log")


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', # Log format with timestamp, log level, and message
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler() 
    ] # using this 2 handlers to log both to file and console
    , force=True
)
logger = logging.getLogger(__name__)
logger.info("-------------------------Start the script-------------------------")


def standardize_re_type(val: str) -> str:
    whitelist = [
        'Căn hộ chung cư', 
        'Nhà mặt phố',
        'Nhà riêng',
        'can-ho-chung-cu',          
        'ban-nha-biet-thu-lien-ke',
        'nha-rieng',
        'ban-nha-mat-pho',
        'ban-shophouse-nha-pho-thuong-mai',
        'ban-nha-rieng',
        'ban-can-ho-chung-cu'
    ]

    def str_normalize(s) -> str:
        if s is None or (isinstance(s, float) and pd.isna(s)):
            return ""
        return str(s).strip().lower()
    
    x = str_normalize(val)
    for token in whitelist:
        if token in x:
            return token
    return x  # or return None if you want to drop non-matching

sb_conn = db.spyno_sb_conn()
sb_conn.autocommit = True

# ------------------------------------------------------------------------------------------------------
# Operating
# ------------------------------------------------------------------------------------------------------

stag_df = db.fetch_to_dataframe(
    conn=sb_conn,
    query="""--sql
        SELECT * FROM staging.real_estate;
    """
)

re_type = db.fetch_to_dataframe(
    conn=sb_conn,
    query="""--sql
        SELECT id, real_estate_type FROM real_estate.re_real_estate_type;
    """
)

prj = db.fetch_to_dataframe(
    conn=sb_conn,
    query="""--sql
        SELECT id, project_name FROM real_estate.re_project;
    """
)

loc_df = db.fetch_to_dataframe(
    conn=sb_conn,
    query="""--sql
        SELECT 
            rd.id AS district_id, 
            rd.district, 
            rc.id AS city_id, 
            rc.city
        FROM real_estate.re_loc_district rd
        JOIN real_estate.re_loc_city rc ON rd.city_id = rc.id
    """
)
loc_city = loc_df[["city_id", "city"]].drop_duplicates()

stag_df[['district', 'city']] = stag_df['location'].str.split(',', n=1, expand=True)
stag_df['city'] = stag_df['city'].str.strip()
stag_df['district'] = stag_df['district'].str.strip()

stag_df = (
    stag_df.merge(
        right=loc_city, 
        how='left',
        on='city'
    ).merge(
        right=loc_df[['district_id', 'district', 'city_id']], 
        how='left', 
        on=['district', 'city_id']
    ).drop(columns=['city', 'district', 'city_id']) 
)
final_df = (
    stag_df
    .merge(re_type, how="left", on="real_estate_type")
    .rename(columns={"id": "re_type_id"})
    .merge(prj, how="left", left_on="project", right_on="project_name")
    .rename(columns={"id": "project_id"})
    .drop(columns=["real_estate_type", "project_name", "project", 'phone'])
    .rename(columns={"unique_id": "id"})   
)

db.upsert_df_to_table(
    conn=sb_conn,
    df=final_df,
    schema="real_estate",
    table="re_real_estate",
    conflict_cols=["id"]
)


logger.info("-------------------------Finish the script-------------------------")
