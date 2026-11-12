# Unified Data Stack Training Lab — Sessions 10–17

**Status:** CI evidence is required before declaring this stack runnable. See [unified GitHub Actions workflow](../../.github/workflows/unified-streaming-lab.yml) for actual test results. The original 2025 article was a **minimal Kafka/Flink/ClickHouse click-count demo**; this is our separate, synthetic trading-data QA implementation.

## Purpose

An optional, isolated but **real** Kafka → Flink SQL → Kafka → Python ClickHouse sink path, anchored by an independent PostgreSQL expected-event manifest. Source manifests are committed before Kafka publish and marked `sealed` only after Kafka delivery callbacks succeed; this is deliberately NOT an atomic cross-system write. The sink commits Kafka offsets only after ClickHouse acknowledges the insert, but these two actions are NOT atomic: replay may duplicate physical deliveries. Business correctness is assessed separately.

```text
source-event fixture -> PostgreSQL streaming_lab.source_events (manifest)
                   \-> Kafka trade-events (2 partitions)
                       -> Flink SQL (1.20.3, connector 3.4.0-1.20)
                       -> Kafka processed-trades (at-least-once)
                       -> Python sink (manual offset commit)
                       -> ClickHouse streaming_lab.raw_events (append-only)
PostgreSQL manifest + ClickHouse raw -> check.py (PASS / FAIL / INDETERMINATE / ERROR + JSON report)
```

### Source manifest contract

One run has an independent `run_id` (generated each time), six source event IDs with three or more business keys, source-side versions and Decimal-as-string PnL. A `conflict` scenario adds a seventh source event with same trade/version but contradictory PnL. `event_id` is immutable *within a run*; `(trade_id,account_id)` is the business key; PnL is a **snapshot** of trade state, not a delta.

`clean`, `replay`, `missing`, `conflict`, `out_of_order` and `corrupt` scenarios are declarative synthetic failures. No customer data, no real Exness schemas.

## Start the optional stack

Requirements: Docker Engine/Desktop with Compose v2, internet access to fetch images and a pinned official Flink Kafka SQL JAR, memory available for multiple JVM services, and Python 3 on the host to inspect the Flink REST API.

From repository root:

```bash
docker compose -f compose.yaml -f labs/unified/compose.streaming.yaml \
  --profile clickhouse --profile streaming up -d --build
python3 labs/unified/wait_for_flink.py
```

- Flink UI: http://localhost:18081
- ClickHouse HTTP: http://localhost:18123
- Kafka host listener: localhost:19092
- PostgreSQL: localhost:5433
- All published ports bind to local loopback; demo `qa/qa` credentials and plaintext Kafka are **not production safe**.
- The existing PostgreSQL volume and historical lab schemas are not reset by these commands. New schemas `streaming_lab` live separately in PostgreSQL and ClickHouse.

## Run scenarios

```bash
DC='docker compose -f compose.yaml -f labs/unified/compose.streaming.yaml --profile clickhouse --profile streaming'

# Example: run the producer; copy printed RUN_ID.
$DC run --rm streaming-tools python /app/producer.py --scenario clean

# Replace RUN_ID with the printed identifier; the check produces JSON evidence.
$DC run --rm streaming-tools python /app/check.py --run-id RUN_ID \
  --expect PASS --wait-seconds 60

# Six positive and negative cases; output files in labs/unified/artifacts.
bash labs/unified/scripts/smoke.sh
```

### Negative scenario expectation

| Scenario | Effect | Gate |
|---|---|---|
| clean | All expected IDs and payloads appear | PASS |
| replay | Extra physical Kafka delivery, same logical event ID/payload | PASS with duplicate diagnostic |
| out_of_order | Older version observed after newer | PASS (raw history preserved) |
| missing | Event E03 in source manifest not published | FAIL: `missing_event` |
| conflict | Distinct event E07 contradicts trade T100/version 2 | FAIL: `conflict_same_version` |
| corrupt | Kafka contains changed PnL versus PostgreSQL | FAIL: `payload_mismatch` |
| unsealed_source | Manifest exists but producer is stopped before Kafka publish | INDETERMINATE: `source_batch_unsealed` |

Run-specific JSON reports include expected/observed unique IDs, physical delivery count, duplicate count and independent DQ issues. `--expect FAIL --require-rule <code>` prevents an infrastructure error from looking like a passing negative control.

## Teardown and data safety

```bash
# Stop containers WITHOUT removing any volumes:
docker compose -f compose.yaml -f labs/unified/compose.streaming.yaml \
  --profile clickhouse --profile streaming down

# DESTRUCTIVE: removes ALL volumes in this combined Compose project,
# including original PostgreSQL and ClickHouse lab volumes. CI ONLY / disposable clones:
docker compose -f compose.yaml -f labs/unified/compose.streaming.yaml \
  --profile clickhouse --profile streaming down -v
```

To reset only Kafka/streaming-specific persisted state, use a separate Compose project on a fresh clone, rather than casually using `down -v` against an existing historical lab.

## Checks and limitations

- `python3 -m unittest discover -s labs/unified/tests` verifies pure DQ logic **without Docker**.
- GitHub Actions [unified-streaming-lab.yml](../../.github/workflows/unified-streaming-lab.yml) is the integration gate, using disposable CI volumes.
- `check.py` compares currently persisted ClickHouse rows against the independent PostgreSQL source manifest. It waits a bounded time for eligible IDs and checks a short stability window. **A green snapshot is not a formal sink-side completion barrier**: late conflicting events could still appear. Producer flush only acknowledges Kafka publish, not ClickHouse durability.
- Flink SQL writes a JSON Kafka key for `(run_id,account_id,trade_id)`. The DQ gate detects cross-partition versions of one trade; incoming and outgoing partition numbers need not match.
- Kafka producer completion (`sealed`) is not a sink completion barrier; an unsealed source batch is `INDETERMINATE`, not downstream data loss.
- Flink SQL runs with at-least-once Kafka output. The Python sink has no Kafka/ClickHouse cross-system transaction; replay duplicates can occur.
- No transactional CDC from PostgreSQL, no production-grade schema registry, Flink HA, DLQ, TLS, multi-node recovery or true exactly-once effect is implemented.
- Current SQL processing projects raw fields; account aggregates, time windows, Flink watermarks and MV/backfill policies are **learner exercises**, not completed by this setup.
- The checker uses event-ID membership, payload equality, source tagging and same-version conflict detection. It does **not** prove full history or event-time SLO for unseen future events.

## Troubleshooting

```bash
docker compose -f compose.yaml -f labs/unified/compose.streaming.yaml --profile clickhouse --profile streaming ps -a
docker compose -f compose.yaml -f labs/unified/compose.streaming.yaml --profile clickhouse --profile streaming logs --tail=150 flink-sql-submit flink-jobmanager flink-taskmanager streaming-sink
python3 labs/unified/wait_for_flink.py --timeout 120
```

- **Flink job absent:** verify `flink-sql-submit` exited 0 and Kafka connector JAR was downloaded in all three Flink containers.
- **No ClickHouse rows:** verify `processed-trades` topic, sink logs, Basic authentication and ClickHouse bootstrapping.
- **Missing despite lag=0:** inspect per-partition offsets and sink visibility; lag does not prove durable sink writes.
- **Unexpected `ERROR`:** verify PostgreSQL source registration and ClickHouse HTTP connectivity; the checker deliberately rejects an invalid/empty manifest.
- **Mac memory pressure:** run the Core SQL profile alone or limit other Docker services; do not shrink Flink memory below a working minimum without re-verifying.
