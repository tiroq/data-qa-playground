# Session 11 — Per-Partition Completion and Flink Reasoning

**Discussion in Russian.** No answer key and no claim of an actual Flink cluster. Reference the existing [real two-partition Kafka teaching test](../../tests/integration/test_kafka_sink_checkpoint.py) **after** proposing a design.

## Case A — End marker does not prove history

A synthetic batch declares 10 immutable events, E01–E10, over two partitions. The observed ClickHouse physical event IDs are E01,E02,E03,E04,E05,E06,E08,E09,E10,E10. Both consumers report lag=0; E10 is present.

**Questions:** What do these observations actually prove? Name two independent checks needed to release the batch. What is the failure signal if the sink completion barrier arrives but an event is absent? Distinguish the existence of E10, physical row count, distinct ID count and payload correctness.

## Case B — Offset committed before durability

Partition 0 has target offset 50 and partition 1 has target offset 70. The consumer's committed offsets are at those ends, but a buffered sink write is still pending for one message. Query visibility lags.

**Questions:** Where should a trustworthy completion acknowledgement be created? What evidence can be recovered after consumer restart? How would you distinguish lack of durability from lack of query visibility?

## Case C — Checkpoint / sink failure

The processing job makes stateful aggregations, and the team proposes checkpointing in Flink and an external ClickHouse sink. A crash may happen between committing a ClickHouse write and recording progress.

**Questions:** What properties would be needed for end-to-end exactly-once effects? Which can be proven by a local fake, a real broker Testcontainer, and a real Flink job? Which recovery test would reveal a double-counting bug?

## Case D — Ordering and time

The older business version is observed at a higher Kafka offset; another partition is delayed. A watermark advances.

**Questions:** Which ordering guarantee still holds? Does a watermark prove specific immutable event IDs have been written to ClickHouse? What is the distinction between event-time window closure and a sink-side batch completion?

## Candidate output

A failure matrix with: injected fault, physical observation, business invariant, **concrete sink evidence**, recovery/replay procedure, negative test and a clearly stated guarantee boundary. Do not infer an implementation from a discussion or a passing status of an unrelated lab.
