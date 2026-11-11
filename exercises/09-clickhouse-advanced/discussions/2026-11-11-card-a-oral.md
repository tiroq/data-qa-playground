# Session 09 — Oral interview record: Card A (in progress)

**Date:** 2026-11-11
**Status:** IN PROGRESS — only answered prompts recorded
**Execution evidence:** None; no ClickHouse queries or tests executed

## Fixture facts
- `trade_id=201, account_id=A1`: version 1 PnL 5.0; version 2 PnL 7.0 twice, ingest IDs 2 and 3.
- These facts are from `clickhouse/init/02-seed.sql`; interview DDLs are hypothetical.

## Actual candidate reasoning and interviewer review

1. **Question:** Does ordinary SELECT without FINAL always return one row under `ReplacingMergeTree(version)`?
   - **Candidate:** "Тут может быть и одна и две строчки, потому что фоновые мержи могли не отработать, и тогда будет две строчки. А если они отработали, то вернут одну."
   - **Review:** Correct asynchronous merge dependency. Missing possibility of three raw rows and sorting-key/partition constraints.
2. **Question:** `ORDER BY (account_id, trade_id, version)`; what remains after eligible merges?
   - **Candidate:** "У меня есть сомнения, как поведет себя с одинаковыми двумя версиями. Хотя, по идее, должен будет вернуть последнюю. То есть вернет, скорее всего, одну последнюю, либо две последние."
   - **Review:** With all records in one partition and full eligible merging, two sorting keys remain (versions 1 and 2). Distinguish replacement-key vs version parameter.
3. **Question:** `ORDER BY (account_id, trade_id)`, `SELECT FINAL`, and same-version tie.
   - **Candidate:** "Здесь вернется одна запись, потому что здесь order by по account и trade произойдет. И касательно какую именно из двух записей вернет Clickhouse, скорее всего последнюю пришедшую."
   - **Review:** One row is right. Docs describe last-inserted winner on equal highest version; insertion order is not a business event-time or ingested_at ordering guarantee.

## Open follow-up
- Trade 205 has two max-version (2) payloads with PnL 8.0 and 8.5. Candidate has **not yet answered** whether last-insert-wins is business-correct or how QA should classify it.

## Agreed conclusions versus open questions
- **Observed candidate understanding:** background deduplication is asynchronous, sorting key affects replacement identity, and `FINAL` returns a single survivor for the hypothetical stable business sorting key.
- **Interviewer correction (not attributed to candidate):** version in ORDER BY prevents replacement of different versions.
- **Still open:** business rule for conflicting max-version PnL, severity, independent reconciliation, and test design.
