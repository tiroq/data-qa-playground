# Session 08 — Async Testing — Eventual Consistency

**Date (Asia/Bangkok):** 2026-11-11 · **Duration:** 60 minutes · **Status:** IN PROGRESS (oral review completed; assistant-authored reference code committed; Session 08-specific CI verification pending)  
**Track:** Exness QA Engineer (Data Stack) interview preparation

> **Language contract:** The actual technical interview is in **Russian**. All live tasks, discussion, follow-up questions, code review, mock interviews, and feedback in ChatGPT must be **in Russian**. SQL, Python, identifiers, and technical terms may remain in English. This repository's written exercise specifications are in English.

## Ready-to-run laboratory (prebuilt)

Start with [START_HERE.md](START_HERE.md): it links to verified input materials, setup commands, and deliberately incomplete learner implementation. Discuss all code and answers in Russian. **Fixture readiness is not interview-task completion.**

## Goal

Test asynchronous processing without brittle sleeps or unbounded waits.

## Practical assignment

1. Implement a bounded `wait_until` helper using a monotonic deadline and configurable poll interval.
2. Use it to assert eventual arrival of a processed trade; report last observed state on timeout.
3. Test timeout, transient exception policy, cancellation, late success, duplicates and stale reads.
4. Discuss retry-safe reads versus unsafe repeated writes.

## Contracts and constraints

- No fixed sleep used as the sole success assertion.
- A timeout must be finite and produce actionable diagnostics.
- Poll cadence and maximum duration are explicit.

## Acceptance criteria

- [x] Unit tests authored for success and failure (execution not yet verified).
- [x] Bounded monotonic polling implemented.
- [x] Documented distinction between eventual consistency and exactly-once business effects.

## Artifacts to add **during** this session

- Reusable wait helper in `src/data_qa/`
- `tests/unit/` verification and short rationale

Do not add a reference solution before the learner has attempted the assignment. Preserve original attempts and explain fixes in separate files or commits.

## Standalone ChatGPT kickoff prompt (Russian)

> Ты — технический интервьюер Exness QA Engineer (Data Stack). Реальное интервью 16 ноября 2026 года проходит **на русском языке**. Проводим сессию 08: «Async Testing — Eventual Consistency» (60 минут), и **всё общение — на русском**, включая задачу, вопросы, оценку, обсуждение SQL/Python-кода и разбор ошибок. Код и общепринятые технические названия могут быть на английском. Мой контекст: Python/Go SDET, FIX и post-trade, reconciliation, нагрузочное тестирование, CI, NATS JetStream; слабее практический ClickHouse и Kafka/Flink. Первая SQL-диагностика пройдена успешно, но нужно особенно проверять JOIN cardinality, полноту output columns, группировку на бизнес-ключ, версии и крайние случаи. Открой в GitHub репозитории `tiroq/data-qa-playground` файл `exercises/08-async-testing/README.md`; используй задание и acceptance criteria как основной контракт. Начни с одной практической задачи, дождись моего решения, не показывай эталон заранее. Далее проведи code review и follow-up, оцени от 0 до 10 и назови три точечных пробела. Сохраняй в репозитории только действительно выполненные решения и подтверждённые результаты.

## Session result (fill **after** completing)

- **Attempt:** oral design discussion, no learner-authored code; reference implementations added on branch.
- **Score / 10:** 8/10 (oral reasoning only; code not graded).
- **What worked:** monotonic deadlines, bounded sleeps, retry diagnostics, predicate separation of concerns.
- **Bugs / edge cases:** async cancellation unfamiliar; snapshot/delta initially confused; deadline boundary clarified.
- **Next-session adjustments:** practice asyncio, idempotent effects, deterministic fake-clock testing.

## Deadline-boundary contract still requires reconciliation

The learner discussed a possible fourth predicate call at exactly t=1.0 for timeout=1.0 and interval=0.4. The currently documented reference contract and deterministic test instead allow starts at t=0, 0.4 and 0.8, with no new attempt at or after t=1.0. **Neither should be called the uniquely correct policy without an explicitly chosen boundary contract.** This has been added to the [final rehearsal](../17-final-review/GAP_REHEARSAL.md). No test or algorithm was changed by the audit.

## Reference implementations and tests (added after oral attempt)

- [wait_until.py](wait_until.py): synchronous basic and diagnostic helpers.
- [wait_until_async.py](wait_until_async.py): asyncio equivalents.
- [test_wait_until.py](test_wait_until.py): deterministic pytest tests.

Run with `python -m pytest -q exercises/08-async-testing/test_wait_until.py` (requires pytest and pytest-asyncio). Test execution/CI result has **not** been verified here.

### Explicit helper contract

- Deadline uses monotonic time. The initial observation is allowed even when timeout=0.
- Once an attempt has occurred, a new predicate call is not started at or after deadline. A call started before deadline can complete after it and still succeed (soft timeout); use driver-level request timeouts for blocking calls.
- Sleep duration is `min(interval, remaining)`; no busy wait.
- Only exceptions listed in `retry_exceptions=(ConnectionError, ...)` are retried; default is empty. Fatal errors propagate. Do not catch cancellation.
- No successful reads + only transient exceptions raises `ObservationUnavailable`; otherwise `WaitTimeout` includes counts, last value, bounded recent history and chained last error.
- `wait_until` checks a generic truthy predicate; business assertions, replica convergence, DQ uniqueness and SLA measurement remain separate.

### Discussed scenarios and expected behavior

| Scenario | Expected |
| --- | --- |
| 1.0s timeout, 0.4s interval | Calls at 0, 0.4, 0.8; deadline at 1.0; 3 calls |
| Late success: call starts 9.99s, finishes 10.14s | Accepted under soft deadline; not proof of SLA |
| None then two ConnectionError then PROCESSED | Success; retry diagnostics retained during polling |
| All ConnectionError | ObservationUnavailable with error counts and last cause |
| Some None and some ConnectionError | WaitTimeout with mixed history |
| Non-allowlisted exception | Immediate propagation |
| Ctrl+C / Task.cancel() | KeyboardInterrupt / CancelledError propagated |
| Async poll with time.sleep | Blocks event loop; use await asyncio.sleep |
| Replica A v2 and B v1 | One read success proves observation only, not convergence |
| ReplacingMergeTree with v1 and v2 | FINAL or deterministic latest-version selection; FINAL cannot replicate absent rows |
| Duplicate Kafka delivery after offset commit failure | Physical duplicates may be allowed; logical effect must be idempotent |
| Snapshot PnL v1=100, v2=150, replay v1 | Current PnL 150 |
| Delta PnL v1=+100, v2=+50, replay v1 | Aggregate 150 after dedup by contractual operation identity |
| SLA from cross-host timestamps | Account for timestamp semantics and clock synchronization uncertainty |
| Repeated writes during polling | Avoid non-idempotent writes; polling should normally repeat reads |

### Interview design notes

The learner verbally chose a generic predicate-based helper rather than embedding replica-specific stability checks. DQ uniqueness should be a separate suite across controlled test records, including explicit idempotency assertions for intentionally duplicated inputs. The learner suggested capturing observation history and distinguishing infrastructure unavailability from an unmet predicate. The reference code is assistant-authored and is **not evidence of learner coding proficiency**.

**Weakest link:** no runtime proof or integration with live ClickHouse/Kafka; fake tests demonstrate helper behavior and illustrate data contracts, not distributed-system guarantees.
