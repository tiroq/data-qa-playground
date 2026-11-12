#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
dc=(docker compose -f compose.yaml -f labs/unified/compose.streaming.yaml --profile clickhouse --profile streaming)

mkdir -p labs/unified/artifacts
echo "[unified] starting isolated streaming stack"
"${dc[@]}" up -d --build
if ! python3 labs/unified/wait_for_flink.py --timeout 120; then
  echo "[unified] Flink SQL submit diagnostics" >&2
  "${dc[@]}" ps -a
  "${dc[@]}" logs --no-color --tail=160 flink-sql-submit flink-jobmanager
  exit 1
fi

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

echo "[unified] scenario=unsealed_source expected=INDETERMINATE"
unsealed_output=$("${dc[@]}" run --rm streaming-tools python /app/producer.py --scenario clean --manifest-only)
unsealed_run_id=$(printf '%s\n' "$unsealed_output" | sed -n 's/^RUN_ID=//p' | tail -1 | tr -d '\r')
[[ -n "$unsealed_run_id" ]] || { echo "Missing unsealed source RUN_ID" >&2; exit 1; }
"${dc[@]}" run --rm streaming-tools python /app/check.py --run-id "$unsealed_run_id" \
  --expect INDETERMINATE --require-rule source_batch_unsealed \
  --wait-seconds 1 --output /artifacts/unsealed_source.json

echo "[unified] all six streaming scenarios + unsealed-source negative control checked"
