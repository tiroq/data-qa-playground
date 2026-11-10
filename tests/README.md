# Testing layout

The repository uses independent test layers. A green CI run verifies only the
boundary exercised by that test, not the full production trading pipeline.

- `tests/unit/`: Session 05 comparator and Data Quality rules.
- `tests/labs/`: lab readiness checks only.
- `tests/session07/`: deterministic in-memory fake, event manifest set/Counter
  reconciliation, payload and version conflict checks, deliberate-empty and
  unexpected-empty scenarios. No Docker required.
- `tests/integration/`: PostgreSQL and ClickHouse Testcontainers, a real
  localhost HTTP 202 service with a controlled worker, and a Kafka broker
  boundary test. All require Docker. The Kafka test has a dedicated marker
  and a separate workflow job.
- `tests/e2e/`: external production-equivalent deployment tests are NOT
  implemented. The localhost teaching HTTP service is intentionally synthetic.

Full lab commands, run scopes, cleanup strategies and limitations:
[Session 07 test coverage](../exercises/07-pytest-architecture/TEST_COVERAGE.md).

No unexpectedly empty data may count as PASS. Deliberately empty input
requires an explicit scenario contract.
