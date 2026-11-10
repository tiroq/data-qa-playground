# Testing layout — introduced as functionality is implemented

The executable PostgreSQL baseline check is `postgres/checks/smoke.sql` via Docker Compose. Tests are added as their contracts become meaningful.

- `tests/unit/`: Python comparators and Data Quality rule logic.
- `tests/labs/`: lab readiness checks; these do **not** prove exercise completion.
- `tests/session07/`: runnable **in-memory fake** contract examples and independent pure-Python event-ID manifest checks for Session 07, including parametrization, duplicate-masks-missing negative control and a no-empty-PASS guard. Run with `uv run pytest -q tests/session07`.
- `tests/integration/`: **real PostgreSQL Testcontainers** transaction-isolation and committed-writer checks for Session 07. They do **not** exercise HTTP API, Kafka, or ClickHouse. Run with Docker, `uv run --with 'testcontainers[postgres]>=4.10,<5' --with 'psycopg[binary]>=3.2,<4' pytest -q tests/integration`. ClickHouse integration is still pending.
- `tests/e2e/`: future full-path checks; not implemented.

Required guard: no unexpectedly empty dataset can be counted as PASS. A deliberately empty input may be valid only under an explicit contract.

Do not present fake tests as full database integration, and do not add placeholder tests that always pass.
