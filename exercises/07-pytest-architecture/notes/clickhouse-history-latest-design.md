# Session 07 — ClickHouse Physical History vs Latest State

**Status:** Design discussed; SQL, actual ClickHouse Testcontainers integration and CI are **not yet implemented or verified**.

## Learner proposal

- PostgreSQL is trusted as the source of truth for the trading lifecycle.
- Keep all physically delivered trade versions in a standard ClickHouse `MergeTree` table.
- Present the latest trade state via a `VIEW` (or materialized projection if performance requires it) rather than making `ReplacingMergeTree` the only historical store.
- Reconcile latest business state separately from the physical event history.

## Review and caveats

1. An append-oriented `MergeTree` can preserve each delivered record, including duplicates, as long as TTL, mutations, or explicit drops do not remove them. A row that never arrived cannot be reconstructed from this table.
2. A regular view using `argMax` or a window function recomputes latest state at read time; an incremental materialized view into `AggregatingMergeTree` with `argMaxState`/`argMaxMerge` may improve performance but adds state-management and backfill concerns.
3. `argMax(pnl, version)` alone is insufficient when multiple physical rows share a maximum version and disagree on critical fields. Detect the conflict separately and, if latest projection must choose a row, define an explicit deterministic tie-breaker/business policy.
4. Data-quality checks and their contracts have distinct grains:
   - **Latest state**: one logical row per `(trade_id, account_id)` according to the agreed version/order policy.
   - **Event history**: compare immutable physical events or `(business key, version, event_id)` depending on the source transport contract.
   - **Delivery duplication**: compare physical delivery multiplicity where transport-level semantics require it.
5. Reconciliation after an incomplete async ingest requires a watermark, processing completion signal, or bounded waiting policy; count comparison alone can produce misleading results.

## Concrete next exercise

Given PostgreSQL with versions 1 and 2 for a trade, and ClickHouse raw data with only version 2, state the expected result of latest-state vs history-completeness tests. Then propose SELECT/pytest checks that prove each independently, without hiding a same-version conflict.

## Verified references

- https://clickhouse.com/blog/change-data-capture-solution-clickhouse-streamkap-cdc
- https://clickhouse.com/blog/using-materialized-views-in-clickhouse

## Follow-up — Processing completion barrier (learner, 2026-11-10)

**Learner's position:** Run full history/reconciliation checks only after there is a reliable indication that every expected trade update has finished processing. If an additional permitted delay expires with missing data, the test fails.

**Review / key distinction:**
- Define **processing completion** independently from **data correctness**. Otherwise waiting until every target row exists masks lost events by waiting forever or by reporting only a generic timeout.
- Record an immutable input manifest (expected event IDs, business keys, versions) before submission. A bounded processing barrier may be derived from correlated processing acknowledgments, a completed batch/checkpoint, or a trustworthy sink-side progress marker. None should be inferred solely from `COUNT(target) == COUNT(expected)`.
- A barrier must cover all relevant workers/partitions and be located *after* durable sink writes if treated as proof of ClickHouse visibility. An upstream offset or consumer lag reaching zero alone is insufficient.
- After completion, run independent latest-state and raw-history reconciliation: a batch with 100 expected events and 99 actual events must FAIL missing event(s), not hang.
- If no completion signal arrives by deadline, report TIMEOUT/INDETERMINATE and preserve diagnostics; don't report PASS. Separate freshness/SLA tests must still detect late/stuck processing even when full completion is unavailable.

**Next interview prompt:** What concrete, independently trustworthy barrier would be available in the actual API → PostgreSQL → Kafka/worker → ClickHouse system? How would it account for multiple partitions and late writes?

**Status:** Design discussion only; completion barrier and ClickHouse checks remain unimplemented.
