# Session 06 — Ready-to-run Data Quality Lab

**Target practice:** 30–45 minutes of focused interview discussion + implementation. **Language:** interact in Russian; code and written artifacts in English.  
**Scope:** synthetic trading batches, no database required. Existing Session 05 logic is not assumed complete.

## Start

```bash
uv sync --group dev
uv run pytest -q tests/labs
python exercises/06-data-quality-rules/starter/rule_runner.py exercises/06-data-quality-rules/fixtures/dq_batches.json
```

The last command displays the provided batch labels, *not* a quality verdict.

## Files

- [Input cohorts](fixtures/dq_batches.json): one valid-looking batch, one mixed-anomaly batch, one empty batch.
- [Rule contract](CONTRACT.md): physical grain, business rules, provisional rule list, denominator policy and failure cases.
- [Starter runner](starter/rule_runner.py): data loading and strongly typed result shape; `evaluate_rules` is deliberately unimplemented.
- [Primary session brief](README.md).

## Live exercise (do not solve in advance)

1. Define at least 10 independently measurable DQ checks. For each name the grain, rule denominator, severity, time cutoff and evidence.
2. Implement at least **two** checks using the provided input: (a) non-vacuous completeness or required-fields; (b) duplicate **event ID**, distinguishing retries of a business trade.
3. Define a severity gate that can fail on critical violations but keep the full anomaly report.
4. Challenge the policy: is a 4% late share a failure under a 95% on-time SLA? What about the empty cohort?
5. Explain differences between `event_id`, business trade key and current version.

## Done when

- A reproducible command shows pass/fail with **nonzero eligible count** unless the contract explicitly allows zero.
- Each failure identifies dataset, rule, business/event identity and reason.
- No rule treats every repeated `trade_id` as an illegal duplicate.
- The learner writes the solution, not the preparation code.

## Interview kickoff prompt

> Продолжаем подготовку к Exness Data Stack QA; всё общение на русском. Прочитай этот START_HERE.md, CONTRACT.md и JSON-фикстуры в GitHub. Дай одну практическую DQ-задачу, дождись моего решения, проверь denominator, семантику дублей, пустой датасет и SLA. Код на английском, объяснения на русском. Не заполняй `evaluate_rules` заранее. После решения оценка /10 и три конкретные ошибки.
