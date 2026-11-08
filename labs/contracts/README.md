# Synthetic TradingEvent contract

This is an illustrative JSON Schema for interview design, **not** a schema from Exness. It encodes decimal PnL as a string and identifies immutable business events separately from transport delivery/offsets. Business identity is `(trade_id, account_id)`; version ties are not settled by arrival timestamp.

Schema validation alone cannot enforce cross-event uniqueness, latest-version correctness, missing-event detection, completeness watermark or time-based SLA. These require stateful DQ rules and independent source evidence.

No JSON Schema validation dependency is installed. Preparation smoke checks verify the file's basic structure, **not** full Draft 2020-12 validation.
