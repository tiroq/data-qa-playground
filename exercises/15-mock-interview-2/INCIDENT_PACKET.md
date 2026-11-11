# Session 15 — Production-Style Incident Mock (Synthetic)

**90 minutes.** The candidate should reason in Russian as a QA/Data Stack incident investigator. The data and constraints are fictional. Present observations in phases; avoid sharing analysis or reference answers in advance.

## Phase 1 — Reported symptom (15 min)

A new ClickHouse latest-state projection was deployed. An operational dashboard shows **zero consumer lag**, its row-count comparison is green, and a last-observed trade ID matches the source batch's terminal marker. An account PnL report sometimes differs after replay.

The business requirement says that a batch's **10 immutable source event IDs** must be represented by correct data in the query-visible durable sink before a release is considered complete. Status and PnL are current-state snapshots; a separate raw log preserves physical deliveries. No global cross-partition order is guaranteed.

Ask the candidate to request evidence, identify which reported signals are insufficient, and define a trustworthy completion criterion.

## Phase 2 — Reveal independent evidence (20 min)

Source manifest IDs: `E01,E02,E03,E04,E05,E06,E07,E08,E09,E10`.

ClickHouse raw physical IDs currently observed: `E01,E02,E03,E04,E05,E06,E08,E09,E10,E10`.

Kafka has two partitions; consumer offsets are committed to their observed ends. E10 is present. A retry of one observed event occurred during a consumer restart. No guarantee is made that the sink ack was durable before the offset commit.

**Questions:** Which tests would detect the anomaly even though two count-like checks are green? What can the committed-offset observation prove? What additional payload/version evidence is needed before calculating PnL?

## Phase 3 — Version and aggregation challenge (20 min)

Trade X55 (account A2) has version 3 twice, in two physical rows with PnL 7.00 and 7.50. A separate event for X55 version 2 arrived *later* in ingestion order. The new projection uses a version-based aggregate, but its conflict policy is undocumented.

**Questions:** Define the defensible quality state and what should be excluded or quarantined. How could a new MV or backfill make reports differ? Distinguish current-state snapshot aggregation from delta aggregation.

## Phase 4 — Failure containment and rollback (20 min)

The team considers rebuilding an MV, running a 24-hour backfill and disabling an old raw table's TTL exception. There is no trustworthy cross-system as-of watermark for historical comparison yet.

**Questions:** Which change should be blocked pending evidence? Define a replay/backfill boundary, independent validations, monitoring and a rollback trigger. Which source records must remain available?

## Phase 5 — Incident report and review (15 min)

Candidate produces a compact incident update:

- **Observed facts** versus hypotheses and what is unknown.
- **Current impact** and what is merely a possible consequence.
- **Five-step investigation** ordered by information gain and safety.
- **Containment / rollback decision** grounded in evidence.
- **Regression tests** with at least one injected negative control.

Save the candidate's first response and [scorecard](SCORECARD_TEMPLATE.md) only after the mock. **Do not claim a real production incident, deployed Flink job or Exness system knowledge.**

Target gaps: G02,G03,G04,G07,G09 in the [audit](../../docs/INTERVIEW_READINESS_AUDIT_2026-11-11.md).
