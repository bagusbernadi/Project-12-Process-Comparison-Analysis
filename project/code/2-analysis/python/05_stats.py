"""05 - Uji statistik untuk Q1-Q5 dan Q7.

Aturan:
- selisih selalu ditulis sebagai rata-rata kiri dikurangi kanan (perbandingan "X vs Y");
- uji utama per cover glass (Welch t, ANOVA, Tukey); uji sensitivitas per sesi (sesi = unit acak);
- koreksi Holm untuk keluarga perbandingan yang sama (Q3 dan Q4);
- "praktis" = selisih mutlak minimal PRACTICAL_DIFF_G (asumsi, lihat project/docs/definitions.md).
Keluaran: results/2-analysis/test_results.csv
"""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import ALPHA, COND_LABEL, DB_PATH, RES_ANA, PRACTICAL_DIFF_G

con = duckdb.connect(str(DB_PATH), read_only=True)
push = con.execute("SELECT session_id, model, condition, force_g FROM v_push ORDER BY session_id, condition, force_g").df()
sess = con.execute("SELECT session_id, model, condition, mean_g FROM v_session_summary ORDER BY session_id").df()
con.close()
push["cond_label"] = push.condition.map(COND_LABEL)
L = lambda c: push.loc[push.condition == c, "force_g"].to_numpy()
LM = lambda m, c: push.loc[(push.model == m) & (push.condition == c), "force_g"].to_numpy()
LS = lambda c: sess.loc[sess.condition == c, "mean_g"].to_numpy()


def welch(a, b):
    na, nb = len(a), len(b)
    va, vb = a.var(ddof=1), b.var(ddof=1)
    se = np.sqrt(va / na + vb / nb)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    diff = a.mean() - b.mean()
    tcrit = stats.t.ppf(1 - ALPHA / 2, df)
    sp = np.sqrt(((na - 1) * va + (nb - 1) * vb) / (na + nb - 2))
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return dict(diff=diff, lo=diff - tcrit * se, hi=diff + tcrit * se, d=diff / sp, stat=t, p=p, na=na, nb=nb)


def holm(pvals):
    p = np.asarray(pvals, float)
    order = np.argsort(p, kind="mergesort")
    m = len(p)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adj[idx] = min(1.0, running)
    return adj


def decide(p_adj, diff):
    if p_adj >= ALPHA:
        return "Tidak signifikan"
    return "Signifikan dan praktis" if abs(diff) >= PRACTICAL_DIFF_G else "Signifikan, selisih kecil"


rows = []


def add(q, uji, comp, res=None, stat=None, p=None, p_adj=None, keputusan="", catatan="", **extra):
    rows.append(dict(pertanyaan=q, uji=uji, perbandingan=comp,
                     n_kiri=extra.get("na", ""), n_kanan=extra.get("nb", ""),
                     selisih_g=extra.get("diff", ""), ci_bawah_g=extra.get("lo", ""), ci_atas_g=extra.get("hi", ""),
                     cohen_d=extra.get("d", ""), statistik=stat, p_value=p, p_terkoreksi=p_adj,
                     keputusan=keputusan, catatan=catatan))


# Q1: setelah oven vs sebelum oven (pooled di kedua model), plus per model
r = welch(L("after_oven"), L("before_oven"))
add("Q1", "Welch t (unit)", "Setelah oven vs Sebelum oven", stat=r["stat"], p=r["p"], p_adj=r["p"],
    keputusan=decide(r["p"], r["diff"]), catatan="pooled dua model; unit = cover glass", **{k: r[k] for k in ["diff", "lo", "hi", "d", "na", "nb"]})
mw = stats.mannwhitneyu(L("after_oven"), L("before_oven"), alternative="two-sided")
add("Q1", "Mann-Whitney U (sensitivitas)", "Setelah oven vs Sebelum oven", stat=mw.statistic, p=mw.pvalue, p_adj=mw.pvalue,
    keputusan=decide(mw.pvalue, r["diff"]), catatan="tidak mengasumsikan normalitas")
rs = welch(LS("after_oven"), LS("before_oven"))
add("Q1", "Welch t per sesi (sensitivitas)", "Setelah oven vs Sebelum oven", stat=rs["stat"], p=rs["p"], p_adj=rs["p"],
    keputusan=decide(rs["p"], rs["diff"]), catatan="unit = rata-rata sesi; 20 sesi per kondisi", **{k: rs[k] for k in ["diff", "lo", "hi", "d", "na", "nb"]})
for m in ["Model A", "Model B"]:
    rm = welch(LM(m, "after_oven"), LM(m, "before_oven"))
    add("Q1", "Welch t (unit)", f"Setelah oven vs Sebelum oven, {m}", stat=rm["stat"], p=rm["p"], p_adj=rm["p"],
        keputusan=decide(rm["p"], rm["diff"]), catatan="per model (subkelompok)", **{k: rm[k] for k in ["diff", "lo", "hi", "d", "na", "nb"]})

# Q2: ANOVA tiga kondisi (pooled) + Tukey HSD
groups = [L(c) for c in ["before_oven", "after_oven", "after_baked"]]
F, pF = stats.f_oneway(*groups)
add("Q2", "ANOVA satu arah", "tiga kondisi", stat=F, p=pF, p_adj=pF,
    keputusan="Signifikan" if pF < ALPHA else "Tidak signifikan", catatan="pooled dua model; F dengan df 2 dan 597")
tk = pairwise_tukeyhsd(push.force_g.to_numpy(), push.condition.to_numpy(), alpha=ALPHA)
tkdf = pd.DataFrame(tk.summary().data[1:], columns=["g1", "g2", "meandiff", "p_adj", "lo", "hi", "reject"])
for _, t in tkdf.iterrows():
    comp = f"{COND_LABEL[t.g2]} vs {COND_LABEL[t.g1]}"  # meandiff = rata-rata g2 - g1
    dif = float(t.meandiff)
    add("Q2", "Tukey HSD", comp, p_adj=float(t.p_adj), p=float(t.p_adj),
        diff=dif, lo=float(t.lo), hi=float(t.hi),
        keputusan=decide(float(t.p_adj), dif), catatan="uji lanjut setelah ANOVA; p sudah terkoreksi")

# Q3: effect size (Cohen's d) dan CI selisih, tiga pasang kondisi; koreksi Holm
pairs = [("after_oven", "before_oven"), ("after_baked", "before_oven"), ("after_baked", "after_oven")]
res = [welch(L(a), L(b)) for a, b in pairs]
adj = holm([r["p"] for r in res])
for (a, b), r, pa in zip(pairs, res, adj):
    add("Q3", "Welch t + Cohen's d + CI", f"{COND_LABEL[a]} vs {COND_LABEL[b]}", stat=r["stat"], p=r["p"], p_adj=pa,
        keputusan=decide(pa, r["diff"]), catatan="p terkoreksi Holm (3 pasang)", **{k: r[k] for k in ["diff", "lo", "hi", "d", "na", "nb"]})

# Q4: Model A vs Model B pada tiap kondisi; koreksi Holm
conds = ["before_oven", "after_oven", "after_baked"]
res4 = [welch(LM("Model A", c), LM("Model B", c)) for c in conds]
adj4 = holm([r["p"] for r in res4])
for c, r, pa in zip(conds, res4, adj4):
    add("Q4", "Welch t (unit)", f"Model A vs Model B, {COND_LABEL[c]}", stat=r["stat"], p=r["p"], p_adj=pa,
        keputusan=decide(pa, r["diff"]), catatan="p terkoreksi Holm (3 kondisi)", **{k: r[k] for k in ["diff", "lo", "hi", "d", "na", "nb"]})
mw4 = [stats.mannwhitneyu(LM("Model A", c), LM("Model B", c), alternative="two-sided").pvalue for c in conds]
adj4m = holm(mw4)
for c, p, pa in zip(conds, mw4, adj4m):
    add("Q4", "Mann-Whitney U (sensitivitas)", f"Model A vs Model B, {COND_LABEL[c]}", p=p, p_adj=pa,
        keputusan=decide(pa, 0.0), catatan="p terkoreksi Holm; tanpa selisih rata-rata")

# Q5: ANOVA dua arah model x kondisi (interaksi) pada unit, dan pada rata-rata sesi
m2 = ols("force_g ~ C(model) * C(condition)", data=push).fit()
a2 = anova_lm(m2, typ=2)
for term, label in [("C(model)", "Model"), ("C(condition)", "Kondisi"), ("C(model):C(condition)", "Interaksi model x kondisi")]:
    add("Q5", "ANOVA dua arah (unit)", label, stat=float(a2.loc[term, "F"]), p=float(a2.loc[term, "PR(>F)"]),
        p_adj=float(a2.loc[term, "PR(>F)"]), keputusan="Signifikan" if a2.loc[term, "PR(>F)"] < ALPHA else "Tidak signifikan",
        catatan="df interaksi 2; unit bersarang dalam sesi, lihat sensitivitas")
s2 = ols("mean_g ~ C(model) * C(condition)", data=sess).fit()
b2 = anova_lm(s2, typ=2)
for term, label in [("C(model)", "Model"), ("C(condition)", "Kondisi"), ("C(model):C(condition)", "Interaksi model x kondisi")]:
    add("Q5", "ANOVA dua arah per sesi (sensitivitas)", label, stat=float(b2.loc[term, "F"]), p=float(b2.loc[term, "PR(>F)"]),
        p_adj=float(b2.loc[term, "PR(>F)"]), keputusan="Signifikan" if b2.loc[term, "PR(>F)"] < ALPHA else "Tidak signifikan",
        catatan="unit = rata-rata sesi (n = 60)")
sw = stats.shapiro(m2.resid)
add("Q5", "Shapiro-Wilk residual (asumsi)", "residual ANOVA dua arah", stat=float(sw.statistic), p=float(sw.pvalue),
    p_adj=float(sw.pvalue), keputusan="Tidak normal (dicatat)" if sw.pvalue < ALPHA else "Normal",
    catatan="karena n besar, uji ini sensitif; Welch dan ANOVA dianggap cukup kuat")

# Q7: sebaran gaya antar kondisi per model (Brown-Forsythe = Levene berpusat median)
for m in ["Model A", "Model B"]:
    gs = [LM(m, c) for c in conds]
    lv = stats.levene(*gs, center="median")
    sds = [g.std(ddof=1) for g in gs]
    add("Q7", "Levene (berpusat median)", f"tiga kondisi, {m}", stat=float(lv.statistic), p=float(lv.pvalue),
        p_adj=float(lv.pvalue), keputusan=decide(lv.pvalue, 0.0),
        catatan=f"rasio simpangan baku maks/min = {max(sds) / min(sds):.2f}")

out = pd.DataFrame(rows)
for c in ["selisih_g", "ci_bawah_g", "ci_atas_g", "cohen_d", "statistik", "p_value", "p_terkoreksi"]:
    out[c] = out[c].apply(lambda v: float(f"{float(v):.6g}") if v not in ("", None) and not pd.isna(v) else v)
out.to_csv(RES_ANA / "test_results.csv", index=False, encoding="utf-8")
print(out[["pertanyaan", "perbandingan", "selisih_g", "p_terkoreksi", "keputusan"]].to_string(index=False))
