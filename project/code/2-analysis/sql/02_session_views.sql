-- 02: ringkasan per sesi uji (satu sesi = satu file mesin). Dipakai untuk tren (Q9) dan uji tingkat sesi.

CREATE OR REPLACE VIEW v_session_summary AS
SELECT
  s.session_id,
  s.test_date,
  s.model,
  s.condition,
  s.bonder,
  s.operator,
  COUNT(*) AS n,
  ROUND(AVG(p.force_g), 6) AS mean_g,
  ROUND(MEDIAN(p.force_g), 6) AS median_g,
  ROUND(STDDEV_SAMP(p.force_g), 6) AS sd_g,
  ROUND(MIN(p.force_g), 6) AS min_g,
  SUM(CASE WHEN p.result = 'NG' THEN 1 ELSE 0 END) AS ng_count
FROM test_sessions s
JOIN push_results p USING (session_id)
GROUP BY s.session_id, s.test_date, s.model, s.condition, s.bonder, s.operator
ORDER BY s.session_id;
