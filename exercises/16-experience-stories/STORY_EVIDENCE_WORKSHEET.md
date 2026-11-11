# Session 16 — Personal Experience Stories: Verification Worksheet

**Use in a Russian-language interview.** This is a set of prompts, not prewritten answers, and not a claim that the user held any specific responsibility or achieved any unverified outcome. The learner must correct or reject premises that do not match their actual work.

## Candidate story 1 — Trading throughput / post-trade incident

Potential evidence to discuss: a FIX Adapter migration between cloud accounts, baseline around 80 TPS versus observed degradation around 40 TPS, clearing backpressure, and validation that the **load and accounts were unchanged**. These figures are prior case context; do **not** say a root cause was proven or a fix deployed unless the learner confirms evidence.

- Situation and original system contract:
- Exactly what the learner personally owned:
- Reproduction method, metrics, controls and traceability:
- How missing/extra/duplicate trades were detected:
- Observed outcome and current known limitations:
- What would be different with hindsight:
- Two skeptical follow-up questions (about causality and baseline reproducibility):

## Candidate story 2 — Reconciliation / Data Quality

Potential evidence to discuss: synthetic or actual trade validation, source/target reconciliation, SQL data checks, CI and reporting. Clarify which project and which statements are verifiable before forming the answer.

- Data grain / authoritative source:
- Main risk (silent loss, duplicates, malformed, PnL):
- Candidate's design choices and trade-offs:
- Tests and an independent negative control:
- Observed outcome; distinguish from proposed design:
- What a failure or unknown meant operationally:

## Candidate story 3 — Streaming or QA automation

Potential evidence to explore: Python/Go SDET work, NATS JetStream, CI/test automation and distributed processing. **Do not imply production Kafka/Flink experience** from a classroom Testcontainer.

- System and constraints:
- Direct contribution:
- Failure injection / rollback / observability:
- Measured outcome, if independently known:
- What was unproven:
- Relevant parallels to Exness Trading Data Flow:

## Spoken STAR checklist (2–3 minutes each)

S (situation, one sentence), T (your specific responsibility), A (your decision and implementation), R (verifiable outcome, including remaining limitations), plus one trade-off and one failure-mode test. Confirm all proprietary/confidential details are safe to disclose.

**Important:** Correct a misleading premise before answering. An authentic limitation is better than attributing a mentor's training code or a hypothetical architecture to one's production work.
