# Session 09 — Progressive Scenario Cards

These are **question cards**, not reference solutions. Read the next card only after the candidate has explained the current one. The values below come from the synthetic `lab03.trade_versions` fixture in `clickhouse/init/02-seed.sql`.

## A — Physical duplicates vs latest state

**Input:** 12 physical stored rows / 6 distinct `(trade_id, account_id)` keys. Trade 201, account A1, has version 2 twice with the same PnL (7.0000), at different ingest IDs.

- Would `count()`, `uniqExact()` and a latest-state aggregation represent the same thing?
- Which of those counts should a DQ alert compare, and why?
- What does `ReplacingMergeTree(version)` eliminate, and on which exact sorting key?
- What test can distinguish a transport retry from a legitimate business update?

**Follow-up:** Explain what could change before/after asynchronous merges without implying an actual data-quality improvement.

## B — Late older version

**Input:** Trade 203, account A2: version 2 (PnL 9.0000) was ingested before version 1 (PnL 1.0000).

- What would be wrong with treating the newest `ingested_at` as the latest business state?
- How would you demonstrate this without depending on background merges?
- What if a version number can be reused during corrections?

**Follow-up:** How would a QA regression test distinguish event-time ordering, ingestion ordering and version ordering?

## C — Same-version conflict

**Input:** Trade 205, account A3: two rows at maximum version 2 have PnL 8.0000 and 8.5000.

- Can `argMax(pnl, version)` alone produce a defensible logical result here?
- Which evidence is needed to classify this as a conflict rather than a legitimate amendment?
- Should the aggregate PnL be marked untrustworthy, excluded, quarantined, or resolved through an explicit rule?

**Follow-up:** Which alert severity is appropriate under **your declared contract**, and how do you prevent silent last-write-wins?

## D — Materialized view design

**Problem:** The team wants both current trade state and per-account PnL in ClickHouse.

- Compare an insert-triggered MV writing raw projections, aggregation states, or derived final values.
- What part of the historical data does a newly created MV automatically process?
- How might delayed or out-of-order events invalidate an apparently correct account aggregate?
- What observation would prove that a view is missing events?

**Follow-up:** What would you do differently if query correctness matters more than query latency?

## E — Replay and historical backfill

**Problem:** The team must backfill already stored rows while incoming events continue; a consumer may replay a previously written event.

- What is the chosen backfill boundary and replay identity?
- How do you avoid double counting between historical backfill and live view writes?
- What checks would you require before cutover?
- How would you recover from a partially completed backfill?

**Follow-up:** A physical row count matches expectations but latest-state account PnL is wrong. What next?

## F — TTL versus auditability

**Problem:** Raw deliveries are kept for 30 days; a reported analytical discrepancy relates to events older than 45 days.

- Can an aggregate alone prove exactly which event was incorrect?
- Where else must replayable history live, and who owns retention?
- What is the trade-off between storage cost, legal/operational retention, and ability to rebuild?

**Follow-up:** What DQ or operational check should fail *before* raw history is lost?

## G — Safe schema migration and rollback

**Problem:** A new target layout and MV have been built next to the current production view.

- Which **before/after invariants** and windows would you compare?
- What difference in counts is expected due to deduplication, and which discrepancy is unacceptable?
- At what point do you cut over? Under what condition do you roll back?
- How do you keep old and new readers consistent if writes continue?

**Follow-up:** How would you test a migration with a late higher version and a same-version conflict?

## H — Distributed extension (optional)

**Problem:** Raw data and aggregates are on multiple shards, and background merges are not synchronized.

- What kind of ordering, uniqueness and `FINAL` assumption is especially risky?
- How could the test compare independently across shards without double counting?
- What additional visibility / replay metrics are necessary?

**Scope limit:** No live cluster exists in this lab. This card is for architecture discussion only.
