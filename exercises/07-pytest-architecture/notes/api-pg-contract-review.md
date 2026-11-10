# Session 07 — API-to-PostgreSQL Contract Review

**Status:** Discussed with learner; database-only executable analogue added. This is **not** an API E2E test, because the repository has no running HTTP API path for this exercise.

## Learner's design

- Identify a trade by the ID sent in the request or returned from the API.
- After HTTP 202, use bounded polling to wait for an expected trade in PostgreSQL without assuming the response implies persistence.
- Query by `(trade_id, account_id, version)`; compare `pnl` and `status` against the contract.
- Detect physical duplicates and conflicting payloads even when one correct payload exists.
- Use soft assertions (for example the third-party `pytest-assume` plugin) to collect multiple failure details.

## Review

- Keep **readiness** (a record exists within the timeout) separate from **correctness** (physical row count, exact payload, no conflict). Whether a transient invalid state should fail immediately depends on the actual business contract.
- One SQL statement with conditional aggregates evaluates checks on the same PostgreSQL READ COMMITTED snapshot. Three separate SELECTs may see different committed states.
- For a strict one-record-per-key-and-version contract, expected: `total=1`, `matching=1`, `conflicting=0`. The three distinct failure channels must all be reported.
- `pytest.assume` is not built into pytest; `pytest-assume` is an optional plugin. The checked-in lab uses a list of diagnostic errors instead, avoiding an extra dependency.
- A single snapshot cannot prove that no conflicting event arrives **after** PASS. For that, define processing completion/watermark or a bounded stability window.
- A separately committed database writer can demonstrate transaction boundaries, but it **does not** verify API response 202, HTTP/network behavior, queue delivery, or ClickHouse persistence.
- Unique per-test business identifiers and a function-scope cleanup handle synchronous writes. Late events require stronger isolation or a lifecycle barrier.

## Files

- [Actual PostgreSQL fixture](../../../tests/integration/conftest.py): lab07 trade_events table and cleanup fixture.
- [Executable data-contract test](../../../tests/integration/test_committed_trade_contract.py): real PostgreSQL, one-query diagnostics, positive and negative scenarios.
- [Integration workflow](../../../.github/workflows/session07-postgres-integration.yml): executes both PostgreSQL test files in a disposable container.

## Remaining exercises

1. Substitute a real API client and API+PostgreSQL service environment for the synthetic writer.
2. Specify how `202 Accepted` correlates to a stable `trade_id`.
3. Define a business-completion signal that prevents late-arriving duplicates from evading an early PASS.
4. Add ClickHouse reconciliation with raw-event and latest-state semantics separated.
