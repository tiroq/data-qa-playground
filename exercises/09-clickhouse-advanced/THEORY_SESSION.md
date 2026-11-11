# Session 09 — Oral Interview Guide (60 minutes)

**Moderator role:** technically demanding QA / Data Quality Engineer interviewer.  
**Speaking language:** Russian only (SQL keywords and technology names may be English).  
**Rule:** Ask one question at a time. Let the learner reason before offering hints or explanations.

## Carry-forward focus

Use [GAP_PROBES.md](GAP_PROBES.md) to select targeted follow-ups from previous sessions, but maintain one-question-at-a-time interviewing and do not reveal any proposed answer in advance.

## Preparation: zero hands-on setup

Read [SCENARIO_CARDS.md](SCENARIO_CARDS.md), the source fixture `clickhouse/init/02-seed.sql`, and [DECISION_MATRIX.md](DECISION_MATRIX.md). You do **not** need Docker, pytest, or live ClickHouse to begin.

The scenario is a simplified delivery history: 12 physical rows, 6 business keys. The real Exness architecture and internal thresholds are **not** known; keep all examples clearly synthetic.

## Interview sequence

### Block 1 — Storage model and semantics (10 min)

Ask what rows `MergeTree` stores, what `ReplacingMergeTree(version)` *can* and *cannot* promise before merges, why `ORDER BY` is not a uniqueness constraint, and when `FINAL` changes query semantics. Follow up by asking for tests that are stable across merge timing.

**Listen for:** separation of physical rows vs current logical state; explicit replacement key; query-time correctness vs storage maintenance and cost.

### Block 2 — Latest-state correctness (15 min)

Present cases **A, B and C** in the scenario deck. Ask how `argMax`, deterministic ties, version ambiguity, aggregate PnL and duplicate delivery interact. Ask for an independent reconciliation source and expected anomaly classification.

**Listen for:** declared business grain, tie/conflict policy, explicit unknown/unresolved cases, separate count/uniq/current-state counts.

### Block 3 — Materialized views and replay (15 min)

Present cases **D and E**. Ask what data an insert-triggered materialized view sees, what it might fail to infer from new blocks alone, how to backfill existing history and avoid a cutover race. Ask how the candidate would test replay idempotency without relying on physical merges.

**Listen for:** raw source retention, backfill boundaries, dual-path comparison, replay-safe logical output, MV target type trade-offs.

### Block 4 — Migrations and TTL (10 min)

Present cases **F and G**. Ask for a rollback condition, before/after validation, data-retention risk and mitigation if a historical query must be rebuilt. A distributed-query topic is optional, not a claim that a cluster exists locally.

**Listen for:** explicit rollback trigger, checkpoint/evidence, non-destructive source preservation, observability.

### Block 5 — Critical review (10 min)

Have the candidate summarize one chosen design and its weakest invariant. Ask for **one falsifying test** (how to prove the design is wrong). Grade observed understanding, not just familiarity with terminology. Select three concise next actions and commit discussed notes only.

## Moderator rules

- No canned solutions before a response. Ask for reasoning, not definitions alone.
- If the candidate makes an uncertain claim, label it **hypothesis** and request a check rather than silently presenting it as a fact.
- If a block takes longer, prioritize A/B/C, D/E, and rollback over encyclopedic coverage.
- Implementation is **optional**: only turn an agreed design into SQL later, as a separate file and commit.
- Do not mark `FINAL`, `argMax`, asynchronous merges or MVs as universally correct without naming the exact query/data contract.
- Never state that Docker, CI or ClickHouse was executed unless it actually was.
- Capture original argument and review correction separately: the learner's first attempt should not be overwritten.

## Assessment (0–10; only after discussion)

| Dimension | Weight | Evidence |
|---|---:|---|
| Semantic correctness / data grain | 35% | Physical vs logical, version/tie policy |
| QA strategy / falsifying tests | 25% | Count vs uniq, replay, DQ cross-checks |
| Architecture / operations | 25% | MVs, backfill, rollback, TTL |
| Reasoning / explanation | 15% | Assumptions, explicit limits, clarity |

Use [DISCUSSION_RECORD_TEMPLATE.md](DISCUSSION_RECORD_TEMPLATE.md) to record only genuinely covered material.
