# Synthetic Trading Data QA Case — Evolving Contract

## Intent and limitations

This is an **invented training dataset**, not Exness production architecture or proprietary schema. It starts from a deliberately small PostgreSQL source and processing log, then gains versions, analytical storage, streaming and quality checks across 17 guided sessions.

## Baseline: already implemented

- **Source:** `trades(trade_id, account_id, symbol, volume)`; 8 source trades, `trade_id` is a PostgreSQL primary key.
- **Processing:** `processed_trades(record_id, trade_id, account_id, status)`; 10 physical records, including two duplicate keys, a missing source match, a target-only orphan, one `FAILED` and one `NULL` status.
- **Business identity for Session 01:** `(trade_id, account_id)`; processing expected exactly once per source trade.
- **Important nuance:** Source's primary key currently guarantees `trade_id` uniqueness, but later exercises may introduce duplicate source events *in separate staging tables*; never change the historical seed to create those scenarios.
- **Data safety:** Processing has no foreign key or business-key unique constraint on purpose; this is a DQ test lab.

## Progressive schema boundaries (proposed, not installed)

| Layer | Proposed grain | Introduced by | Key test obligation |
|---|---|---|---|
| Versioned source/events | One physical row per ingest ID; many versions/retries per business key | 02 | Latest-state selection and deterministic tie policy |
| ClickHouse raw events | One stored delivery/event | 03, 09 | Dedup and merge timing |
| Reconciliation snapshot | One *valid* business key and evaluation cutoff | 04 | No join amplification, independent flags |
| Python comparison report | One anomaly per documented identity/grain | 05 | Deterministic classification and decimals |
| DQ measurements | One rule, cohort, window and run ID | 06 | Correct denominators and non-vacuous PASS |
| Stream transport | One immutable event ID with delivery attempts | 11 | Replay, idempotency and ordering |
| Aggregate/API view | One account or trade per declared as-of time | 12 | Traceable source-to-output consistency |

## Cross-cutting invariants

1. **Identity:** distinguish business trade ID, source version, processing attempt, immutable event ID and physical delivery row.
2. **Cardinality:** define expected multiplicity on each side of every join; aggregate before joining when either side can repeat.
3. **Time:** record event time, ingestion time and processing time separately. Late arrival is not necessarily data loss. Specify watermark and cutoff before labeling a trade missing.
4. **Quality:** preserve independent anomaly flags; a single headline status does not erase secondary defects.
5. **SLA:** for a defined *eligible population*, at least 95% of trades should be processed within ten minutes. Calculate `on_time / eligible_count` (handle zero and missing timestamps explicitly). 80 late of 100,000 is 0.08% late; alone it does not violate a 95% target.
6. **Recovery:** replay must not introduce extra logical trades, even if transport is at-least-once.
7. **Traceability:** retain source IDs, versions and run/window metadata for investigating mismatches.
8. **Automation:** zero eligible rows must not silently count as quality success unless the contract explicitly permits an empty cohort.

## Scope discipline

- Do not install every service on Day 1. The current `compose.yaml` is PostgreSQL-only.
- Keep future tasks self-contained and respect original Session 01 reference SQL.
- No production credentials, real trades or client data belong in this repository.
- When streaming infrastructure is too costly for a short session, label simulations clearly and verify semantics instead of claiming full Kafka/Flink end-to-end testing.
