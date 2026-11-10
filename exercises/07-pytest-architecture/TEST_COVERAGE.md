# Session 07 — Complete pytest lab implementation and verification

**Verification:** 2026-11-10, in GitHub Actions
[run 42826563119](https://github.com/tiroq/data-qa-playground/actions/runs/42826563119)
— PostgreSQL/ClickHouse/HTTP job **SUCCESS**, Kafka/ClickHouse job **SUCCESS**.
[Unit/fake run 42826267851](https://github.com/tiroq/data-qa-playground/actions/runs/42826267851)
— **SUCCESS**. The earlier failed CI revisions were investigated and fixed;
do not mistake them for the final status.

## Scope and executable test inventory

| Area | Real dependency | Implementation | Key failure modes |
| --- | --- | --- | --- |
| API-style fake and fixture isolation | Python only | `tests/session07/test_pipeline.py`, `conftest.py` | API failures, repeated submit, absent processing, no-empty-PASS |
| Physical event ID reconciliation | Python only | `src/data_qa/delivery_manifest.py`, `tests/session07/test_delivery_manifest.py` | missing, unexpected, identical duplicates masking missing, invalid planned manifest |
| Payload and version DQ | Python only | `src/data_qa/delivery_quality.py`, `tests/session07/test_delivery_quality.py` | same-version PnL conflict, same-event wrong payload, Decimal scale equality |
| PostgreSQL READ COMMITTED / transaction semantics | PostgreSQL 16 Testcontainer | `tests/integration/test_transaction_isolation.py`, `test_committed_trade_contract.py` | unseen uncommitted INSERT, ROLLBACK, committed independent writer, invalid payload, duplicate |
| Teardown when assertion fails | PostgreSQL 16 + nested pytest subprocess | `tests/integration/test_yield_fixture_teardown.py` | `try/finally` rollback vs an accidental `with psycopg.connect` COMMIT on failing test |
| Raw historical events and latest view | ClickHouse 25.8 + PostgreSQL 16 Testcontainers | `tests/integration/test_pg_clickhouse_reconciliation.py` | latest PASS/history FAIL, missing version, same-version conflict, same-event wrong PnL, duplicates |
| HTTP API → asynchronous worker → data sinks | Real localhost HTTP + PostgreSQL and ClickHouse containers | `tests/integration/lab_api.py`, `test_lab_http_api.py` | 202 before persistence, bounded polling and timeout, sink drop, duplicate delivery, corrupted PnL, invalid request |
| Kafka offset vs durable sink | Kafka + ClickHouse Testcontainers | `tests/integration/test_kafka_sink_checkpoint.py` | committed lag=0 with empty sink, two independent partitions, last event present while an earlier event missing |

## Run with Docker

From the repository root. Python 3.12+, `uv`, and running Docker are required.
Containers are disposable.

```bash
# Session 07 pure-Python checks (also runs on CI):
uv sync --group dev
uv run pytest -q tests/session07

# Real PostgreSQL, ClickHouse and the synthetic HTTP pipeline:
uv run --with 'testcontainers[postgres,clickhouse]>=4.10,<5' \
  --with 'psycopg[binary]>=3.2,<4' \
  --with 'clickhouse-driver>=0.2.9,<1' \
  pytest -v tests/integration/ -m 'not kafka'

# Separate, heavier two-partition Kafka + ClickHouse boundary test:
uv run --with 'testcontainers[postgres,clickhouse,kafka]>=4.10,<5' \
  --with 'psycopg[binary]>=3.2,<4' \
  --with 'clickhouse-driver>=0.2.9,<1' \
  --with 'confluent-kafka>=2.7,<3' \
  pytest -v tests/integration/test_kafka_sink_checkpoint.py -m kafka
```

The second integration command excludes Kafka by design; the third runs a real
Kafka broker and exercises its committed offsets. Both run automatically in
separate jobs of `.github/workflows/session07-postgres-integration.yml`.

## Isolation and teardown

- One PostgreSQL and ClickHouse container per worker session (pytest-xdist
  creates separate Python processes, not threads).
- Function-scoped unique trade identifiers and committed-row cleanup in PG.
- Function-scoped ClickHouse database and `DROP DATABASE ... SYNC` for cleanup.
- HTTP worker stops before its database fixtures are torn down.
- A nested pytest subprocess deliberately fails assertions and proves that
  the rollback fixture reverts writes, while `with psycopg.connect` can
  commit unless rollback is explicit.
- If an operating-system process is killed abruptly, Python finalizers cannot
  be guaranteed; Testcontainers' reaper is a secondary cleanup mechanism.
- An external background process may write *after* a test finishes; use
  per-test isolation and an explicit completion barrier instead of a rollback
  from an unrelated connection.

## Semantics: no false green

- The test's planned source count is declared independently from actual
  target row counts. An intentionally empty scenario declares zero explicitly.
- Expected and actual event IDs are compared by set difference; multiplicity
  by Counter. Equal `COUNT(*)` or even equal distinct counts are insufficient.
- Payload mismatch is a separate checker; matching IDs are not proof of
  matching PnL/status.
- A standard `MergeTree` stores physical history. A normal latest-state
  `VIEW` using `argMax` is for analytics only, not evidence of history
  completeness. Same-version payload conflicts make argMax's tie ambiguous
  and must be rejected by the DQ checker.
- A localhost 202 response does not promise persistence. Polling is bounded,
  and processing completion is separate from reconciliation PASS.
- Kafka committed offsets (per partition) can reach the high-watermark before
  durable ClickHouse writes. A terminal sink signal must be defined in a real
  service; a final trade ID or lag=0 alone is insufficient.

## Deliberate boundaries / what is NOT claimed

- The HTTP service in this repo is a controlled training application; it
  uses a local Python queue and worker, **not a Kafka-backed production API**.
- The Kafka test uses a real two-partition broker and separately writes to
  real ClickHouse. It demonstrates the false-completion problem, but it is
  **not** a production consumer, exactly-once guarantee, transactional
  Kafka/ClickHouse protocol, or a full external deployment.
- No enterprise API authentication, multi-node fault recovery, consumer
  rebalance, per-partition sink checkpoint service, Flink job or external
  staging cluster is included.
- The suggested weighted dynamic xdist scheduler is documented in
  `notes/scheduling-review.md`; not implemented because it is a
  performance-planning concern, not a correctness assertion.
- Session 08's reusable general-purpose `wait_until` assignment remains
  **PLANNED for 2026-11-11**. A small Session 07-specific polling helper exists
  only inside the integration test.

## Assessment

The learner correctly reasoned about session vs function fixtures, isolation
with two connections, the limits of rollback for external commits, bounded
polling, source-of-truth assumptions, raw history vs latest views, set/Counter
reconciliation, and in-flight Kafka records. Final testing is a reviewed and
CI-executed implementation of those ideas. No artificial interview score is
assigned without a separate timed mock interview.
