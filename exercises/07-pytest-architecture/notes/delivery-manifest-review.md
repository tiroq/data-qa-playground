# Session 07 — Physical Delivery Manifest Checker

**Learner conclusion:** matching total row counts are not proof of complete delivery; a duplicate can mask a missing event. `set` compares identities and `Counter` measures multiplicity.

## Implemented and tested

- [Pure Python checker](../../../src/data_qa/delivery_manifest.py): `reconcile_delivery(expected, actual, planned_count=...)`.
- [Regression tests](../../../tests/session07/test_delivery_manifest.py): total-count masking, equal distinct counts but wrong IDs, missing+unexpected+duplicate simultaneously, valid empty input, invalid unexpected-empty setup.
- Aggregates are diagnostics, but the authoritative check compares exact event ID populations.
- An explicit `planned_count` catches an accidentally empty source manifest. It must be independently declared by the test scenario, not computed as `len(expected)` inside the test.
- The caller must ensure the expected IDs are unique; invalid expectations trigger a setup error.
- Duplicate counts refer to physical target occurrences. A duplicate ID present with conflicting payload needs an additional payload-consistency checker.

## Not proved by this unit test

- Transport acceptance / successful submission of planned events.
- Sink-side completion barrier (Kafka lag=0 is insufficient).
- Real ClickHouse `MergeTree` storage, delivery order, retry semantics, or latest-state projection.
- PnL/status, version conflicts and same-ID different-payload DQ.
- The independent source contract still must be trustworthy: `planned_count` alone cannot prove a generator ran or events were submitted.

These remain separate integration/E2E checks and should not be inferred from a green unit test.
