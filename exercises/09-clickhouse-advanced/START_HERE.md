# Session 09 — Start Here: Oral ClickHouse Interview

**Default mode:** theoretical **conversation in Russian** (up to 60 minutes). There is **no Docker setup, SQL coding or code generation required** to begin.

## Carry-forward weakness probes

Read [GAP_PROBES.md](GAP_PROBES.md) to target the observed Sessions 01–08 gaps. **Keep the prompts oral; do not read or write answers ahead of the candidate.**

## Start in three steps

1. Open [THEORY_SESSION.md](THEORY_SESSION.md) for the moderator's 60-minute flow.
2. Use [SCENARIO_CARDS.md](SCENARIO_CARDS.md) one card at a time. They are grounded in the existing 12-row synthetic fixture; **do not expose answers in advance**.
3. After each actually discussed case, record reasoning in [discussions/](discussions/) using [DISCUSSION_RECORD_TEMPLATE.md](DISCUSSION_RECORD_TEMPLATE.md). Fill [DECISION_MATRIX.md](DECISION_MATRIX.md) only when alternatives were genuinely compared.

**Interview prompt (copy into a new ChatGPT conversation):**

> Проводи Session 09 как устное техническое интервью по ClickHouse Advanced на русском, максимум 60 минут. Открой в `tiroq/data-qa-playground` файлы `exercises/09-clickhouse-advanced/THEORY_SESSION.md`, `SCENARIO_CARDS.md` и `DECISION_MATRIX.md`; проверь факты фикстуры `clickhouse/init/02-seed.sql`. Давай по одному вопросу или кейсу и жди моего ответа, затем проверяй допущения, задавай follow-up и контрпример. Не заставляй писать SQL и не раскрывай эталон заранее. По результатам каждого кейса сохраняй в GitHub только мои реальные ответы, рассмотренные альтернативы, выводы и открытые вопросы. Код/SQL создавать лишь по отдельному решению после обсуждения. В конце дай оценку /10 и три приоритета.

## Optional runnable lab — only if we decide to validate something

The existing synthetic `lab03.trade_versions` contains 12 physical records and 6 logical business keys. `lab09.raw_events` can be recreated as an isolated copy for verifying an agreed hypothesis.

```bash
docker compose --profile clickhouse up -d --wait clickhouse
docker compose --profile clickhouse exec -T clickhouse \
  clickhouse-client --user qa --password qa --multiquery < clickhouse/fixtures/09-advanced.sql
docker compose --profile clickhouse exec -T clickhouse \
  clickhouse-client --user qa --password qa --multiquery < clickhouse/checks/09-advanced-smoke.sql
```

**Warning:** `09-advanced.sql` destroys and recreates **only `lab09`** on every invocation. It does not modify `lab03`, but it will erase any unsaved work stored in `lab09`. The smoke checks are fixture readiness only, not acceptance of any learner SQL.

Optional implementation ideas remain in [BACKFILL_BRIEF.md](BACKFILL_BRIEF.md). No claims of execution are made by this documentation.
