import argparse

from sqlalchemy import inspect

from utils.sqlalchemy_conn import dbConnector as db
from utils.gcp_conn import get_bigquery_client, upload_df_to_bigquery
from utils.common_tools import setup_logging

logger = setup_logging()

SCHEMAS = ["re_bronze", "re_silver"]


def ensure_dataset(bq_client, dataset_id):
    bq_client.create_dataset(dataset_id, exists_ok=True)


def get_tables(pg_engine, schema):
    return sorted(inspect(pg_engine).get_table_names(schema=schema))


def migrate_table(pg_conn, bq_client, schema, table):
    df = db.fetch_to_dataframe(pg_conn, f'SELECT * FROM "{schema}"."{table}"')
    if df.empty:
        logger.info(f"Skipping {schema}.{table}: table is empty")
        return 0

    table_id = f"{bq_client.project}.{schema}.{table}"
    rows = upload_df_to_bigquery(
        bq_client, df, table_id,
        write_disposition="WRITE_TRUNCATE",
        allow_field_addition=True,
    )
    logger.info(f"Migrated {rows} rows: {schema}.{table} -> {table_id}")
    return rows


def main(schemas: list[str], tables: list[str] | None = None):
    pg_conn = db.spyno_sb_conn()
    bq_client = get_bigquery_client()

    summary = []
    for schema in schemas:
        ensure_dataset(bq_client, schema)
        for table in get_tables(pg_conn, schema):
            if tables and table not in tables:
                continue
            try:
                rows = migrate_table(pg_conn, bq_client, schema, table)
                summary.append((schema, table, rows, None))
            except Exception as e:
                logger.error(f"Failed to migrate {schema}.{table}: {e}")
                summary.append((schema, table, None, str(e)))

    logger.info("=== Migration summary ===")
    for schema, table, rows, error in summary:
        status = f"ERROR: {error}" if error else f"{rows} rows"
        logger.info(f"  {schema}.{table}: {status}")
    return summary


def parse_args():
    parser = argparse.ArgumentParser(description="Migrate Supabase (Postgres) re_bronze/re_silver schemas to BigQuery datasets of the same name.")
    parser.add_argument("--schemas", nargs="+", default=SCHEMAS, help="Schemas to migrate. Default: %(default)s")
    parser.add_argument("--tables", nargs="+", default=None, help="Only migrate these table names (applies across all --schemas). Default: all tables.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(schemas=args.schemas, tables=args.tables)
