# Session 12 — Trading Data Pipeline Design

**Focused practice:** 60 minutes. Interview conversation and review strictly in **Russian**; schemas and written artifacts in English.

## Preparation pack

- [Synthetic case study](CASE_STUDY.md): non-production load, freshness, correctness and recovery requirements.
- [Failure injection cards](FAILURE_CARDS.md): reveal **one at a time after** the baseline architecture.
- [Decision log template](DECISION_LOG.md): document data identities, guarantees, test strategy and recovery.
- [Event contract](../../labs/contracts/trading_event.schema.json): example JSON Schema, not a real Exness schema.
- Existing Session 04 PostgreSQL reconciliation, Session 03 ClickHouse raw input and Session 11 file-based replay examples.

## Interview task

Design an end-to-end source → broker → processing → ClickHouse → API pipeline, including ownership, raw replayable storage, business-version correctness, CDC/contract changes, reconciliation as-of cutoff, meaningful QA gates and monitoring. **Do not prewrite the answer**: propose architecture first, then investigate failure cards in order.

## Acceptance criteria

- Separate immutable event identity, business key, version and physical broker delivery.
- Define what at-least-once delivery means at every storage boundary; do not invent global ordering or end-to-end exactly-once.
- Provide an explicit watermark/as-of policy so a temporarily in-flight trade is not falsely classified missing.
- Build a recoverable backfill and rollback strategy with independent reconciliation.
- Distinguish unit fakes, Docker integration and actual Kafka/Flink/distributed integration.

## Russian kickoff prompt

> Проведи интервью по проектированию Data Stack для Exness только на русском. Дай мне CASE_STUDY.md, дождись моей архитектуры, затем по одной выдавай карточки из FAILURE_CARDS.md. Проверяй инварианты, RPO/RTO assumptions, replay, idempotency, data contracts, ClickHouse, watermark, reconciliation и QA-гейты. Не предлагай эталон до моей защиты решения.
