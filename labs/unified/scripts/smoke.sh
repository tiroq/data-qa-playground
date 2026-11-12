#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
dc=(docker compose -f compose.yaml -f labs/unified/compose.streaming.yaml --profile clickhouse --profile streaming)

mkdir -p labs/unified/artifacts
echo "[unified] starting isolated streaming stack"
"${dc[@]}" up -d --build
python3 labs/unified/wait_for_flink.py --timeout 180

run_case() {
  local scenario="$1" expected="$2" rule="${3:-}"
  echo "[unified] scenario=$scenario expected=$expected"
  local output run_id
  output=$("${dc[@]}" run --rm streaming-tools python /app/producer.py --scenario "$scenario")
  echo "$output"
  run_id=$(printf '%s\n' "$output" | sed -n 's/^RUN_ID=//p' | tail -1 | tr -d '\r')
  if [[ -z "$run_id" ]]; then
    echo "[unified] producer returned no run ID" >&2
    exit 1
  fi
  args=(--run-id "$run_id" --expect "$expected" --wait-seconds 45
        --settle-seconds 3 --output "/artifacts/${scenario}.json")
  if [[ -n "$rule" ]]; then
    args+=(--require-rule "$rule")
  fi
  "${dc[@]}" run --rm streaming-tools python /app/check.py "${args[@]}"
}

run_case clean PASS
run_case replay PASS
run_case out_of_order PASS
run_case missing FAIL missing_event
run_case conflict FAIL conflict_same_version
run_case corrupt FAIL payload_mismatch
echo "[unified] all six synthetic positive/negative scenarios checked"
