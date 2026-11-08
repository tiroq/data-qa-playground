# Session 04 — Source-to-Target Reconciliation & SLA

**Date (Asia/Bangkok):** 2026-11-07 · **Duration:** 90 minutes · **Status:** IN PROGRESS (guided SQL and assertions authored; runtime verification pending)  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Goal

Build a trustworthy reconciliation report that resists join multiplication and false latency alarms.

## Practical assignment

1. Define source and target grains separately; allow repeated keys on both sides in an additional **session-owned** fixture.
2. Aggregate each side at its business grain **before** joining; show a failure case for a naive many-to-many join.
3. Classify missing, orphan, duplicates, mismatched values, failed and unknown status without losing secondary flags.
4. Measure `processed_at - created_at` with an explicit eligible population, event-time cutoff and SLA: at least 95% within 10 minutes. Separate late records from an SLA breach.
5. Explain reconciliation windows, watermark, consumer lag and when a provisional missing record becomes actionable.

## Contracts and constraints

- Original Session 01 source keys are unique; construct an additional fixture to simulate duplicated source keys, rather than altering the original seed.
- Never count an outer join's fabricated null-side row as a real target record.
- SLA numerator and denominator must be defined over the same eligible cohort; no division-by-zero or null timestamp ambiguity.

## Acceptance criteria

- [ ] Cardinality checks protect the report from accidental record multiplication.
- [ ] Required columns and independent anomaly flags are complete.
- [ ] The SLA decision matches its definition on a small hand-computed example.
- [ ] Explicit policy for in-flight, late and invalid-key records.

## Artifacts to add **during** this session

- New scenario fixture, reconciliation SQL and verification assertions
- `notes/04-reconciliation-review.md` documenting edge cases

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Guided SQL implementation (2026-11-08)

The learner completed substantial **interactive design reasoning** and requested
the interviewer to write the SQL instead of doing further manual live coding.
The following files are therefore **interviewer-authored guided implementation
drafts**, not an independent candidate SQL submission:

- [01-fixture.sql](sql/01-fixture.sql): isolated `lab04` source/target staging
  snapshots, version ties, invalid keys and deterministic delivery cohorts.
- [02-reconciliation.sql](sql/02-reconciliation.sql): independent source and
  target aggregation BEFORE a FULL JOIN, plus version-aware mismatch flags.
- [03-sla.sql](sql/03-sla.sql): delivery-event cohort, ten-minute deadline,
  late/overdue/in-flight events and 95% SLA decision.
- [04-assertions.sql](sql/04-assertions.sql): explicit cardinality, business-key,
  null, version-tie and SLA sample assertions.

**Run from the repository root with Docker running:**

```bash
docker compose up -d --wait
for f in exercises/04-reconciliation/sql/0{1,2,3,4}-*.sql; do
  docker compose exec -T postgres psql -U qa -d trading \
    -v ON_ERROR_STOP=1 -f /dev/stdin < "$f"
done

docker compose exec -T postgres psql -U qa -d trading \
  -c "SELECT * FROM lab04.sla_summary ORDER BY cohort_label;"
docker compose exec -T postgres psql -U qa -d trading \
  -c "SELECT * FROM lab04.reconciliation_report ORDER BY trade_id, account_id;"
docker compose exec -T postgres psql -U qa -d trading \
  -c "SELECT * FROM lab04.invalid_keys ORDER BY side, physical_id;"
```

The fixture is idempotent by dropping **only** schema `lab04` on reload; it
does not change Session 01/02 data. The SQL operates on *staged snapshots*
in PostgreSQL: it does **not** assume a direct SQL JOIN across PostgreSQL and
ClickHouse servers.

**Expected assertions (not yet observed in a running PostgreSQL instance):**

- 14 valid business keys in the report, one row per key.
- Sum of source counts = 15, sum of target counts = 17; 3 invalid-key rows
  quarantined separately.
- Trade 101 has source_count=2 and target_count=2 (no four-row JOIN inflation).
- Trade 108 has a missing latest version; 110 has target-ahead version;
  111 has conflicting latest payload including NULL; 112 has a historical
  version conflict but an unambiguous matching latest state.
- SLA `pass_95`: 19 of 20 on time, one late, 95.00%, **PASS**.
- SLA `fail_90`: 18 of 20 on time, one late, one undelivered overdue,
  90.00%, **FAIL**. Three new in-flight events are excluded, one
  malformed timestamp is separately flagged.

**Business definitions / limits:**

- Business key is `(trade_id, account_id)`. Any row with a NULL component
  goes into `invalid_keys`; it must not be called MISSING or ORPHAN.
- More than one *version* per trade is normal. The duplicate flag refers to
  repeated **key plus version**, not simply `COUNT(*) > 1` on the trade.
- `amount_mismatch = NULL` means *not evaluated*, due to missing side,
  unequal versions, or conflicting latest version; not the same as `FALSE`.
  Null-vs-null compares equal but `has_null_amount` still flags bad input.
- `has_failed` and `has_unknown_status` are observed across the target's
  physical history, not necessarily the status of the final business state.
- SLA is per **unique event_id**, not physical delivery receipts. Query-visible
  `available_at` is a simulated trusted observation; in a real pipeline this
  requires an independently measured availability/commit contract.
- The fixed `evaluated_at` and `event_cutoff` make examples reproducible.
  The SLA cohort includes only source events whose 10-minute deadlines have
  matured. Watermark/consumer lag are diagnostic signals and do not extend SLA.
- These fixtures do not model a transactionally consistent CDC snapshot or
  prove a real ClickHouse insert. Source commit ordering and downstream PnL
  reconciliation are further production integration tests.

**Runtime verification:** not performed here. Do not mark checkboxes or CI green
until the exact PostgreSQL command output has been observed.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 04: «Source-to-Target Reconciliation & SLA» (90 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/04-reconciliation/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt / PR:** _not yet completed_
- **Score / 10:** _not assessed_
- **What worked:** _not assessed_
- **Bugs / edge cases:** _not assessed_
- **Next-session adjustments:** _not assessed_
