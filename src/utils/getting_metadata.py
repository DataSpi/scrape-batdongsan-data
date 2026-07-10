"""Utilities for fetching database metadata."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from sqlalchemy import text

from utils.sqlalchemy_conn import dbConnector


def get_table_column_names(schema_name: str, table_name: str) -> List[str]:
	"""Return ordered column names for a given schema/table from PostgreSQL."""
	query = text(
		"""
		SELECT column_name
		FROM information_schema.columns
		WHERE table_schema = :schema_name
		  AND table_name = :table_name
		ORDER BY ordinal_position
		"""
	)

	engine = dbConnector.spyno_sb_conn()
	with engine.connect() as conn:
		rows = conn.execute(
			query,
			{"schema_name": schema_name, "table_name": table_name},
		).fetchall()

	return [row[0] for row in rows]


def parse_cli_args() -> tuple[str, str]:
	parser = argparse.ArgumentParser(
		description="Get column names for a table from database",
		epilog=(
			"Examples:\n"
			"  python utils/getting_metadata.py re_broze m_wards\n"
			"  python utils/getting_metadata.py --schema_name re_broze --table_name m_wards\n"
			"  python utils/getting_metadata.py schema_name=re_broze table_name=m_wards"
		),
		formatter_class=argparse.RawTextHelpFormatter,
	)
	parser.add_argument("schema_name", nargs="?", help="Schema name, e.g. public")
	parser.add_argument("table_name", nargs="?", help="Table name")
	parser.add_argument("--schema_name", dest="schema_name_opt", help="Schema name")
	parser.add_argument("--table_name", dest="table_name_opt", help="Table name")

	args, unknown_args = parser.parse_known_args()
	key_value_args = {}
	for item in unknown_args:
		if "=" not in item:
			parser.error(f"Unrecognized argument: {item}")
		key, value = item.split("=", 1)
		key = key.strip().lstrip("-")
		key_value_args[key] = value.strip()

	schema_name = args.schema_name_opt or args.schema_name or key_value_args.get("schema_name")
	table_name = args.table_name_opt or args.table_name or key_value_args.get("table_name")

	if not schema_name or not table_name:
		parser.error(
			"Missing required values. Provide schema/table using positional args, "
			"--schema_name/--table_name, or schema_name=... table_name=..."
		)

	return schema_name, table_name


def main() -> None:
	schema_name, table_name = parse_cli_args()

	columns = get_table_column_names(schema_name, table_name)
	if not columns:
		print(f"No columns found for {schema_name}.{table_name}")
		return

	output_dir = Path(__file__).resolve().parents[1] / "data" / "tmp"
	output_dir.mkdir(parents=True, exist_ok=True)
	output_file = output_dir / f"{schema_name}_{table_name}_columns.csv"
	output_file.write_text("\n".join(columns), encoding="utf-8")

	print(f"Saved {len(columns)} columns to {output_file}")


if __name__ == "__main__":
	main()
