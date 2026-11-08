# Session 12 — Decision Log (complete during live interview)

## Architecture sketch / diagram

## Logical versus physical identity
- Immutable event ID:
- Business key:
- Version/tie/conflict rule:
- Physical broker delivery identifier:

## Guarantee boundaries

| Boundary | Claimed guarantee | How to verify | Important counterexample |
|---|---|---|---|
| Upstream → log | | | |
| Log → processor | | | |
| Processor → ClickHouse | | | |
| Raw history → aggregate | | | |
| ClickHouse → API | | | |

## Freshness/reconciliation
- Eligibility, cutoff, denominator and watermark:
- Source of query-visible timestamps:
- Late/in-flight vs missing:
- Non-vacuous checks:

## Reliability and quality
- Crash/replay/backfill behavior:
- Migration and rollback:
- Test pyramid and data contracts:
- Operational metrics, logs and DLQ:
- Weakest assumption / counterexample:
