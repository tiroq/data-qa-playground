# Unified Lab SQL Tasks — independent candidate work

**Do not prefill solutions.** These queries run against the real unified lab in PostgreSQL or ClickHouse; the two engines do not share a cross-database join. Use the `RUN_ID` from `producer.py`.

## Connect to SQL consoles

From repository root:

```bash
DC='docker compose -f compose.yaml -f labs/unified/compose.streaming.yaml --profile clickhouse --profile streaming'

# PostgreSQL source / expected manifest:
$DC exec postgres psql -U qa -d trading

# ClickHouse physical sink (SQL):
$DC exec clickhouse clickhouse-client --user qa --password qa --database streaming_lab
```

Source tables: `streaming_lab.batches`, `streaming_lab.source_events`.  
Target table: `streaming_lab.raw_events` (physical delivery grain; may contain replays).  
Reconciliation outside one SQL engine: `python /app/check.py` fetches each side separately.

## Task A — Contract and grain (15 minutes)

Write source and sink SQL that returns the same columns: `run_id`, physical rows, distinct immutable `event_id`, distinct `(account_id,trade_id)` business keys. Explain why equal physical counts cannot establish correct event population. Compare a `clean` and `replay` run.

## Task B — Latest trade state (15 minutes)

In ClickHouse write one row per `(run_id,account_id,trade_id)` with `latest_version`, latest `status` and PnL **only when the version is unambiguous**. Detect conflicts among records with the same maximum version **before** selecting one. Explain the corresponding PostgreSQL `ROW_NUMBER` or `DISTINCT ON` formulation.

## Task C — Reconciliation (15 minutes)

Design a source/target comparison that preserves missing/extra immutable event IDs, payload mismatch and version ambiguity. You may write separate SQL for each database and compare outputs in Python; do not invent cross-engine JOIN capabilities.

## Task D — Quality Gate / CI (15 minutes)

Use a run generated with `--scenario missing` and prove an independent negative control fails on event ID E03, even though many records are present. Repeat with `conflict` and `corrupt`. Explain why `PASS`, `FAIL` and `ERROR` have different meanings.

## Reviewer checklist

- Output columns complete and each row has declared grain.
- Count versus distinct ID and physical retries not conflated.
- Equal version conflicting PnL never silently accepted by a tie-breaker.
- Nullable/invalid keys and missing authoritative source evidence handled.
- No claims that Kafka committed offset proves ClickHouse durability.
- Candidate's original SQL preserved before refactoring.

**No reference answers are provided.** This is the interactive Session 10+13 practice, not a solved acceptance query set.
