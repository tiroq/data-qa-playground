# Prebuilt Labs — Sessions 06–13

These laboratories turn interview time into **implementation, reasoning and code review**, not Docker setup or boilerplate creation. All data is synthetic. The actual Exness interview and all interactive practice are **in Russian**; repository artifacts are in English.

| Session | Starting material | Core problem intentionally left to learner |
|---|---|---|
| [06](../exercises/06-data-quality-rules/START_HERE.md) | JSON batches with controlled DQ violations; typed runner API | Rule definitions, thresholds, report and severity |
| [07](../exercises/07-pytest-architecture/START_HERE.md) | In-memory processing fake and case matrix | pytest fixture scopes, isolation, integration strategy |
| [08](../exercises/08-async-testing/START_HERE.md) | Deterministic manual clock and delayed-read fake | bounded async polling, retries, diagnostic errors |
| [09](../exercises/09-clickhouse-advanced/START_HERE.md) | Oral-first ClickHouse scenario cards and optional isolated lab09 fixture | Discuss MV/aggregate design, migration validation and rollback; implement only agreed cases |
| [10](../exercises/10-sql-mock/START_HERE.md) | Isolated PostgreSQL tables, timed task brief | SQL solutions under time pressure |
| [11](../exercises/11-kafka-flink/START_HERE.md) | Reproducible transport delivery traces | offset/checkpoint reasoning, idempotency and recovery |
| [12](../exercises/12-pipeline-design/START_HERE.md) | Architecture requirements, event schema and failure cards | end-to-end test strategy and design decisions |
| [13](../exercises/13-quality-gates-ci/START_HERE.md) | Minimal lab readiness CI and independent smoke tests | blocking data quality gate and evidence policy |

## Isolation rules

- Existing Session 01 seed and Session 05 learner objects/tests must not be modified by lab setup.
- PostgreSQL labs use dedicated schemas (`lab10`); ClickHouse advanced uses `lab09` and never rewrites `lab03`.
- Files under `exercises/NN-*/starter/` may deliberately raise `NotImplementedError`. **Do not count them as implemented features**.
- `tests/labs/` verifies only preparation artifacts and helper behavior, not learner exercise acceptance.
- Use explicit input grain, version policy, event/time cutoffs and no-empty-PASS assertions.
- Separate physical deliveries from immutable event identifiers; do not claim the transport simulator is Kafka/Flink.

## Fast verification

```bash
uv sync --group dev
uv run pytest -q tests/labs
```

This readiness check is intentionally independent from the incomplete Session 05 reconciliation exercise. Each session's `START_HERE.md` contains the specific setup and acceptance work.

## Unified five-block preparation option (2026-11-12)

The [Unified Data Stack Training Lab](../labs/unified/README.md) provides an optional real Kafka → Flink SQL → Kafka → ClickHouse path with a PostgreSQL manifest and standalone DQ checker. The [five-block curriculum](../labs/unified/CURRICULUM.md) groups original Sessions **10+13**, **11+12**, **14**, **15**, and **16+17** into ~7 hours **excluding environment setup**, without deleting existing exercises, independent mock material or calendar entries. See the separate integration CI for validated claims; a runnable profile alone does not prove end-to-end exactly-once. Session titles retain the canonical `🎯 Exness | Session NN — ...` format.

