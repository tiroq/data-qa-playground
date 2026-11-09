# Session 05 — compare_events implementation review

## Design and control flow

`compare_events(source, target)` is a batch orchestrator. It does not
reimplement per-trade anomaly rules. It returns five lists of standalone
findings: missing, extra, changed, duplicates, malformed.

1. **Validate before grouping.** Reject absent/invalid identifiers, invalid
   version or event ID, missing/invalid status, and nonnumeric/nonfinite PnL.
   A `Decimal` parse checks money; binary floating-point input is rejected
   rather than silently passing rounded values through. Explicit null PnL
   remains valid at structural level until a business-state policy is defined.
2. **Keep evidence for bad rows.** Every malformed row receives its own issue,
   even without a usable business key. The report retains the side, reason,
   all validation errors and a detached JSON-like copy of the row.
3. **Continue checks despite malformed records.** Preserve usable records
   while recording excluded observations by known business identity. A row
   with only a valid trade ID or account ID can plausibly belong to multiple
   keys; unknown identity can affect all keys. Suppress a presence finding
   only if an excluded row could belong to the apparently missing side.
   Suppress latest-version and latest-state findings only if an excluded row
   could alter the maximum version or its payload.
4. **Group all valid records using** `(trade_id, account_id)`. Do not use
   `event_id` or `version` as the business grouping key.
5. **Invoke the existing chain** once for every group with valid events. An
   empty *batch* is valid (empty report), whereas a constructed empty
   `TradeGroup` is invalid if sent to `run_checks()`.
6. **Flatten findings** to dicts with exactly
   `trade_id`, `account_id`, `details`, preserving independent issues
   instead of reducing every trade to one boolean status.
7. **Sort every category** using business identity and stable serialized
   details, making output independent of source/target input order.
8. **Expose check coverage separately.** `compare_events_detailed()` returns
   `{"report": ..., "coverage": ...}`. Each business key has per-check
   `complete`, `partial`, or `blocked` status. `compare_events()` retains the
   original five-category shape for existing callers.

## Reasoning about separation of responsibilities

- `MissingHandler` / `ExtraHandler`: key-level presence.
- `DuplicateHandler`: repeated same-event payload on the same side;
  arbitrary number of deliveries, with `duplicate_count=N-1`.
- `ChangedHandler`: conflicts within a side and PnL/status mismatches
  at the same latest version.
- `VersionMismatchHandler`: latest source/target version difference,
  represented as `changed` with reason `version_mismatch`.
- `latest()`: pure choice of current state; equal semantic Decimal PnL
  representations are equivalent. It is not a substitute for diagnostics.

## Check uncertainty policy

- **presence**: complete if both sides have valid records or a missing side
  has no potentially matching malformed observation; otherwise blocked.
- **duplicates / payload_conflict**: keep confirmed findings from valid
  records and mark coverage partial when excluded rows could also belong
  to either side. Block only if there are no valid rows to inspect.
- **version_mismatch / state_mismatch**: block if a candidate malformed row
  has an unknown version or a version equal to or greater than the maximum
  known version on its side. A known *older* malformed row does not prevent
  an otherwise unambiguous latest comparison.
- **identity matching**: a malformed row with known trade and account affects
  only its key; one known field constrains plausible matches; two unknown
  fields can affect all observed keys. Unkeyed malformed rows are also
  counted in `coverage.unkeyed_malformed_count`.
- **malformed-only keys**: report validation problems and blocked coverage
  without invoking `TradeGroup.run_checks()` on an empty group.

## Complexity and limitations

Let N be the total number of input events. Validation and grouping are
O(N) expected time and O(N) memory, plus sorting group IDs and findings.
The **existing checker implementations** revisit a side for each unique
version, so a pathological trade with V versions and M rows can cost
O(V*M), up to quadratic. This is the first optimization target for large
histories (pre-index each group by side and version once).

The function is not a streaming algorithm: it materializes groups in memory.
Coverage lookup indexes malformed observations by full key, partial trade ID,
partial account ID and completely unknown identity. An unkeyed observation
may affect many business keys, so very large malformed populations can make
coverage construction expensive.
It also does not enforce Kafka/warehouse event-time cutoffs, SLA eligibility,
watermarks, or status-specific PnL rules. A missing trade cannot be declared
lost without a defined reconciliation cutoff in a real pipeline.

## Run

```bash
uv run pytest -q tests/unit/test_reconciliation.py tests/unit/test_trade_scenarios.py
```
