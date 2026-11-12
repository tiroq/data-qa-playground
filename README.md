# Data QA Playground

A hands-on lab for SQL diagnostics, trading-data reconciliation, and QA automation interview practice.

## Prerequisites

- Docker Engine / Docker Desktop with Docker Compose v2

## Quick start

```bash
git clone https://github.com/tiroq/data-qa-playground.git
cd data-qa-playground
docker compose up -d --wait
docker compose wait postgres-lab02-init
docker compose exec postgres psql -U qa -d trading
```

In `psql`:

```sql
SELECT * FROM trades;
SELECT * FROM processed_trades;
```

Useful psql commands: `\dt` (tables), `\d trades` (schema), `\timing on` (timing), `\x auto` (expanded display), `\q` (quit).

### Connect from local tools

- Host: `127.0.0.1`
- Port: `5433`
- Database: `trading`
- User: `qa`
- Password: `qa` (local development only)

```bash
psql 'postgresql://qa:qa@127.0.0.1:5433/trading'
```

## Dataset

Session 01 tables (public schema):

- `trades`: eight source trading transactions, unique `trade_id`.
- `processed_trades`: ten processing records, including duplicates, missing matches, an orphan record, a failed status, and a NULL status.

Business assumptions for the first exercise: each source trade should have exactly one processing record; `SUCCESS` and `FAILED` have different meanings from a missing record. `record_id` identifies processing rows; `(trade_id, account_id)` is a composite business identity to validate.

The processed table intentionally has **no foreign key** or uniqueness constraint on its business fields: the lab needs to preserve incorrect data for diagnosis.

## Practice questions (no solutions)

1. **Missing trades — JOIN:** Return `trade_id`, `account_id`, `symbol` for source trades that have no processing record. Duplicates in processing must not change the result.
2. **Duplicate processing — GROUP BY / HAVING:** Find business identifiers with more than one processing row; return the number of rows.
3. **Reconciliation — JOIN + aggregation:** Summarize data-quality anomalies for source vs. processed data, distinguishing missing, orphan, duplicate, FAILED and unknown status cases. Explain whether these categories may overlap.

Follow-up cases to discuss: SQL three-valued logic, `NULL` in join columns, composite-key joins vs. joining on `trade_id` alone, and what happens when source or target has a duplicated business key.

## Detailed SQL walkthroughs

The exercises below include reference SQL, design rationale, expected results, NULL/composite-key caveats, and verification scenarios. Try the unsolved practice questions above before opening the walkthroughs.

1. [Missing trades — LEFT JOIN and composite keys](exercises/01-sql-diagnostics/01-missing-trades.md)
2. [Duplicate processing — GROUP BY and HAVING](exercises/01-sql-diagnostics/02-duplicate-processing.md)
3. [Full reconciliation — FULL JOIN, aggregate flags, and DQ precedence](exercises/01-sql-diagnostics/03-full-reconciliation.md)

## Validate

```bash
docker compose exec -T postgres psql -U qa -d trading -v ON_ERROR_STOP=1 -f /dev/stdin < postgres/checks/smoke.sql
```

## Reset

**Destructive:** removes your local PostgreSQL volume and all changes made in the database.

```bash
docker compose down -v
docker compose up -d --wait
```

The original `postgres/init/` files are executed only when PostgreSQL first initializes an **empty** volume. On every `docker compose up`, the separate `postgres-lab02-init` service also applies the idempotent Session 02 fixture, including when the volume already exists. `docker compose restart postgres` alone does **not** rerun this fixture service.

## Roadmap

- PostgreSQL: advanced DQ scenarios and constraints
- Python + pytest + Testcontainers: automated reconciliation tests
- ClickHouse: analytics SQL and deduplication patterns
- Kafka: ingestion, delivery semantics, and idempotency

## Exness interview training track (17 linked sessions)

The repository now also includes a structured, **incremental** practice track for a synthetic trading-data QA case. Session 01 remains unchanged; Sessions 02–17 are specified in advance and will gain implementations only after each practical exercise.

- [Session roadmap and progress](ROADMAP.md)
- [Full exercise index](exercises/README.md)
- [Synthetic trading-data contract](docs/TRADING-DATA-CASE.md)
- [How to run and review each session](docs/SESSION-WORKFLOW.md)
- [Assessment rubric](docs/ASSESSMENT-RUBRIC.md)

**Language:** the actual interview and interactive training discussions are in **Russian**; SQL/Python, technical terms, repository code and written specifications remain in English.

**Session 02 isolated SQL dataset (auto-loaded):**

`docker compose up -d --wait` starts `postgres-lab02-init` after PostgreSQL becomes healthy. It applies `postgres/fixtures/02-trade-versions.sql` on both fresh and existing database volumes. The loader exits with code 0 on success and leaves PostgreSQL running. Check the loader and dataset:

```bash
docker compose wait postgres-lab02-init
docker compose ps --all
docker compose logs postgres-lab02-init
docker compose exec -T postgres psql -U qa -d trading -c "SELECT COUNT(*) AS physical_rows, COUNT(DISTINCT (trade_id, account_id)) AS logical_keys FROM lab02.trade_versions;"
```

Expected fixture counts: **12 physical rows, 6 logical keys**. Re-running `docker compose up` does not duplicate the fixture rows because it uses stable `ingest_id` values and `ON CONFLICT DO NOTHING`. The fixture creates only the separate `lab02` schema and does not alter the original Session 01 seed. Do not assume Python, ClickHouse, Kafka or CI implementations are already present: these are added gradually in their designated sessions.

## Session 03 — ClickHouse practice environment

ClickHouse is an **optional Compose profile**; it does not start during the default PostgreSQL workflow. First-run initialization loads two independent raw datasets (6-row interview case, plus a 12-row copy of Session 02). No latest-state or PnL solutions are prefilled.

```bash
docker compose --profile clickhouse up -d --wait clickhouse
docker compose --profile clickhouse exec -T clickhouse clickhouse-client --user qa --password qa --multiquery < clickhouse/checks/smoke.sql
docker compose --profile clickhouse exec clickhouse clickhouse-client --user qa --password qa --database lab03
```

Inside the client, run `SELECT * FROM lab03.trading_events ORDER BY ingest_id;`. The complete setup, client connection, practice sequence and safe fixture reload are in [clickhouse/README.md](clickhouse/README.md).

**Status:** configured in Git; runtime validation on the learner's Docker host is still pending.

## Ready-to-run Exness labs (Sessions 06–13)

Use [labs/README.md](labs/README.md) and the session-specific `START_HERE.md` files. Preparatory validation: `uv sync --group dev && uv run pytest -q tests/labs`. The GitHub Actions `lab-readiness` workflow checks only fixture structure and disposable PostgreSQL data. It **does not** claim that learner solutions, full DQ gates or live Kafka/Flink and ClickHouse advanced exercises have been completed. All interactive interview practice is in Russian.

## Gap-based interview readiness review (11 November 2026)

See [the evidence-based audit of Sessions 01–08](docs/INTERVIEW_READINESS_AUDIT_2026-11-11.md). Sessions 09–17 include additional targeted scenarios, scorecard templates and follow-up questions, without reference answers ahead of a candidate attempt. Session 09 remains oral-first and is deliberately not pre-solved. Documentation updates are not a substitute for test execution or independently demonstrated interview performance.

## Unified five-block preparation option (2026-11-12)

The [Unified Data Stack Training Lab](labs/unified/README.md) provides an optional real Kafka → Flink SQL → Kafka → ClickHouse path with a PostgreSQL manifest and standalone DQ checker. The [five-block curriculum](labs/unified/CURRICULUM.md) groups original Sessions **10+13**, **11+12**, **14**, **15**, and **16+17** into ~7 hours **excluding environment setup**, without deleting existing exercises, independent mock material or calendar entries. See the separate integration CI for validated claims; a runnable profile alone does not prove end-to-end exactly-once. Session titles retain the canonical `🎯 Exness | Session NN — ...` format.


Verified integration evidence: [Unified Streaming Lab, 12 November 2026](docs/UNIFIED_LAB_VERIFICATION_2026-11-12.md) (all six synthetic scenarios validated in CI; production exactly-once not claimed).
