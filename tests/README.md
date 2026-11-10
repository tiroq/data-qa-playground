# Testing layout — introduced as functionality is implemented

The executable PostgreSQL baseline check is `postgres/checks/smoke.sql` via Docker Compose. Tests are added as their contracts become meaningful.

- `tests/unit/`: Python comparators and Data Quality rule logic.
- `tests/labs/`: lab readiness checks; these do **not** prove exercise completion.
- `tests/session07/`: runnable **in-memory fake** contract examples for Session 07, including parametrization and a no-empty-PASS negative control. Run with `uv run pytest -q tests/session07`.
- `tests/integration/`: future real PostgreSQL/ClickHouse adapter tests, requiring isolated lifecycle and cleanup; not implemented for Session 07.
- `tests/e2e/`: future full-path checks; not implemented.

Required guard: no unexpectedly empty dataset can be counted as PASS. A deliberately empty input may be valid only under an explicit contract.

Do not present fake tests as full database integration, and do not add placeholder tests that always pass.
