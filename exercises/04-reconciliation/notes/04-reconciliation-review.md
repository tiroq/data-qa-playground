# Session 04 — Reconciliation review notes (in progress)

**Date:** 2026-11-08 (Asia/Bangkok)  
**Status:** Discussion / guided design, not a completed or runtime-verified solution.  
**Scope:** PostgreSQL source -> ClickHouse target, staged PostgreSQL snapshots for the join exercise.

## Learner's actual reasoning and confirmed conclusions

- Proposed `FULL OUTER JOIN` plus `COALESCE` for source/target business keys.
- Recognized the risk of join multiplication when both source and target contain repeated business keys; agreed to aggregate each input by `(trade_id, account_id)` **before** joining.
- Correctly identified why grouping by `status` would split one business key into multiple groups.
- Distinguished physical target presence from business status: a target record with `FAILED` is physically present and should still contribute to `target_count`.
- Initially suggested comparing source/target counts to identify missing/orphan; refined definition to *present only on source* / *present only on target*, respectively, while count discrepancies alone are not necessarily missing trades.
- Recognized that a deduplicated ClickHouse current state may reflect an obsolete source version, motivating `MISSING_UPDATE` / `STALE_VERSION` checks independent of physical row counts.
- Correctly classified source v3 vs target v2 as missing update, and matching versions with different amounts as amount mismatch.
- Recognized the ambiguity of equal-version conflicting values in `ReplacingMergeTree(version)` and the potential for retries or insert ordering to mask bad data.
- Proposed distinct amount counting via `HAVING uniqExact(amount) > 1`; recognized that replacing null with a numeric sentinel (e.g. -1) can collide with valid values.
- Accepted the null-sensitive conflict check: `uniqExact(amount) + toUInt8(countIf(isNull(amount)) > 0) > 1`, where null is counted as one distinct state. This check assumes raw, unmerged history remains observable.
- Reasoned that `amount = NULL` violates the trade data contract if amount is required, even when target/source keys and versions match.
- Correctly distinguished event processing from ClickHouse write acknowledgement and query visibility; noted `wait_for_async_insert` semantics and risk of using a pre-write acknowledgement as delivery time.
- Recognized that watermark progress does **not** prove any particular event has reached ClickHouse.

## Corrections made in review

1. `MISSING` means present in source only; `ORPHAN` means present in target only. Validate null-containing keys separately as `INVALID_KEY`.
2. `BOOL_OR(status = 'FAILED')` produces NULL for an all-NULL group; use null-aware status flags rather than interpreting this as success.
3. `source_count > target_count` does not imply lost business events when duplicates/versions are intentional.
4. A 10-minute SLA deadline counted from 12:03 expires at 12:13 even if Kafka lag persists; watermark/lag may explain lateness but do not extend the business deadline.
5. Current mismatch (source `amount=120`, target `amount=NULL` at the same key and version) is detectable **immediately**; a 10-minute SLA may affect alert escalation, not whether the data currently mismatches.
6. Delivery SLA must define its success criterion: physical/query-visible row vs semantically correct complete state. These are not automatically equivalent.

## Pending work / not yet demonstrated

- Complete executable reconciliation SQL, null-key quarantine, mismatch and independent status flags.
- Fixture containing repeated source and target keys and conflict cases; assertions for one row per valid business key.
- Explicit version-aware current-state projection, with tie/conflict checks and a physical-history retention plan.
- Cohort-based SLA SQL including undelivered matured events, arrival times, lag and watermark examples.
- Execution / tests / CI results and final session score: **not yet available**.

## Next discussion point

For source `(trade_id=101, version=3, amount=120, created_at=12:03)` and ClickHouse `(trade_id=101, version=3, amount=NULL, available_at=12:05)`, at 12:06:
- key/version match;
- current `amount_mismatch=true` (null-safe comparison);
- `has_null_amount=true`;
- a *physical-delivery* SLA reports 2 minutes;
- a *semantically-valid-delivery* SLA remains unsatisfied until the contractually correct state is query-visible; one record cannot decide a 95% cohort SLA.

## Follow-up: version-first amount comparison

- Learner correctly prioritized missing current version over comparing the values of different versions, recognizing the apparent amount discrepancy as a consequence of staleness rather than evidence of corrupted values.
- Proposed diagnostic policy in discussion: when a source and target current version differ, return an explicit `missing_update` / stale-version signal and leave `amount_mismatch` **not evaluated** (nullable), rather than incorrectly reporting mismatched amounts across unlike versions.
- Example: source v3/120 vs target v2/150 => `missing_update=true`, `amount_mismatch=NULL` (not evaluated); same version v3/120 vs v3/180 => `amount_mismatch=true`.
- Required implementation refinement: handle missing sides and target-ahead-of-source independently; nullable comparability must not be silently interpreted as a PASS.
- Discussion only; no executable SQL/test result has been observed yet.

## Follow-up: target version ahead of PostgreSQL

- Learner proposed two timing/architecture explanations for target v3 vs source v2: PostgreSQL write not yet committed while target receives update, or separate workers/buffers causing source-side delay.
- Review: such ordering is possible with **independent writers** or publication before the PostgreSQL transaction, but not the normal expectation of a strictly PostgreSQL-commit-driven CDC path (Postgres WAL -> Debezium -> Kafka -> ClickHouse). Debezium's main CDC contract streams committed database changes; see https://debezium.io/documentation/reference/connectors/postgresql.html for documented nuances during commit/failover.
- Additional crucial explanation discussed: source and target **snapshots may represent different points in time**, creating apparent target-ahead-of-source without any delivery defect.
- Classification policy pending: represent `TARGET_AHEAD` and `INCONSISTENT_SNAPSHOT` as investigative signals; don't mislabel target as automatically corrupt before checking cutoffs, commit order, and snapshot consistency.
- No executable validation performed.

## Follow-up: reconciliation cutoffs and snapshot consistency

- Learner proposed (a) a time condition in the reconciliation query, (b) capturing PostgreSQL before ClickHouse, and (c) checking records after the contractual 10-minute allowance.
- Review: these are relevant techniques, but source-first/target-second reads alone do not establish a consistent *as-of* snapshot. Example: source at 12:00 shows v2, source commits v3 at 12:02, target receives v3 at 12:03, target snapshot at 12:10 shows v3: apparent `TARGET_AHEAD` is not necessarily a defect.
- Recommended distinction: delivery reconciliation over a closed source **event cohort** (explicit cutoff and maturity/deadline), versus state reconciliation as of the same source commit/version/CDC offset. Comparing two independently chosen latest versions need not yield meaningful mismatches.
- Waiting past the 10-minute SLA reduces premature missing alerts but does not itself fix snapshot skew. A watermark is event-time progress, not confirmation that each event was materialized in ClickHouse.
- Future discussion: if ClickHouse exposes only deduplicated latest state via `ReplacingMergeTree FINAL`, historical as-of comparison may be impossible without retained history or CDC/audit metadata.
- Discussion only; no SQL test execution.

## Follow-up: historical state after ReplacingMergeTree merges

- Learner inferred correctly that reconstructing historical as-of states requires retained changes or differences, but was unsure whether ReplacingMergeTree keeps merge diffs.
- Review conclusion: ReplacingMergeTree is **not** a historical revision store. Background merges discard superseded versions from the active table; `SELECT ... FINAL` performs deduplication over the currently available parts and **cannot recover versions already removed** by a merge.
- A time condition on `trades_current FINAL` does not reconstruct an older as-of state once superseded rows have gone.
- Potential architecture (design only; not yet implemented): append-only `trade_events` using ordinary `MergeTree` (or another retained immutable source event log), plus `trades_current` using `ReplacingMergeTree(version)`. Preserve stable event IDs, trade composite keys, versions, source commit sequence/LSN and timestamps so historical state can be reconstructed for a common as-of boundary.
- Audit events need an explicit retention and replay policy; merge logs are not a substitute for durable event history.
- ClickHouse references:
  - https://clickhouse.com/blog/handling-updates-and-deletes-in-clickhouse
  - https://clickhouse.com/blog/updates-in-clickhouse-1-purpose-built-engines
  - https://clickhouse.com/blog/change-data-capture-solution-clickhouse-streamkap-cdc
- This was a guided conceptual discussion, not a verified running test.

## Follow-up: selecting historical as-of state

- Learner correctly argued that **the event set must first be restricted to the desired temporal or commit-position boundary**, and only then may the latest business state/version be selected. Selecting global `MAX(version)` first would choose a later update and fail to recover the historical state.
- Example: trade 101 v1 committed 11:50, v2 at 11:58, v3 at 12:03; an as-of boundary of 12:00 yields v2, not v3.
- Important nuance discussed: distinguish original source commit time/sequence from event occurrence time and ClickHouse arrival/ingestion time. Stable source ordering (e.g., CDC commit metadata with ordering rules, transaction position, and any needed tie-breakers) is preferable for consistent historical cuts.
- Additional proof obligation: the target event journal must actually contain all source events eligible for the cutoff; otherwise an as-of query is a partial reconstruction.
- Next exercise: guided, small-step SQL to filter and select the latest per-key historical version, while preserving invalid-key and conflicting-version diagnostics.
- The exercise remains **IN PROGRESS**; no SQL execution evidence or final score.

## Follow-up: argMax versus ROW_NUMBER for historical selection

- Learner preferred ClickHouse `argMax` to a window function, expecting that tied versions might make conflicts easier to detect.
- Review correction: `argMax(amount, version)` is a state-selection aggregate, **not** a version-conflict validator; if multiple rows tie for maximum version, selection of the associated amount is not deterministic.
- `ROW_NUMBER()` ordered solely by descending version is similarly ambiguous when versions tie.
- Separate DQ assertions must identify same-key/same-version conflicting payloads **before** choosing a representative state.
- Critical NULL caveat from official ClickHouse `argMax` docs: aggregate processing skips NULL arguments. `argMax(amount, version)` can select an earlier non-null amount rather than a later version with NULL amount. A tuple wrapper on the argument can preserve a nullable member for explicit validation, but does not solve tied-version conflicts.
- Reference: https://clickhouse.com/docs/reference/functions/aggregate-functions/argMax
- This is a guided correction, not an executed SQL attempt.

## Follow-up: argMax skips nullable latest amount

- Learner correctly predicted that `argMax(amount, version)` over (v2, 150) and (v3, NULL) will return 150 rather than the NULL amount of v3.
- Official ClickHouse explanation: `argMax(x, t)` selects the latest **non-null** argument; later null values are skipped. https://clickhouse.com/blog/clickhouse-25-6-coalescingmergetree
- To keep the latest row's null payload visible, a tuple argument, e.g. `argMax(tuple(version, amount), version)`, retains the null member while the tuple itself remains non-null; inspect the result as (3, NULL).
- This does not resolve conflicting payloads that have the same maximum version; independently check those conflicts before relying on any selected row.
- This was a guided discussion only: no executed ClickHouse query has been observed.

## Follow-up: equal-max-version ambiguity with nullable amounts

- Given (v2, amount 150), (v3, amount NULL), (v3, amount 180), learner correctly concluded that `argMax(tuple(version, amount), version)` may return different tied v3 payloads, cannot be trusted as a unique current business state, and requires a separate DQ check.
- Distinguish `latest_version=3` (known) from `latest_amount` (ambiguous); report `has_conflicting_version=true` and `has_null_amount=true` independently.
- If business contract requires a unique valid state at maximum version, do **not** interpret an arbitrary selected value as proof of `amount_mismatch` or `OK`. Record amount comparison as not evaluated/ambiguous until data quality policy resolves the conflict.
- Next discussion: historical conflict on superseded versions vs conflict on latest version; decide which affects the current-state reconciliation outcome and which remains a historical DQ incident.
- This remains a guided design conversation; no runtime tests completed.

## Follow-up: historical conflict on superseded version

- Given two conflicting v2 payloads (150, 180), followed by an unambiguous v3/120 that matches PostgreSQL, learner proposed recognizing the **current reconciliation as valid** and separately recording/investigating the historical conflict.
- Review: correct separation of current-state invariant and historical event-quality invariant. Potential fields: `current_state_valid=true` and `historical_conflict=true`. These independent findings must not suppress each other.
- Important risk: historical conflicting states may already have influenced downstream PnL, risk exposure, materialized views, accounting, or regulatory reporting; subsequent correct v3 does not automatically repair previously derived outputs. Severity/quality gate depends on lineage, downstream impact, audit contract and remediation/replay requirements.
- Interview assessment: appropriate pragmatic answer, with downstream contamination as key follow-up to strengthen it. No runtime verification performed.
