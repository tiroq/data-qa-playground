# Data QA Playground

A hands-on lab for SQL diagnostics, trading-data reconciliation, and QA automation interview practice.

## Prerequisites

- Docker Engine / Docker Desktop with Docker Compose v2

## Quick start

```bash
git clone https://github.com/tiroq/data-qa-playground.git
cd data-qa-playground
docker compose up -d --wait
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

Two tables:

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

Init files are executed only on the first startup of an **empty** PostgreSQL volume. A normal `docker compose restart` does not reload seed data.

## Roadmap

- PostgreSQL: advanced DQ scenarios and constraints
- Python + pytest + Testcontainers: automated reconciliation tests
- ClickHouse: analytics SQL and deduplication patterns
- Kafka: ingestion, delivery semantics, and idempotency
