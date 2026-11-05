CREATE TABLE trades (
    trade_id BIGINT PRIMARY KEY,
    account_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    volume NUMERIC(18, 4) NOT NULL
);

CREATE TABLE processed_trades (
    record_id BIGINT PRIMARY KEY,
    trade_id BIGINT,
    account_id TEXT,
    status TEXT
);

CREATE INDEX idx_processed_trades_business_key
    ON processed_trades (trade_id, account_id);
