-- No exercise solutions here: only verify that initialization worked.
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM trades) <> 8 THEN
        RAISE EXCEPTION 'Expected 8 source trades';
    END IF;
    IF (SELECT COUNT(*) FROM processed_trades) <> 10 THEN
        RAISE EXCEPTION 'Expected 10 processing records';
    END IF;
END
$$;
SELECT 'seed data OK' AS result;
