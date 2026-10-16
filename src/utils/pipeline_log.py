"""
Operational log of pipeline runs in BigQuery (dataset `re_meta`), written by
src/orchestrator/run_pipeline.py.

Two append-only tables (load jobs, not DML/streaming: works on the free tier and has no
streaming-buffer lock):

    re_meta.pipeline_runs       2 rows per run: event='start' (status=running) and event='end'
                                (status=success|failed|interrupted). A run with no 'end' row
                                was killed hard (power loss, SIGKILL) -- vw_pipeline_runs shows it as
                                'running'/'unfinished'.
    re_meta.pipeline_step_runs  1 row per executed step, written when the step ends.

    re_meta.vw_pipeline_runs    1 row per run: latest status joined with step stats.

Logging must never break the pipeline: every public function swallows and warns on error.
"""

import json
import logging
import os
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from google.cloud import bigquery

from src.utils.gcp_conn import get_bigquery_client

logger = logging.getLogger(__name__)

META_DATASET = "re_meta"
# Reference dataset the new one is colocated with (BigQuery requires same location for
# joins between datasets, and dbt/Looker read re_bronze/re_silver).
LOCATION_REFERENCE_DATASET = "re_bronze"

RUNS_SCHEMA = [
    bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("event", "STRING", mode="REQUIRED", description="start | end"),
    bigquery.SchemaField("event_ts", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("status", "STRING", description="running | success | failed | interrupted"),
    bigquery.SchemaField("trigger", "STRING", description="launchd | manual (env PIPELINE_TRIGGER)"),
    bigquery.SchemaField("host", "STRING"),
    bigquery.SchemaField("git_commit", "STRING"),
    bigquery.SchemaField("failed_step", "STRING", description="First fatal step that failed (end event)"),
    bigquery.SchemaField("steps_total", "INT64"),
    bigquery.SchemaField("steps_failed", "INT64", description="Includes non-fatal failures"),
    bigquery.SchemaField("duration_s", "FLOAT64"),
]

STEP_RUNS_SCHEMA = [
    bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("step_order", "INT64"),
    bigquery.SchemaField("step_name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("fatal", "BOOL"),
    bigquery.SchemaField("status", "STRING", description="success | failed"),
    bigquery.SchemaField("exit_code", "INT64"),
    bigquery.SchemaField("started_at", "TIMESTAMP"),
    bigquery.SchemaField("ended_at", "TIMESTAMP"),
    bigquery.SchemaField("duration_s", "FLOAT64"),
    bigquery.SchemaField("rows_loaded", "INT64", description="Rows appended to bronze by the step (scrapers only)"),
    bigquery.SchemaField("error_tail", "STRING", description="Last output lines of a failed step"),
]

_client = None
_disabled = False


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def git_commit() -> str | None:
    try:
        root = Path(__file__).resolve().parents[2]
        return (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            or None
        )
    except Exception:
        return None


def run_context() -> dict:
    return {
        "trigger": os.environ.get("PIPELINE_TRIGGER", "manual"),
        "host": socket.gethostname(),
        "git_commit": git_commit(),
    }


def _get_client():
    global _client, _disabled
    if _disabled:
        return None
    if _client is None:
        try:
            _client = get_bigquery_client()
            ensure_schema(_client)
        except Exception as e:
            _disabled = True
            logger.warning(f"pipeline_log disabled, cannot reach BigQuery meta schema: {e}")
            return None
    return _client


def ensure_schema(client) -> None:
    """Idempotent: create dataset, tables and view if missing."""
    location = client.get_dataset(f"{client.project}.{LOCATION_REFERENCE_DATASET}").location
    dataset = bigquery.Dataset(f"{client.project}.{META_DATASET}")
    dataset.location = location
    dataset = client.create_dataset(dataset, exists_ok=True)

    for name, schema in (("pipeline_runs", RUNS_SCHEMA), ("pipeline_step_runs", STEP_RUNS_SCHEMA)):
        client.create_table(bigquery.Table(f"{client.project}.{META_DATASET}.{name}", schema=schema), exists_ok=True)

    view = bigquery.Table(f"{client.project}.{META_DATASET}.vw_pipeline_runs")
    view.view_query = f"""
        WITH runs AS (
          SELECT
            run_id,
            MIN(IF(event = 'start', event_ts, NULL)) AS started_at,
            MAX(IF(event = 'end', event_ts, NULL)) AS ended_at,
            ARRAY_AGG(IF(event = 'start', trigger, NULL) IGNORE NULLS LIMIT 1)[SAFE_OFFSET(0)] AS trigger,
            ARRAY_AGG(IF(event = 'start', git_commit, NULL) IGNORE NULLS LIMIT 1)[SAFE_OFFSET(0)] AS git_commit,
            ARRAY_AGG(IF(event = 'end', status, NULL) IGNORE NULLS LIMIT 1)[SAFE_OFFSET(0)] AS end_status,
            ARRAY_AGG(IF(event = 'end', failed_step, NULL) IGNORE NULLS LIMIT 1)[SAFE_OFFSET(0)] AS failed_step
          FROM `{client.project}.{META_DATASET}.pipeline_runs`
          GROUP BY run_id
        ),
        steps AS (
          SELECT
            run_id,
            COUNT(*) AS steps_run,
            COUNTIF(status = 'failed') AS steps_failed,
            SUM(rows_loaded) AS rows_loaded
          FROM `{client.project}.{META_DATASET}.pipeline_step_runs`
          GROUP BY run_id
        )
        SELECT
          r.run_id, r.started_at, r.ended_at, r.trigger, r.git_commit,
          COALESCE(r.end_status, 'unfinished') AS status,
          r.failed_step,
          TIMESTAMP_DIFF(r.ended_at, r.started_at, SECOND) AS duration_s,
          s.steps_run, s.steps_failed, s.rows_loaded
        FROM runs r
        LEFT JOIN steps s USING (run_id)
    """
    client.create_table(view, exists_ok=True)


def _insert(table: str, rows: list[dict]) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        job = client.load_table_from_json(
            json.loads(json.dumps(rows, default=lambda o: o.isoformat() if isinstance(o, datetime) else str(o))),
            f"{client.project}.{META_DATASET}.{table}",
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND"),
        )
        job.result()
    except Exception as e:
        logger.warning(f"pipeline_log: failed to write {table}: {e}")


def log_run_event(run_id: str, event: str, **fields) -> None:
    _insert("pipeline_runs", [{"run_id": run_id, "event": event, "event_ts": now_utc(), **fields}])


def log_step(run_id: str, **fields) -> None:
    _insert("pipeline_step_runs", [{"run_id": run_id, **fields}])
