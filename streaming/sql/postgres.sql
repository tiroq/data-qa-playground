-- Safe to run repeatedly. Isolated from the existing Session 01/02/04 schemas.
CREATE SCHEMA IF NOT EXISTS labstream;

CREATE TABLE IF NOT EXISTS labstream.runs (
  run_id TEXT PRIMARY KEY,
  scenario TEXT NOT NULL,
  planned_events INTEGER NOT NULL CHECK (planned_events >= 0),
  sealed BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS labstream.expected_events (
  run_id TEXT NOT NULL REFERENCES labstream.runs(run_id),
  event_id TEXT NOT NULL,
  trade_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  pnl TEXT NOT NULL,
  status TEXT NOT NULL,
  event_time_ms BIGINT NOT NULL,
  PRIMARY KEY (run_id, event_id)
);

CREATE INDEX IF NOT EXISTS labstream_expected_trade_idx
 ON labstream.expected_events (run_id, account_id, trade_id, version);
