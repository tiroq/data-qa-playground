# Five-session consolidated interview plan — Unified Data Stack Lab

**Interview:** 2026-11-16; interactive explanations and feedback are **in Russian**. All event data is synthetic. **Original session folders 10–17, titles and independent mock packets are preserved** so historic references and calendar events do not break. This plan groups learning outcomes; it does **not automatically reschedule Google Calendar**.

See [README.md](README.md) for Docker setup, scenario commands, safety and actual CI evidence.

| New block | Uses historical sessions | Default duration | Learning proof |
|---|---|---:|---|
| **A. SQL, DQ & CI** | [10 SQL Mock](../../exercises/10-sql-mock/README.md) + [13 Quality Gates](../../exercises/13-quality-gates-ci/README.md) | 90 min | Source/target SQL and negative-control gate |
| **B. Kafka, Flink & System Design** | [11 Kafka/Flink](../../exercises/11-kafka-flink/README.md) + [12 Data Pipeline](../../exercises/12-pipeline-design/README.md) | 90 min | Trace each identity/offset/checkpoint/sink boundary |
| **C. Independent Mock 1** | [14 SQL/Python Testing](../../exercises/14-mock-interview-1/README.md) | 90 min | Time-limited unassisted SQL/Python attempt |
| **D. Incident Mock 2** | [15 ClickHouse/Streaming](../../exercises/15-mock-interview-2/README.md) | 90 min | Root-cause evidence, containment and regression tests |
| **E. Stories & Final Review** | [16 Experience Stories](../../exercises/16-experience-stories/README.md) + [17 Final Review](../../exercises/17-final-review/README.md) | 60 min | Three factual STAR stories and final gap rehearsal |

**Total:** 7 hours of practice, excluding initial Compose build, image downloads and troubleshooting. The two 90-minute mocks are deliberately protected.

## Block A — SQL + QA CI (90m)

1. **0–15:** Run or inspect an isolated `clean` source manifest; declare physical grain, immutable event ID, logical business key, source/truth contract and denominator.
2. **15–45:** Unassisted SQL: query PostgreSQL `streaming_lab.source_events` and ClickHouse `streaming_lab.raw_events` separately to derive correct counts, latest versions and tie/conflict checks. The two engines **do not share a JOIN namespace**; the Python checker reconciles their result sets. Preserve original attempt.
3. **45–65:** Inject `missing` and `corrupt`. Define a blocking gate that fails with source-ID evidence, not `0 == 0`. Explain PASS/FAIL/ERROR.
4. **65–90:** Review correctness, CI artifacts and one independent negative control. Distinguish fast preparation smoke from true Flink integration.

**Unsolved:** exact candidate SQL and gate-design interview questions; keep original [SQL Mock](../../exercises/10-sql-mock/INTERVIEW_TASKS.md) closed until timed phase.

## Block B — Streaming + Design (90m)

1. **0–20:** Draw actual data path and physical Kafka partitions/topics, Flink SQL transform, Python ClickHouse sink. Explain where checkpoints and offset commits happen.
2. **20–40:** `replay`, `out_of_order`, `conflict` cases; distinguish ingestion order from business version and intentional physical replays from logical duplicates.
3. **40–65:** Challenge design with crash-after-ClickHouse-insert/before-offset-commit; design sink-side completion evidence and replay-safe current-state aggregates. No unsupported claims of Kafka+ClickHouse atomic exactly-once.
4. **65–90:** Design Flink event-time windows and watermarks, as-of reconciliation, backfill/rollback and incident tests. **Implement only a design actually agreed after discussion**.

**Unsolved:** Flink watermarks, stateful aggregations, CDC and production-grade sink checkpoints. The provided Flink SQL is intentionally only a minimal real transport transform.

## Block C — Independent Mock #1 (90m)

- Use the pre-existing [sealed mock packet](../../exercises/14-mock-interview-1/MOCK_PACKET.md) and [scorecard](../../exercises/14-mock-interview-1/SCORECARD_TEMPLATE.md).
- No model answers, reference code, ChatGPT suggestions or repo searches until the timed independent answer is submitted.
- Run one small negative check against the unified lab **after** submission. Assess SQL grain/columns, Python time complexity and test isolation.
- Candidate-only authored attempt and observed score are separate from the prebuilt infrastructure.

## Block D — Incident Mock #2 (90m)

- Use [multi-phase incident packet](../../exercises/15-mock-interview-2/INCIDENT_PACKET.md); disclose observations sequentially.
- Recreate a comparable `missing` / `conflict` / `replay` failure, with independent PostgreSQL manifest and ClickHouse persisted raw evidence.
- Investigate before proposing rollback. The candidate must distinguish failed source generation, Kafka publication, Flink processing, ClickHouse write/visibility, version conflict and QA query bugs.
- Record a factual incident report and [scorecard](../../exercises/15-mock-interview-2/SCORECARD_TEMPLATE.md).

## Block E — Experience and final revision (60m)

- **0–30:** Build three short STAR stories from [the evidence worksheet](../../exercises/16-experience-stories/STORY_EVIDENCE_WORKSHEET.md), with personally verifiable contributions and no invented metrics.
- **30–60:** Use [the final gap rehearsal](../../exercises/17-final-review/GAP_REHEARSAL.md), focusing on wrong PnL, empty data PASS, version ties, lag=0, checkpoint versus durable sink, and one genuine weak point from each mock.

## Explicit teaching boundaries

- Run IDs are independent, PostgreSQL and ClickHouse schemas are namespaced `streaming_lab`. Do not reset existing historical lab volumes for a new scenario.
- Local `replay` demonstrates possible duplicate *physical* delivery; the DQ check considers the immutable event identity.
- Flink SQL transforms real Kafka messages but does not implement sophisticated state/window processing by default.
- A PASS means currently observed persisted data matches the expected manifest; it does **not** prove future absence of late corruption or atomic end-to-end exactly-once.
- A generated input set and answer key must not be mistaken for evidence of independent interview skill.
- The existing calendar's eight individual entries remain unchanged until a separate scheduling request.
