# Session 12 — Build an Auditable Evidence Chain

This worksheet targets weak points from earlier source/target reconciliation and Kafka completion discussion. **Do not prefill the architecture.** Ask the candidate to propose each proof step during the Russian-language design interview.

## Declare the business contract first

- Source of truth:
- Event is snapshot or delta:
- Immutable event ID versus business key and version:
- What makes an event eligible for comparison:
- Source commit / CDC position / event-time / query-visible time:
- Expected source manifest and trusted generator:
- Retention and recovery horizon:
- What must remain INDETERMINATE until more evidence arrives:

## Evidence path

| Stage | Trace ID and payload proof | What it guarantees | What it explicitly does NOT guarantee | Failure injection |
|---|---|---|---|---|
| Source transaction / event log | | | | |
| Kafka accepted and partition/offset | | | | |
| Processor accepted and checkpointed | | | | |
| ClickHouse durable raw write | | | | |
| Latest-state / aggregate read | | | | |
| Reconciliation of eligible cohort | | | | |
| API quality gate and report | | | | |

## Cross-system counterexamples to discuss

1. Latest-state matches but raw history misses an intermediate event.
2. Both sides report the same count but contain different event IDs.
3. A duplicate transport replay inflates delta-style PnL but not snapshot-style PnL.
4. PostgreSQL and ClickHouse snapshots represent different source-commit boundaries.
5. A target row is visible without proof that every earlier relevant partition delivery is durable.
6. The source-of-truth manifest is empty because the generator silently failed.
7. A backfill reads a different cutoff than the live MV and double-counts a boundary event.

## Reviewer outputs (after answers only)

- One falsifying test for each declared guarantee.
- One independent source of truth per important correctness claim.
- A concrete rollback and replay decision; distinguish infrastructure timeout and business mismatch.
- Explicit unverified assumptions, especially for real Flink and distributed ClickHouse.
