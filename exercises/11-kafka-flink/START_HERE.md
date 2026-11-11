# Session 11 — Streaming Failure Scenarios

**Chat title (copy to rename the conversation):** `🎯 Exness | Session 11 — Kafka / Flink`  
**Session short name:** `Kafka / Flink`  

**Practice:** 60 minutes; discuss and review in Russian.

After the standard trace exercise, use [BARRIER_AND_CHECKPOINT_DRILLS.md](BARRIER_AND_CHECKPOINT_DRILLS.md) to probe the observed per-partition completion and Flink knowledge gaps. Do not present answers before the candidate's proposal.

The [trace contract](TRACE_CONTRACT.md) defines physical deliveries, immutable event IDs, version ordering and simulated replay. The [failure matrix](FAILURE_MATRIX.md) is an unfinished learner deliverable.

```bash
python labs/streaming/replay_driver.py --scenario clean
python labs/streaming/replay_driver.py --scenario replay
python labs/streaming/replay_driver.py --scenario out_of_order
python labs/streaming/replay_driver.py --scenario conflict
python labs/streaming/replay_driver.py --scenario clean --repeat-step 2
```

The driver emits raw JSONL observations. **It is not Kafka, Flink or a broker with proven partition/checkpoint guarantees.** No event-processing or deduplication answer is supplied.

## Interview task

Explain partition ordering and offsets, devise idempotency and replay-safe processing, diagnose maximum-version conflict, propose recovery of a write-acknowledgement uncertainty, and populate failure matrix with test evidence, lag, DLQ and checkpoint behavior.

> Проведи сессию 11 на русском. Используй START_HERE.md и trace-сценарии; не выдавай обработчик событий или решение для deduplication. Попроси меня объяснить реальную семантику Kafka/Flink, составить failure matrix и предложить проверяемую стратегию replay/recovery.
