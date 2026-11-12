# Interview Backup Lab — isolated live demo + offline fallback

This is an optional **independent** synthetic data stack for a technical interview. The [primary unified lab](../unified/README.md) and its CI remain untouched. The backup has its own Docker Compose project, volumes, host ports, SQL/Kafka/Flink pipeline, source manifest, Data Quality checker and read-only dashboard.

## Backup Level 0 — offline (no Docker, network or pip dependencies)

From repository root:

    bash labs/interview-backup/scripts/run.sh offline

Open **labs/interview-backup/artifacts/offline-report.html** in any browser. This standalone page displays six synthetic PASS/FAIL examples and underlying evidence. It is prominently labelled **SIMULATION ONLY**. Do not present it as evidence of live Kafka/Flink processing.

## Backup Level 1 — full live Data Stack

Pre-download all images and start the lab once **before** the interview. The first build downloads multiple Docker images and a Kafka connector JAR. Requirements: Docker Desktop/Engine, Compose v2, Bash, Python 3, and sufficient RAM for PostgreSQL, Kafka, Flink and ClickHouse.

From repository root:

    bash labs/interview-backup/scripts/run.sh up

Open the [visual DQ dashboard](http://127.0.0.1:28765) at localhost:28765. Flink UI is at http://127.0.0.1:28081.

To publish a test scenario:

    bash labs/interview-backup/scripts/run.sh seed clean

Copy the printed RUN_ID and pass its actual value to:

    bash labs/interview-backup/scripts/run.sh check YOUR_RUN_ID PASS

To demonstrate a missing event:

    bash labs/interview-backup/scripts/run.sh seed missing
    bash labs/interview-backup/scripts/run.sh check YOUR_RUN_ID FAIL missing_event

A full pre-interview readiness sweep runs six live scenarios, one unsealed source manifest and the offline simulation:

    bash labs/interview-backup/scripts/run.sh demo

The demo stores machine-readable JSON evidence under **labs/interview-backup/artifacts**. Run it *before* interview day, not during timed questions. Afterward the containers stay up, so individual fresh scenarios can be shown quickly.

## Unique localhost host ports

| Service | Primary lab | Independent backup |
|---|---:|---:|
| PostgreSQL | 5433 | **15433** |
| Kafka | 19092 | **29092** |
| Flink UI | 18081 | **28081** |
| ClickHouse HTTP | 18123 | **28123** |
| ClickHouse native | 19000 | **29000** |
| Read-only DQ dashboard | Not provided | **28765** |

Backup Compose project name is **dataqa-interview-backup**. Its Kafka, PostgreSQL, Flink and ClickHouse volumes are separate. All host ports bind only to 127.0.0.1.

## Added proof boundaries

1. **Post-Flink Kafka business key**: Flink writes a JSON record key derived from run ID, account ID and trade ID. The ClickHouse sink checks this key before accepting the event. Same trade can be mapped consistently within the processed Kafka topic; exact input/output partition numbers need not match.
2. **Source publication seal**: manifest rows are first registered as PENDING, and promoted to PUBLISHED only after Kafka publishing is acknowledged. An unsealed run is explicitly INDETERMINATE, not a false green business check or a proven permanent loss.
3. **Offset commit inspection**: sink inserts into ClickHouse, then checks synchronous Kafka offset commit results. This is at-least-once, not an atomic transaction; replay may still create extra physical rows.
4. **Single restart owner**: Docker Compose restarts the sink after a process error, rather than combining process-level and Compose retry loops.
5. **Read-only dashboard**: live query-visible counts, physical vs distinct IDs, PnL, version, expected/observed events, negative-control diagnostics, and source publication state. It has no write endpoints and does not promise sink completion or exactly-once.
6. **Fallback simulation**: standalone static HTML with original pure-Python DQ rules for six deterministic fixtures. Works even without Docker.

## Controlled failure injection

To pause only the data sink, while Kafka and source continue to accept messages:

    bash labs/interview-backup/scripts/run.sh pause-sink
    bash labs/interview-backup/scripts/run.sh seed clean

The dashboard will show incomplete target evidence. Then recover:

    bash labs/interview-backup/scripts/run.sh resume-sink
    bash labs/interview-backup/scripts/run.sh check YOUR_RUN_ID PASS

Do **not** describe a missing in-flight event as confirmed permanent loss until the sink completion contract has been satisfied. A positive snapshot cannot prove no late conflicting event will arrive.

## Status, diagnosis, safe teardown

    bash labs/interview-backup/scripts/run.sh status
    docker compose -f labs/interview-backup/compose.yaml config --quiet
    python3 -m unittest discover -s labs/interview-backup/tests -v
    docker compose -f labs/interview-backup/compose.yaml logs --tail=120 flink-sql-submit streaming-sink dashboard
    bash labs/interview-backup/scripts/run.sh down

The normal down operation **retains all named volumes** and does not affect the primary lab. The dedicated backup CI uses destructive volume cleanup **only on its own disposable runner**, not on your Mac.

## Verification and training limits

The [dedicated workflow](../../.github/workflows/interview-backup.yml) has separate **validate** (offline/unit/Compose) and **e2e** (real Docker) jobs. A passing validate job alone does not certify the live stack. Check an exact-head successful e2e run before calling it ready for interview use.

The system does not implement production-grade CDC, Flink stateful window recovery, transactional Kafka/ClickHouse exactly-once, cross-partition sink completion barriers, schema registry, multi-broker Kafka HA, or TLS. The Flink SQL pipeline is a real streaming transformation without a windowed aggregate. Those topics remain genuine interview design questions.

Useful materials: [five-block curriculum](../unified/CURRICULUM.md), [SQL practice](../unified/SQL_TASKS.md), [streaming failure drills](../../exercises/11-kafka-flink/BARRIER_AND_CHECKPOINT_DRILLS.md), [incident mock](../../exercises/15-mock-interview-2/INCIDENT_PACKET.md).
