# Synthetic Trading Data Flow — System Design Case

All numbers here are **exercise assumptions**, not Exness architecture, measurements or internal rules.

## Context

Upstream creates versioned trading events; a log transports them to one or more processors. ClickHouse serves account-level analytics to an API. An independent durable log or source database supports reconciliation, audit and replay.

| Requirement | Hypothetical training constraint |
|---|---|
| Input | 500 events/s steady, bursts of 2,000 events/s |
| Stored history | 25 million physical deliveries; retry/replay permitted |
| Freshness | At least 95% of eligible events query-visible within 10 minutes |
| Business correctness | No silent loss, arbitrary conflict winner or double-counted PnL |
| Recovery | Reprocess 24 hours after a faulty deploy without changing logical output |
| Traceability | Immutable event ID, composite business key, version, run ID and evaluation window |
| Development | Reproducible local Docker/pytest checks, production may have multiple workers |

## Deliverables

1. Logical/physical event flow with source-of-truth and schema ownership.
2. Transport/processing guarantees at each boundary and effect of uncertain acknowledgements.
3. Raw history, latest-state and aggregate data models; explicit tie/conflict policy.
4. Data-quality rules, no-empty-PASS behavior and 95% SLA denominator/cutoff.
5. Layered QA plan (unit, integration, contract, stage end-to-end, production reconciliation).
6. Observability, lag, DLQ, event tracing, replay, backfill and rollback.
7. Migration and retention policy, including preservation of source raw history.

Use [the example event JSON Schema](../../labs/contracts/trading_event.schema.json). Physical Kafka partition/offset belong in a transport envelope rather than the immutable business payload. The design cannot assume distributed transactions magically cover ClickHouse, Kafka and the API.
