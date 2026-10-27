-- 01: view per cover glass dan ringkasan per kombinasi model x kondisi.
-- Pembulatan 6 desimal agar hasil tidak berbeda antar rerun (float paralel).

CREATE OR REPLACE VIEW v_push AS
SELECT p.session_id, p.sample_no, p.force_g, p.result,
       s.model, s.condition, c.label AS condition_label, c.sequence, s.test_date, p.bonder, p.operator
FROM push_results p
JOIN test_sessions s USING (session_id)
JOIN dim_condition c ON c.condition = s.condition;

CREATE OR REPLACE VIEW v_group_summary AS
SELECT
  model,
  condition,
  condition_label,
  sequence,
  COUNT(*) AS n,
  ROUND(MEDIAN(force_g), 6) AS median_g,
  ROUND(quantile_cont(force_g, 0.25), 6) AS q1_g,
  ROUND(quantile_cont(force_g, 0.75), 6) AS q3_g,
  ROUND(AVG(force_g), 6) AS mean_g,
  ROUND(STDDEV_SAMP(force_g), 6) AS sd_g,
  ROUND(MIN(force_g), 6) AS min_g,
  ROUND(MAX(force_g), 6) AS max_g,
  SUM(CASE WHEN result = 'NG' THEN 1 ELSE 0 END) AS ng_count,
  ROUND(AVG(CASE WHEN result = 'NG' THEN 1.0 ELSE 0.0 END), 6) AS fail_rate
FROM v_push
GROUP BY model, condition, condition_label, sequence
ORDER BY model, sequence, condition;
