# Session 05 — compare_events implementation review

## Design and control flow

\`compare_events(source, target)\` is a batch orchestrator. It does not
reimplement per-trade anomaly rules. It returns five lists of standalone
findings: missing, extra, changed, duplicates, malformed.

1. **Validate before grouping.** Reject absent/invalid identifiers, invalid
   version or event ID, missing/invalid status, and nonnumeric/nonfinite PnL.
   A \`Decimal\` parse checks money; binary floating-point input is rejected
   rather than silently passing rounded values through. Explicit null PnL
   remains valid at structural level until a business-state policy is defined.
2. **Keep evidence for bad rows.** Every malformed row receives its own issue,
   even without a usable business key. The report retains the side, reason,
   all validation errors and a detached JSON-like copy of the row.
3. **Quarantine keys containing malformed records.** If a malformed row still
   has a valid trade/account key, skip normal reconciliation for that key.
   Otherwise a valid target plus invalid source would incorrectly become
   \`extra\`. This is a conservative design choice: other valid records for
   that key are also skipped and may contain additional issues. This should
   eventually be exposed as a quarantined/partial population metric.
4. **Group all valid records using** \`(trade_id, account_id)\`. Do not use
   \`event_id\` or \`version\` as the business grouping key.
5. **Invoke the existing chain** once for every non-quarantined group. An
   empty *batch* is valid (empty report), whereas a constructed empty
   \`TradeGroup\` is invalid if sent to \`run_checks()\`.
6. **Flatten findings** to dicts with exactly
   \`trade_id\`, \`account_id\`, \`details\`, preserving independent issues
   instead of reducing every trade to one boolean status.
7. **Sort every category** using business identity and stable serialized
   details, making output independent of source/target input order.

## Reasoning about separation of responsibilities

- \`MissingHandler\` / \`ExtraHandler\`: key-level presence.
- \`DuplicateHandler\`: repeated same-event payload on the same side;
  arbitrary number of deliveries, with \`duplicate_count=N-1\`.
- \`ChangedHandler\`: conflicts within a side and PnL/status mismatches
  at the same latest version.
- \`VersionMismatchHandler\`: latest source/target version difference,
  represented as \`changed\` with reason \`version_mismatch\`.
- \`latest()\`: pure choice of current state; equal semantic Decimal PnL
  representations are equivalent. It is not a substitute for diagnostics.

## Complexity and limitations

Let N be the total number of input events. Validation and grouping are
O(N) expected time and O(N) memory, plus sorting group IDs and findings.
The **existing checker implementations** revisit a side for each unique
version, so a pathological trade with V versions and M rows can cost
O(V*M), up to quadratic. This is the first optimization target for large
histories (pre-index each group by side and version once).

The function is not a streaming algorithm: it materializes groups in memory.
It also does not enforce Kafka/warehouse event-time cutoffs, SLA eligibility,
watermarks, or status-specific PnL rules. A missing trade cannot be declared
lost without a defined reconciliation cutoff in a real pipeline.

## Run

\`\`\`bash
uv run pytest -q tests/unit/test_reconciliation.py tests/unit/test_trade_scenarios.py
\`\`\`
