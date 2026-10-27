"""Generator Report v2 (Project 12). Membaca outputs/*.csv, merakit design-and-report/index.html.

Jalankan dari root repo (setelah scripts/01-07 dijalankan berurutan):
    python design-and-report/src/build_report.py
Pane Design diambil dari src/page_v1.html dan tidak diubah; dicek identik sebelum dan sesudah.
"""
import re
import sys
from html import escape as esc
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "outputs"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts"))
import report_lib as R
from report_lib import D, I, P, audit, cs, gbars, legend, pill, qa, table
from common import ALPHA, CPK_TARGET, COND_LABEL, LSL_G, PRACTICAL_DIFF_G

# ---------- data ----------
rd = lambda f: pd.read_csv(OUT / f)
dq = {r.metrik: r.nilai for r in rd("data_quality.csv").itertuples()}
cl = rd("cleaning_log.csv")
cr = rd("crosscheck.csv")
grp = rd("group_summary.csv")
cap = rd("capability.csv")
tests = rd("test_results.csv")
trend = rd("trend.csv")
sv = rd("source_variation.csv")
rec = rd("recommendation.csv")
sens = rd("sensitivity.csv")
gt = rd("ground_truth_check.csv")
sess = rd("session_summary.csv")

# Setiap CSV hasil harus terdaftar di daftar ini (dipakai di 1.2c)
FILES = {
    "cleaning_log.csv": ("Q12", "Log setiap baris yang dibuang atau diubah"),
    "data_quality.csv": ("Q12", "Ringkasan kualitas data dan NG naif vs bersih"),
    "crosscheck.csv": ("Q14", "Cek silang SQL vs pandas dan ringkasan mesin"),
    "group_summary.csv": ("Q1-Q8", "Ringkasan per kombinasi model x kondisi"),
    "session_summary.csv": ("Q5, Q9", "Ringkasan per sesi uji"),
    "capability.csv": ("Q6, Q8", "Cpk, fail rate, dan estimasi ppm"),
    "test_results.csv": ("Q1-Q5, Q7", "Hasil uji statistik dan koreksi"),
    "trend.csv": ("Q9", "Tren residual sesi per bulan"),
    "source_variation.csv": ("Q10", "Variasi antar bonder dan operator"),
    "recommendation.csv": ("Q11", "Kondisi rekomendasi per model"),
    "sensitivity.csv": ("Q11", "Uji sensitivitas batas praktis dan sesi outlier"),
    "ground_truth_check.csv": ("Q13", "Temuan dibandingkan fakta yang ditanam"),
}
assert set(FILES) == {p.name for p in OUT.glob("*.csv")}, "ada CSV hasil yang belum terdaftar"


def T(pert, uji, perb=None):
    m = tests[(tests.pertanyaan == pert) & (tests.uji == uji)]
    if perb is not None:
        m = m[m.perbandingan == perb]
    assert len(m) == 1, (pert, uji, perb, len(m))
    return m.iloc[0]


def pv(p):
    return "< " + D(0.001, 3) if p < 0.001 else D(p, 3)


def cap_of(m, c):
    return cap[(cap.model == m) & (cap.condition == c)].iloc[0]


def grp_of(m, c):
    return grp[(grp.model == m) & (grp.condition == c)].iloc[0]


def slot(txt, cls=""):
    return f'<div class="qa{(" " + cls) if cls else ""}"><p>{txt}</p></div>'


# Angka dasar
N_FILES, N_RAW, N_CLEAN = I(dq["file mesin dibaca"]), I(dq["baris data mentah"]), I(dq["baris dipakai"])
N_SESI = I(dq["sesi"])
PCT_KOTOR = P(dq["persentase baris kotor"], 1)
N_GAP, N_GNOL, N_GANDA = I(dq["baris gaya kosong"]), I(dq["baris gaya nol"]), I(dq["baris ganda"])
NG_NAIF, NG_BERSIH = I(dq["NG naif (tanpa cleaning)"]), I(dq["NG bersih"])
MEAN_NAIF, MEAN_BERSIH = D(dq["rata-rata gaya naif (g)"], 1), D(dq["rata-rata gaya bersih (g)"], 1)
N_CR = len(cr)
N_PASS = int((cr.hasil == "PASS").sum())
N_COMBO = len(grp)

q1 = T("Q1", "Welch t (unit)", "Setelah oven vs Sebelum oven")
q1s = T("Q1", "Welch t per sesi (sensitivitas)", "Setelah oven vs Sebelum oven")
q1mw = T("Q1", "Mann-Whitney U (sensitivitas)", "Setelah oven vs Sebelum oven")
q1a = T("Q1", "Welch t (unit)", "Setelah oven vs Sebelum oven, Model A")
q1b = T("Q1", "Welch t (unit)", "Setelah oven vs Sebelum oven, Model B")
tk = tests[tests.uji == "Tukey HSD"]
anova2 = T("Q2", "ANOVA satu arah", "tiga kondisi")
q3 = tests[tests.pertanyaan == "Q3"]
q4 = tests[(tests.pertanyaan == "Q4") & (tests.uji == "Welch t (unit)")]
q4mw = tests[(tests.pertanyaan == "Q4") & (tests.uji == "Mann-Whitney U (sensitivitas)")]
q5 = tests[(tests.pertanyaan == "Q5") & (tests.uji == "ANOVA dua arah (unit)")]
q5s = tests[(tests.pertanyaan == "Q5") & (tests.uji == "ANOVA dua arah per sesi (sensitivitas)")]
q5sw = T("Q5", "Shapiro-Wilk residual (asumsi)")
q7 = tests[tests.pertanyaan == "Q7"]
tr_all = trend[trend.kelompok.str.startswith("Seluruh")].iloc[0]
rec_a = rec[rec.model == "Model A"].iloc[0]
rec_b = rec[rec.model == "Model B"].iloc[0]
gt_ok = int((gt.hasil == "Ditemukan").sum())
N_GT = len(gt)
gt3 = gt.iloc[2]

# Interaksi dari GT check (MDE dan selisih) diambil dari tabel 1.3/2.6b; angka mentah untuk teks
mde_txt = gt3.nilai_analisis.split("MDE ±")[1]
mde_val = float(mde_txt.split(" ")[0].strip())
did_obs_txt = gt3.nilai_analisis.split(" g;")[0]
did_obs = float(did_obs_txt)
did_gt_val = float(gt3.nilai_ditanam.split(" g")[0])
okkk = lambda n: I(n)

# ---------- Status verdict kosakata ----------
OKP = lambda t: pill(t)
PRT = lambda t: pill(t, "p")
NOP = lambda t: pill(t, "d")
def verdict(v):
    if v in ("Tidak ditemukan (daya rendah)", "Tidak ditemukan", "Tidak signifikan", "Tidak dibuat", "Belum dikerjakan", "Belum ada", "Tidak terbukti"):
        return NOP(v)
    if v in ("Sebagian", "Berubah", "Simulasi", "Sesuai + penyesuaian", "Sesuai + tambahan", "Diganti pandas", "Belum diuji", "Tidak di-commit", "Signifikan, selisih kecil", "Bersyarat", "Sesuai + penyesuaian (daftar)"):
        return PRT(v)
    return OKP(v)


# ---------- bagian 1 ----------
def sec1():
    kp = (f'<div class="kpis">'
          f'<div class="card"><b>{N_SESI}</b><br>sesi uji (file mesin)</div>'
          f'<div class="card"><b>{N_CLEAN}</b><br>cover glass yang dianalisis</div>'
          f'<div class="card"><b>{I(6)}</b><br>kombinasi model x kondisi</div>'
          f'<div class="card"><b>{PCT_KOTOR}</b><br>baris kotor dibuang</div>'
          f'<div class="card"><b>{NG_BERSIH}</b><br>NG setelah cleaning</div>'
          f'<div class="card"><b>{N_CR}</b><br>pemeriksaan cek silang</div></div>')
    callout = ('<div class="callout c"><b>Data project ini adalah simulasi.</b> Angka menggambarkan data buatan yang meniru '
               'format file mesin push test, bukan lini produksi. Lihat data/ground_truth.md dan docs/definitions.md.</div>')
    rows = [
        ["File mesin dibaca", N_FILES, "file CSV di data/machine_files"],
        ["Baris data mentah", N_RAW, "termasuk baris kotor yang disisipkan"],
        ["Baris gaya kosong", N_GAP, "dibuang"],
        ["Baris gaya nol", N_GNOL, "dibuang"],
        ["Baris ganda", N_GANDA, "dibuang (baris kedua)"],
        ["Baris dipakai", N_CLEAN, "masuk tabel push_results"],
        ["Persentase baris kotor", PCT_KOTOR, "(mentah − dipakai) / mentah"],
        ["Sesi dengan label dari nama file", I(dq["sesi label dari nama file"]), "kolom Condition di ringkasan kosong"],
    ]
    t11 = table(["Metrik", "Nilai", "Catatan"], rows)
    dbrows = [["dim_condition", I(3), "tiga kondisi proses"], ["test_sessions", N_SESI, "satu baris per file mesin"],
              ["push_results", N_CLEAN, "satu baris per cover glass"], ["group_summary", I(N_COMBO), "model x kondisi, dengan Cpk dan fail rate"]]
    t12a = table(["Tabel", "Baris", "Isi"], dbrows)
    cr_ok = f"{I(N_PASS)} dari {I(N_CR)} pemeriksaan lulus"
    t12b = table(["Pemeriksaan", "Hasil"], [["Cek silang SQL vs pandas dan ringkasan mesin (Q14)", cr_ok]])
    t12c = table(["File", "Dipakai untuk", "Isi"], [[f, FILES[f][0], FILES[f][1]] for f in FILES])
    t13 = table(["KPI", "Rumus ringkas", "Hasil", "Jumlah data"], [
        ["Median gaya per kombinasi", "median(force_g)", f"{D(grp.median_g.min(), 1)} s.d. {D(grp.median_g.max(), 1)} g", I(N_CLEAN)],
        ["Simpangan baku", "stddev sampel per kombinasi", f"{D(grp.sd_g.min(), 1)} s.d. {D(grp.sd_g.max(), 1)} g", I(N_CLEAN)],
        ["Cpk satu sisi (LSL 2.000 g)", "(mean − LSL) / (3 × sd)", f"{D(cap.cpk.min(), 2)} s.d. {D(cap.cpk.max(), 2)}", I(N_COMBO)],
        ["Fail rate (NG)", "NG / n", f"{P(cap.fail_rate.min(), 1)} s.d. {P(cap.fail_rate.max(), 1)}", I(N_CLEAN)],
        ["Selisih setelah oven vs sebelum oven", "rata-rata kiri − kanan", f"{D(q1.selisih_g, 0)} g", I(q1.n_kiri + q1.n_kanan)],
    ])
    return (kp + callout +
            "<h4>1.1 Data mentah dan kualitas data</h4>" + t11 +
            "<h4>1.2 Tabel di database dan file hasil</h4>" + t12a + t12b +
            "<p>Daftar file hasil (CSV) di folder outputs/:</p>" + t12c +
            "<h4>1.3 Angka kunci</h4>" + t13)


# ---------- bagian 2 ----------
def sec2():
    g = {}
    for m in ["Model A", "Model B"]:
        g[m] = [grp_of(m, c) for c in ["before_oven", "after_oven", "after_baked"]]
    intro = (f'<div class="callout a"><b>Jawaban singkat.</b> Semua {I(14)} pertanyaan terjawab dengan data. '
             f'{I(5)} jawaban bercatatan (kuning): Q5, Q6, Q8, Q11, dan Q13. Klik nomor pertanyaan untuk melompat.</div>')
    sub_of = {**{n: "sec21" for n in (1, 2, 3)}, **{n: "sec22" for n in (4, 5)}, **{n: "sec23" for n in (6, 7, 8)},
              **{n: "sec24" for n in (9, 10)}, 11: "sec25", **{n: "sec26" for n in (12, 13, 14)}}
    chips = "<div class=\"qchips\">" + "".join(
        f'<a class="qc{" w" if n in (5, 6, 8, 11, 13) else ""}" href="#{sub_of[n]}">Q{I(n)}</a>' for n in range(1, 15)) + "</div>"
    chips_note = '<p class="report-note">Q hijau = terjawab. Q kuning = terjawab dengan catatan.</p>'

    # 2.1 Kondisi proses (Q1-Q3)
    gc = gbars([COND_LABEL[c] for c in ["before_oven", "after_oven", "after_baked"]],
               [("Model A", "#1A73E8", [grp_of("Model A", c).median_g for c in ["before_oven", "after_oven", "after_baked"]]),
                ("Model B", "#E8710A", [grp_of("Model B", c).median_g for c in ["before_oven", "after_oven", "after_baked"]])],
               lambda v: D(v, 0), "Grafik 2.1a median gaya per kondisi dan model")
    t21b = table(["Perbandingan", "Selisih (g)", "CI 95%", "d", "p terkoreksi", "Keputusan"],
                 [[r.perbandingan, D(r.selisih_g, 0), f"{D(r.ci_bawah_g, 0)} s.d. {D(r.ci_atas_g, 0)}", D(r.cohen_d, 2),
                   pv(r.p_terkoreksi), verdict(r.keputusan)] for r in q3.itertuples()] +
                 [[f"{t.perbandingan} (Tukey)", D(t.selisih_g, 0) if not pd.isna(t.selisih_g) else "-", "-", "-", pv(t.p_terkoreksi), verdict(t.keputusan)]
                  for t in tk.itertuples()])
    q1_txt = (f'Ya. Gaya setelah oven rata-rata {D(q1.selisih_g, 0)} g lebih tinggi dibanding sebelum oven '
              f'(CI 95% {D(q1.ci_bawah_g, 0)} s.d. {D(q1.ci_atas_g, 0)} g; p {pv(q1.p_value)}). '
              f'Sensitivitas per sesi tetap signifikan (p {pv(q1s.p_value)}), dan Mann-Whitney juga (p {pv(q1mw.p_value)}).')
    sb =tests[(tests.pertanyaan == "Q2") & (tests.perbandingan == "Setelah oven 1 jam vs Setelah baked")].iloc[0]
    q2_txt = (f'Tidak. ANOVA tiga kondisi signifikan (p {pv(anova2.p_value)}), tetapi setelah oven 1 jam dan setelah baked '
              f'tidak berbeda bermakna: selisih {D(sb.selisih_g, 0)} g, p terkoreksi {pv(sb.p_terkoreksi)}.')
    q3_txt = (f'Sebelum oven ke setelah oven sekitar {D(q1.selisih_g, 0)} g (d {D(q1.cohen_d, 2)}). '
              f'Sebelum oven ke setelah baked sekitar {D(q3.iloc[1].selisih_g, 0)} g. Setelah baked ke setelah oven '
              f'hanya {D(abs(q3.iloc[2].selisih_g), 0)} g dan termasuk selisih kecil. Rentang dibaca dari CI di tabel 2.1b.')

    s21 = (gc + "<p class=\"report-note\">Tabel 2.1b: selisih per pasang kondisi, Holm (Q3) dan Tukey (Q2).</p>" + t21b +
           qa("Q1", "Apakah kekuatan setelah oven berbeda signifikan dibanding sebelum oven?", "Utama · Welch t, Mann-Whitney", q1_txt) +
           qa("Q2", "Apakah ada perbedaan setelah oven 1 jam dan setelah baked?", "Utama · ANOVA, Tukey", q2_txt, warn=False) +
           qa("Q3", "Seberapa besar perbedaan antar kondisi dalam gram?", "Pendukung · Cohen's d, CI", q3_txt))

    # 2.2 Model (Q4-Q5)
    t22a = table(["Kondisi", "Model A (median, g)", "Model B (median, g)", "Selisih A − B (g)", "p terkoreksi Welch", "Keputusan"],
                 [[COND_LABEL[c], D(grp_of("Model A", c).median_g, 0), D(grp_of("Model B", c).median_g, 0),
                   D(r.selisih_g, 0), pv(r.p_terkoreksi), verdict(r.keputusan)]
                  for c, r in zip(["before_oven", "after_oven", "after_baked"], q4.itertuples())])
    q5r = {r.perbandingan: r for r in q5.itertuples()}
    t22b = table(["Faktor", "F", "p", "Keputusan", "Sensitivitas per sesi (p)"],
                 [[k, D(q5r[k].statistik, 2), pv(q5r[k].p_value), verdict(q5r[k].keputusan), pv(q5s[q5s.perbandingan == k].iloc[0].p_value)]
                  for k in ["Model", "Kondisi", "Interaksi model x kondisi"]])
    s_m = q5r["Model"]
    q4_txt = (f'Pada sebelum oven, Model A {D(q4.iloc[0].selisih_g, 0)} g lebih tinggi (p terkoreksi {pv(q4.iloc[0].p_terkoreksi)}). '
              f'Pada setelah baked, selisihnya {D(q4.iloc[2].selisih_g, 0)} g (p terkoreksi {pv(q4.iloc[2].p_terkoreksi)}). '
              f'Keduanya di bawah {I(PRACTICAL_DIFF_G)} g, jadi selisih kecil. Setelah oven 1 jam tidak berbeda '
              f'(p terkoreksi {pv(q4.iloc[1].p_terkoreksi)}).')
    q5_txt = (f'Model {D(s_m.statistik, 2)} dan kondisi signifikan, tetapi interaksi tidak signifikan (F {D(q5r["Interaksi model x kondisi"].statistik, 2)}, '
              f'p {pv(q5r["Interaksi model x kondisi"].p_value)}). Selisih efek oven antar model teramati {I(did_obs)} g, '
              f'sedangkan daya deteksi interaksi hanya sekitar ±{I(mde_val)} g. Interaksi tidak terbukti, dan tidak juga dibantah.')
    s22 = (t22a + "<p class=\"report-note\">Tabel 2.2a: Welch per kondisi, koreksi Holm, dan sensitivitas Mann-Whitney tersedia di test_results.csv.</p>" +
           qa("Q4", "Apakah Model A dan Model B berbeda kekuatannya pada kondisi yang sama?", "Utama · Welch t per kondisi", q4_txt) +
           "<p class=\"report-note\">Tabel 2.2b: ANOVA dua arah pada unit dan pada rata-rata sesi.</p>" + t22b +
           qa("Q5", "Apakah pengaruh oven sama besar untuk kedua model?", "Utama · ANOVA dua arah", q5_txt, warn=True))

    # 2.3 Variasi dan kapabilitas (Q6-Q8)
    gcpk = gbars([f"{m[-1]} · {COND_LABEL[c].lower()}" for m in ["Model A", "Model B"] for c in ["before_oven", "after_oven", "after_baked"]],
                 [("Cpk", "#1A73E8", [cap_of(m, c).cpk for m in ["Model A", "Model B"] for c in ["before_oven", "after_oven", "after_baked"]])],
                 lambda v: D(v, 2), "Grafik 2.3a Cpk per kombinasi")
    t23b = table(["Model", "Kondisi", "n", "Cpk", "CI 95% Cpk", "NG", "Fail rate (CI Wilson)", "Estimasi ppm"],
                 [[r.model, r.condition_label, I(r.n), D(r.cpk, 2), f"{D(r.cpk_lo, 2)} s.d. {D(r.cpk_hi, 2)}", I(r.ng_count),
                   f"{P(r.fail_rate, 1)} ({P(r.fail_rate_lo, 1)} s.d. {P(r.fail_rate_hi, 1)})", D(r.est_ppm, 2)] for r in cap.itertuples()])
    s_out = sens[sens.uji.str.startswith("Kapabilitas Model A, Sebelum")].iloc[0]
    cpk_tanpa = float(re.search(r"(\d+\.\d+) tanpa", s_out_keputusan := s_out.keputusan).group(1))
    q6_txt = (f'Semua kombinasi memenuhi target Cpk {D(CPK_TARGET, 2)}, dengan Cpk terendah pada Model A sebelum oven '
              f'({D(cap_of("Model A", "before_oven").cpk, 2)}). Angka ini ditarik oleh satu sesi S037 yang sangat menyebar; '
              f'tanpa sesi itu Cpk-nya {D(cpk_tanpa, 2)}.')
    q8_txt = (f'Fail rate aktual sangat kecil: {I(dq["NG bersih"])} NG dari {I(N_CLEAN)} cover glass, semuanya pada sesi S037. '
              f'Estimasi ppm dari sebaran normal {D(cap.est_ppm.min(), 3)} s.d. {D(cap.est_ppm.max(), 2)} per 1 juta unit, '
              f'sejalan dengan fail rate aktual (bukti sebagian, karena NG hanya {I(dq["NG bersih"])} kejadian).')
    s23 = (gcpk + t23b + qa("Q6", "Berapa Cpk setiap kombinasi terhadap batas bawah 2.000 g?", "Utama · Cpk satu sisi", q6_txt, warn=True) +
           qa("Q7", "Apakah sebaran gaya berbeda antar kondisi?", "Pendukung · Levene (berpusat median)",
              "Tidak. Levene tidak signifikan untuk Model A (p " + pv(q7.iloc[0].p_value) + ") dan Model B (p " + pv(q7.iloc[1].p_value) + ")." ) +
           qa("Q8", "Berapa fail rate aktual dan estimasi fail rate dari sebaran gaya?", "Utama · proporsi NG dan estimasi ppm", q8_txt, warn=True))

    # 2.4 Waktu dan sumber variasi (Q9-Q10)
    t24a = table(["Kelompok", "Jumlah sesi", "Median residual (g)", "Sesi dengan NG"],
                 [[r.kelompok, I(r.n_sesi), D(r.median_residual_g, 1) if not pd.isna(r.median_residual_g) else "-",
                   I(r.sesi_ng) if not pd.isna(r.sesi_ng) else "-"] for r in trend.itertuples() if not r.kelompok.startswith("Seluruh")])
    q9_txt = (f'Tidak ada tren bermakna. Spearman antara tanggal dan residual sesi {D(tr_all.spearman_rho, 2)} '
              f'(p {pv(tr_all.p_value)}). Residual per bulan berada di sekitar nol (lihat tabel 2.4a).')
    bon = sv[sv.faktor == "bonder"]
    opr = sv[sv.faktor == "operator"]
    t24b = table(["Faktor", "Kelompok", "n", "Median residual (g)", "p Kruskal-Wallis"],
                 [[r.faktor, r.kelompok, I(r.n), D(r.median_residual_g, 1), pv(r.p_value)] for r in sv.itertuples()])
    q10_txt = (f'Tidak ada perbedaan bermakna antar bonder (p {pv(bon.p_value.iloc[0])}) maupun operator (p {pv(opr.p_value.iloc[0])}). '
               f'Residual per kelompok berada dalam rentang yang sama.')
    s24 = (t24a + qa("Q9", "Apakah kekuatan berubah dari sesi ke sesi atau dari bulan ke bulan?", "Pendukung · tren residual", q9_txt) +
           "<p class=\"report-note\">Tabel 2.4b: variasi antar bonder dan operator (residual terhadap rata-rata kombinasi).</p>" + t24b +
           qa("Q10", "Apakah ada perbedaan antar mesin bonder atau operator?", "Tambahan · Kruskal-Wallis", q10_txt))

    # 2.5 Rekomendasi dan dampak (Q11)
    t25a = table(["Model", "Kondisi lama", "Kondisi rekomendasi", "Median lama (g)", "Median rekomendasi (g)", "Selisih (g)", "Praktis", "Penurunan est. ppm"],
                 [[r.model, r.kondisi_lama, r.kondisi_rekomendasi, D(r.median_lama_g, 0), D(r.median_rekomendasi_g, 0),
                   D(r.selisih_median_g, 0), OKP("Ya") if r.praktis == "Ya" else NOP("Tidak"), D(r.penurunan_est_ppm, 3)]
                  for r in rec.itertuples()])
    q11_txt = (f'Setelah oven 1 jam untuk kedua model. Median naik {D(rec_a.selisih_median_g, 0)} g pada Model A dan '
               f'{D(rec_b.selisih_median_g, 0)} g pada Model B, di atas batas praktis {I(PRACTICAL_DIFF_G)} g. '
               f'Penurunan fail rate estimasinya hanya sekitar {D(rec_a.penurunan_est_ppm, 2)} ppm (Model A) dan {D(rec_b.penurunan_est_ppm, 3)} ppm (Model B), '
               f'karena proses sebelum oven sudah cukup mampu. Dampak ini bergantung pada asumsi sebaran normal dan satu sesi outlier.')
    s25 = t25a + qa("Q11", "Kondisi proses mana yang direkomendasikan, dan berapa estimasi penurunan fail rate?",
                    "Utama · penurunan = fail rate lama − baru", q11_txt, warn=True)

    # 2.6 Validitas (Q12-Q14)
    t26a = table(["Pemeriksaan", "Hasil"], [["Cek silang SQL vs pandas dan ringkasan mesin", f"{I(N_PASS)} dari {I(N_CR)} PASS"],
                                              ["Baris kotor dibuang", f"{I(dq['baris gaya kosong'] + dq['baris gaya nol'] + dq['baris ganda'])} dari {N_RAW} ({PCT_KOTOR})"],
                                              ["NG naif vs NG bersih", f"{NG_NAIF} vs {NG_BERSIH}"],
                                              ["Rata-rata gaya naif vs bersih (g)", f"{MEAN_NAIF} vs {MEAN_BERSIH}"]])
    t26b = table(["Fakta yang ditanam", "Nilai ditanam", "Nilai hasil analisis", "Kriteria", "Hasil"],
                 [[r.fakta, cs(r.nilai_ditanam), cs(r.nilai_analisis), r.kriteria, verdict(r.hasil)] for r in gt.itertuples()])
    q12_txt = (f'{I(dq["baris ganda"] + dq["baris gaya nol"] + dq["baris gaya kosong"])} baris tidak valid dari {N_RAW}: '
               f'{N_GANDA} ganda, {N_GNOL} gaya nol, dan {N_GAP} gaya kosong. Tanpa pembersihan, NG naif {NG_NAIF} dan rata-rata {MEAN_NAIF} g; '
               f'setelah pembersihan NG {NG_BERSIH} dan rata-rata {MEAN_BERSIH} g. Hasil berubah, sehingga pembersihan diperlukan.')
    q13_txt = (f'{I(gt_ok)} dari {I(N_GT)} fakta terdeteksi. Fakta 3 (interaksi) tidak terdeteksi karena daya uji rendah; '
               f'lihat 7.6. Efek oven, perbedaan model, sesi outlier, dan data kotor dipulihkan.')
    q14_txt = f"Ya. {I(N_PASS)} dari {I(N_CR)} pemeriksaan cek silang lulus, termasuk per kombinasi dan per sesi (scripts/04_crosscheck.py)."
    s26 = (t26a + qa("Q12", "Berapa data yang tidak valid, dan apakah hasil berubah setelah diperbaiki?", "Utama · audit kualitas data", q12_txt) +
           "<p class=\"report-note\">Tabel 2.6a: hasil cek silang dan efek pembersihan.</p>" +
           qa("Q13", "Apakah analisis menemukan semua fakta yang sengaja ditanam?", "Utama · cocokkan dengan ground truth", q13_txt, warn=True) +
           "<p class=\"report-note\">Tabel 2.6b: validasi ground truth (hanya skrip validasi yang membaca parameter simulasi).</p>" + t26b +
           qa("Q14", "Apakah angka dari SQL sama dengan hitungan pandas?", "Pendukung · cek silang SQL vs Python", q14_txt))

    body = (intro + chips + chips_note +
            '<h3 id="sec21">2.1 Kondisi proses</h3>' + s21 +
            '<h3 id="sec22">2.2 Model produk</h3>' + s22 +
            '<h3 id="sec23">2.3 Variasi dan kapabilitas</h3>' + s23 +
            '<h3 id="sec24">2.4 Waktu dan sumber variasi</h3>' + s24 +
            '<h3 id="sec25">2.5 Rekomendasi dan dampak</h3>' + s25 +
            '<h3 id="sec26">2.6 Validitas</h3>' + s26)
    return body


def sec3():
    rows = [
        ["Sumber data", "Data simulasi yang meniru format file mesin push test", "Simulasi meniru format file mesin, dibuat di scripts/01", verdict("Sesuai")],
        ["Ukuran", "±60 sesi, ±10 cover glass per sesi, ±600 hasil", f"{N_SESI} sesi, {N_CLEAN} cover glass setelah cleaning", verdict("Sesuai")],
        ["Tabel", "test_sessions, push_results, dim_condition, group_summary", "4 tabel di DuckDB dan 2 view SQL (v_push, v_group_summary)", verdict("Sesuai")],
        ["Pengaturan uji", "Mode DS20KG, destructive, kecepatan 0,3 mm/s", "Sama di setiap file", verdict("Sesuai")],
        ["Batas spesifikasi", "Batas bawah 2.000 g; batas atas 20.000 g", "Sama di setiap file; NG dihitung dari batas bawah", verdict("Sesuai")],
    ]
    for r in gt.itertuples():
        rows.append([f"Fakta ditanam: {r.fakta}", cs(r.nilai_ditanam), cs(r.nilai_analisis), verdict(r.hasil)])
    t = table(["Aspek", "Rancangan", "Realisasi", "Verdict"], rows)
    txt = ("<p>Data simulasi sesuai rancangan. Verdict baris fakta mengikuti tabel 2.6b. Empat dari lima fakta terdeteksi; "
           "fakta interaksi tidak, dan itu dicatat di 7.6.</p>")
    return txt + t


def sec4():
    rows = [
        ["Python (pandas, SciPy, statsmodels)", "Membuat data, parsing, uji t, ANOVA, Tukey, Levene, Cpk", "scripts/01 s.d. 07", verdict("Sesuai")],
        ["DuckDB + SQL", "Database dan view ringkasan", "pushtest.duckdb (tidak di-commit), sql/01 dan sql/02", verdict("Sesuai")],
        ["Jupyter Notebook", "Langkah analisis Q1–Q14 dengan grafik", "notebooks/analysis.ipynb (dibangun dan dieksekusi)", verdict("Sesuai")],
        ["Streamlit", "Dashboard 4 halaman, dipublikasikan", "dashboard/app.py; belum dipublikasikan", verdict("Sebagian")],
        ["GitHub", "Kode, contoh file, README", "Branch project-12-build; belum digabung ke main", verdict("Sebagian")],
        ["Markdown", "README", "README.md dan docs/", verdict("Sesuai")],
    ]
    return ("<p>Notebook dan dashboard sudah dibuat. Dashboard belum dipublikasikan.</p>"
            + table(["Tool", "Rancangan", "Realisasi", "Verdict"], rows))


def sec5():
    steps = [
        ("1", "Aturan uji dan KPI", "docs/analysis_plan.md, docs/definitions.md", "Sesuai + penyesuaian"),
        ("2", "Struktur tabel dan kamus data", "docs/data_dictionary.md", "Sesuai"),
        ("3", "Buat file CSV simulasi dan ground truth", "scripts/01_generate_machine_files.py, data/ground_truth.md", "Sesuai"),
        ("4", "Parsing dan cleaning", "scripts/02_parse_load.py, outputs/cleaning_log.csv", "Sesuai"),
        ("5", "Muat ke DuckDB", "scripts/02_parse_load.py (pushtest.duckdb)", "Sesuai"),
        ("6", "Statistik deskriptif dengan view SQL", "sql/01_group_views.sql, sql/02_session_views.sql, scripts/03_sql_views.py", "Sesuai"),
        ("7", "Cek silang SQL dan Python (Q14)", "scripts/04_crosscheck.py", "Sesuai"),
        ("8", "Uji statistik Q1–Q5 dan Q7", "scripts/05_stats.py", "Sesuai + tambahan"),
        ("9", "Cpk, fail rate, dan sumber variasi (Q6, Q8–Q10)", "scripts/06_capability.py", "Sesuai + tambahan"),
        ("10", "Rekomendasi dan validasi ground truth (Q11, Q13)", "scripts/07_recommend_validate.py", "Sesuai + penyesuaian"),
        ("11", "Dashboard dan one-sheet", "dashboard/app.py, scripts/08_one_sheet.py", "Sesuai"),
        ("12", "README dan finalisasi repositori", "README.md; branch belum digabung", "Sebagian"),
    ]
    t = table(["No", "Langkah rancangan", "Realisasi (file)", "Verdict"],
              [[a, b, c, verdict(d)] for a, b, c, d in steps])
    card = ('<div class="card"><h4>Penyesuaian dan improvisasi yang tidak ada di rancangan</h4><ul>'
            '<li>Penomoran skrip 01–07 mengikuti urutan data (aturan portofolio). Tabel di bawah memetakan nama rancangan ke nama file.</li>'
            '<li>Ditambahkan sensitivitas per sesi, Mann-Whitney, dan koreksi Holm untuk Q3 dan Q4.</li>'
            f'<li>Ditambahkan uji sensitivitas batas praktis ({I(250)}, {I(500)}, {I(1000)} g) dan analisis tanpa sesi S037.</li>'
            '<li>Ditambahkan perhitungan daya deteksi interaksi (MDE) setelah data dibuat. Ini tidak direncanakan.</li>'
            '<li>Batas praktis 500 g dan target Cpk 1,33 adalah asumsi (lihat docs/definitions.md).</li>'
            '</ul></div>')
    mapping = [
        ("scripts/generate_machine_files.py", "scripts/01_generate_machine_files.py"),
        ("scripts/parse_load.py", "scripts/02_parse_load.py"),
        ("sql/", "sql/01_group_views.sql, sql/02_session_views.sql, scripts/03_sql_views.py"),
        ("(tidak ada di rancangan)", "scripts/04_crosscheck.py, 05_stats.py, 06_capability.py, 07_recommend_validate.py"),
        ("index.html (rancangan)", "design-and-report/src/page_v1.html (pane Design tidak diubah); design-and-report/index.html dibangun ulang; index.html root = pengalihan"),
        ("notebooks/analysis.ipynb", "scripts/09_build_notebook.py"),
        ("dashboard/app.py", "dashboard/app.py (Streamlit, 4 halaman)"),
        ("outputs/one_sheet.pdf / .png", "scripts/08_one_sheet.py"),
        ("(tidak ada di rancangan)", "design-and-report/src/build_report.py, report_lib.py, report.css"),
    ]
    mt = table(["Rancangan", "Realisasi"], [[a, b] for a, b in mapping])
    return ("<p>Sebelas dari dua belas langkah dikerjakan. Dashboard sudah dibuat, belum dipublikasikan.</p>" + t + card +
            "<h4>Perubahan nama dan lokasi file terhadap rancangan</h4>" + mt)


def exists_status(path):
    p = ROOT / path
    if path.endswith("*.csv"):
        return "Ada" if any((ROOT / "data/machine_files").glob("*.csv")) else "Belum ada"
    if path == "pushtest.duckdb":
        return "Tidak di-commit" if p.exists() else "Belum ada"
    return "Ada" if p.exists() else "Belum ada"


def sec6():
    outs = [
        ("Dashboard interaktif", "Utama", "Sebagian", "dashboard/app.py; belum dipublikasikan"),
        ("One-sheet infografik", "Utama", "Tercapai", "outputs/one_sheet.png dan .pdf"),
        ("Database dan query SQL", "Utama", "Tercapai", "pushtest.duckdb (tidak di-commit), sql/*.sql"),
        ("Generator dan parser file mesin", "Utama", "Tercapai", "scripts/01_generate_machine_files.py, 02_parse_load.py"),
        ("Notebook analisis", "Utama", "Tercapai", "notebooks/analysis.ipynb"),
        ("Laporan temuan dan rekomendasi", "Utama", "Tercapai", "README.md dan halaman Report ini"),
        ("Repositori GitHub", "Utama", "Sebagian", "Branch project-12-build; belum digabung ke main"),
        ("Slide presentasi", "Opsional", "Tidak dibuat", "Belum dibuat"),
    ]
    t = table(["Output", "Label", "Status", "Bukti"], [[a, b, verdict_out(c), d] for a, b, c, d in outs])
    docs = [("index.html (rancangan)", "A", "Utama", "design-and-report/index.html"),
            ("docs/analysis_plan.md", "A", "Utama", "docs/analysis_plan.md"),
            ("docs/data_dictionary.md", "A", "Utama", "docs/data_dictionary.md"),
            ("scripts/01_generate_machine_files.py", "B", "Utama", "scripts/01_generate_machine_files.py"),
            ("data/ground_truth.md", "B", "Utama", "data/ground_truth.md"),
            ("data/machine_files/*.csv", "B", "Utama", "data/machine_files/*.csv"),
            ("scripts/parse_load.py", "B", "Utama", "scripts/02_parse_load.py"),
            ("outputs/cleaning_log.csv", "B", "Utama", "outputs/cleaning_log.csv"),
            ("pushtest.duckdb", "B", "Utama", "pushtest.duckdb"),
            ("requirements.txt", "B", "Utama", "requirements.txt"),
            ("sql/", "C", "Utama", "sql/"),
            ("notebooks/analysis.ipynb", "C", "Utama", "notebooks/analysis.ipynb"),
            ("outputs/test_results.csv", "C", "Utama", "outputs/test_results.csv"),
            ("dashboard/app.py", "D", "Utama", "dashboard/app.py"),
            ("outputs/one_sheet.pdf / .png", "D", "Utama", "outputs/one_sheet.pdf"),
            ("README.md", "D", "Utama", "README.md"),
            ("slides/", "D", "Opsional", "slides/")]
    drows = []
    for name, tahap, label, path in docs:
        st = exists_status(path)
        drows.append([name, tahap, label, verdict_doc(st)])
    dt = table(["Dokumen", "Tahap", "Label", "Status"], drows)
    return (t + "<h4>Daftar dokumen yang akan dihasilkan</h4>" + dt)


def verdict_out(s):
    return {"Tercapai": OKP("Tercapai"), "Sebagian": PRT("Sebagian"), "Tidak dibuat": NOP("Tidak dibuat")}[s]


def verdict_doc(s):
    return {"Ada": OKP("Ada"), "Belum ada": NOP("Belum ada"), "Tidak di-commit": PRT("Tidak di-commit")}[s]


def sec7():
    n_ok_crit = 2
    crit = [
        ["Sembilan pertanyaan Utama terjawab dengan angka dari data", "Q1, Q2, Q4, Q5, Q6, Q8, Q11, Q12, Q13 terjawab; Q5, Q6, Q8, Q11, Q13 bercatatan", "Tercapai"],
        ["Parser membaca semua file tanpa kesalahan dan hitung ulang cocok", f"{N_FILES} file dibaca; {I(N_PASS)} dari {I(N_CR)} pemeriksaan PASS", "Tercapai"],
        ["Kelima fakta yang ditanam ditemukan oleh analisis", f"{I(gt_ok)} dari {I(N_GT)} ditemukan; fakta interaksi tidak", "Sebagian"],
        ["Orang awam membuka dashboard dan menyebut kondisi terbaik dalam kurang dari 1 menit", "Dashboard sudah dibuat, belum diuji pembaca awam", "Belum diuji"],
        ["Checklist standar terpenuhi (dashboard deploy, README berisi insight dan rekomendasi)", "README dan Report ada; dashboard ada, belum dipublikasikan", "Sebagian"],
    ]
    ct = table(["Kriteria", "Bukti", "Status"], [[a, b, verdict_out(c) if c in ("Tercapai", "Sebagian") else PRT(c)] for a, b, c in crit])
    hasil = f'<p><b>Hasil: {I(n_ok_crit)} dari {I(len(crit))} kriteria tercapai penuh.</b></p>'
    s71 = (f'<p>Efek oven terbukti: gaya setelah oven 1 jam rata-rata {D(q1.selisih_g, 0)} g lebih tinggi dibanding sebelum oven, '
           f'dan selisih ini di atas batas praktis {I(PRACTICAL_DIFF_G)} g. Setelah baked tidak berbeda dengan setelah oven 1 jam. '
           f'Model B sedikit lebih lemah daripada Model A, tetapi selisihnya di bawah batas praktis. Interaksi model dan oven tidak terbukti.</p>')
    s72 = (f'<p>Estimasi (label estimated): penurunan fail rate estimasi {D(rec_a.penurunan_est_ppm, 2)} ppm untuk Model A dan '
           f'{D(rec_b.penurunan_est_ppm, 3)} ppm untuk Model B per 1 juta unit. Angka ini kecil karena kedua model sudah memenuhi Cpk {D(CPK_TARGET, 2)} sebelum oven. '
           f'Nilai praktis utamanya adalah margin median {D(rec_a.selisih_median_g, 0)} g dan {D(rec_b.selisih_median_g, 0)} g.</p>')
    s74 = (f'<p>Gunakan setelah oven 1 jam untuk kedua model sebagai kondisi proses default, dengan verifikasi pada data lini nyata. '
           f'Selidiki sesi S037 dan lot glue-nya sebelum menyimpulkan tentang variasi sebelum oven.</p>')
    s75 = ('<ul><li>Hitung daya setiap fakta sebelum membuat data simulasi, agar efek kecil tidak diuji tanpa daya.</li>'
           '<li>Tambahkan jumlah sesi per kombinasi, karena uji per unit dengan sesi terbatas mudah terlalu percaya diri.</li>'
           '<li>Catat lot glue per sesi agar pola yang terlihat bisa dipisahkan dari hari atau lot.</li>'
           '<li>Publikasikan dashboard, lalu minta pembaca awam menguji dashboard.</li></ul>')
    s76 = ('<ul>'
           '<li><b>Data adalah simulasi.</b> Angka menggambarkan data buatan, bukan lini produksi.</li>'
           f'<li>Fakta interaksi tidak terdeteksi. Daya deteksi hanya ±{I(mde_val)} g, sedangkan selisih yang ditanam {I(did_gt_val)} g. '
           'Ini kesalahan perancangan, karena daya tidak dihitung sebelum data dibuat.</li>'
           f'<li>Sesi {GT_OUT} sangat menyebar dan menentukan semua NG. Kapabilitas Model A sebelum oven sensitif terhadap sesi ini (lihat tabel sensitivitas).</li>'
           '<li>Unit bersarang dalam sesi. Uji per unit bisa terlalu percaya diri, sehingga uji per sesi dilaporkan sebagai pembanding.</li>'
           '<li>Residual tidak normal (Shapiro-Wilk). Welch dan Mann-Whitney dilaporkan bersama.</li>'
           f'<li>Asumsi: batas praktis {I(PRACTICAL_DIFF_G)} g, target Cpk {D(CPK_TARGET, 2)}, estimasi ppm dengan sebaran normal, koreksi Holm. Semuanya diuji sensitivitasnya.</li>'
           f'<li>NG hanya {I(dq["NG bersih"])} kejadian, sehingga fail rate dan ppm tidak stabil.</li>'
           '<li>Dashboard belum dipublikasikan. Repositori belum digabung ke main.</li>'
           '<li>Pola yang terlihat belum tentu penyebab. Sesi yang berbeda bisa berbeda lot glue atau hari.</li>'
           '</ul>')
    return ("<h4>7.1 Hasil analisis</h4>" + s71 +
            "<h4>7.2 Impact</h4>" + s72 +
            "<h4>7.3 Success criteria</h4>" + ct + hasil +
            "<h4>7.4 Rekomendasi</h4>" + s74 +
            "<h4>7.5 Saran perbaikan</h4>" + s75 +
            "<h4>7.6 Batasan</h4>" + s76)


GT_OUT = "S037"


# ---------- perakitan halaman ----------
STATIC = {f"{a}.{b}" for a in range(1, 8) for b in range(1, 13)} | {
    "01", "02", "03", "04", "05", "06", "07", "95", "2026", "2.000", "20.000", "0,3", "1,33", "1.000", "2–3", "3", "2", "4", "5", "6", "7", "8", "9", "10",
    "11", "12", "14", "15", "60", "600", "100", "0,05", "80", "1,96", "0,84", "0", "1", "2–3%"}


def evq():
    rows = [
        ["1", "Apakah data yang didapat sesuai rancangan dan bersih?", verdict("Simulasi"),
         f'{N_CLEAN} cover glass dari {N_RAW} baris mentah; {PCT_KOTOR} kotor dibersihkan. <a href="#rp1">Lihat bagian 1</a>.'],
        ["2", "Apakah business question terjawab?", verdict("Sesuai"),
         f'{I(14)} dari {I(14)} pertanyaan terjawab, {I(5)} bercatatan. <a href="#rp2">Lihat bagian 2</a>.'],
        ["3", "Apakah dataset sesuai Design Project?", verdict("Sesuai"),
         f'Simulasi meniru format mesin dengan {N_SESI} sesi. <a href="#rp3">Lihat bagian 3</a>.'],
        ["4", "Apakah tools yang digunakan sesuai?", verdict("Sesuai"),
         'DuckDB, SQL, pandas, SciPy, statsmodels dipakai. Notebook dan dashboard belum. <a href="#rp4">Lihat bagian 4</a>.'],
        ["5", "Apakah alur pengerjaan sesuai Design Project?", verdict("Sesuai + penyesuaian"),
         '11 dari 12 langkah dikerjakan; penomoran dan nama file berbeda. <a href="#rp5">Lihat bagian 5</a>.'],
        ["6", "Apakah project output tercapai?", verdict("Sebagian"),
         "Database, generator, notebook, dashboard, one-sheet, dan laporan jadi; dashboard belum dipublikasikan. <a href=\"#rp6\">Lihat bagian 6</a>."],
        ["7", "Apakah hasil menjawab pertanyaan utama?", verdict("Sebagian"),
         'Efek oven terbukti dan kondisi terbaik ditemukan; interaksi model tidak terdeteksi. <a href="#rp7">Lihat bagian 7</a>.'],
    ]
    return ('<div class="callout a"><b>Report Project versi 2: evaluasi hasil terhadap Design Project.</b> '
            f'{I(14)} pertanyaan dijawab dengan {I(N_CR)} cek silang dan {I(len(FILES))} file hasil. '
            '<b>Data pada project ini adalah simulasi.</b></div>' +
            '<div class="scroll"><table class="evq"><tr><th>No</th><th>Pertanyaan evaluasi</th><th>Verdict</th><th>Ringkasan</th></tr>' +
            "".join(f"<tr><td><span class=\"en\">{a}</span></td><td>{esc(b)}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in rows) +
            "</table></div>")


def h2(i, title, sub):
    return f'<h2 id="rp{i}">{i}. {esc(title)}<small>{sub}</small></h2>'


def build_report_pane():
    head = ('<div class="pane" id="report" data-tab="report" hidden>\n')
    parts = [
        head,
        evq(),
        h2(1, "Data yang berhasil didapatkan", "Isi data mentah, tabel di database, dan data hasil analisis"), sec1(),
        h2(2, "Apakah business question terjawab?", f"{I(14)} pertanyaan pada Design Project, dijawab dengan data"), sec2(),
        h2(3, "Apakah dataset sesuai dengan Design Project?", "Perbandingan rancangan dengan realisasi"), sec3(),
        h2(4, "Apakah tools yang digunakan sesuai?", "Perbandingan rancangan dengan eksekusi"), sec4(),
        h2(5, "Apakah alur pengerjaan sesuai dengan Design Project?", f"{I(12)} langkah rancangan vs yang dijalankan"), sec5(),
        h2(6, "Apakah project output tercapai?", "Output pada Design Project, bagian 7"), sec6(),
        h2(7, "Kesimpulan", "Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan"), sec7(),
        "\n</div>\n",
    ]
    return "".join(parts)


NAV_REPORT = ('<div class="links" data-tab="report" hidden>'
              '<a href="#rp1">Data</a><a href="#rp2">Business Questions</a><a href="#rp3">Dataset</a>'
              '<a href="#rp4">Tools</a><a href="#rp5">Alur Kerja</a><a href="#rp6">Project Output</a>'
              '<a href="#rp7">Kesimpulan</a></div>')


def main():
    src = (HERE / "page_v1.html").read_text(encoding="utf-8")
    m = re.search(r'<div class="pane" id="design"', src)
    r = src.index('<div class="pane" id="report"')
    d0 = m.start()
    design_block = src[d0:r]
    body_pane = build_report_pane()
    # 1. Nav: ganti link Report saja
    nav_old = re.search(r'<div class="links" data-tab="report" hidden>.*?</div>', src, re.S).group(0)
    html = src[:r] + body_pane + src[src.index("</main>"):]
    html = html.replace(nav_old, NAV_REPORT, 1)
    # 2. CSS tambahan sebelum </style>
    css = (HERE / "report.css").read_text(encoding="utf-8")
    assert html.count("</style>") == 1
    html = html.replace("</style>", css + "\n</style>", 1)
    # 3. Pane Design tidak boleh berubah
    assert html[html.index('<div class="pane" id="design"'):].startswith(design_block[:200])
    assert design_block in html, "pane Design berubah"
    out = ROOT / "design-and-report" / "index.html"
    out.write_text(html, encoding="utf-8")
    # 4. Audit angka: setiap token numerik di Report harus berasal dari data atau daftar STATIC
    n_tok, bad = audit(body_pane, STATIC)
    print(f"audit: {n_tok} token diperiksa, tidak terdaftar: {bad}")
    print("ditulis:", out)


if __name__ == "__main__":
    main()
