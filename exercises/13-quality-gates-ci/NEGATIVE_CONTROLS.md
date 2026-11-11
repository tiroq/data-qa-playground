# Session 13 — Failure-First Gate Design

**These are test cases, not implemented business-quality checks.** All interview discussion and feedback in Russian. Do not treat the existing `lab-readiness` CI as proof of end-to-end data quality.

## Gate outcomes to define during the exercise

- **PASS** only when the expected input population and independent evidence are sufficient.
- **FAIL** for a confirmed violation under a rule's declared severity and threshold.
- **INDETERMINATE / SETUP_ERROR** when a required manifest, cutoff, source snapshot, test suite or sink completion barrier is unavailable. A blocking gate must not silently report success in this state.

A candidate must choose whether a warning-only DQ failure blocks a PR. All thresholds and severity rules here are synthetic training contracts.

## Negative-control matrix

| ID | Given failure injection | Why a naive suite can return green | Candidate must specify failing evidence |
|---|---|---|---|
| N01 | Expected 5 events, generator submits 0 | Expected and actual both derived from empty actual list | Independent planned manifest; setup failure |
| N02 | Expected E1,E2,E3,E4; actual E1,E2,E2,E4 | Physical row count matches | Exact ID set and multiplicity |
| N03 | Expected E1..E4; actual four distinct but one unexpected | Distinct counts match | Set difference and unexpected IDs |
| N04 | IDs/versions match, one PnL is corrupted | ID membership passes | Payload/Decimal consistency |
| N05 | Two max-version records have different PnL | `argMax` chooses one physical row | Same-version conflict detection before projection |
| N06 | Event has NULL availability timestamp | SLA filter removes an overdue expected ID | Denominator and conservative UNKNOWN bounds |
| N07 | No source manifest / as-of cutoff | Quality rule lacks evidence to evaluate | Explicit indeterminate status, blocking policy |
| N08 | All pytest tests skipped or none collected | No tests ran but workflow step marked success | Test collection checks / required suite evidence |
| N09 | Kafka lag=0 but a sink write is missing | Offset progress mistaken for ClickHouse durability | End-to-end sink-side barrier + manifest check |
| N10 | Testcontainers setup fails | CI retries are confused with business retries | Separate infrastructure failure classification |

## Evidence manifest for a failed gate

Require: `run_id`, `git_sha`, dataset, source-of-truth manifest ID, `as_of`, rule ID, business key/event ID, severity, observation/threshold, one-line failure cause, regression seed and reproducible command.

## Candidate interview outputs

1. Write an independent negative test that actually returns **nonzero exit status**.
2. Explain why a successful fixture smoke is a prerequisite, **not a release-quality PASS**.
3. Assign clear owner and escalation severity for FAIL versus INDETERMINATE.
4. Show how skipped tests and `xfail(strict=True)` are represented in the report.
5. Propose a reproducible minimal CI gate without calling real production services.

Do not pre-implement the candidate's rule engine or edit source reconciliation logic as part of this preparation.
