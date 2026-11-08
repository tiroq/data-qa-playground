-- Event-level SLA: availability within 10 minutes of source event creation.
-- Synthetic fixed clock for deterministic interview verification.
-- A Kafka lag or Flink watermark does not move the business deadline.
CREATE OR REPLACE VIEW lab04.sla_event_report AS
WITH params AS (
  SELECT TIMESTAMPTZ '2026-11-08 12:30:00+00' AS evaluated_at,
         TIMESTAMPTZ '2026-11-08 12:30:00+00' AS event_cutoff,
         INTERVAL '10 minutes' AS deadline_interval
),
receipts AS (
  SELECT o.event_id,
         MIN(o.available_at) AS first_available_at,
         COUNT(*) AS receipt_count
  FROM lab04.delivery_observations o CROSS JOIN params p
  WHERE o.available_at <= p.evaluated_at
  GROUP BY o.event_id
),
classified AS (
  SELECT e.event_id, e.cohort_label, e.trade_id, e.account_id,
         e.version, e.created_at,
         r.first_available_at, COALESCE(r.receipt_count,0) AS receipt_count,
         p.evaluated_at, p.event_cutoff,
         CASE
           WHEN e.created_at IS NULL THEN 'INVALID_TIMESTAMP'
           WHEN e.created_at > p.event_cutoff THEN 'AFTER_CUTOFF'
           WHEN r.first_available_at < e.created_at THEN 'INVALID_TIMESTAMP'
           WHEN e.created_at > p.evaluated_at - p.deadline_interval
             THEN 'IN_FLIGHT'
           WHEN r.first_available_at <= e.created_at + p.deadline_interval
             THEN 'ON_TIME'
           WHEN r.first_available_at > e.created_at + p.deadline_interval
             THEN 'LATE'
           ELSE 'UNDELIVERED_OVERDUE'
         END AS delivery_status,
         (e.created_at IS NOT NULL
            AND e.created_at <= p.event_cutoff
            AND e.created_at <= p.evaluated_at - p.deadline_interval
            AND (r.first_available_at IS NULL
                 OR r.first_available_at >= e.created_at)
         ) AS eligible_for_sla,
         r.first_available_at - e.created_at AS delivery_lag
  FROM lab04.delivery_events e
  CROSS JOIN params p
  LEFT JOIN receipts r USING (event_id)
)
SELECT * FROM classified;

CREATE OR REPLACE VIEW lab04.sla_summary AS
SELECT cohort_label,
       COUNT(*) AS eligible_events,
       COUNT(*) FILTER (WHERE delivery_status='ON_TIME') AS on_time_events,
       COUNT(*) FILTER (WHERE delivery_status='LATE') AS late_events,
       COUNT(*) FILTER (WHERE delivery_status='UNDELIVERED_OVERDUE')
         AS overdue_undelivered_events,
       ROUND(
         100.0 * COUNT(*) FILTER (WHERE delivery_status='ON_TIME')
         / NULLIF(COUNT(*),0), 2
       ) AS on_time_percent,
       (100.0 * COUNT(*) FILTER (WHERE delivery_status='ON_TIME')
         / NULLIF(COUNT(*),0) >= 95.0) AS sla_met
FROM lab04.sla_event_report
WHERE eligible_for_sla
GROUP BY cohort_label;

-- False-positive prevention: report IN_FLIGHT separately from matured missing
-- events; preserve INVALID_TIMESTAMP as a DQ incident, not a dropped record.
