# Session 06 — Ready-to-run Data Quality Lab

**Target practice:** 30–45 minutes of focused interview discussion + implementation. **Language:** interact in Russian; code and written artifacts in English.  
**Scope:** synthetic trading batches, no database required. Existing Session 05 logic is not assumed complete.

## Start

From the repository root:

```bash
uv sync --group dev
uv run pytest -q tests/labs tests/unit/test_dq_rule_runner.py

# Human-readable report for all cohorts (default bundled JSON fixture):
uv run python exercises/06-data-quality-rules/starter/rule_runner.py

# Evaluate only the healthy cohort:
uv run python exercises/06-data-quality-rules/starter/rule_runner.py --cohort mostly_healthy

# Machine-readable results, optionally persisted to a file:
uv run python exercises/06-data-quality-rules/starter/rule_runner.py --format json --output dq-report.json

# Supply another fixture in the same schema:
uv run python exercises/06-data-quality-rules/starter/rule_runner.py path/to/dq_batches.json --format json
```

Exit codes: `0` means all selected cohorts passed; `1` means at least one cohort failed or is indeterminate; `2` means invalid input or a runner error. The bundled fixture **intentionally includes failures**, so running all three cohorts exits with `1`; this is not a script crash.

## Report semantics

- Each cohort reports physical record count, count of observed nonempty distinct event IDs, and the supplied `expected_events` and `as_of`. The observed ID count is **not** a measured completeness or on-time SLA.
- Each **implemented** rule returns one explicit outcome (PASS, FAIL or INDETERMINATE), its severity, and individual issues. Rules without implementations are **not reported as PASS**.
- The independent input gate fails for an unexpectedly empty cohort (`expected_events > 0`). When no records exist, DQ-01 is INDETERMINATE: no fields were actually examined. An empty cohort with zero expected events is still INDETERMINATE until an explicit empty-cohort policy is implemented.
- The overall gate fails for an input failure or a `critical` rule failure; any remaining indeterminate evaluation prevents PASS. A `warning` rule failure stays visible without automatically blocking a cohort.
- Current implemented rules: **DQ-01 required-field presence/nullability** and **DQ-02 identical event-ID re-delivery**. The rules do not yet validate blank strings, version domain, valid statuses, completeness, conflicting event payloads (DQ-03), freshness, or SLA. These remain future exercises.

## Files

- [Input cohorts](fixtures/dq_batches.json): one valid-looking batch, one mixed-anomaly batch, one empty batch.
- [Rule contract](CONTRACT.md): physical grain, business rules, provisional rule list, denominator policy and failure cases.
- [Shared result model](starter/rule_result.py): immutable DQ outcome.
- [Implemented checkers](starter/checkers.py): learner's DQ-01 plus room to add future checks.
- [CLI runner](starter/rule_runner.py): cohort execution, gate and text/JSON reports.
- [Primary session brief](README.md).

## Next live exercise

1. Define at least 10 independently measurable DQ checks. For each name the grain, denominator, severity, time cutoff and evidence.
2. **DQ-02** now detects identical replay and is registered in `evaluate_rules`. Next design **DQ-03** for conflicting payloads sharing an `event_id`.
3. Discuss per-record defects vs aggregate SLO/SLA, thresholds, late events and safe alerting.

Do not claim unimplemented rules have passed.

## Interview kickoff prompt

> Продолжаем подготовку к Exness Data Stack QA; всё общение на русском. Прочитай этот START_HERE.md, CONTRACT.md и JSON-фикстуры в GitHub. DQ-01 и CLI runner уже подключены, но DQ-02 и SLA ещё не реализованы. Проведи ревью текущего DQ-01, затем дай практическое задание на DQ-02 и DQ thresholds/alerting. Не раскрывай решения заранее. Код на английском, объяснения на русском.
