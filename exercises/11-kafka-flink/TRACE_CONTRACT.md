# Synthetic streaming trace contract

This file-based dataset is **not** a Kafka/Flink integration environment. Rows represent physical consumer observations. `step` indexes a fixture; `partition` and `offset` are illustrative log coordinates. A replay shows the SAME offset twice after a simulated restart; the broker did not append the offset twice.

`event_id` is an immutable event identity; `(trade_id, account_id)` is a business identity; `version` orders business states, not physical observation order. `event_time` and `observed_at` are distinct. `pnl` is a decimal string.

Kafka log order is guaranteed within a partition by offset, **not globally across partitions**. An old business version can be produced later at a higher offset without violating Kafka ordering.

## Interview checks

1. Distinguish physical retries from legitimate lifecycle transitions.
2. Identify the exact effect of crash-after-write / before-checkpoint.
3. Specify conflict semantics for two different events with same maximal version.
4. Define what metrics and evidence make replay safe.
5. Explain why exactly-once inside a stream processor does not automatically prove exactly-once ClickHouse effects.
6. Choose event-time cutoff and watermark before treating an absent target as missing.
