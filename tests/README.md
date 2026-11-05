# Testing layout — introduced as functionality is implemented

Currently the executable baseline check is `postgres/checks/smoke.sql` via Docker Compose. Additional `tests/unit/`, `tests/integration/` and `tests/e2e/` test code must be added with the exercises that make it meaningful.

- Unit tests: Python comparators, DQ classification, polling clock behavior.
- Integration tests: PostgreSQL/ClickHouse adapters with isolated fixtures and explicit setup/cleanup.
- End-to-end tests: delayed/replayed delivery and source-to-aggregate reconciliation only when an actual path exists.
- Required guard: no unexpected empty dataset may be counted as a PASS.

Don't claim these suites exist yet or create placeholder tests that always pass.
