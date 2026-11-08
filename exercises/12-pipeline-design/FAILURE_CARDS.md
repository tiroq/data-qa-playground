# Interview Failure Cards — reveal only after baseline design

For each card, provide hypothesis, evidence, mitigation, recovery step and regression test.

1. **Uncertain target write:** consumer writes to ClickHouse, crashes before checkpoint; same offset is read again.
2. **Conflicting maximum version:** two distinct immutable events have identical business key and max version but different PnL.
3. **Late older version:** target contains version 2; version 1 arrives later. Broker offset ordering remains correct.
4. **Partial backfill:** a materialized view is recreated, but only 80% of source history was processed before cutover.
5. **False missing alert:** processing lag rises to 15 minutes; a naive reconciliation job runs every minute.
6. **Schema evolution:** new optional field is emitted; one consumer rejects the payload while another silently ignores it.
7. **Vacuous green CI:** environment starts but zero input rows are delivered, so both sides compare `0 == 0`.
8. **TTL data loss:** the raw source needed for audit/rebuild expires before an investigation.

These are deliberately unsolved. The interviewer scores correctness, design trade-offs, explicit test evidence and operational safety.
