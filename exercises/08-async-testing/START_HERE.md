# Session 08 — Deterministic Async Polling Lab

**Focused practice:** 35–45 minutes; questions and feedback entirely in Russian.

## Prepared components

- [Manual clock and eventually-visible feed](support/fake_time.py) — zero real-time waiting, configurable visibility and transient-read failures.
- [Incomplete polling function](starter/wait_until.py) — provides signature and error type, **not** the solution.
- [Scenario contract](SCENARIOS.md) — exact behavior to validate.

## Launch

```bash
uv sync --group dev
uv run pytest -q tests/labs
```

The readiness tests validate fake-time mechanics only. They do not claim `wait_until` works.

## Interview task

Implement `async wait_until(...)` with monotonic deadlines, configurable interval, retry policy and diagnostics. Use `asyncio.run` for simple local tests (no additional async pytest plugin required). Write tests showing success after delayed visibility, timeout, transient read failure and no busy-wait.

## Acceptance

- No real `sleep(1)`-style wall-clock waiting in deterministic unit tests.
- A predicate exception is not silently swallowed without the explicit policy.
- Bounded retries use the same deadline across exceptions and attempts.
- Timeout reports attempts, elapsed time and last observed value or failure.

## Interview kickoff prompt

> Проведи сессию 08 для Exness на русском. Открой fake_time.py, wait_until.py и SCENARIOS.md. Попроси меня реализовать алгоритм ожидания eventual consistency и обосновать retry/timeout/cancellation. Не решай TODO заранее; задавай вопросы по моим тестам и по сложным случаям.
