#!/usr/bin/env bash
# Unified Data QA teaching environment; never use against production clusters.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
DC=(docker compose -f compose.yaml -f compose.streaming.yaml --profile clickhouse --profile streaming)
OUTPUT_DIR="$ROOT/.streaming-runs"

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/streaming_lab.sh up
  bash scripts/streaming_lab.sh seed <healthy|duplicate|missing|corrupt|out_of_order|conflict|extra> [run_id]
  bash scripts/streaming_lab.sh gate <run_id> [expected_failure_rule]
  bash scripts/streaming_lab.sh status
  bash scripts/streaming_lab.sh down

Run IDs: ASCII letters, digits, _ or -, length 1..48. Generated run IDs and
reports are written under .streaming-runs/ (gitignored). 'down' preserves volumes.
No command drops the existing Session 01/02/03/04 databases.
USAGE
}

run_id_check() {
  [[ "$1" =~ ^[a-zA-Z0-9_-]{1,48}$ ]] || {
    echo "Invalid run_id: allowed [A-Za-z0-9_-], max 48 chars" >&2
    exit 4
  }
}

wait_flink() {
  local i
  for ((i=1; i<=45; i++)); do
    if curl --silent --fail http://127.0.0.1:18081/overview >/dev/null; then
      return 0
    fi
    sleep 2
  done
  echo "Flink REST endpoint did not start. Check docker compose logs flink-jobmanager" >&2
  return 1
}

running_flink_jobs() {
  curl --silent --fail http://127.0.0.1:18081/jobs/overview |
    python3 -c 'import json,sys; j=json.load(sys.stdin); print(sum(
      x.get("state")=="RUNNING" and x.get("name")=="trading-versioned-events-lab"
      for x in j.get("jobs", [])))'
}

up() {
  "${DC[@]}" up -d --build --wait postgres clickhouse kafka flink-jobmanager flink-taskmanager

  # Explicitly create both topics: no auto-create and no implicit partition count.
  "${DC[@]}" exec -T kafka /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server kafka:9092 --create --if-not-exists \
    --topic trades-input --partitions 2 --replication-factor 1
  "${DC[@]}" exec -T kafka /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server kafka:9092 --create --if-not-exists \
    --topic trade-processed --partitions 2 --replication-factor 1

  "${DC[@]}" exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1 \
    < streaming/sql/postgres.sql
  "${DC[@]}" exec -T clickhouse clickhouse-client --user qa --password qa --multiquery \
    < streaming/sql/clickhouse.sql
  wait_flink
  if [[ "$(running_flink_jobs)" == "0" ]]; then
    "${DC[@]}" exec -T flink-jobmanager \
      /opt/flink/bin/sql-client.sh -f /opt/flink/jobs/trading.sql
  else
    echo "Existing trading-versioned-events-lab Flink job is already RUNNING."
  fi
  echo "Streaming lab started. Flink UI: http://127.0.0.1:18081"
}

seed() {
  local scenario="${1:-healthy}" run_id="${2:-lab-$(date +%s)-$$}"
  run_id_check "$run_id"
  mkdir -p "$OUTPUT_DIR/$run_id"
  python3 -m streaming_lab.fixtures --run-id "$run_id" \
    --scenario "$scenario" --output-dir "$OUTPUT_DIR/$run_id"

  # The authoritative manifest exists before Kafka submission.
  "${DC[@]}" exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1 \
    < "$OUTPUT_DIR/$run_id/manifest.sql"

  # Kafka console producer uses account_id:trade_id as the partition key.
  "${DC[@]}" exec -T kafka /opt/kafka/bin/kafka-console-producer.sh \
    --bootstrap-server kafka:9092 --topic trades-input \
    --property parse.key=true --property 'key.separator=|' \
    < "$OUTPUT_DIR/$run_id/kafka-input.txt"

  # A failed producer command leaves sealed=FALSE: the DQ gate is INDETERMINATE.
  "${DC[@]}" exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1 \
    < "$OUTPUT_DIR/$run_id/seal.sql"
  echo "Seeded run $run_id; now: bash scripts/streaming_lab.sh gate $run_id"
}

snapshot() {
  local run_id="$1" dest="$OUTPUT_DIR/$1"
  run_id_check "$run_id"
  mkdir -p "$dest"
  "${DC[@]}" exec -T postgres psql -U qa -d trading -A -t \
    -v ON_ERROR_STOP=1 -c \
    "SELECT row_to_json(t) FROM (SELECT run_id,scenario,planned_events,sealed FROM labstream.runs WHERE run_id='$run_id') t;" \
    > "$dest/manifest.jsonl"
  "${DC[@]}" exec -T postgres psql -U qa -d trading -A -t \
    -v ON_ERROR_STOP=1 -c \
    "SELECT row_to_json(t) FROM (SELECT run_id,event_id,trade_id,account_id,version,pnl,status,event_time_ms FROM labstream.expected_events WHERE run_id='$run_id' ORDER BY event_id) t;" \
    > "$dest/source.jsonl"
  "${DC[@]}" exec -T clickhouse clickhouse-client --user qa --password qa --query \
    "SELECT run_id,event_id,trade_id,account_id,version,pnl,status,event_time_ms,toString(available_at,'UTC') AS available_at FROM labstream.raw_events WHERE run_id='$run_id' FORMAT JSONEachRow" \
    > "$dest/target.jsonl"
}

gate() {
  local run_id="${1:-}" expected_rule="${2:-}" dest n delivered=0 i rc
  run_id_check "$run_id"
  dest="$OUTPUT_DIR/$run_id"
  if [[ ! -s "$dest/events.jsonl" ]]; then
    echo "No local published-event fixture. Run 'seed' first." >&2
    exit 4
  fi
  n="$(wc -l < "$dest/events.jsonl" | tr -d ' ')"
  # Wait for evidence of sink visibility, never infer delivery from Kafka lag=0.
  for ((i=1; i<=45; i++)); do
    snapshot "$run_id"
    delivered="$(wc -l < "$dest/target.jsonl" | tr -d ' ')"
    if (( delivered >= n )); then break; fi
    sleep 2
  done
  if (( delivered < n )); then
    echo "Timed out waiting for expected published physical rows (saw $delivered of $n)." >&2
    echo "Proceeding to independent DQ report; missing rows must not become PASS." >&2
  fi

  set +e
  python3 -m streaming_lab.gate --manifest "$dest/manifest.jsonl" \
    --expected "$dest/source.jsonl" --actual "$dest/target.jsonl" \
    --report "$dest/report.json"
  rc=$?
  set -e

  if [[ -n "$expected_rule" ]]; then
    if [[ "$rc" != "2" ]]; then
      echo "Expected a DQ FAIL with rule $expected_rule, observed exit=$rc" >&2
      exit 1
    fi
    python3 - "$dest/report.json" "$expected_rule" <<'PY'
import json
import sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
if sys.argv[2] not in [i["rule"] for i in report.get("issues", [])]:
    raise SystemExit(f"Expected negative-control rule {sys.argv[2]} was not raised")
print(f"Confirmed negative control: {sys.argv[2]}")
PY
  else
    return "$rc"
  fi
}

case "${1:-}" in
  up) up ;;
  seed) shift; seed "$@" ;;
  gate) shift; gate "$@" ;;
  status)
    "${DC[@]}" ps
    curl --silent --fail http://127.0.0.1:18081/jobs/overview || true
    ;;
  down) "${DC[@]}" down ;;
  *) usage; exit 1 ;;
esac
