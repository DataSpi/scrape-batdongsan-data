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

exec caffeinate -i "$CONDA_ENV_BIN/python" -m src.orchestrator.run_pipeline >> "$LOG_FILE" 2>&1
