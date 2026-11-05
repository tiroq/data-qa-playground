INSERT INTO trades (trade_id, account_id, symbol, volume) VALUES
(101, 'A1', 'EURUSD', 1.0),
(102, 'A1', 'GBPUSD', 2.0),
(103, 'A2', 'EURUSD', 1.5),
(104, 'A2', 'USDJPY', 3.0),
(105, 'A3', 'EURUSD', 0.5),
(106, 'A3', 'GBPUSD', 1.0),
(107, 'A4', 'EURUSD', 2.0),
(108, 'A4', 'USDJPY', 1.5);

INSERT INTO processed_trades (record_id, trade_id, account_id, status) VALUES
(1, 101, 'A1', 'SUCCESS'),
(2, 102, 'A1', 'SUCCESS'),
(3, 102, 'A1', 'SUCCESS'),
(4, 103, 'A2', 'FAILED'),
(5, 104, 'A2', 'SUCCESS'),
(6, 105, 'A3', 'SUCCESS'),
(7, 105, 'A3', 'SUCCESS'),
(8, 107, 'A4', 'SUCCESS'),
(9, 109, 'A5', 'SUCCESS'),
(10, 108, 'A4', NULL);
