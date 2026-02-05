from utils import dbConnector as db
import logging
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "..", "logs", "staging_to_real_estate_type.log")

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
# sb_conn.close()
# stag_df = db.fetch_to_dataframe(sb_conn, "SELECT * FROM staging.real_estate")

def count_rows(): 
    return db.execute_query(
    conn=sb_conn,
    query="SELECT COUNT(*) FROM real_estate.re_real_estate_type;",
    fetch=True,
    )[0][0]

count_start = count_rows()
db.execute_query(
    conn=sb_conn,
    query="""--sql
    INSERT INTO real_estate.re_real_estate_type (real_estate_type) 
    SELECT DISTINCT real_estate_type 
    FROM staging.real_estate re 
    WHERE re.real_estate_type IS NOT NULL
    AND re.real_estate_type <> 'NaN'
    AND re.real_estate_type <> ''
    ON CONFLICT (real_estate_type) 
    DO NOTHING
    """,
    fetch=False,
)

count_end = count_rows()
logger.info(f"[{count_start} -> {count_end}]: Inserted {count_end - count_start} new rows into real_estate.re_real_estate_type")

logger.info("-------------------------End the script-------------------------")
