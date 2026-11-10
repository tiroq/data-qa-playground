# Session 07 — PostgreSQL Transaction Isolation Exercise

**Status:** Learner approach reviewed; executable integration test verified in GitHub Actions (2026-11-10). The broader Session 07 exercise remains in progress.

## Learner approach

1. INSERT a unique trade using connection A.
2. SELECT COUNT(*) by trade ID using A; expect 1.
3. SELECT COUNT(*) by the same trade ID using B; expect 0.
4. ROLLBACK connection A.
5. SELECT COUNT(*) again using A; expect 0.

## Review and refinements

- Correct under PostgreSQL's default READ COMMITTED semantics: own uncommitted changes are visible to their writer, but not to a different connection.
- Added an assertion on B **after** rollback, to observe the final state from both connections.
- Generate a unique trade ID per test, so concurrent runs have independent business keys.
- CREATE SCHEMA/TABLE is done once and committed in a session-scoped container fixture, not repeated per test.
- The test is self-contained and does not depend on other pytest tests running before it.
- **Important limitation:** An explicit rollback within the test does not demonstrate the teardown of a function-scoped connection fixture. That requires its own test/fixture lifecycle proof.
- **Important limitation:** This does not cover API-created committed writes or any ClickHouse/queue state. Those boundaries need separate isolation/cleanup contracts.

## Run

From the repository root with a running Docker daemon:

```bash
uv sync --group dev
uv run --with 'testcontainers[postgres]>=4.10,<5' --with 'psycopg[binary]>=3.2,<4' \
    pytest -v tests/integration/test_transaction_isolation.py
```

Run against a **disposable PostgreSQL container**; it does not use the repository's docker-compose PostgreSQL seed. The `--with` dependencies keep this teaching-only integration exercise separate from the default locked unit-test environment.

## Runtime verification

- GitHub Actions: [Session 07 PostgreSQL Testcontainers integration](https://github.com/tiroq/data-qa-playground/actions/runs/42799506346) — **SUCCESS**, actual disposable PostgreSQL container on CI runner.
- Verified commit: `5fb98bb46b5944d1ef7b6ef9f6f38aef5fba75a3`.
- Local Docker execution was not performed in this ChatGPT session.

## Follow-up task

Demonstrate that a function-scoped fixture rolls back an uncommitted INSERT after both successful and failing assertions, without depending on test order; then discuss committed API writes and async delivery.
