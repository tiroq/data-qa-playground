# Session 07 — Pytest Architecture Prebuilt Lab

**Focused practice:** 60 minutes. Discuss all tasks and review in Russian. Python and repository documents are in English. Session 05 remains the learner's existing implementation; do not overwrite it.

## Prebuilt assets

- [In-memory processing fake](support/fake_pipeline.py): deterministic API-style submission and queued processing, with a failure switch.
- [Scenario matrix](fixtures/api_cases.json): exact input and expected lifecycle for healthy, failed and duplicate calls.
- [Pytest design contract](TEST_DESIGN.md): fixture scope and isolation constraints.
- [Starter pytest suite](../../tests/session07/test_pipeline.py) and [fixture setup](../../tests/session07/conftest.py): minimal runnable fake-based examples, **not** real database integration coverage.
- [Original full brief](README.md).

## Start

From the repository root:

```bash
uv sync --group dev
uv run pytest -q tests/labs
uv run pytest -q tests/session07
python exercises/07-pytest-architecture/support/fake_pipeline.py
```

The first test command checks lab preparation only. The second exercises the in-memory fake's supplied case matrix. The final command is a smoke demonstration. **None of these is a real PostgreSQL/ClickHouse integration test.**

The baseline is starter material, not a learner interview attempt or a completed exercise. The dedicated CI workflow `.github/workflows/session07-fake-tests.yml` runs only the fake contract tests.

## Live assignment

1. Review the starter fixture architecture and defend `function` vs `session` scope. Explain teardown on setup failures, assertion failures and parallel workers.
2. Extend the parametrized tests with independently meaningful failure diagnostics and no-empty-PASS assertions. Distinguish the intentionally empty case from accidentally missing processing.
3. Design `tests/integration/conftest.py` for real PostgreSQL and ClickHouse Testcontainers: database lifecycle, deterministic seeds, namespace/schema isolation and reliable cleanup.
4. Decide which checks belong to unit, fake contract, real integration and E2E suites. Account for retries and idempotence without confusing the fake with production semantics.

## Acceptance

- No state leakage between cases; no false green results when tests skip required processing.
- Clear separation between fake-level verification and actual integration coverage.
- Reproducible setup and teardown, even if assertions fail.
- Identified risk: the Session 05 `xfail(strict=True)` cases do not represent feature completion.

## Interview kickoff prompt

> Продолжаем Exness Data Stack QA. Всё обсуждение и обратная связь на русском; Python-код на английском. Изучи START_HERE.md, fake_pipeline.py, TEST_DESIGN.md и текущий код Session 05. Проведи ревью starter fixtures и тестов, попроси меня самостоятельно расширить архитектуру. Спрашивай об изоляции, scope, teardown, no-empty-PASS и границах настоящих интеграционных проверок.
