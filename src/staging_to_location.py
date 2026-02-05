# from utils import dbConnector as db
from utils_sqlalchemy import dbConnector as db
import logging
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "..", "logs", "staging_to_location.log")

logging.basicConfig(
    level=logging.INFO,
    # Log format with timestamp, log level, and message
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(),
    ],  # using this 2 handlers to log both to file and console
    force=True,
)
logger = logging.getLogger(__name__)
logger.info("-------------------------Start the script-------------------------")


sb_conn = db.spyno_sb_conn()
stag_df = db.fetch_to_dataframe(sb_conn, "SELECT unique_id, location FROM staging.real_estate")


stag_df[['district', 'city']] = stag_df['location'].str.split(',', n=1, expand=True)
stag_df['city'] = stag_df['city'].str.strip()
stag_df['district'] = stag_df['district'].str.strip()
city = stag_df.query('city.notnull()')['city'].unique()
district = stag_df[['city', 'district']].dropna().drop_duplicates()

db.upsert_df_to_table(
    conn=sb_conn,
    df=pd.DataFrame(city, columns=['city']),
    schema='real_estate',
    table='re_loc_city',
    conflict_cols=['city'],
)

city_df = db.fetch_to_dataframe(
    conn=sb_conn,
    query="""
    SELECT id, city
    FROM real_estate.re_loc_city
    """
)

district = district.merge(
    right=city_df,
    how='left',
    left_on='city',
    right_on='city'
).drop(columns=['city']).rename(columns={'id': 'city_id'}).query('district!="·"')

db.upsert_df_to_table(
    conn=sb_conn,
    df=district,
    schema='real_estate',
    table='re_loc_district',
    conflict_cols=['district', 'city_id'],
)

logger.info("-------------------------End the script-------------------------")
