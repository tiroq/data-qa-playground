# Session 05 — 45-minute live-coding starter

This is an **unfinished learner exercise**, not a reference implementation.

## Timeboxed plan (45 min)

1. **20 min:** Implement `compare_events` in `src/data_qa/reconciliation.py`. Keep the algorithm in memory.
2. **10 min:** Review defects, version semantics, duplicate/conflict policy, and `Decimal`.
3. **10 min:** Make the parameterized pytest suite pass and add one important missing edge case.
4. **5 min:** Explain complexity and how a sorted/streaming solution would change the approach.

The original [90-minute exercise](README.md) remains the full learning contract; this is an abbreviated live session.

## Files to edit

- `src/data_qa/reconciliation.py` — function and typed report stub (intentionally raises `NotImplementedError`).
- `tests/unit/test_reconciliation.py` — runnable, **currently failing** parameterized checks. Expand them after the first attempt.
- `notes/05-python-review.md` — review notes and verified results, not a claimed score.

## Run locally

```bash
uv sync --group dev
uv run pytest -q tests/unit/test_reconciliation.py
```

Alternative (without uv): create a Python 3.12+ venv, install `-e '.[dev]'` only if a corresponding optional extra exists; this scaffold instead uses a dependency group, so `uv` is the recommended workflow.

## Comparison contract

- Business key: `(trade_id, account_id)`. Compare the latest state at maximum `version`.
- Validate key, version, event identity and monetary values. Malformed input must not be dropped.
- Compare current `version`, `status`, and `pnl` using `Decimal`, without tolerance.
- Report `missing`, `extra`, `changed`, `duplicates`, `malformed` separately.
- Repeat delivery of identical `event_id` and payload is a duplicate; conflicting payload for the same event or ambiguous maximum version needs explicit diagnostic classification, **not last-write-wins**.
- Reports must be deterministic; input objects must not be modified.

## Interview follow-up (no answer provided)

How do you resolve two distinct `event_id` values that share a business key and the same maximum version but disagree on `pnl`? Which report category would represent this, and what evidence is required?

## Verification status

Scaffold committed; tests **not claimed passing**. No learner implementation, benchmark, or interview score recorded.
