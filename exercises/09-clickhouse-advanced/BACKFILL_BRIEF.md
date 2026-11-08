# Advanced ClickHouse migration / materialized view challenge

## Context

Raw stored deliveries are preserved in `lab09.raw_events` with the same 12 physical rows as `lab03.trade_versions`, including duplicate representation of version 2 for trade 201 and contradictory version-2 PnL for trade 205.

## Tasks

1. Propose a **separate** target representation for latest logical trade states. Explicitly choose the business-key grain and tie/conflict policy.
2. Explain whether a materialized view should write aggregate states, raw projections, or finalized numbers. State limitations of incremental inserts and cross-partition data.
3. Build the target and insert existing history by an explicit backfill approach; then support future deliveries without silently double-counting.
4. Design SQL checks to compare raw event identity coverage, logical trade coverage and account-level PnL **with a declared conflict policy**.
5. Simulate a post-deploy replay and describe how you would detect and recover from partial backfill or duplicate processing.
6. Propose a rollback: what must be kept, how to avoid raw-data loss, and when to disable the new MV.
7. Discuss TTL: under what retention policy would a later reconciliation or backfill become impossible?

## Required evidence

- Original 12 physical rows remain queryable in `lab09.raw_events` before your modification.
- Account or trade-level aggregates do not assert a deterministic answer for conflicting maximum-version data unless an explicit policy is enforced.
- At least one BEFORE/AFTER validation query and one counterexample.
- Final SQL saved into the exercise directory, not into auto-executed `clickhouse/init/` scripts.

## Explicitly out of scope

No live distributed ClickHouse cluster is provisioned. Replication/distributed consistency must be addressed as a **design discussion**, not claimed validated.
