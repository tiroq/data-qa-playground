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

## Test states

**Should pass already:** fixture shape, exact missing/extra keys,
three normal presence-table cases, and identity-only lifecycle guard.

**Strict `xfail` (not yet implemented):**

1. Empty-on-both-sides should not generate missing and extra.
2. Latest version for 201, 202, 203, 206; empty target.
3. Conflicting latest payload for 205 must not choose an arbitrary winner.
4. Stale target, changed PnL, and Decimal precision.
5. Same-event transport replay, missing **plus** replay, conflicting
   payload for one event ID.
6. Null-key rows must be reported as malformed.

The `xfail(strict=True)` tests run and document expected failures.
When one begins to pass, pytest reports **XPASS as a failure**: remove
the marker once the behavior is correctly implemented. A green suite
with `xfailed` cases does **not** mean all acceptance criteria are met.

## Implementation checkpoint

1. Run `uv run pytest -q tests/unit/test_trade_objects.py tests/unit/test_trade_scenarios.py`.
2. Fix the empty-group presence edge case (does not need new classes).
3. Implement `TradeGroup.latest(side)`; enable relevant tests.
4. Add `Changed` and `Duplicate` checkers **in your naming style**.
   Extend `presence_chain()` inside the test file as you connect them.
5. Implement raw-key validation and `compare_events` aggregation.
6. Run `uv run pytest -q tests/unit/test_reconciliation.py` when the
   batch comparison contract is ready.

The learner's five passing structural tests and all existing source files
are preserved. No runtime/CI pass is claimed until separately verified.
