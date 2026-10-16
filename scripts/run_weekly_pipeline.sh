#!/bin/bash
# Weekly launchd entrypoint for the scrape -> dbt pipeline. Triggered by
# ~/Library/LaunchAgents/com.dataspi.batdongsan-weekly.plist (installed from
# scripts/com.dataspi.batdongsan-weekly.plist) -- see docs/quickstart.md for setup.
#
# run_pipeline.py's own logging only goes to stdout (see setup_logging() in
# src/utils/common_tools.py); launchd doesn't capture that on its own, so this script
# redirects to a timestamped file under logs/ (gitignored) for after-the-fact debugging.
#
# caffeinate -i keeps the machine awake for the run's duration -- a multi-step scrape +
# dbt run can take long enough that a laptop going to sleep mid-run would stall it.
set -euo pipefail

# launchd runs with a minimal environment (no shell profile sourced, no PATH set up
# like an interactive login shell), so this script hardcodes the conda env's own
# python binary directly instead of relying on `conda activate`/PATH lookup.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_ENV_BIN="/Users/spinokiem/miniconda3/envs/scrape_bds/bin"
# run_pipeline.py also shells out to `dbt` by bare name (see its STEPS list), so PATH
# needs the env's bin dir too, not just an absolute python path.
export PATH="$CONDA_ENV_BIN:$PATH"

mkdir -p "$PROJECT_ROOT/logs"
LOG_FILE="$PROJECT_ROOT/logs/pipeline_$(date +%Y%m%d_%H%M%S).log"

cd "$PROJECT_ROOT"

# Observability: only pull the two notification vars out of .env (not `source`-ing the whole
# file, whose other values may contain characters bash would misparse). Both are optional --
# empty/missing means that channel is silently disabled (e.g. on a dev machine).
env_var() { grep -E "^$1=" "$PROJECT_ROOT/.env" 2>/dev/null | tail -1 | cut -d= -f2- | sed -E "s/^['\"]|['\"]$//g"; }
HEALTHCHECK_URL="$(env_var HEALTHCHECK_URL)"
SLACK_WEBHOOK_URL="$(env_var SLACK_WEBHOOK_URL)"

# Ping failures must never change the pipeline's exit status or abort it -- WARN to the log only.
hc_ping() {  # $1 = "" (success) | "start" | exit code
  [ -n "$HEALTHCHECK_URL" ] || return 0
  curl -fsS -m 10 --retry 3 -o /dev/null "${HEALTHCHECK_URL%/}${1:+/$1}" >> "$LOG_FILE" 2>&1 \
    || echo "WARN: healthcheck ping '${1:-ok}' failed" >> "$LOG_FILE"
}
slack() {  # $1 = message text
  [ -n "$SLACK_WEBHOOK_URL" ] || return 0
  PAYLOAD="$(python3 -c 'import json,sys; print(json.dumps({"text": sys.argv[1]}))' "$1")"
  curl -fsS -m 10 --retry 3 -o /dev/null -H 'Content-Type: application/json' -d "$PAYLOAD" \
    "$SLACK_WEBHOOK_URL" >> "$LOG_FILE" 2>&1 || echo "WARN: slack post failed" >> "$LOG_FILE"
}

STATUS=0
FINISHED=0
finish() {
  # Called right after the pipeline step (so the ping/alert isn't delayed by the slow edr
  # report below) and again from the EXIT trap as a safety net for early/abnormal exits.
  [ "$FINISHED" -eq 0 ] || return 0
  FINISHED=1
  local rc=$STATUS
  [ "$rc" -eq 0 ] && [ "${1:-0}" -ne 0 ] && rc=$1
  hc_ping "$rc"
  if [ "$rc" -eq 0 ]; then
    slack ":white_check_mark: batdongsan weekly pipeline OK ($(date '+%d/%m %H:%M'))"
  else
    local failed
    failed="$(grep -o 'Pipeline stopped at step: .*' "$LOG_FILE" | tail -1 || true)"
    slack ":x: batdongsan weekly pipeline FAILED (exit $rc). ${failed:-no step info (killed/crashed?)} -- log: $LOG_FILE"
  fi
}
trap 'finish $?' EXIT
trap 'exit 143' TERM INT

hc_ping start

# Not `exec`: we need to keep running afterwards to archive dbt's raw run artifacts.
# Elementary already stores run/test history in BigQuery (re_elementary); this local copy
# of run_results.json/manifest.json is a safety net independent of the warehouse, since
# dbt/target/ is overwritten by the next run.
PIPELINE_TRIGGER=launchd caffeinate -i "$CONDA_ENV_BIN/python" -m src.orchestrator.run_pipeline >> "$LOG_FILE" 2>&1 || STATUS=$?

finish 0

ARTIFACT_DIR="$PROJECT_ROOT/logs/dbt_artifacts/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARTIFACT_DIR"
cp "$PROJECT_ROOT"/dbt/target/run_results.json "$PROJECT_ROOT"/dbt/target/manifest.json "$ARTIFACT_DIR"/ 2>/dev/null || true

# Elementary HTML report (needs `pip install elementary-data[bigquery]` and an `elementary`
# profile -- see dbt/profiles.yml.example). Best-effort: never fails the weekly run.
# perl alarm = 15 min cap: macOS has no `timeout`, and edr hung for days once, which kept the
# launchd job "running" and blocked every later scheduled run.
perl -e 'alarm shift; exec @ARGV' 900 "$CONDA_ENV_BIN/edr" report --project-dir "$PROJECT_ROOT/dbt" --profiles-dir "$PROJECT_ROOT/dbt" \
  --file-path "$PROJECT_ROOT/logs/elementary_report.html" --open-browser false >> "$LOG_FILE" 2>&1 || true

exit "$STATUS"  # EXIT trap -> finish() sends the ping/alert with this status
