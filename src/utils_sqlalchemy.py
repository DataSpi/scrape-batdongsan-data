import logging
import time
import platform
import shutil
import subprocess
import os
from typing import List, Tuple, Optional, Union
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine, Connection
from sqlalchemy import literal_column
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
        
    def connect_to_database(host, port, dbname, user, password) -> Engine:
        try:
            connection = create_engine(
                f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}",
                pool_pre_ping=True,
                future=True
            )
            logger.info("Successfully connected to the database")
            return connection
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def execute_query(conn: Union[Engine, Connection], query: str, params: Optional[Tuple] = None, fetch: bool = True) -> Optional[List[Tuple]]:
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
            if isinstance(conn, Engine):
                with conn.begin() as connection:
                    result = connection.exec_driver_sql(query, params or ())
                    if fetch:
                        return result.fetchall()
                    return None
            else:
                result = conn.exec_driver_sql(query, params or ())
                if fetch:
                    return result.fetchall()
                conn.commit()
                return None
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise

    def fetch_to_dataframe(conn: Union[Engine, Connection], query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a pandas DataFrame.
        
        Args:
            query (str): SQL query to execute
            params (Optional[Tuple]): Parameters for the query
        
        Returns:
            pd.DataFrame: Query results as DataFrame
        """
        try:
            df = pd.read_sql_query(sql=query, con=conn, params=params)
            logger.info(f"Successfully fetched {len(df)} rows to DataFrame")
            return df
        except Exception as e:
            logger.error(f"Unexpected error fetching to DataFrame: {e}")
            raise

    def write_df_to_table(conn: Union[Engine, Connection], df: pd.DataFrame, schema: str, table: str):
        if df.empty:
            logger.info(f"Write skipped: DataFrame is empty for {schema}.{table}")
            return

        engine = conn if isinstance(conn, Engine) else conn.engine
        with engine.begin() as connection:
            connection.exec_driver_sql(f'TRUNCATE TABLE "{schema}"."{table}"')
            df.to_sql(
                name=table,
                con=connection,
                schema=schema,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000
            )

    # def upsert_df_to_table(conn: Union[Engine, Connection], df: pd.DataFrame, schema: str, table: str, conflict_cols: List[str]):
    #     if df.empty:
    #         return

    #     records = df.where(pd.notnull(df), None).to_dict(orient="records")
    #     engine = conn if isinstance(conn, Engine) else conn.engine
    #     metadata = MetaData()
    #     table_obj = Table(table, metadata, schema=schema, autoload_with=engine)

    #     insert_stmt = pg_insert(table_obj).values(records)
    #     update_cols = {c: insert_stmt.excluded[c] for c in table_obj.columns.keys() if c not in conflict_cols}
    #     upsert_stmt = insert_stmt.on_conflict_do_update(
    #         index_elements=conflict_cols,
    #         set_=update_cols,
    #         where=text(f'("{table}".*) IS DISTINCT FROM (EXCLUDED.*)')
    #     )

    #     with engine.begin() as connection:
    #         result = connection.execute(upsert_stmt)
    #         logger.info(
    #             f"Upserted {result.rowcount} rows into {schema}.{table} (attempted {len(df)})."
    #         )
    

    def upsert_df_to_table(conn, df, schema, table, conflict_cols):
        if df.empty:
            return 0, 0

        records = df.where(pd.notnull(df), None).to_dict(orient="records")
        engine = conn if isinstance(conn, Engine) else conn.engine
        metadata = MetaData()
        table_obj = Table(table, metadata, schema=schema, autoload_with=engine)

        insert_stmt = pg_insert(table_obj).values(records)
        update_cols = {c: insert_stmt.excluded[c] for c in table_obj.columns.keys() if c not in conflict_cols}
        
        # 1. Define the upsert
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_=update_cols,
            where=text(f'("{table}".*) IS DISTINCT FROM (EXCLUDED.*)')
        )

        # 2. Add RETURNING clause to detect if it was an insert or update
        # xmax is a system column: 0 for new rows, non-zero for updated rows
        upsert_stmt = upsert_stmt.returning(literal_column("xmax"))

        with engine.begin() as connection:
            result = connection.execute(upsert_stmt).fetchall()
            
            # 3. Analyze the results
            # In Postgres, xmax == 0 means it's a fresh INSERT
            # xmax != 0 means it was an UPDATE
            inserts = sum(1 for row in result if row[0] == 0)
            updates = sum(1 for row in result if row[0] != 0)
            
            logger.info(f"Finished: {inserts} new, {updates} updated, {len(df) - len(result)} skipped to {schema}.{table} (attempted {len(df)}).")
            return inserts, updates
    
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
        