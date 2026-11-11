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
- Trade 205 has two max-version (2) payloads with PnL 8.0 and 8.5. Candidate answered the classification question; handling of account aggregate remains open.

## Agreed conclusions versus open questions
- **Observed candidate understanding:** background deduplication is asynchronous, sorting key affects replacement identity, and `FINAL` returns a single survivor for the hypothetical stable business sorting key.
- **Interviewer correction (not attributed to candidate):** version in ORDER BY prevents replacement of different versions.
- **Still open:** business rule for conflicting max-version PnL, severity, independent reconciliation, and test design.

## Card C — same-version conflict (first actual answer)

- **Question posed:** Can `FINAL` selecting PnL 8.5 be considered DQ-correct; how should QA classify trade 205?
- **Candidate actual answer:** "С точки зрения data quality по второй версии очень неоднозначный вопрос, потому что здесь конфликт P&L и для этого должна быть отдельная data quality проверка."
- **Interviewer assessment:** Correctly separates same-version conflicting PnL from simple duplicate detection. This does **not** yet establish a business conflict resolution policy, severity, or account-aggregate treatment.
- **Next follow-up:** Whether/how trade 205 should contribute to account A3's `SUM(PnL)` until conflict is resolved.
- **Status:** open; no SQL executed or implementation authorized.

## Card C — account aggregate under unresolved conflict (actual answer)

- **Question:** How should trade 205 affect account A3 aggregate while max-version PnL values 8.0 and 8.5 conflict?
- **Candidate actual answer:** "Смотри, если мы из агрегата выкинем её, то это будет уже некорректная аналитика. С другой стороны мы можем в аналитике указать, что, например, диапазон у нас и недетерминировано пока значение, и вот в таких-то диапазонах."
- **Candidate proposal:** Do not silently exclude the trade; explicitly represent uncertain aggregate as a range instead of falsely precise value.
- **Interviewer qualification (not attributed to candidate):** For the fixture, account A3 PnL could be 8.0–8.5 assuming the only valid alternatives for trade 205 are those two rows and trade 206 contributes 0.0. This is not an approved financial settlement value. A range may be acceptable for provisional analytics but insufficient for financial reporting.
- **Open follow-up:** Define different quality gates, if any, for monitoring dashboard versus final financial reporting.
- **Status:** Interview discussion only; no SQL or test execution.

## Card C — consumer-specific quality gates (actual answer)

- **Question:** Should a monitoring dashboard and financial report both use an unresolved PnL range?
- **Candidate actual answer:** "Я бы, наверное, допустил в мониторинге, а вот в финансовом репорте я бы уже не допустил это значение, пока конфликт не разрешен."
- **Candidate conclusion:** Permit explicitly flagged uncertainty in monitoring, but block the affected financial result until conflict resolution.
- **Interviewer review (not candidate claim):** Reasonable risk-based quality-gate separation. Pending contract detail: whether the blocking scope is trade, account, period or whole report; a FAIL need not halt the entire pipeline.
- **Next follow-up:** If ReplacingMergeTree has merged away the conflicting raw version, how can a DQ check still detect historical conflict?
- **Execution evidence:** None.

## Card C/D — preserving evidence before ReplacingMergeTree replacement (actual answer)

- **Question:** How can DQ detect same-version conflicting PnL once ReplacingMergeTree merges have removed one competing row?
- **Candidate actual answer:** "На входе в ClickHouse как минимум на лету можно смотреть, и если есть конкретный конфликт при записи, можно об этом сразу же сигнализировать уже при записи второй агрегации. Либо, если у нас нету какого-то промежуточного мониторингового звена, то надо отдельно как минимум хранить все значения для того, чтобы производить data quality. А для аналитики и бизнеса уже, допустим, пусть replace merge3 работает, или же поверх merge3 view, которая будет делать все эти агрегации."
- **Candidate proposals:** Entry-time conflict detection and signaling; otherwise immutable/raw historical values retained separately for DQ; analytical read model may use ReplacingMergeTree or a view.
- **Interviewer caveat (not attributed to candidate):** Insert-triggered ClickHouse materialized views process the incoming inserted block, so straightforward grouped calculations do not automatically compare events arriving in separate insert blocks. Stateful aggregation or a separate stateful processor/check is needed for cross-insert conflict detection.
- **Open follow-up:** How to detect conflict across separate INSERTs efficiently without rescanning the complete table for each event.
- **Status:** Design discussion only; no implementation or executed checks.
