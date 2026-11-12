-- Isolated training schema; never touches public or earlier lab schemas.
CREATE SCHEMA IF NOT EXISTS streaming_lab;
CREATE TABLE IF NOT EXISTS streaming_lab.batches (
  run_id TEXT PRIMARY KEY,
  scenario TEXT NOT NULL,
  planned_count INTEGER NOT NULL CHECK (planned_count > 0),
  sealed BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- CREATE TABLE IF NOT EXISTS does not upgrade persisted training volumes.
ALTER TABLE streaming_lab.batches ADD COLUMN IF NOT EXISTS sealed BOOLEAN NOT NULL DEFAULT FALSE;
CREATE TABLE IF NOT EXISTS streaming_lab.source_events (
  run_id TEXT NOT NULL REFERENCES streaming_lab.batches(run_id),
  event_id TEXT NOT NULL,
  trade_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  version INTEGER NOT NULL CHECK (version > 0),
  status TEXT NOT NULL,
  pnl NUMERIC(18,4) NOT NULL,
  event_time TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (run_id, event_id)
);
CREATE INDEX IF NOT EXISTS idx_streaming_source_business
  ON streaming_lab.source_events(run_id, account_id, trade_id, version);
