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

## Card D — Materialized View learning clarification

- **Candidate actual request:** "Ну здесь Materialized View я не знаком, поэтому разбери мне этот очень коротко кейс."
- **Candidate familiarity:** Explicitly stated unfamiliarity with Materialized View; no candidate implementation proposal was provided for cross-INSERT checking.
- **Interviewer explanation:** Insert-triggered MV processes incoming blocks; use raw MergeTree deliveries, MV aggregate states by trade/version into AggregatingMergeTree (e.g. min/max PnL states), query merged states to detect discrepancy; alerting needs separate polling/check and the MV alone does not guarantee immediate notification.
- **Status:** Theory explained, not experimentally verified. No SQL/DDL requested or implemented.

## Card D — AggregatingMergeTree explanation and actual candidate inference

- **Candidate actual answer/request:** "Давай разберем агрегейтинг merge, как работает, потому что я тоже про него не в курсе. Хотя, ну подожди, агрегейтинг merge 3, скорее всего, покажет, что min и max разные, то, по идее, без дополнительного чтения всей таблицы мы как раз-таки поймем, что они разные, значит у нас на одну и ту же версию какая-то ерунда получилась."
- **Candidate inference:** If aggregated min/max PnL for the same trade/version differ, a same-version conflict can be detected without rescanning all raw rows.
- **Interviewer explanation (not candidate-authored implementation):** AggregatingMergeTree stores intermediate aggregate-function states by sorting key; insert-triggered MV can write minState/maxState for separate blocks; minMerge/maxMerge with GROUP BY consolidates across parts even before background merges. No automatic alert is emitted by the engine; an explicit check is required. Duplicate delivery and NULL semantics need separate handling.
- **Status:** Theoretical only, no DDL, SQL validation, or tests executed.

## Card D — aggregation-state persistence after repeated value

- **Question:** For same trade/version PnL sequence 8.0 → 8.5 → 8.0, do min/max conflict signals disappear after third event?
- **Candidate actual answer:** "Не должен исчезнуть, потому что максимум должен остаться восемь с половиной, а минимум как был, так и будет восьмёркой."
- **Interviewer review:** Correct for min/max aggregate states: minimum remains 8.0, maximum 8.5; incoming duplicate does not erase existing conflict. This does not itself identify authoritative value or correction status.
- **Next question:** Kafka replay of previously processed events and which of min/max/count remain invariant under replay.
- **Status:** Discussion only; no SQL or executions.

## Card E — replay idempotency of aggregate states (actual answer)

- **Question:** After Kafka replay of 100 previously processed events, which of min(PnL), max(PnL), count() remain correct?
- **Candidate actual answer:** "Ну если это те же самые события и там нет каких-то конфликтов, то у нас увеличится только count. Amin и Max будут соответствовать одинаковым значениям, и это будет идентифицировать нам как минимум точно, что дубликаты получились. Ну если другие поля не поменялись, конечно. Это мы не учитываем сейчас."
- **Correct observation:** For identical replayed values, min/max are invariant under duplicate delivery, while raw-delivery count grows.
- **Interviewer correction, not attributed to candidate:** A count increase and unchanged min/max do not alone *prove* duplicate delivery; independent legitimate events can share the same PnL. Need stable event identity and contract. Ingestion-generated ID may not persist across replay.
- **Open follow-up:** Extend aggregation to distinguish 100 replayed deliveries from 100 genuinely new events using stable event_id.
- **Status:** Oral reasoning only; no SQL, tests, or implementation.

## Card E — event identity versus version/status (actual answer)

- **Question:** How to distinguish 100 replay deliveries from 100 legitimate new events, assuming stable event_id?
- **Candidate actual answer:** "Ну, с event ID также можно поступать, потому что event ID, скорее всего, циферное обозначение статуса будет, и у нас будет min и max разные, при том, что count также будет изменён. И мы сможем для одной версии определить, было ли изменение event ID за счёт обновления. Ну, то, что пришла сначала с одним event ID у нас запись, потом той же версии с другим event ID. Так мы сможем отследить."
- **Candidate hypothesis:** Treat min/max event IDs as detecting a change of event identity within one trade/version.
- **Interviewer correction (not attributed to candidate):** event_id should be defined by an explicit immutable event identity contract, not assumed numeric/status or ordered; min/max IDs do not reveal how many distinct events/deliveries exist. With stable event_id, compare delivery count to uniqExact(event_id) to identify repeat deliveries, and separately detect same-event_id conflicting payload. Different event_id at same trade/version can be legitimate separate events or conflict depending on business contract.
- **Open follow-up:** Same event_id but changed PnL on replay — how should DQ classify and alert independently of duplicate count?
- **Status:** Oral-only; no SQL/test execution.

## Card E — same event_id with changed payload (actual answer)

- **Question:** Two records with event_id E100 and version 2 but PnL 8.0 vs 8.5: duplicate, new event, or consistency breach?
- **Candidate actual answer:** "Слушай, но здесь у нас в моем понимании бизнес-конфликт получается, потому что у тебя EID и PNL изменились с одной и той же версии."
- **Interviewer review:** Correctly recognizes a business/payload conflict, not simple duplicate delivery. Correction: EID itself was unchanged (E100 in both records); only PnL changed, with constant version. Under immutable event identity contract this is an event-payload consistency breach. Separate duplicate delivery checks from conflicting payload checks.
- **Next case posed:** MV backfill over 10 million existing events while Kafka continues delivering; prevent misses/double counting and validate cutover.
- **Status:** Oral only; no SQL/DDL/test run.

## Card E — live MV and bounded historical backfill (actual answer)

- **Question:** How to populate new aggregate target from 10 million existing raw events while Kafka continues to deliver events, without misses/double counts?
- **Candidate actual answer:** "Тут сначала пусть считает только для новых сделок и можно взять backfill, к примеру, для какого-то последнего финансового отчетного периода."
- **Candidate proposal:** Start processing fresh data first and backfill a bounded relevant financial-reporting period rather than entire history.
- **Interviewer review (not candidate claim):** Good scoped rollout, but "new trades" must be distinguished from new deliveries/versions on old trades. Asynchronous backfill overlapping with live insert-triggered MV can double-process deliveries; backfill boundaries must be explicit and validated.
- **Open follow-up:** Choose safe boundary between historical and live deliveries, accounting for late versions of previously existing trades.
- **Status:** Oral only; no migrations, code, or validation executed.

## Card E — clarified finality-based backfill eligibility (actual answer)

- **Candidate clarification (verbatim):** "Ну, я изначально подразумевал, что исторический бэкфилл делать для сделок, которые пришли к какому-то конечному состоянию. Например, они filled, и это уже закреплено по каким-то критериям, что её нельзя поменять, эту сделку. То есть filled, и, допустим, с точки зрения бизнеса есть дополнительное требование трёх суток для изменения данных, и только в этом случае эту сделку можно бэкфилить полностью, потому что она не изменится."
- **Candidate proposal clarified:** Restrict historical backfill to trades considered immutable under the hypothetical business contract: FILLED plus a three-day correction window elapsed. Not merely an arbitrary reporting-period cutoff.
- **Interviewer review (not candidate assertion):** Business finality and delivery completeness are separate guarantees. A trade may be unchangeable yet have delayed or replayed deliveries. Finality-based selection alone does not prevent overlap between backfill and incremental MV writes. Also ensure the 72-hour starting point and proof of immutability are explicitly contracted.
- **Open follow-up:** A FILLED trade final on Nov 8 and backfilled receives a replayed Kafka event on Nov 11. How prevent duplicated accounting in MV target?
- **Status:** Theory interview only; no SQL or migration run.

## Card E — finality violation versus replay (actual answer)

- **Question context:** A final/backfilled trade receives an event on Nov 11; how avoid double accounting?
- **Candidate actual answer:** "Но это будет уже прям какой-то экстраординарный случай, если пришел апдейт. Первая же. Это явно будет какой-то... Надо, в общем, в любом случае это будет проработать. То есть если закрытую сделку как-то умудрились провернуть на изменение, тут надо уже смотреть, почему какой-то из вышестоящих сервисов, которые нам продюсят это данные, разрешили такое. Вообще тут может быть уже какой-то секьюрити там."
- **Candidate proposal:** A genuine business update after finality is exceptional; investigate upstream validation and consider possible security implications.
- **Interviewer clarification (not candidate claim):** A replay of an *unchanged* event is not itself a forbidden business update and remains possible with at-least-once delivery. Distinguish duplicate replay from late mutation; security is a hypothesis requiring evidence, not an automatic classification. Need idempotency even for immutable finalized trades.
- **Open follow-up:** Choose primary idempotency enforcement at Kafka consumer, ClickHouse storage, and/or analytical read model for identical replayed event_id after backfill.
- **Status:** Discussion only, no implementation or execution.

## Card E — request for idempotency alternatives and interviewer explanation

- **Candidate actual request:** "Ну, как минимум у Kafka Consumer наверняка есть параметр, насколько старые обрабатывать или нет. Ещё-то я даже не знаю про ClickHouse финальный. накидай мне вариантов, какие есть."
- **Candidate hypothesis:** Kafka Consumer may have configuration to limit the age of messages processed; explicitly requests alternative approaches instead of selecting one.
- **Interviewer explanation (not candidate choice):** Kafka auto.offset.reset controls where consumers start without valid committed offsets (earliest/latest/by_duration), not whether a business event is too old and not end-to-end deduplication. Compared consumer event_id dedup, offset management, ClickHouse block INSERT dedup, ReplacingMergeTree with FINAL, aggregation-state uniqueness, and dedup-before-sum logical read model. Proposed a layered architecture (Kafka → immutable raw → logical current state + conflict checks → account PnL) as **interviewer recommendation**, not candidate decision.
- **Open:** Candidate has not selected a primary idempotency boundary or designed an executable backfill/cutover strategy; no SQL/DDL/verification executed.

## Card E — replay reconciliation metrics (actual answer)

- **Question:** Given 1,000 unique trades, 1,100 physical rows after replay without business-state change, which two checks prove financial PnL is unchanged?
- **Candidate actual answer:** "Ну, можно, в принципе, event ID уникальный и PNL по каждой сделке идентифицировать, правильные ли они или нет. Если там расхождение в минимум-максимум значениях."
- **Candidate proposal:** Compare unique event identities and PnL per trade, detecting min/max discrepancies.
- **Interviewer review (not candidate assertion):** Useful for event coverage and same-version payload conflict, but min/max alone cannot demonstrate that duplicate delivery was not double-counted in sum. Independent invariants proposed: logical latest-state identity and PnL per trade, plus account/reporting-period aggregate PnL reconciliation before/after replay. Illustrative 1,000 unique events requires an explicitly assumed one-event-per-trade contract.
- **Next topic:** Raw TTL 30 days; financial discrepancy for a trade older than 45 days, with aggregates but no raw data in ClickHouse. How investigate and recover?
- **Status:** Oral only; no SQL or validation run.
