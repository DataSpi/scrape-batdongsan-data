"""
One-off enrichment script: geocode every legacy district (v1) and active ward (v2)
into lat/lng, writing the result to dbt seed CSVs that stg_locations_v1/v2 join in.

Not part of the weekly cron pipeline -- districts/wards are near-static reference
data (see src/orchestrator/run_pipeline.py docstring), so this only needs re-running
when new districts/wards show up (e.g. a future administrative reform, like the one
that produced the "v2" address scheme).

Usage:
    python -m src._geocode.geocode_locations

Requires GOOGLE_MAPS_API_KEY in .env, scoped to the Geocoding API only. The Geocoding
API only accepts an API key -- it does not accept the GCP service account credentials
used elsewhere in this repo (utils/gcp_conn.py), so this is a separate credential.
"""
import csv
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.utils.common_tools import setup_logging
from src.utils.gcp_conn import get_bigquery_client, query_to_df

load_dotenv()
logger = setup_logging()

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
REQUEST_DELAY_SECONDS = 0.1

SEEDS_DIR = Path(__file__).resolve().parents[2] / "dbt" / "seeds"


def geocode(address: str, api_key: str) -> tuple[float, float] | None:
    resp = requests.get(GEOCODE_URL, params={"address": address, "key": api_key}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK" or not data.get("results"):
        logger.warning(f"No geocode result for '{address}': {data.get('status')}")
        return None
    location = data["results"][0]["geometry"]["location"]
    return location["lat"], location["lng"]


def geocode_rows(rows: list[dict], id_col: str, label_col: str, api_key: str) -> list[dict]:
    out = []
    for row in rows:
        address = f"{row[label_col]}, Việt Nam"
        result = geocode(address, api_key)
        out.append({
            id_col: row[id_col],
            "lat": result[0] if result else "",
            "lng": result[1] if result else "",
        })
        time.sleep(REQUEST_DELAY_SECONDS)
    return out


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    resolved = sum(1 for r in rows if r["lat"] != "")
    logger.info(f"Wrote {path} ({resolved}/{len(rows)} resolved)")


def main() -> None:
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_MAPS_API_KEY not set in .env")

    client = get_bigquery_client()

    districts = query_to_df(client, """--sql
        select d.districtId, concat(d.name, ', ', c.name) as label
        from re_bronze.m_districts d
        left join re_bronze.m_cities c on d.cityCode = c.code
    """).to_dict(orient="records")
    logger.info(f"Geocoding {len(districts)} v1 districts...")
    district_geo = geocode_rows(districts, "districtId", "label", api_key)
    write_csv(SEEDS_DIR / "district_geo_v1.csv", district_geo, ["districtId", "lat", "lng"])

    wards = query_to_df(client, """--sql
        select w.wardId, concat(w.name, ', ', c.name) as label
        from re_bronze.m_wards_v2 w
        left join re_bronze.m_cities_v2 c on w.cityCode = c.code
    """).to_dict(orient="records")
    logger.info(f"Geocoding {len(wards)} v2 wards...")
    ward_geo = geocode_rows(wards, "wardId", "label", api_key)
    write_csv(SEEDS_DIR / "ward_geo_v2.csv", ward_geo, ["wardId", "lat", "lng"])

    logger.info(
        "Done. Run `dbt seed` then "
        "`dbt run --select stg_locations_v1+ stg_locations_v2+ stg_projects+` "
        "to rebuild location lineage with the new coordinates."
    )


if __name__ == "__main__":
    main()
