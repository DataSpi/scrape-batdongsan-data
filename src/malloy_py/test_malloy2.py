import asyncio
import os

from dotenv import load_dotenv
from malloy.data.duckdb import DuckDbConnection

import malloy

load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


COMPAT_TABLES = [
  "supabase2.re_bronze.m_cities",
  "supabase2.re_bronze.m_districts",
  "supabase2.re_bronze.m_wards",
  "supabase2.re_bronze.m_streets",
  "supabase2.re_bronze.m_cities_v2",
  "supabase2.re_bronze.m_wards_v2",
  "supabase2.re_bronze.m_streets_v2",
  "supabase2.re_bronze.m_projects",
  "supabase2.re_bronze.m_projects_v2",
  "supabase2.re_silver.real_estate",
]


async def main():
  home_dir = "/Users/spinokiem/scrape-batdongsan-data/"
  duck_conn = DuckDbConnection(home_dir=home_dir, name="supabase")

  # Run setup SQL on the exact same DuckDB connection Malloy will use.
  duck_conn.run_query("INSTALL postgres; LOAD postgres;")
  duck_conn.run_query(f"""
    ATTACH IF NOT EXISTS
    'host={DB_HOST} user={DB_USER} password={DB_PASSWORD} port={DB_PORT} dbname={DB_NAME}'
    AS supabase2 (TYPE POSTGRES);
  """)

  # Work around Malloy DuckDB connector quoting behavior for multi-part table paths.
  for table_name in COMPAT_TABLES:
    duck_conn.run_query(
      f'CREATE OR REPLACE VIEW "{table_name}" AS SELECT * FROM {table_name}'
    )

  with malloy.Runtime() as runtime:
    runtime.add_connection(duck_conn)

    data = await runtime.load_file(home_dir + "malloy/malloy_publisher/real_estate.malloy").run(
        named_query="general_info_by_project")

    if data is None:
      raise RuntimeError("Malloy query returned no data. Check upstream catalog/schema/table errors.")

    dataframe = data.to_dataframe()
    print(dataframe)


if __name__ == "__main__":
  asyncio.run(main())
