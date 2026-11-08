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
