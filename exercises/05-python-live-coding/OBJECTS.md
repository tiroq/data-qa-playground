# Session 05 — Object-oriented checker scaffold

The learner is building a **self-checking group of trading events** with
pluggable checkers. These domain objects are structural scaffolding; they
do **not** implement reconciliation or choose latest versions.

## Created objects

- `data.base.Record` — existing learner dataclass; `business_key()` now
  returns the typed tuple `(trade_id, account_id)` rather than a string.
- `data.trade_group.TradeGroup` — owns source/target event lists for one
  composite key; validates record membership and has an extension hook
  `run_checks(checkers)`.
- `data.trade_group.GroupChecker` — Protocol: `check(group, result) -> None`.
- `data.trade_result.TradeResult` — one known business key and many findings;
  `add_issue(category, **details)`, `issues_of(category)`, `has_issues`.
- `data.trade_result.CheckIssue` — issue type and diagnostic payload.

## Intended use (a checker implementation is deliberately omitted)

```python
from data_qa.data import Record, TradeGroup

group = TradeGroup(
    business_key=("T1", 100),
    source=[Record(trade_id="T1", account_id=100, version=2, event_id="E2")],
)
# After you implement your checker(s):
# result = group.run_checks([MissingChecker(), VersionChecker()])
```

## Work left to the learner

1. Add validation/parsing for raw input; the current `Record` default
   values are **not** sufficient validation.
2. Implement `TradeGroup.latest(side)` with a documented conflict policy.
3. Implement actual checkers for missing/extra/changed/duplicates.
4. Build source/target groups across multiple business keys and integrate
   them with `compare_events`, or replace that legacy wrapper cleanly.
5. Decide how to collect malformed rows **without** a usable business key;
   do not silently discard them or assign them to a random `TradeGroup`.
6. Expand tests for order independence, one-to-many, Decimal, and conflicts.

## Compatibility note

The learner's existing `checkers/base.py` remains unchanged. Its original
`handle(source: list[Record], target: list[Record]) -> Dict` API operates
at batch level; it is **not yet** connected to `GroupChecker.check`.
Do not claim these two handler interfaces are already integrated.

The original `compare_events` function also remains an unimplemented
starter. The object scaffold tests are independent of the red reconciliation
tests.

## Verification

Run `uv run pytest -q tests/unit/test_trade_objects.py` for the scaffold,
then `uv run pytest -q tests/unit/test_reconciliation.py` for the still-open
learner exercise. No runtime or CI pass is claimed by this document.
