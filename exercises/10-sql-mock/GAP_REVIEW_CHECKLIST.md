# Session 10 — Post-Submission SQL Audit

**Only open AFTER the 45-minute independent SQL phase.** Not an answer key. Derived from Sessions 01, 02 and 04; see [readiness audit](../../docs/INTERVIEW_READINESS_AUDIT_2026-11-11.md).

For each submitted query:

| Check | Candidate observation and evidence | PASS / FAIL / NOT TESTED |
|---|---|---|
| Every explicitly required output column exists | | |
| Each row has the declared business-key grain | | |
| Source/target duplicate multiplicity cannot inflate JOIN results | | |
| Invalid NULL business keys are explicitly treated | | |
| Version ties are checked **before** representative row selection | | |
| PnL NULL is distinguished from same-version PnL conflict | | |
| Account totals cannot silently include uncertain current states | | |
| A late older version does not supersede business newer version | | |
| Final ORDER BY is explicit when output ordering is required | | |
| SLA denominator uses mature eligible events and a stated as-of | | |
| An empty unexpected cohort is not reported as PASS | | |
| At least one negative-control scenario is discussed | | |

## Fixed review protocol

- Freeze the original SQL files before discussion; do not silently edit them into reference code.
- Ask the candidate to find **one** bug themselves before showing a model approach.
- Assign separate scores for correctness, completeness, edge cases and explanation.
- Carry three observed, specific gaps into Sessions 14 and 17.
- If the candidate proposes `argMax` in PostgreSQL, ask them to contrast it with PostgreSQL `DISTINCT ON`/`ROW_NUMBER` in their actual SQL dialect.

## Optional adversarial fixture

After the original submission is frozen, the interviewer may apply `postgres/fixtures/10-followup-perturbations.sql` to an isolated `lab10` database. This adds an additional candidate maximum-version payload and a NULL PnL case. **Do not apply before the timed mock**; it changes the baseline physical counts and invalidates the baseline smoke-test expectation.

The optional follow-up tests robustness of the candidate's solution; no reference SQL is provided.
