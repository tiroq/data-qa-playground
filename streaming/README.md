# Unified Streaming Data QA Lab — PostgreSQL + Kafka + Flink + ClickHouse

**Purpose:** synthetic versioned-trade environment for Exness QA interview preparation. It provides an independently seeded PostgreSQL manifest, Kafka KRaft, an actual Flink SQL stream job, a Kafka-topic boundary, ClickHouse Kafka Engine + raw MergeTree, a Python DQ gate, and GitHub Actions. No production data or network services are required.

**Status policy:** Unit/config validation and full Docker E2E have separate CI jobs. Do not claim that the pipeline is verified until the **e2e** job for the exact main commit passes. The basic `lab-readiness` workflow only validates unrelated learning fixtures.

## Quick start

Prerequisites: Docker Desktop/Engine with Compose v2, Python 3.12+, Bash, curl, several GB of free RAM for the Flink/Kafka/ClickHouse JVM/database stack. macOS and Linux supported by the Bash wrapper.

```bash
# Run from repository root. Builds compatible Flink Kafka SQL connector image.
bash scripts/streaming_lab.sh up

# Create a unique independent PostgreSQL manifest, publish Kafka records,
# and mark the synthetic source batch sealed AFTER successful publication.
bash scripts/streaming_lab.sh seed healthy demo-001

# Wait for matching ClickHouse physical rows, then check source ID/payload,
# same-version conflicts, PnL decimal and a synthetic visibility SLO.
bash scripts/streaming_lab.sh gate demo-001

# Repeat with new run IDs. A negative control must actually FAIL for the
# stated reason; the wrapper inverts that specific failure into test success.
bash scripts/streaming_lab.sh seed missing demo-002
bash scripts/streaming_lab.sh gate demo-002 DQ-MISSING

bash scripts/streaming_lab.sh seed corrupt demo-003
bash scripts/streaming_lab.sh gate demo-003 DQ-PAYLOAD

bash scripts/streaming_lab.sh seed duplicate demo-004
bash scripts/streaming_lab.sh gate demo-004

bash scripts/streaming_lab.sh status
bash scripts/streaming_lab.sh down
```

For a new attempt, change the `run_id` (a previous run is intentionally not overwritten). All generated SQL/JSONL and the machine-readable DQ report are under `.streaming-runs/<run_id>/`, ignored by Git. The optional `seed` argument automatically generates a unique run_id when omitted.

## Components and ownership

```text
Synthetic fixtures.py
  ├─ PostgreSQL labstream.runs / expected_events  [INDEPENDENT source manifest]
  └─ Kafka trades-input (2 partitions, business-keyed JSON)
       ↓
     Flink SQL 1.20.x (Kafka source, event_ts + watermark, identity projection)
       ↓
     Kafka trade-processed (2 partitions)
       ↓
     ClickHouse Kafka Engine table + insert-triggered MV
       ↓
     ClickHouse labstream.raw_events (append-only physical delivery records)
       ├─ SQL inspection: physical / distinct IDs / candidate latest state
       └─ Python gate.py: independent identity, payload, versions, SLA decision
```

- `compose.streaming.yaml`: an additive overlay; original `compose.yaml` and exercises are not changed. Kafka runs in single-broker **KRaft** mode with PLAINTEXT internal listeners, bound to localhost externally. Demonstration-only; not production security, HA or broker replication.
- `streaming/flink/Dockerfile`: Flink 1.20.3 and matching Apache Kafka SQL connector `3.4.0-1.20` from Maven Central. No local JDK or manual Maven build required. Network to Maven Central is needed **on first image build**; do not use the older patched JAR recipe from the supplied Medium article unchanged.
- `streaming/flink/sql/trading.sql`: real Flink SQL source → sink, `WATERMARK` declaration and periodic checkpoints. This identity projection intentionally does **not** implement deduplication; ingestion semantics are inspected separately.
- `streaming/sql/postgres.sql`: stable source manifest; one event per immutable `(run_id,event_id)`, with `planned_events` and `sealed` metadata.
- `streaming/sql/clickhouse.sql`: Kafka Engine consumer, MV, raw `MergeTree`. Physical repeats are retained; no `ReplacingMergeTree` merge is used to assert data correctness.
- `streaming_lab/fixtures.py`: synthetic trade lifecycle, keyed Kafka CLI batches, controlled injected anomalies, separate SQL manifest and publication-seal statements.
- `streaming_lab/gate.py`: pure-Python data-quality assertions and JSON report; does **not** depend on Kafka offsets or Grafana dashboards to declare successful business delivery.

## Scenarios

| Name | Injection | Expected gate | Important evidence |
|---|---|---|---|
| `healthy` | Six unique business events | PASS | 6 expected IDs and matching raw/payload |
| `duplicate` | Extra physical delivery of E002 | PASS with `DQ-REDELIVERY` warning | 7 physical, 6 distinct event IDs |
| `out_of_order` | Newer business version published before older version | PASS | Latest must still use version, not ingest order |
| `missing` | Omit E004 after manifest creation | FAIL / `DQ-MISSING` | Independent source manifest |
| `corrupt` | Mutate E003 target PnL | FAIL / `DQ-PAYLOAD` | Payload check independent of event ID |
| `conflict` | Distinct E007 with same max version, different PnL | FAIL / `DQ-SAME-VERSION` | Conflict before latest-state collapse |
| `extra` | Publish E999 without source manifest entry | FAIL / `DQ-UNEXPECTED` | Set difference, not only COUNT |

The synthetic freshness objective is at least 95% of eligible events query-visible within 10 minutes; it is **not an Exness policy**. `gate.py` reports its on-time/late/overdue/in-flight counts independently from correctness. An expected event missing from raw history prevents final PASS, even when its freshness deadline has not matured.

## Standalone contract validation

```bash
uv sync --group dev
uv run python -m pytest -q tests/streaming
docker compose -f compose.yaml -f compose.streaming.yaml \
  --profile clickhouse --profile streaming config --quiet
bash -n scripts/streaming_lab.sh
```

These checks are fast and **not** evidence that Flink/Kafka/ClickHouse actually ran. The full integration suite is `.github/workflows/streaming-lab.yml`, with separate `validate` and `e2e` jobs, preserving raw JSON reports as GitHub artifacts.

## Exercise boundaries and technical risks

1. Kafka single broker, 2 partitions, no ACL/TLS, no multi-broker failover. Kafka offset progress and lag=0 do not independently prove ClickHouse durability or query visibility.
2. Flink Kafka SQL job is a simple transport pass-through with watermark declaration. A real keyed/window aggregate, session window, stateful recovery and an **actual Flink checkpoint restore** are future interview exercises, not claimed implemented.
3. ClickHouse Kafka Engine + MV is **at-least-once in practice**; it can duplicate physical rows. The gate compares immutable event IDs, payloads and versions instead of relying on physical row count equality.
4. The gate's "sealed" flag proves only that the local CLI producer returned successfully. It is **not** a durable, post-ClickHouse per-partition completion barrier. A final business PASS comes from independent source/target comparison after bounded polling.
5. The candidate latest-state SQL in `streaming/sql/inspection.sql` is *illustrative*, not authoritative for conflicting maximum-version PnL. Fail-closed DQ detects those conflicts first.
6. Timestamp basis is source event_time_ms and ClickHouse available_at; cross-host clock skew and authoritative commit/visibility definitions need explicit discussion before applying this as a real SLA.
7. Every run ID must be unique. Source data and volumes persist after `down`. To intentionally erase data use Compose `down -v` only after understanding the impact on **all** associated PostgreSQL, ClickHouse and Kafka named volumes. The wrapper does **not** provide a destructive reset operation.
8. On the first build, the Flink connector JAR is downloaded from Maven Central; pin/review hashes for a hardened supply chain.
9. On slower Apple Silicon laptops the full stack may exceed available memory; use Sessions 10/13 PostgreSQL and standalone Python checks when a heavy stream is not needed.

## Relation to the article

The uploaded Medium example (Rongjin Zh, 2025) demonstrated Kafka 7.2.10 / Flink 1.16.3 / ClickHouse 23.8 / Grafana and a click-count window. Our lab keeps the basic streaming architecture but changes to synthetic versioned trades, KRaft, matching Flink 1.20 connector, real source/target quality checks and reproducible CI. Grafana is intentionally omitted to minimize setup; it is optional visualization rather than a correctness oracle.

## Interview routing

See [five-session learning route](../docs/UNIFIED_FIVE_SESSION_PLAN.md) and [Sessions 01–08 audit](../docs/INTERVIEW_READINESS_AUDIT_2026-11-11.md). Sessions 10–17 remain as separate historical/assessment modules; the new route combines them to avoid repeated environment setup.
