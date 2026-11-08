-- Session 04 synthetic fixture. PostgreSQL staging snapshots represent exports from
-- separate source/target systems; no cross-database JOIN is presumed.
-- Idempotent reset affects ONLY lab04; original Session 01/02 seeds are untouched.
DROP SCHEMA IF EXISTS lab04 CASCADE;
CREATE SCHEMA lab04;

CREATE TABLE lab04.source_snapshot (
  src_id BIGINT PRIMARY KEY,
  trade_id BIGINT,
  account_id TEXT,
  version INTEGER NOT NULL CHECK (version > 0),
  amount NUMERIC(18,2)
);

CREATE TABLE lab04.target_snapshot (
  record_id BIGINT PRIMARY KEY,
  trade_id BIGINT,
  account_id TEXT,
  version INTEGER NOT NULL CHECK (version > 0),
  amount NUMERIC(18,2),
  status TEXT
);

-- The same business key may have multiple versions, identical replays,
-- or divergent payloads at the SAME version; do not add UNIQUE constraints.
INSERT INTO lab04.source_snapshot
    (src_id, trade_id, account_id, version, amount)
VALUES
 (1,101,'A1',1,100),(2,101,'A1',1,100), -- repeated source event
 (3,102,'A1',1,200),                    -- missing in target
 (4,103,'A2',2,300),                    -- same-version mismatch
 (5,105,'A3',1,NULL),                   -- same null value, invalid amount
 (6,106,'A3',1,50),                     -- physical row with FAILED status
 (7,107,'A4',1,120),                    -- unknown target status
 (8,108,'A5',2,150),(9,108,'A5',3,120), -- latest update missing
 (10,109,'A5',3,120),                   -- mismatched amount on same v3
 (11,110,'A6',2,150),                   -- target ahead
 (12,111,'A6',3,120),                   -- conflicting latest target v3
 (13,112,'A7',3,120),                   -- correct latest, historical conflict
 (14,113,'A7',2,150),(15,113,'A7',3,130), -- valid version progression
 (16,NULL,'A4',1,20);                   -- invalid source key

INSERT INTO lab04.target_snapshot
    (record_id, trade_id, account_id, version, amount, status)
VALUES
 (11,101,'A1',1,100,'SUCCESS'),(12,101,'A1',1,100,'SUCCESS'),
 (13,103,'A2',2,290,'SUCCESS'),
 (14,104,'A2',1,70,'SUCCESS'),            -- orphan
 (15,105,'A3',1,NULL,'SUCCESS'),
 (16,106,'A3',1,50,'FAILED'),
 (17,107,'A4',1,120,NULL),
 (18,NULL,'A4',1,20,'SUCCESS'),          -- invalid target key
 (19,108,'A5',2,150,'SUCCESS'),
 (20,109,'A5',3,180,'SUCCESS'),
 (21,110,'A6',3,120,'SUCCESS'),
 (22,111,'A6',3,NULL,'SUCCESS'),(23,111,'A6',3,180,'SUCCESS'),
 (24,112,'A7',2,150,'SUCCESS'),(25,112,'A7',2,180,'SUCCESS'),
 (26,112,'A7',3,120,'SUCCESS'),
 (27,113,'A7',3,130,'SUCCESS'),
 (28,114,NULL,1,99,'SUCCESS'),          -- invalid target key
 (29,115,'A8',1,300,'PENDING');         -- orphan with unknown status

-- SLA is per unique source EVENT, not per physical retry or current trade row.
-- available_at is a synthetic independently verified QUERY-VISIBLE timestamp,
-- not a Kafka/Flink processing timestamp or async-buffer acknowledgement.
CREATE TABLE lab04.delivery_events (
  event_id BIGINT PRIMARY KEY,
  cohort_label TEXT NOT NULL,
  trade_id BIGINT NOT NULL,
  account_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  created_at TIMESTAMPTZ
);
CREATE TABLE lab04.delivery_observations (
  receipt_id BIGINT PRIMARY KEY,
  event_id BIGINT NOT NULL REFERENCES lab04.delivery_events(event_id),
  available_at TIMESTAMPTZ NOT NULL
);

-- Cohort pass: 19/20 on time -> 95%.
INSERT INTO lab04.delivery_events
    (event_id, cohort_label, trade_id, account_id, version, created_at)
SELECT 1000+n, 'pass_95', 5000+n, 'A1', 1,
       TIMESTAMPTZ '2026-11-07 11:00:00+00'
FROM generate_series(1,20) n;

-- Cohort fail: 18 on time, one late, one overdue and undelivered -> 90%.
INSERT INTO lab04.delivery_events
    (event_id, cohort_label, trade_id, account_id, version, created_at)
SELECT 2000+n, 'fail_90', 6000+n, 'A2', 1,
       TIMESTAMPTZ '2026-11-08 11:00:00+00'
FROM generate_series(1,20) n;

-- Recent events (deadline not yet reached at 12:30 UTC) do not enter SLA denominator.
INSERT INTO lab04.delivery_events
    (event_id, cohort_label, trade_id, account_id, version, created_at)
VALUES
 (3001,'in_flight',7001,'A3',1,TIMESTAMPTZ '2026-11-08 12:25:00+00'),
 (3002,'in_flight',7002,'A3',1,TIMESTAMPTZ '2026-11-08 12:26:00+00'),
 (3003,'in_flight',7003,'A3',1,TIMESTAMPTZ '2026-11-08 12:27:00+00'),
 (4001,'invalid_timestamp',8001,'A4',1,NULL);

INSERT INTO lab04.delivery_observations (receipt_id, event_id, available_at)
SELECT event_id, event_id, created_at + INTERVAL '5 minutes'
FROM lab04.delivery_events
WHERE (event_id BETWEEN 1001 AND 1019)
   OR (event_id BETWEEN 2001 AND 2018);

INSERT INTO lab04.delivery_observations (receipt_id, event_id, available_at)
SELECT event_id, event_id, created_at + INTERVAL '12 minutes'
FROM lab04.delivery_events WHERE event_id IN (1020,2019);

-- One additional retry must NOT increase the SLA denominator.
INSERT INTO lab04.delivery_observations (receipt_id, event_id, available_at)
VALUES
 (9001,1001,TIMESTAMPTZ '2026-11-07 11:06:00+00'),
 (9002,3001,TIMESTAMPTZ '2026-11-08 12:27:00+00');
