import pandas as pd
from dotenv import load_dotenv
load_dotenv()
import os
import logging
from supabase import create_client, Client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "..", "logs", "main.log")


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


import psycopg2
from psycopg2.extras import execute_batch
from typing import Dict, List, Tuple, Any, Optional, Union


# ------------------------------------------------------------------------------------------------------
# Define functions
# ------------------------------------------------------------------------------------------------------

def connect_to_database(host, port, dbname, user, password) -> psycopg2.extensions.connection:
    try:
        connection = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        logger.info("Successfully connected to the database")
        return connection
    except psycopg2.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

def execute_query(conn, query: str, params: Optional[Tuple] = None, fetch: bool = True) -> Optional[List[Tuple]]:
    """
    Execute a SQL query on the database connection.
    
    Args:
        query (str): SQL query to execute
        params (Optional[Tuple]): Parameters for the query
        fetch (bool): Whether to fetch results (for SELECT queries)
    
    Returns:
        Optional[List[Tuple]]: Query results if fetch=True, None otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetch:
            results = cursor.fetchall()
            cursor.close()
            return results
        else:
            conn.commit()
            cursor.close()
            return None
            
    except psycopg2.Error as e:
        logger.error(f"Database error executing query: {e}")
        conn.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error executing query: {e}")
        raise

def fetch_to_dataframe(conn, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
    """
    Execute a SQL query and return results as a pandas DataFrame.
    
    Args:
        query (str): SQL query to execute
        params (Optional[Tuple]): Parameters for the query
    
    Returns:
        pd.DataFrame: Query results as DataFrame
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Fetch all results
        results = cursor.fetchall()
        cursor.close()
        
        # Create DataFrame
        df = pd.DataFrame(results, columns=columns)
        logger.info(f"Successfully fetched {len(df)} rows to DataFrame")
        return df
        
    except psycopg2.Error as e:
        logger.error(f"Database error fetching to DataFrame: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching to DataFrame: {e}")
        raise



# ------------------------------------------------------------------------------------------------------
# Operating
# ------------------------------------------------------------------------------------------------------

DB_PASSWORD    = os.getenv("DB_PASSWORD")
DB_USER        = os.getenv("DB_USER")
DB_PORT        = os.getenv("DB_PORT")
DB_HOST        = os.getenv("DB_HOST")
DB_DB_NAME     = os.getenv("DB_DB_NAME")
sb_conn = connect_to_database(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)


# Fetch new projects from staging.real_estate_20260131 that are not in re_project
execute_query(
    conn=sb_conn,
    query="""--sql
        INSERT INTO real_estate.re_project (project_name)
        SELECT project FROM staging.real_estate_20260131
        WHERE project IS NOT NULL
        EXCEPT
        SELECT project_name FROM postgres.real_estate.re_project;
    """,
    fetch=False
)


re_df = fetch_to_dataframe(
    conn=sb_conn,
    query="""--sql
        SELECT * FROM public.real_estate;
    """
)


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

def standardize_re_type(val: str) -> str:
    def str_normalize(s) -> str:
        if s is None or (isinstance(s, float) and pd.isna(s)):
            return ""
        return str(s).strip().lower()
    
    x = str_normalize(val)
    for token in whitelist:
        if token in x:
            return token
    return x  # or return None if you want to drop non-matching

re_df['real_estate_type'] = re_df['real_estate_type'].map(standardize_re_type)

re_df['real_estate_type'].value_counts()

type_mapping = {
    "nhà riêng":"nhà riêng", 
    "căn hộ chung cư":"căn hộ chung cư", 
    "nhà mặt phố":"nhà mặt phố", 
    "ban-nha-biet-thu-lien-ke":"nhà biệt thự liền kề", 
    "nha-rieng":"nhà riêng", 
    "ban-nha-mat":"nhà mặt phố", 
    "ban-nha-mat-pho":"nhà mặt phố", 
    "ban-shophouse-nha-pho-thuong-mai":"shophouse nhà phố thương mại", 
    "ban-shophouse-nha":"shophouse nhà phố thương mại", 
    "can-ho-chung-cu":"căn hộ chung cư", 
}
re_df['real_estate_type'] = re_df['real_estate_type'].replace(type_mapping, regex=False)



def write_df_to_table(conn, df: pd.DataFrame, schema: str, table: str):
    cols = list(df.columns)
    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join([f'"{c}"' for c in cols])

    with conn.cursor() as cur:
        cur.execute(f'TRUNCATE TABLE "{schema}"."{table}"')
        execute_batch(
            cur,
            f'INSERT INTO "{schema}"."{table}" ({col_names}) VALUES ({placeholders})',
            df.itertuples(index=False, name=None),
            page_size=1000
        )
    conn.commit()

write_df_to_table(sb_conn, re_df, "staging", "real_estate_20260131")


logger.info("-------------------------Finish the script-------------------------")
