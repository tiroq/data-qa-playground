# Session 05 — Fixture-driven pytest scenarios

The tests in `tests/unit/test_trade_scenarios.py` extend the **learner's**
`Record → TradeGroup → Checker chain → TradeResult` design without
implementing the missing reconciliation/checker algorithms.

## Provenance (synthetic, not production)

- `exercises/04-reconciliation/sql/01-fixture.sql`: source/target snapshots
  for **business-key presence**. The in-memory scenario transcribes all
  rows with usable business keys (15 source and 17 target physical rows).
  The three rows with null keys are tested separately. It must report:
  - missing: `(102, A1)`
  - extra: `(104, A2)` and `(115, A8)`
  - no additional missing/extra for the remaining keys.
- `postgres/fixtures/02-trade-versions.sql` and its ClickHouse mirror:
  version histories and actual fixture `pnl` values. These include
  identical payloads in v2 for 201, an older version arriving later for
  203, and two conflicting v2 PnL values for 205.

**Schema limitation:** SQL uses `(BIGINT trade_id, TEXT account_id)`, but
the current Python `Record` uses `(str trade_id, int account_id)`. The
fixture uses a documented test-only normalization, e.g.
`(201, "A1") → ("T201", 1)`. It is not a general-purpose production
mapping. Session 04 snapshots contain `amount`, not `pnl`: the
presence-test records intentionally leave financial and status data
unset rather than falsely relabeling `amount` as `pnl`.

SQL ingest/physical IDs are used only as synthetic `event_id` labels in
the Python projection. An ingest row ID is **not** evidence that two
rows are repeated deliveries of the same immutable event; replay cases
use explicitly constructed synthetic event IDs.

## Test state

The Session 05 Python unit suite is enabled: the previously planned
`latest()`, missing/extra, duplicate, changed, version mismatch and
malformed tests are now implemented. No strict xfail is required for these
cases. CI runs `uv run pytest -q tests/unit` independently of lab readiness.

Additional best-effort tests in `tests/unit/test_reconciliation.py` cover:

- Valid duplicates plus malformed records on the same business key
- Unknown latest version blocking only version/state-dependent checks
- Known *older* malformed versions allowing latest-version comparison
- Partially known identity limiting the affected candidate business keys
- Malformed-only keys yielding blocked coverage without running an empty group
- Input-order independence of both issues and coverage

The compatibility API `compare_events()` still returns exactly five issue
lists. The detailed API `compare_events_detailed()` additionally returns
per-key check coverage and a count of unkeyed malformed observations.

## Implementation checkpoint

1. Run `uv run pytest -q tests/unit`.
2. Inspect `src/data_qa/reconciliation.py` and `src/data_qa/data/check_context.py`.
3. Review the trade-offs of best-effort findings versus blocked conclusions.
4. For scaling, index each group's events by side/version once and define
   a time cutoff/watermark for real streaming reconciliation.

The tests use synthetic fixtures; passing them is not proof of correctness
for production post-trade schemas or timing rules.

## ChangedHandler behavior (current implementation)

- Same-version rows with different status/PnL on one side produce one
  `changed` issue with `reason=payload_conflict`, side, version, event_ids,
  and sorted record evidence. `event_id` is included when all conflicting
  rows share it. The checker inspects both sides independently.
- Identical replays are handled by DuplicateHandler, not ChangedHandler.
- With an unambiguous latest payload on both sides and the same latest
  version, differing status or numeric PnL produces `state_mismatch`.
  Valid PnL strings are compared with Decimal; malformed/NULL PnL is a
  future validation responsibility.
- A conflict at the latest version blocks cross-side current-state comparison
  for that side, but still gets reported as an issue.
- Version mismatches remain outside this handler's policy and are handled
  by the separate VersionMismatchHandler.

## VersionMismatchHandler (implemented)

- Compares `group.latest(source)` and `group.latest(target)` only when
  both sides have records and latest states are unambiguous.
- Emits `changed` with `reason=version_mismatch`, `source_version`,
  `target_version`, and `direction=target_behind|target_ahead`.
- If either side has an ambiguous latest payload, it does not choose
  arbitrarily. `ChangedHandler` reports the underlying `payload_conflict`.
- The Session 04 fixture presence test explicitly filters to missing/extra;
  it does not fail simply because VersionMismatchHandler now reports valid
  additional findings (e.g. trade 108/A5 and 110/A6).
- DuplicateHandler now supports arbitrary repeated deliveries with Counter.
