#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
BASE=labs/interview-backup
DC=(docker compose -f "$BASE/compose.yaml")
usage() {
cat <<'HELP'
Interview Backup Lab (independent Docker project and isolated host ports)
  bash labs/interview-backup/scripts/run.sh up
  bash labs/interview-backup/scripts/run.sh demo
  bash labs/interview-backup/scripts/run.sh seed <clean|replay|out_of_order|missing|conflict|corrupt>
  bash labs/interview-backup/scripts/run.sh check <RUN_ID> [PASS|FAIL|INDETERMINATE] [required_rule]
  bash labs/interview-backup/scripts/run.sh pause-sink
  bash labs/interview-backup/scripts/run.sh resume-sink
  bash labs/interview-backup/scripts/run.sh status
  bash labs/interview-backup/scripts/run.sh down
  bash labs/interview-backup/scripts/run.sh offline

Live Dashboard: http://127.0.0.1:28765 | Flink: http://127.0.0.1:28081
All data is synthetic. 'offline' needs only Python 3.12; other commands use Docker.
'down' retains volumes and never removes the main laboratory's data.
HELP
}
case "${1:-}" in
  up)
    "${DC[@]}" up -d --build
    python3 "$BASE/wait_for_flink.py" \
      --url http://127.0.0.1:28081/jobs/overview --timeout 180
    python3 - <<'PY'
import json,time
from urllib.request import urlopen
deadline=time.monotonic()+60
while time.monotonic()<deadline:
    try:
        with urlopen("http://127.0.0.1:28765/api/health",timeout=4) as r:
            status=json.load(r)
        if status.get("ready"):
            print("BACKUP_READY: Dashboard http://127.0.0.1:28765")
            break
    except Exception:
        pass
    time.sleep(2)
else:
    raise SystemExit("Backup dashboard did not become ready")
PY
    ;;
  demo)
    bash "$BASE/scripts/smoke.sh"
    ;;
  seed)
    shift
    "${DC[@]}" run --rm streaming-tools python /app/producer.py --scenario "${1:-clean}"
    ;;
  check)
    shift
    run_id="${1:?Pass RUN_ID as the first argument}"
    expected="${2:-PASS}"
    extra=()
    if [[ -n "${3:-}" ]]; then extra=(--require-rule "$3"); fi
    "${DC[@]}" run --rm streaming-tools python /app/check.py \
      --run-id "$run_id" --expect "$expected" --wait-seconds 45 "${extra[@]}"
    ;;
  pause-sink)
    "${DC[@]}" stop streaming-sink
    echo "Sink stopped. Source, Kafka and ClickHouse remain unchanged."
    ;;
  resume-sink)
    "${DC[@]}" up -d streaming-sink
    echo "Sink resumed. Check a particular run ID to verify observed evidence."
    ;;
  status)
    "${DC[@]}" ps -a
    python3 "$BASE/wait_for_flink.py" \
      --url http://127.0.0.1:28081/jobs/overview --timeout 3 || true
    ;;
  down)
    "${DC[@]}" down
    echo "Interview backup stopped. Volumes retained."
    ;;
  offline)
    python3 "$BASE/offline_demo.py"
    ;;
  *)
    usage
    exit 1
    ;;
esac
