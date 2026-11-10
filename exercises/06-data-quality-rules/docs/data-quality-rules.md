# Session 06 — Independent Data Quality Rule Catalog

These policies are **synthetic training assumptions, not Exness production thresholds**.

## Identity and grain

- Physical grain: one ingested JSON record (can include transport replays).
- Logical event: one immutable `event_id`.
- Business trade: composite `(trade_id, account_id)`.
- State version: `(trade_id, account_id, version)`.
- No checker changes, deduplicates, or suppresses the input to another checker.

## Rule matrix

| Rule | Independent responsibility | Grain / evidence | Threshold | Severity | Illustrative owner |
|---|---|---|---|---|---|
| DQ-01 FieldsChecker | Required field presence and non-NULL | physical record | 0 missing | critical | ingestion |
| DQ-02 DuplicateChecker | Identical event redeliveries (N-1) | event ID + immutable payload | 0 replays to PASS | warning | streaming |
| DQ-03 PayloadConsistencyChecker | Same event ID with conflicting business payload | event ID | 0 conflicts | critical | producer |
| DQ-04 VersionDomainChecker | Positive integer version | physical record | 0 invalid | critical | producer |
| DQ-05 StatusDomainChecker | Allowed NEW/FILLED/CANCELLED/FAILED | physical record | 0 invalid | critical | schema |
| DQ-06 DecimalValidityChecker | Finite string-encoded Decimal PnL | physical record | 0 invalid | critical | finance |
| DQ-07 ExpectedCompletenessChecker | Expected vs observed distinct event *count*; optional membership | cohort, event IDs | count equal, 0 missing/extra IDs | critical | source |
| DQ-08 VisibilitySLAChecker | At least 95% matured expected events visible <=10min | authoritative expected event manifest, as_of | >=95% | critical | data SRE |
| DQ-09 VersionConsistencyChecker | Same trade/version cannot have divergent states from distinct event IDs | business key+version | 0 conflicts | critical | producer |
| DQ-10 SourceTargetLifecycleChecker | Latest source/target status consistency | matched latest versions | 0 mismatches | critical | reconciliation |
| DQ-11 FreshnessChecker | Per-event delivery latency | distinct event, event_time, available_at | <=10min for PASS | warning | data SRE |
| DQ-12 EmptyCohortChecker | Unexpected empty batch is not PASS | cohort | 0 unexpected empty cohorts | critical | scheduler |
| DQ-13 BusinessConsistencyChecker | FILLED requires non-NULL PnL; other statuses may be NULL | status/PnL relationship | 0 violations | critical | trading domain |
| DQ-14 SourceTargetPresenceChecker | MISSING/ORPHAN after explicit finalized cutoff | source and target business keys | 0 unmatched | critical | reconciliation |
| DQ-15 ProcessedSnapshotUniquenessChecker | Repeated processed snapshot rows | target_grain=snapshot, composite key | <=1 row/key | critical | storage |
| DQ-16 BusinessKeyValidityChecker | Non-NULL ID domain: nonempty string | physical event identity | 0 invalid | critical | ingestion |
| DQ-17 CrossSideVersionChecker | Latest source/target version mismatch | matched composite key | 0 mismatches | critical | replication |
| DQ-18 FailedProcessingChecker | Explicit FAILED target processing | target row | 0 failures to PASS | warning | processing ops |
| DQ-19 UnknownProcessingStatusChecker | NULL/unknown target processing status | target row | 0 invalid | critical | processing ops |
| DQ-20 SourceTargetPnlChecker | Latest matching version PnL mismatch, Decimal-aware | matched composite key + version | 0 mismatches | critical | financial reconciliation |

Each handler independently appends one `RuleOutcome` with `PASS`, `FAIL`,
or `INDETERMINATE`. The chain is only an executor. Confirmed violations
dominate unknown coverage, but both remain in `issues`. Severity is separate
from rule status; a warning FAIL may leave the overall blocking gate healthy.

## Windows, denominators and prerequisites

- DQ-07: `expected_events` is a **distinct immutable-event count**, never physical
  row count. Matching cardinality is not proof of correct event identities.
  Provide `expected_event_ids` to verify exact membership.
- DQ-08: requires `expected_event_manifest` (event ID and source-side
  `event_time`) plus `as_of`. Eligible means event_time + 10 minutes <= as_of.
  Missing expected events with matured deadlines are **overdue**. Physically
  observed events without `available_at` are **unknown**, not excluded from
  the denominator. Calculate lower = on_time/eligible and upper =
  (on_time + unknown)/eligible. PASS when lower >= 95%; FAIL when upper <95%;
  otherwise INDETERMINATE. Zero eligible is INDETERMINATE.
- DQ-11: independent single-record freshness, not the aggregate SLA.
  One 15-minute event among 100 may violate DQ-11 while DQ-08 passes.
- DQ-10, 17, 20: require `source_records` and `target_records`; never select an
  arbitrary winner in a conflicting latest version; no source/target input
  means INDETERMINATE, not an invented PASS.
- DQ-14: also requires `reconciliation_finalized: true`. A missing target
  before cutoff may be in flight; NULL business keys cannot be joined safely.
- DQ-15: requires `target_grain: snapshot`. Different trade versions in an
  event log are legitimate and are not duplicate snapshot rows.
- DQ-12: `expected_events > 0` and empty input is FAIL; empty expected count
  requires explicit `allow_empty: true` to pass.
- DQ-13: requiring FILLED PnL is an **exercise-specific business assumption**,
  not a universal trading rule.
- DQ-18/19: base PostgreSQL `processed_trades` statuses are SUCCESS/FAILED,
  while the event-contract status enum differs. Keep those domains distinct.

## Alerting and quarantine

| Finding | Response | Alert discipline |
|---|---|---|
| Identical replay (DQ-02) | Preserve raw, idempotently process one logical event | Warning counter; trend, not per-retry page |
| Invalid business identity (DQ-01/16) | Quarantine unjoinable row with raw evidence | Critical |
| Same-event conflict (DQ-03) | Quarantine event ID; do not choose last arrival | Critical |
| Conflicting trade version (DQ-09) | Quarantine business key/version | Critical |
| Wrong expected population (DQ-07) | Investigate missing/extra source events | Critical after cutoff |
| Matured-event SLA breach (DQ-08) | Alert with numerator, denominator, cutoff and samples | Critical only for confirmed breach |
| Individual late event (DQ-11) | Persist latency violation | Warning, not automatically SLA page |
| MISSING/ORPHAN (DQ-14) | Reconcile or quarantine after watermark/cutoff | Critical |
| Explicit FAILED (DQ-18) | Retain processing-failure evidence; retry according to contract | Warning, not MISSING |
| Invalid target status (DQ-19) | Quarantine invalid state | Critical |

Deduplicate alerts by `(rule_id, cohort, environment)` and apply cooldowns.
Preserve evidence and counts, and never transform INDETERMINATE to PASS.
A confirmed critical issue should not be hidden by another partial rule.

## False positives and false negatives

- **False positive:** declaring MISSING while delivery is still in flight:
  DQ-14 requires finalized reconciliation cutoff.
- **False positive:** treating two versions of one trade as duplicate snapshot:
  DQ-15 is only valid on declared snapshot grain.
- **False negative:** equal expected/actual event counts but wrong event IDs:
  add the expected IDs catalog; count equality alone cannot verify membership.
- **False negative:** dropping NULL availability timestamps from SLA denominator:
  DQ-08 keeps eligible IDs and reports conservative success bounds.
- **False negative:** taking an arbitrary latest row when same-version PnL
  differs: DQ-09 isolates this ambiguity.

## Run / reproducibility

From repository root:

```bash
uv run python exercises/06-data-quality-rules/starter/rule_runner.py \
  exercises/06-data-quality-rules/fixtures/dq_full_green.json --format json

uv run python exercises/06-data-quality-rules/starter/rule_runner.py \
  exercises/06-data-quality-rules/fixtures/dq_batches.json --format json

uv run pytest -q tests/unit/test_dq*.py
```

The green fixture supplies complete evidence, while the original three
batches intentionally contain defects and missing prerequisites.

## Separate baseline SQL checks

The original PostgreSQL schema (`trades` / `processed_trades`) has no
event IDs or version history; these queries are separate, runnable
business-key diagnostics, **not DQ-02 event-replay checks**.

- [MISSING](../sql/01-missing-processing.sql)
- [ORPHAN](../sql/02-orphan-processing.sql)
- [DUPLICATE processing](../sql/03-duplicate-processing.sql)
- [FAILED processing](../sql/04-failed-processing.sql)
- [UNKNOWN status](../sql/05-unknown-processing.sql)
- [INVALID business key](../sql/06-invalid-processing-keys.sql)

For version-aware SQL and source-to-target SLA, reuse Session 04's
[reconciliation SQL](../../04-reconciliation/sql/02-reconciliation.sql)
and [SLA SQL](../../04-reconciliation/sql/03-sla.sql) with lab04 fixtures,
rather than running them against the unversioned base tables.
