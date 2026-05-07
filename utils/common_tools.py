import logging
import time
import platform
import shutil
import subprocess
import os
import psycopg2
from psycopg2.extras import execute_batch, execute_values
from typing import List, Tuple, Optional
import pandas as pd



def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)
logger = setup_logging()

def prevent_sleep():
    system = platform.system().lower()
    if system == "darwin" and shutil.which("caffeinate"):
        return subprocess.Popen(["caffeinate"])
    if system == "linux" and shutil.which("systemd-inhibit"):
        proc = subprocess.Popen(
            [
                "systemd-inhibit",
                "--what=sleep",
                "--why=Scraping",
                "--mode=block",
                "sleep",
                "infinity"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(0.2)
        if proc.poll() is not None:
            logging.getLogger(__name__).warning("Sleep prevention not available (systemd-inhibit denied).")
            return None
        return proc
    logging.getLogger(__name__).warning("Sleep prevention not available on this system.")
    return None

def stop_sleep(proc):
    if proc:
        proc.terminate()

def format_worksheet(worksheet):
    worksheet.spreadsheet.batch_update({
        "requests": [
            # Resize column F
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS",
                        "startIndex": 5,
                        "endIndex": 6
                    },
                    "properties": {"pixelSize": 500},
                    "fields": "pixelSize"
                }
            },
            # Resize column A & B
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": 2
                    },
                    "properties": {"pixelSize": 500},
                    "fields": "pixelSize"
                }
            },
            # Resize image column
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS",
                        "startIndex": 10,
                        "endIndex": 20
                    },
                    "properties": {"pixelSize": 200},
                    "fields": "pixelSize"
                }
            },
            # Enable text wrapping
            {
                "repeatCell": {
                    "range": {
                        "sheetId": worksheet.id,
                        "startColumnIndex": 0,
                        "endColumnIndex": 20
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "wrapStrategy": "WRAP"
                        }
                    },
                    "fields": "userEnteredFormat.wrapStrategy"
                }
            }
        ]
    })

class dbConnector:
        
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
            # logger.info(f"Query executed successfully:\n{query}")
            
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

    def upsert_df_to_table(conn, df: pd.DataFrame, schema: str, table: str, conflict_cols: List[str]):
        if df.empty:
            return
        
        # Convert all numpy types (int64, float64, etc.) to native Python types
        data = df.astype(object).where(pd.notnull(df), None).values.tolist()

        cols = list(df.columns)
        col_names = ", ".join([f'"{c}"' for c in cols])
        conflict_cols_quoted = ", ".join([f'"{c}"' for c in conflict_cols])
        update_cols = [c for c in cols if c not in conflict_cols]
        set_clause = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in update_cols])

        sql = f'''
            INSERT INTO "{schema}"."{table}" ({col_names})
            VALUES %s
            ON CONFLICT ({conflict_cols_quoted})
            DO UPDATE SET {set_clause}
            WHERE ("{table}".*) IS DISTINCT FROM (EXCLUDED.*)
        '''

        with conn.cursor() as cur:
            # execute_values is more efficient for this use case
            execute_values(
                cur, 
                sql, 
                # df.to_records(index=False), # Converts DF to list of tuples
                data,
                template=None, 
                page_size=1000
            )
            
            # Now cur.rowcount will correctly return the total number of affected rows
            affected_rows = cur.rowcount
            logger.info(
                f"Upserted {affected_rows} rows into {schema}.{table} (attempted {len(df)})."
            )
        conn.commit()
    
    def spyno_sb_conn():
        DB_PASSWORD    = os.getenv("DB_PASSWORD")
        DB_USER        = os.getenv("DB_USER")
        DB_PORT        = os.getenv("DB_PORT")
        DB_HOST        = os.getenv("DB_HOST")
        DB_DB_NAME     = os.getenv("DB_DB_NAME")
        sb_conn = dbConnector.connect_to_database(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return sb_conn
        