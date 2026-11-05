select t.trade_id,
       t.account_id,
       t.symbol
from trades as t
LEFT JOIN processed_trades as processed ON t.trade_id = processed.trade_id
-- Это корректно при условии, что trade_id глобально уникален и именно он определяет соответствие сделок.
-- Но если бизнес-идентификатором является (trade_id, account_id), необходимо отдельно проверить,
-- достаточно ли одного поля.
AND processed.account_id = t.account_id
WHERE processed.trade_id IS NULL;