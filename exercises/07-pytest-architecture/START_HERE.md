# Session 07 — Pytest Architecture Prebuilt Lab

**Focused practice:** 60 minutes. Discuss all tasks and review in Russian. Python and repository documents are in English. Session 05 remains the learner's existing implementation; do not overwrite it.

## Prebuilt assets

- [In-memory processing fake](support/fake_pipeline.py): deterministic API-style submission and queued processing, with a failure switch.
- [Scenario matrix](fixtures/api_cases.json): exact input and expected lifecycle for healthy, failed and duplicate calls.
- [Pytest design contract](TEST_DESIGN.md): fixture scope and isolation constraints.
- [Original full brief](README.md).

## Start

```bash
uv sync --group dev
uv run pytest -q tests/labs
python exercises/07-pytest-architecture/support/fake_pipeline.py
```

The final command is only a smoke demonstration. **Do not confuse it with a real PostgreSQL/ClickHouse integration test.**

## Live assignment

1. Design `tests/integration/conftest.py` fixtures for database lifecycle, deterministic seeds, per-test isolation and teardown. Explain `function` vs `session` scope.
2. Write parameterized tests for the supplied API cases; show an intentionally empty dataset that must **fail**.
3. Propose which parts require actual PostgreSQL + ClickHouse Testcontainers, and which can be verified with the fake.
4. Show how retries, cleanup on failure and fixtures under parallel pytest workers would behave.

## Acceptance

- No state leakage between cases; no false green results when tests skip processing.
- Clear separation between fake-level verification and actual integration coverage.
- Reproducible setup and teardown, even if assertions fail.
- Identified risk: the Session 05 `xfail(strict=True)` cases do not represent feature completion.

## Interview kickoff prompt

> Продолжаем Exness Data Stack QA. Всё обсуждение и обратная связь на русском; Python-код на английском. Изучи START_HERE.md, fake_pipeline.py, TEST_DESIGN.md и текущий код Session 05. Попроси меня спроектировать pytest fixtures и написать тесты, не предоставляя готовых решений. Спрашивай об изоляции, scope, teardown, no-empty-PASS и границах настоящих интеграционных проверок.
