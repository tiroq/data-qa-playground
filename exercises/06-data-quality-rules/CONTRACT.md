# Quality contract — synthetic trading batches

## Physical grain and key semantics

Each JSON cohort is a point-in-time evaluation batch. Its `records` are **physical ingested records**, which may contain multiple versions and transport replays. `event_id` is an intended immutable event identity; `(trade_id, account_id)` is the business trade identity. Neither `trade_id` nor `version` alone is a universal deduplication key.

`status` is one of `NEW`, `FILLED`, `CANCELLED`, or `FAILED`. The case has `event_time` and `available_at` ISO UTC timestamps. `pnl` is a string-encoded decimal amount to avoid binary float conversions; an explicit null is possible.

## Cohort assumptions for this **training exercise**

- `expected_events` is the number of distinct immutable events expected to be visible for the cohort, not the physical row count.
- A transport redelivery with the same `event_id` and identical payload **must not** increase a logical count.
- Two distinct event IDs and higher versions may legitimately belong to the same trade. Distinct event IDs with contradictory payload at the same version need investigation; do not pick the last array element.
- A late record can be a **per-record defect** without causing an **aggregate** SLA violation.
- The illustrative SLA is at least **95% of eligible distinct events visible within 10 minutes**; events whose deadline has not elapsed by `as_of` are excluded. An eligible event with no observation is overdue, not automatically excluded.
- `expected_events=0` is not permission to pass silently: classify empty cohorts explicitly. All thresholds and severities here are hypothetical and are **not Exness internal requirements**.

## Candidate rule ideas — decide actual logic during session

| Rule ID | Dimension | Deliberate pitfall |
|---|---|---|
| DQ-01 | Required business fields | NULL key vs legitimate nullable PnL |
| DQ-02 | Immutable event-ID uniqueness | Same event delivered twice |
| DQ-03 | Same-event payload consistency | Conflicting payload with same event ID |
| DQ-04 | Version domain | Zero or negative version |
| DQ-05 | Allowed status values | Unknown status vs a missing record |
| DQ-06 | Decimal amount validity | Float precision and invalid text |
| DQ-07 | Expected event completeness | Expected distinct events vs physical rows |
| DQ-08 | On-time visibility SLA | Distinct cohort denominator and as-of |
| DQ-09 | Latest-version ambiguity | Same version, divergent events |
| DQ-10 | Source/target lifecycle consistency | FAILED != missing |
| DQ-11 | Freshness | Event time differs from available time |
| DQ-12 | Empty-cohort policy | Unexpected empty batch must not PASS |

## Required report shape (learner defines implementation)

```json
{
  "cohort": "some_label",
  "eligible_count": 0,
  "results": [
    {"rule_id": "DQ-01", "status": "PASS|FAIL|INDETERMINATE", "severity": "critical|warning", "issues": []}
  ]
}
```

Expected exact results and severity selection are **not supplied**; they are the interview deliverable. Document how you handle timestamps after `as_of`, rows without `event_id`, and absent expected events.
