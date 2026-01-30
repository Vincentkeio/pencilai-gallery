#!/usr/bin/env bash
set -euo pipefail

# PencilAI scripts helper (Open Source)
# - No hard-coded absolute paths.
# - Reads config from scripts/config.json.

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$BASE_DIR/main.py"
PID_FILE="$BASE_DIR/script.pid"
LOG_FILE="$BASE_DIR/run.log"

status() {
  if [[ -f "$PID_FILE" ]] && ps -p "$(cat "$PID_FILE")" >/dev/null 2>&1; then
    echo "running (PID $(cat "$PID_FILE"))"
  else
    echo "stopped"
  fi
}

case "${1:-}" in
  once)
    python3 -u "$PY_SCRIPT" once
    ;;
  daemon-start)
    if [[ -f "$PID_FILE" ]] && ps -p "$(cat "$PID_FILE")" >/dev/null 2>&1; then
      echo "Already running: $(status)"; exit 0
    fi
    nohup python3 -u "$PY_SCRIPT" daemon >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Started: $(status)"
    ;;
  daemon-stop)
    if [[ -f "$PID_FILE" ]]; then
      kill "$(cat "$PID_FILE")" 2>/dev/null || true
      rm -f "$PID_FILE"
    fi
    echo "Stopped: $(status)"
    ;;
  daemon-restart)
    "$0" daemon-stop
    "$0" daemon-start
    ;;
  status)
    echo "$(status)"
    ;;
  *)
    echo "Usage: $0 {once|daemon-start|daemon-stop|daemon-restart|status}";
    exit 1
    ;;
esac
