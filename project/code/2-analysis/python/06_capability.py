"""06 - Kapabilitas dan risiko NG (Q6, Q8), tren per sesi (Q9), dan variasi bonder/operator (Q10).

- Cpk satu sisi terhadap LSL: (mean - LSL) / (3 * sd). CI pendekatan normal (Bissell).
- Fail rate aktual: NG / n, dengan CI Wilson.
- Estimasi ppm: P(gaya < LSL) dari distribusi normal dengan mean dan sd kombinasi (asumsi normal, dicek ulang di 07).
- Tren (Q9) dan bonder/operator (Q10) memakai residual terhadap rata-rata kombinasi agar tidak tercampur kondisi.
Keluaran: results/2-analysis/capability.csv, trend.csv, source_variation.csv; tabel DuckDB group_summary.
"""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportion_confint

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import COND_LABEL, CPK_TARGET, DB_PATH, LSL_G, RES_ANA

con = duckdb.connect(str(DB_PATH))
push = con.execute("SELECT session_id, model, condition, sequence, force_g, result, bonder, operator, test_date "
                   "FROM v_push ORDER BY session_id, sample_no").df()
sess = con.execute("SELECT session_id, model, condition, test_date, mean_g, sd_g, ng_count FROM v_session_summary "
                   "ORDER BY session_id").df()

# Q6 dan Q8 per kombinasi
rows = []
for (m, c), g in push.groupby(["model", "condition"], sort=False):
    x = g.force_g.to_numpy()
    n, mu, sd = len(x), x.mean(), x.std(ddof=1)
    cpk = (mu - LSL_G) / (3 * sd)
    se = np.sqrt(1 / (9 * n) + cpk ** 2 / (2 * (n - 1)))
    ng = int((g.result == "NG").sum())
    lo, hi = proportion_confint(ng, n, alpha=0.05, method="wilson")
    ppm = stats.norm.cdf((LSL_G - mu) / sd) * 1e6
    rows.append(dict(model=m, condition=c, condition_label=COND_LABEL[c], n=n, median_g=float(np.median(x)),
                     mean_g=mu, sd_g=sd, cpk=cpk, cpk_lo=cpk - 1.96 * se, cpk_hi=cpk + 1.96 * se,
                     memenuhi_target=("Memenuhi" if cpk >= CPK_TARGET else "Belum memenuhi"),
                     ng_count=ng, fail_rate=ng / n, fail_rate_lo=lo, fail_rate_hi=hi, est_ppm=ppm))
cap = pd.DataFrame(rows)
cap = cap.sort_values(["model", "condition"], key=lambda s: s.map(
    {"Model A": 0, "Model B": 1, "before_oven": 0, "after_oven": 1, "after_baked": 2})).reset_index(drop=True)
cap_out = cap.copy()
for c in ["mean_g", "sd_g", "cpk", "cpk_lo", "cpk_hi", "fail_rate", "fail_rate_lo", "fail_rate_hi", "est_ppm", "median_g"]:
    cap_out[c] = cap_out[c].astype(float).round(6)
cap_out.to_csv(RES_ANA / "capability.csv", index=False, encoding="utf-8")

# Tabel group_summary di database (model x kondisi, dengan Cpk dan fail rate)
con.register("cap_df", cap)
con.execute("CREATE OR REPLACE TABLE group_summary AS SELECT model, condition, n, median_g, sd_g, cpk, fail_rate "
            "FROM cap_df ORDER BY model, condition")

# Q9: tren per sesi. Residual sesi = rata-rata sesi - rata-rata kombinasi model x kondisi.
combo_mean = push.groupby(["model", "condition"]).force_g.mean().rename("combo_mean").reset_index()
sr = sess.merge(combo_mean, on=["model", "condition"])
sr["resid_g"] = sr.mean_g - sr.combo_mean
sr["test_date"] = pd.to_datetime(sr.test_date)
rho, p_rho = stats.spearmanr(sr.test_date.map(pd.Timestamp.toordinal), sr.resid_g)
sr["bulan"] = sr.test_date.dt.strftime("%Y-%m")
trend_rows = []
for b, g in sr.groupby("bulan"):
    trend_rows.append(dict(kelompok=f"Bulan {b}", n_sesi=len(g), median_residual_g=float(g.resid_g.median()),
                           sesi_ng=int((g.ng_count > 0).sum()), spearman_rho="", p_value=""))
trend_rows.append(dict(kelompok="Seluruh sesi (Spearman tanggal vs residual)", n_sesi=len(sr), median_residual_g="",
                       sesi_ng="", spearman_rho=float(rho), p_value=float(p_rho)))
pd.DataFrame(trend_rows).to_csv(RES_ANA / "trend.csv", index=False, encoding="utf-8")

# Q10: bonder dan operator (residual cover glass terhadap rata-rata kombinasi)
push = push.merge(combo_mean, on=["model", "condition"])
push["resid_g"] = push.force_g - push.combo_mean
sv = []
for var in ["bonder", "operator"]:
    groups = [g.resid_g.to_numpy() for _, g in push.groupby(var)]
    H, p = stats.kruskal(*groups)
    for k, g in push.groupby(var):
        sv.append(dict(faktor=var, kelompok=k, n=len(g), median_residual_g=float(g.resid_g.median()),
                       kruskal_H=float(H), p_value=float(p)))
pd.DataFrame(sv).sort_values(["faktor", "kelompok"]).to_csv(RES_ANA / "source_variation.csv", index=False, encoding="utf-8")
con.close()

print(cap_out[["model", "condition", "n", "median_g", "cpk", "memenuhi_target", "ng_count", "est_ppm"]].to_string(index=False))
print("Spearman tren:", round(rho, 4), "p =", round(p_rho, 4))
