# Session 09 — Targeted Follow-up Questions from Sessions 01–08

**Oral-first. Do not provide answers in advance.** Conduct all discussion and code review in Russian; write down only the candidate's actual answers after each prompt. Use [SCENARIO_CARDS.md](SCENARIO_CARDS.md) as the source of data, and [the audit](../../docs/INTERVIEW_READINESS_AUDIT_2026-11-11.md) for why these prompts were selected.

## Essential prompts (priority order)

1. **G03 Replacement identity:** For a table containing several versions per trade, which fields should define the replacement equivalence class? Challenge an `ORDER BY` that includes `version` and one that includes `ingest_id`. How would a test detect a mistake?
2. **G03 Partition boundaries:** What happens if two versions of the *same* trade belong to different monthly partitions? Which invariant must hold for a proposed stable partition key?
3. **G02 Tied max version:** Trade 205 has two maximum-version rows with different PnL. Require a business-authoritative conflict policy **before** choosing a representative.
4. **G07 Snapshot vs delta:** If PnL is current-state value versus delta operation, how do the correct aggregate and replay invariants differ? State the contract before calculating.
5. **G09 MV evidence:** What does an insert-triggered MV observe? How could source rows exist while a new MV is missing their history?
6. **G04 Backfill cutover:** What evidence separates partially backfilled history from a temporarily lagging live stream? How would the reviewer falsify completeness?
7. **G10 Cost:** Compare correctness and cost of `FINAL`, query-time state selection and persisted aggregate-state approach at a qualitative level.
8. **G03/G09 TTL:** When old raw deliveries have been deleted, which historical claims can still be tested and which cannot?

## How to record

For each actually discussed question record: (a) candidate's initial reasoning, (b) precise counterexample, (c) revised conclusion or unresolved ambiguity, (d) a falsifying test, (e) expected implementation work if agreed. **Do not auto-create SQL solutions.**

A passing oral explanation is not evidence of executing the query.
