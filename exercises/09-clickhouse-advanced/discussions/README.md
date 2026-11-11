# Session 09 — Discussion Artifacts

This directory is a durable knowledge log for the **oral-first** ClickHouse session.

## When to write an artifact

- After **each genuinely discussed scenario**, create `case-<ID>-<slug>.md` containing the actual question, the learner's reasoning, a counterexample, trade-offs, the agreed or unresolved outcome, and one test idea.
- At the end of the session, create `2026-11-11-session-review.md` using [DISCUSSION_RECORD_TEMPLATE.md](../DISCUSSION_RECORD_TEMPLATE.md). Only report actual coverage and score.
- When the conversation produces a useful alternative design, update [DECISION_MATRIX.md](../DECISION_MATRIX.md) with the actual comparison.
- If the learner explicitly asks for SQL/DDL after design review, save it to a separately named `solutions/<case-id>-<topic>.sql` and reference it from the case note. Keep historical attempts and improvements separately.

## Non-negotiable distinctions

- **Fixture fact** ≠ verified behavior of real ClickHouse.
- **Design hypothesis** ≠ tested guarantee.
- **Proposed SQL** ≠ SQL executed with a passing result.
- **Uncovered topic** ≠ incorrect answer.

Do not pre-populate these files with invented candidate answers. Do not touch historical Session 03 solutions or reset `lab03`. Oral discussion does not require any Docker service to be started.
