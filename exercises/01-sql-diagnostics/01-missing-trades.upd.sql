select t.trade_id,
       t.account_id,
       t.symbol
from trades as t
LEFT JOIN processed_trades as processed ON t.trade_id = processed.trade_id
WHERE processed.trade_id IS NULL;