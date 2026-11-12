# Consolidated 5-Session Exness Data QA Interview Route

**Revision date:** 2026-11-12. **Interview:** 2026-11-16, 17:00 Bangkok, Russian-language.  
**Source of lessons:** [readiness audit 01–08](INTERVIEW_READINESS_AUDIT_2026-11-11.md).  
**Reusable environment:** [streaming lab README](../streaming/README.md).

## Objective and provenance

Preserve every original Session 10–17 question, answer history and chat title, but run **five** combined meetings where shared versioned-trade data and QA evidence remove duplicated context/setup time. The original eight sessions were approximately 10 hours; the proposed combined meetings total **7 hours**. The time saving excludes one-time infrastructure build/troubleshooting. This plan does **not** update Google Calendar and does **not** mark any session complete.

| Combined meeting (90/90/90/90/60 min) | Original sessions | Primary skill and deliverable | Dependency |
|---|---|---|---|
| **A — SQL & Quality Gates (90m)** | **10 + 13** | 45m independent SQL mock, 30m independent DQ/CI negative controls, 15m graded review | PostgreSQL lab10 and synthetic DQ runner; full streaming lab optional |
| **B — Kafka/Flink & System Design (90m)** | **11 + 12** | 45m Kafka/Flink actual pipeline/failure review, 35m architecture and sink evidence, 10m review | Streaming lab recommended; JSONL trace fallback |
| **C — Mock Interview №1 (90m)** | **14** | Independent SQL+Python coding and pytest challenge | Prepared mock packet; no hints |
| **D — Mock Interview №2 (90m)** | **15** | Incident-style Kafka/Flink/ClickHouse diagnosis and rollback | Read-only synthetic evidence or working stack |
| **E — Experience Stories & Final Review (60m)** | **16 + 17** | 30m personally verifiable STAR cases; 30m targeted quick questions and remaining gaps | Scores from C/D |

**Do not collapse both mock interviews into lecture time.** These sessions are the best independent readiness measurement given the prior assistant-assisted implementations.

## Canonical chat titles remain unchanged

- `🎯 Exness | Session 10 — SQL Mock`
- `🎯 Exness | Session 11 — Kafka / Flink`
- `🎯 Exness | Session 12 — Data Pipeline Design` (integrated into B)
- `🎯 Exness | Session 13 — Quality Gates / CI` (integrated into A)
- `🎯 Exness | Session 14 — Mock Interview №1`
- `🎯 Exness | Session 15 — Mock Interview №2`
- `🎯 Exness | Session 16 — Experience Stories`
- `🎯 Exness | Session 17 — Final Review` (integrated into E)

A separate chat can still be opened for any original module if a particular gap requires extra time.

## Meeting A — SQL & Quality Gates

1. **Session 10**: freeze original SQL answers before feedback; use `lab10` schema and [SQL Mock tasks](../exercises/10-sql-mock/INTERVIEW_TASKS.md).
2. **Session 13**: from original DQ list identify three blocking invariants and two nonblocking warnings. Show why source/target counts can match while an event is lost.
3. Use [pure Python gate tests](../tests/streaming/test_fixtures_and_gate.py) and [negative-control matrix](../exercises/13-quality-gates-ci/NEGATIVE_CONTROLS.md).
4. If stack is running, run `healthy`, `missing`, `corrupt`; otherwise test the same contract offline. Verify actual failure exit status for negative controls.
5. Score independent SQL correctness and contract ownership; record three gaps.

## Meeting B — Streaming & Design

1. **Session 11**: inspect real Kafka input/output topics, partitions, Flink SQL and ClickHouse raw events; explain what can be proven for each boundary.
2. Discuss `duplicate`, `out_of_order`, `conflict` and partial sink/write acknowledgement. Use the original [trace simulator](../labs/streaming/replay_driver.py) when the actual stack cannot run.
3. **Session 12**: design architecture and QA evidence path. Separate event identity, business version, raw physical delivery and latest query state.
4. Defend snapshot vs delta PnL under replays, checkpoint semantics, per-partition progress, an as-of cutoff and recovery.
5. Produce a minimal failure matrix and a rollout/rollback hypothesis; keep unverified claims labelled.

## Meeting C — Mock SQL/Python

Unseen [Session 14 packet](../exercises/14-mock-interview-1/MOCK_PACKET.md). No prompts before the timer, no reference implementation, preserve original attempt. Grade correctness, output completeness, test isolation, complexity.

## Meeting D — Incident Response

Staged [Session 15 packet](../exercises/15-mock-interview-2/INCIDENT_PACKET.md); only reveal evidence as candidate investigates. Score uncertainty, sink durability, conflicting versions, SQL/MV backfill and response prioritization.

## Meeting E — Experience and final gaps

Three accurate [STAR evidence worksheets](../exercises/16-experience-stories/STORY_EVIDENCE_WORKSHEET.md) and [rapid final rehearsal](../exercises/17-final-review/GAP_REHEARSAL.md). Do not invent achievements. Prioritize missed questions from the mock scorecards, not new infrastructure.

## Explicit scope and failure handling

- An unavailable Flink image/JAR must **not** force you to abandon Sessions 10, 13, 14 or 16/17. The existing PostgreSQL/ClickHouse Testcontainers and offline synthetic checks remain usable.
- Passing `lab-readiness` is not evidence of the new streaming E2E; consult its separate workflow.
- A generated manifest with no records, unsealed source batch or unverified target is never a green business verdict.
- Full production "exactly once" and Flink stateful checkpoint recovery cannot be inferred from the baseline lab.
- Keep scheduling unchanged until explicitly asked to change it.
