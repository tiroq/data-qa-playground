# Unified Streaming Lab — Verified CI Evidence (2026-11-12)

**Verified code commit:** `688f34de6be07187fb2b00ea2a1d94197ab6eafa`  
**GitHub Actions:** [Unified Streaming Data QA Lab — SUCCESS, run 43200534924](https://github.com/tiroq/data-qa-playground/actions/runs/43200534924)  
**Jobs:** `source-and-compose` SUCCESS; `streaming-e2e` SUCCESS.  
**Artifact:** `unified-streaming-dq-reports`, six synthetic JSON quality reports attached to that run.

## What the run actually demonstrated

1. Python `unittest` negative controls passed and combined Docker Compose configuration validated.
2. Disposable Kafka in KRaft mode, PostgreSQL, ClickHouse, Flink JobManager and TaskManager started with healthy status.
3. A real Flink SQL job named `trade-pipeline-lab` entered `RUNNING` (logged job ID `c72af552e25657af9a0adb2fcdcc7d8b`).
4. Synthetic trades were registered to the independent PostgreSQL source manifest, produced to Kafka, processed by Flink SQL, consumed from the processed Kafka topic and persisted to ClickHouse.
5. The `check.py` report matched independently expected outcomes for all six scenarios:

| Scenario | Result | Verified observations |
|---|---|---|
| clean | PASS | All expected event IDs and payloads observed |
| replay | PASS with warning evidence | 6 expected distinct event IDs, 7 physical target rows; extra delivery for E02 detected |
| out_of_order | PASS | All 6 event IDs observed with versioned raw history |
| missing | FAIL (`missing_event`) | The expected event was deliberately not sent |
| conflict | FAIL (`conflict_same_version`) | Same trade/version has conflicting payload values |
| corrupt | FAIL (`payload_mismatch`) | Source and sink PnL differ for an immutable event |

The three negative scenarios used `--expect FAIL --require-rule ...`; infrastructure errors could not fulfill those assertions. Each JSON report was uploaded even if a workflow failed.

## Corrections found during validation

- SQL Client startup initially skipped its actual `-f` argument; fixed Compose command vector.
- Overriding the official Flink entrypoint hid `FLINK_PROPERTIES` and caused a REST connection failure; restored official entrypoint.
- Starting SQL Client before the JobManager REST endpoint was ready caused a race; added healthcheck and dependency.
- The shared checkpoint volume was not writable by Flink; added a local-only one-shot volume permission initializer.

Earlier failed runs correspond to intermediate revisions and are **not** evidence of a failing final implementation.

## Not validated / limits

- End-to-end atomic exactly-once across Kafka and ClickHouse: **not implemented**.
- A true sink-side completion barrier across all partitions: **not implemented**; current checker validates observed persisted rows after bounded waiting.
- Flink HA/failover, production-grade CDC, watermark-based aggregate SQL, multi-shard ClickHouse, DLQ and a schema registry: **not tested**.
- Mac hardware-specific Docker run: **not verified**; CI used an Ubuntu runner.
- Passing this tutorial does **not** mean the student independently solved interview SQL/Python questions.

The educational environment is suitable for the consolidated five-block Sessions 10–17 plan, with failures intentionally reproducible and clearly separated from guarantees that remain design exercises.
