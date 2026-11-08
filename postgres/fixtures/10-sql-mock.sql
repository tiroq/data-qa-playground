-- Session 10 only: this reload is destructive only to lab10.
DROP SCHEMA IF EXISTS lab10 CASCADE;
CREATE SCHEMA lab10;

CREATE TABLE lab10.source_events (
 src_id BIGINT PRIMARY KEY, trade_id BIGINT, account_id TEXT, version INTEGER NOT NULL,
 event_id TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL,
 pnl NUMERIC(18,4), status TEXT
);
CREATE TABLE lab10.target_events (
 target_id BIGINT PRIMARY KEY, trade_id BIGINT, account_id TEXT, version INTEGER NOT NULL,
 event_id TEXT NOT NULL, available_at TIMESTAMPTZ NOT NULL,
 pnl NUMERIC(18,4), status TEXT
);

INSERT INTO lab10.source_events (src_id,trade_id,account_id,version,event_id,created_at,pnl,status) VALUES
(1,301,'A1',1,'S301-1','2026-11-08 12:00:00+00',0,'NEW'),
(2,301,'A1',2,'S301-2','2026-11-08 12:01:00+00',10,'FILLED'),
(3,302,'A1',1,'S302-1','2026-11-08 12:02:00+00',-2,'FILLED'),
(4,303,'A2',1,'S303-1','2026-11-08 12:03:00+00',0,'NEW'),
(5,304,'A2',2,'S304-2','2026-11-08 12:04:00+00',4,'FILLED'),
(6,304,'A2',2,'S304-2','2026-11-08 12:04:00+00',4,'FILLED'),
(7,305,'A3',1,'S305-1','2026-11-08 12:05:00+00',9,'FILLED'),
(8,306,'A3',1,'S306-1','2026-11-08 12:06:00+00',0,'CANCELLED'),
(9,307,'A4',1,'S307-1','2026-11-08 12:07:00+00',7,'FILLED'),
(10,308,'A4',2,'S308-2','2026-11-08 12:08:00+00',6,'FILLED'),
(11,309,'A5',1,'S309-1','2026-11-08 12:09:00+00',3,'FILLED'),
(12,NULL,'A9',1,'S-INVALID','2026-11-08 12:10:00+00',1,'NEW');

INSERT INTO lab10.target_events (target_id,trade_id,account_id,version,event_id,available_at,pnl,status) VALUES
(101,301,'A1',2,'S301-2','2026-11-08 12:02:00+00',10,'FILLED'),
(102,302,'A1',1,'S302-1','2026-11-08 12:13:00+00',-2,'FILLED'),
(103,303,'A2',1,'S303-1','2026-11-08 12:04:00+00',0,'NEW'),
(104,304,'A2',2,'S304-2','2026-11-08 12:05:00+00',4,'FILLED'),
(105,304,'A2',2,'S304-2','2026-11-08 12:05:00+00',4,'FILLED'),
(106,305,'A3',1,'S305-1','2026-11-08 12:06:00+00',10,'FILLED'),
(107,306,'A3',1,'S306-1','2026-11-08 12:07:00+00',0,'CANCELLED'),
(108,308,'A4',1,'S308-1','2026-11-08 12:09:00+00',5,'NEW'),
(109,309,'A5',1,'S309-1','2026-11-08 12:10:00+00',3,'FILLED'),
(110,310,'A5',1,'S310-1','2026-11-08 12:11:00+00',1,'FILLED'),
(111,307,'A999',1,'S307-1','2026-11-08 12:12:00+00',7,'FILLED'),
(112,NULL,'A9',1,'S-INVALID','2026-11-08 12:12:00+00',1,'NEW');

CREATE INDEX idx_lab10_source_key ON lab10.source_events (trade_id,account_id);
CREATE INDEX idx_lab10_target_key ON lab10.target_events (trade_id,account_id);
