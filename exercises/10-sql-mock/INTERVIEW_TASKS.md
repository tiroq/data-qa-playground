# SQL Mock — Open only when the 45-minute coding timer starts

**PostgreSQL:** `lab10.source_events`, `lab10.target_events`. Physical rows have `src_id`/`target_id`. Business identity is `(trade_id, account_id)`. NULL-key rows are not trusted matches. Evaluation cutoff: `2026-11-08 13:30:00+00`.

## Task A — Latest state (15 min)

For every valid source business key, produce `trade_id, account_id, latest_version, latest_status, latest_pnl, is_ambiguous`. Treat identical repeated payloads differently from disagreeing maximum-version payloads. Do not pick an arbitrary row on an ambiguous maximum.

## Task B — Reconciliation (15 min)

Reconcile the two sides at the **logical trade grain**, not physical-row grain. Preserve unmatched keys in both directions. Required: `trade_id, account_id, source_count, target_count, source_latest_version, target_latest_version, has_mismatch, dq_status`. Define the priority of `MATCH, MISSING, ORPHAN, STALE_TARGET, MISMATCH, AMBIGUOUS`. Report invalid keys separately by physical row ID. Prevent join multiplication.

## Task C — SLA and cutoff (15 min)

For valid latest-source trades eligible by the cutoff, measure first matching query-visible target state. Synthetic objective: 95% visible within 10 minutes. Required: `eligible_count, on_time_count, late_count, missing_count, on_time_pct, sla_met`. Define behavior for an empty cohort, ambiguous latest version and incomplete target version history. Source timestamp is `created_at`; target is `available_at`.

No interviewer hints during the 45-minute interval. Reference SQL and result totals are intentionally not included.
