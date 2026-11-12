#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
dc=(docker compose -f labs/interview-backup/compose.yaml)
base=labs/interview-backup
mkdir -p "$base/artifacts"
"${dc[@]}" up -d --build
python3 "$base/wait_for_flink.py" \
  --url http://127.0.0.1:28081/jobs/overview --timeout 180
python3 - <<'PY'
from urllib.request import urlopen
import json,time
for _ in range(30):
    try:
        with urlopen("http://127.0.0.1:28765/api/health",timeout=4) as r:
            data=json.load(r)
        if data["ready"]:
            print("Backup dashboard health verified")
            break
    except Exception:
        pass
    time.sleep(2)
else:
    raise SystemExit("Backup dashboard not healthy")
PY
check_case() {
  local scenario="$1" expectation="$2" expected_rule="${3:-}" result run_id
  echo "BACKUP_E2E: $scenario -> $expectation"
  result=$("${dc[@]}" run --rm streaming-tools python /app/producer.py --scenario "$scenario")
  echo "$result"
  run_id=$(printf '%s\n' "$result" | sed -n 's/^RUN_ID=//p' | tail -1 | tr -d '\r')
  [[ -n "$run_id" ]] || { echo "Producer returned no RUN_ID" >&2; exit 1; }
  local args=(--run-id "$run_id" --expect "$expectation" --wait-seconds 45
              --settle-seconds 2 --output "/artifacts/${scenario}.json")
  [[ -z "$expected_rule" ]] || args+=(--require-rule "$expected_rule")
  "${dc[@]}" run --rm streaming-tools python /app/check.py "${args[@]}"
  python3 - "$run_id" <<'PY'
import json,sys
from urllib.request import urlopen
from urllib.parse import quote
with urlopen("http://127.0.0.1:28765/api/run?run_id="+quote(sys.argv[1]),timeout=10) as r:
    obj=json.load(r)
assert obj["run_id"]==sys.argv[1]
assert obj["result"]["status"] in ("PASS","FAIL")
assert len(obj["events"])>=6
print("Dashboard displays evidence for",sys.argv[1])
PY
}
check_case clean PASS
check_case replay PASS
check_case out_of_order PASS
check_case missing FAIL missing_event
check_case conflict FAIL conflict_same_version
check_case corrupt FAIL payload_mismatch
pending="pending-${GITHUB_RUN_ID:-local}-$$"
"${dc[@]}" run --rm streaming-tools python -c "
from producer import build_events,register_source
run_id='$pending'
events,_=build_events(run_id,'clean')
register_source(run_id,'clean',events)
print('PENDING_RUN='+run_id)
"
"${dc[@]}" run --rm streaming-tools python /app/check.py \
  --run-id "$pending" --expect INDETERMINATE \
  --require-rule publication_incomplete --wait-seconds 0 \
  --output "/artifacts/pending.json"
python3 "$base/offline_demo.py"
echo "BACKUP_E2E_COMPLETE: six live scenarios + unsealed source + offline fallback"
