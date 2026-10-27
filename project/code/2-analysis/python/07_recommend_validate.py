"""07 - Rekomendasi (Q11), uji sensitivitas asumsi, daya deteksi, dan validasi ground truth (Q13).

Hanya skrip ini (bersama 01) yang membaca parameter GT. Analisis Q1-Q11 tidak bergantung padanya.
Keluaran: results/2-analysis/recommendation.csv, sensitivity.csv, ground_truth_check.csv
"""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import ALPHA, COND_LABEL, DB_PATH, DIRT, GT, LSL_G, RES_ANA, RES_PREP, PRACTICAL_DIFF_G

con = duckdb.connect(str(DB_PATH), read_only=True)
push = con.execute("SELECT session_id, model, condition, force_g, result FROM v_push").df()
cap = pd.read_csv(RES_ANA / "capability.csv")
tests = pd.read_csv(RES_ANA / "test_results.csv")
dq = pd.read_csv(RES_PREP / "data_quality.csv")
sess = con.execute("SELECT session_id, model, condition, sd_g, ng_count FROM v_session_summary").df()
con.close()
ORDER = {"before_oven": 0, "after_oven": 1, "after_baked": 2}

# Q11: kondisi terbaik per model (median tertinggi), dibandingkan dengan sebelum oven
rec = []
for m, g in cap.groupby("model"):
    g = g.assign(seq=g.condition.map(ORDER)).sort_values("seq")
    before = g[g.condition == "before_oven"].iloc[0]
    best = g.sort_values(["median_g", "seq"], ascending=[False, True]).iloc[0]
    gain = best.median_g - before.median_g
    row = dict(model=m, kondisi_lama=COND_LABEL["before_oven"], kondisi_rekomendasi=COND_LABEL[best.condition],
               median_lama_g=before.median_g, median_rekomendasi_g=best.median_g, selisih_median_g=gain,
               praktis=("Ya" if gain >= PRACTICAL_DIFF_G else "Tidak"),
               fail_rate_lama=before.fail_rate, fail_rate_rekomendasi=best.fail_rate,
               est_ppm_lama=before.est_ppm, est_ppm_rekomendasi=best.est_ppm,
               penurunan_est_ppm=before.est_ppm - best.est_ppm)
    rec.append(row)
rec = pd.DataFrame(rec)
rec.round(6).to_csv(RES_ANA / "recommendation.csv", index=False, encoding="utf-8")

# Uji sensitivitas: batas praktis 250, 500, 1000 g; dan tanpa sesi outlier
sens = []
key = tests[tests.pertanyaan.isin(["Q1", "Q2", "Q3", "Q4"]) & tests.p_terkoreksi.notna()]
for _, t in key.iterrows():
    if pd.isna(t.selisih_g) or t.perbandingan.startswith("Tukey"):
        continue
    for thr in [250.0, 500.0, 1000.0]:
        sens.append(dict(uji=f"{t.pertanyaan}: {t.perbandingan}", batas_praktis_g=thr, selisih_g=t.selisih_g,
                         p_terkoreksi=t.p_terkoreksi,
                         keputusan=("Signifikan dan praktis" if t.p_terkoreksi < ALPHA and abs(t.selisih_g) >= thr
                                    else "Signifikan, selisih kecil" if t.p_terkoreksi < ALPHA else "Tidak signifikan"),
                         catatan="uji sensitivitas batas praktis (asumsi 500 g)"))
out_s = push[push.session_id != GT["outlier_session"]]
rows_wo = []
for (m, c), g in out_s.groupby(["model", "condition"]):
    x = g.force_g.to_numpy()
    mu, sd = x.mean(), x.std(ddof=1)
    rows_wo.append(dict(model=m, condition=c, cpk_tanpa_outlier=(mu - LSL_G) / (3 * sd),
                        est_ppm_tanpa_outlier=stats.norm.cdf((LSL_G - mu) / sd) * 1e6,
                        ng_tanpa_outlier=int((g.result == "NG").sum())))
wo = pd.DataFrame(rows_wo)
both = cap.merge(wo, on=["model", "condition"])
for _, r in both.iterrows():
    sens.append(dict(uji=f"Kapabilitas {r.model}, {COND_LABEL[r.condition]}", batas_praktis_g="",
                     selisih_g="", p_terkoreksi="",
                     keputusan=f"Cpk {r.cpk:.2f} dengan outlier; {r.cpk_tanpa_outlier:.2f} tanpa",
                     catatan=f"ppm {r.est_ppm:.3f} dengan, {r.est_ppm_tanpa_outlier:.3f} tanpa outlier {GT['outlier_session']}"))
pd.DataFrame(sens).to_csv(RES_ANA / "sensitivity.csv", index=False, encoding="utf-8")

# Daya deteksi interaksi model x kondisi (efek oven pada Model B vs Model A), dari sebaran sel
cell = cap.set_index(["model", "condition"])
se_did = np.sqrt(sum((cell.loc[k, "sd_g"] ** 2) / cell.loc[k, "n"] for k in
                     [("Model A", "before_oven"), ("Model A", "after_oven"),
                      ("Model B", "before_oven"), ("Model B", "after_oven")]))
mde = (stats.norm.ppf(1 - ALPHA / 2) + stats.norm.ppf(0.8)) * se_did
gain_a = cell.loc[("Model A", "after_oven"), "mean_g"] - cell.loc[("Model A", "before_oven"), "mean_g"]
gain_b = cell.loc[("Model B", "after_oven"), "mean_g"] - cell.loc[("Model B", "before_oven"), "mean_g"]
did_obs = gain_b - gain_a
did_gt = GT["base_g"]["Model B"] * GT["oven_effect"]["Model B"]["after_oven"] - \
         GT["base_g"]["Model A"] * GT["oven_effect"]["Model A"]["after_oven"]

# Q13: validasi ground truth (fakta yang ditanam vs temuan)
pooled_before = push.loc[push.condition == "before_oven", "force_g"].mean()
pooled_after = push.loc[push.condition == "after_oven", "force_g"].mean()
est_oven = pooled_after / pooled_before - 1
gt_oven = np.mean([GT["oven_effect"][m]["after_oven"] for m in ["Model A", "Model B"]])
q1 = tests[(tests.pertanyaan == "Q1") & (tests.perbandingan == "Setelah oven vs Sebelum oven")].iloc[0]
ok1 = abs(est_oven - gt_oven) <= 0.02 and q1.p_terkoreksi < ALPHA

mA = push.loc[push.model == "Model A", "force_g"].mean()
mB = push.loc[push.model == "Model B", "force_g"].mean()
est_b = 1 - mB / mA
gt_b = 0.05
b_sig = int(((tests.pertanyaan == "Q4") & (tests.uji == "Welch t (unit)") & (tests.p_terkoreksi < ALPHA)).sum())
ok2 = abs(est_b - gt_b) <= 0.02 and b_sig >= 1

q5i = tests[(tests.pertanyaan == "Q5") & (tests.perbandingan == "Interaksi model x kondisi")].iloc[0]
ok3 = bool(q5i.p_value < ALPHA and did_obs > 0)

big = sess.sort_values(["sd_g", "session_id"], ascending=[False, True]).iloc[0]
ng_big = int(sess.loc[sess.session_id == GT["outlier_session"], "ng_count"].iloc[0])
ok4 = big.session_id == GT["outlier_session"] and ng_big == len(GT["outlier_low_g"])

raw_n = int(dq.loc[dq.metrik == "baris data mentah", "nilai"].iloc[0])
dropped = {k: int(dq.loc[dq.metrik == k, "nilai"].iloc[0]) for k in
           ["baris gaya kosong", "baris gaya nol", "baris ganda"]}
pct = (raw_n - int(dq.loc[dq.metrik == "baris dipakai", "nilai"].iloc[0])) / raw_n
ok5 = (0.02 <= pct <= 0.03 and dropped["baris ganda"] == DIRT["duplicate_rows"]
       and dropped["baris gaya nol"] == DIRT["zero_force_rows"] and dropped["baris gaya kosong"] == DIRT["empty_force_rows"])

def label(ok):
    return "Ditemukan" if ok else "Tidak ditemukan"

gt = pd.DataFrame([
    dict(fakta="1. Setelah oven lebih kuat ±10%", nilai_ditanam=f"{gt_oven * 100:.1f}%",
         nilai_analisis=f"{est_oven * 100:.1f}% (Q1 p terkoreksi {q1.p_terkoreksi:.2e})",
         kriteria="selisih ≤ 2 poin persentase dan Q1 signifikan", hasil=label(ok1)),
    dict(fakta="2. Model B ±5% lebih lemah", nilai_ditanam=f"{gt_b * 100:.1f}%",
         nilai_analisis=f"{est_b * 100:.1f}%; Q4 signifikan pada {b_sig} dari 3 kondisi",
         kriteria="selisih ≤ 2 poin persentase dan Q4 signifikan minimal 1 kondisi", hasil=label(ok2)),
    dict(fakta="3. Efek oven lebih besar di Model B (interaksi)", nilai_ditanam=f"{did_gt:.0f} g (selisih kenaikan)",
         nilai_analisis=f"{did_obs:.0f} g; p interaksi {q5i.p_value:.3f}; MDE ±{mde:.0f} g",
         kriteria="Q5 interaksi signifikan dengan arah B > A",
         hasil=label(ok3) if ok3 else "Tidak ditemukan (daya rendah)"),
    dict(fakta="4. Satu sesi sangat menyebar dengan 2 unit NG", nilai_ditanam=f"{GT['outlier_session']}, 2 NG",
         nilai_analisis=f"sesi dengan sd terbesar {big.session_id} ({big.sd_g:.0f} g), NG = {ng_big}",
         kriteria="sesi sd terbesar adalah sesi yang ditanam dan NG sesuai", hasil=label(ok4)),
    dict(fakta="5. Data kotor 2–3%", nilai_ditanam="2–3% (15 baris)",
         nilai_analisis=f"{pct * 100:.2f}% ({raw_n - int(dq.loc[dq.metrik == 'baris dipakai', 'nilai'].iloc[0])} baris): "
                        f"ganda {dropped['baris ganda']}, gaya nol {dropped['baris gaya nol']}, kosong {dropped['baris gaya kosong']}",
         kriteria="persentase 2–3% dan jumlah tiap jenis sama dengan yang disisipkan", hasil=label(ok5)),
])
gt.to_csv(RES_ANA / "ground_truth_check.csv", index=False, encoding="utf-8")
print(gt.to_string(index=False))
print("rekomendasi:"); print(rec.to_string(index=False))
print(f"daya interaksi: SE {se_did:.1f} g, MDE {mde:.1f} g, selisih teramati {did_obs:.1f} g, selisih ditanam {did_gt:.1f} g")
