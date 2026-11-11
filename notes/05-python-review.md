# Session 05 — Python Live Coding Review (updated evidence index)

**Status:** Implementation now exists in `main`; previous starter-only assessment was stale. **Independent timed interview score:** not assessed.  
**Primary review:** [Session 05 implementation and complexity](../exercises/05-python-live-coding/IMPLEMENTATION.md).  
**Recorded unit CI:** [successful historical Session 05 run](https://github.com/tiroq/data-qa-playground/actions/runs/42825189862), not evidence of subsequent doc-only commits or production behavior.

## Progress and provenance

- Initial learner-designed object model: `Record`, `TradeGroup`, `TradeResult`, chain-of-responsibility checkers and invariant tests.
- Subsequent implementation (discussion/review assisted): `TradeGroup.latest()`, `compare_events()`, independent findings, malformed-event coverage and version/conflict handling.
- Verified by code inspection: `src/data_qa/reconciliation.py` no longer raises `NotImplementedError`; numerous unit scenario tests exist.
- Evidence limit: the historical unit CI run demonstrates the tests selected by that workflow, **not** a fresh candidate-only live-coding exercise.
- Performance limit: current checks can revisit the same event history per version, leading to O(V×M) or quadratic behavior for pathological histories.

## Observed strengths

Composite identity, separation of missing/extra/changed/duplicate/malformed, independent quality findings, Decimal semantics, deterministic output and explicit unknown check coverage.

## Pending assessment

- Re-implement one nontrivial checker from requirements in **20 minutes without a reference answer**.
- Explain complexity and propose a linear or near-linear indexed version-history approach.
- Independently test conflicting latest versions, malformed rows that could hide missing events, and stable ordering.
- Clearly distinguish structurally empty batches from an invalid constructed `TradeGroup`.
- Add a real timed score only after a candidate attempt and review; do not invent one.

## Forward links

See [readiness audit](../docs/INTERVIEW_READINESS_AUDIT_2026-11-11.md), [Session 14](../exercises/14-mock-interview-1/README.md) and [Session 17](../exercises/17-final-review/README.md).
