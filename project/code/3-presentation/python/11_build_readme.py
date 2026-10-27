# Tahap 3: menulis README.md (root repo) dari CSV hasil. Angka tidak diketik manual.
import sys, re, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import pandas as pd
from common import RES_PREP, RES_ANA, ROOT, LSL_G, PRACTICAL_DIFF_G, CPK_TARGET

dq = pd.read_csv(RES_PREP / "data_quality.csv").set_index("metrik")["nilai"]
t = pd.read_csv(RES_ANA / "test_results.csv")
cap = pd.read_csv(RES_ANA / "capability.csv")
rec = pd.read_csv(RES_ANA / "recommendation.csv").set_index("model")
sens = pd.read_csv(RES_ANA / "sensitivity.csv")
gt = pd.read_csv(RES_ANA / "ground_truth_check.csv")
cc = pd.read_csv(RES_ANA / "crosscheck.csv")

def f(x, d=0):
    return f"{float(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def pv(p):
    p = float(p)
    return "< 0,001" if p < 0.001 else f(p, 2)

def row(q, uji, comp):
    r = t[(t.pertanyaan == q) & (t.uji == uji) & (t.perbandingan == comp)]
    assert len(r) == 1, (q, uji, comp)
    return r.iloc[0]

q1 = row("Q1", "Welch t (unit)", "Setelah oven vs Sebelum oven")
tk = row("Q2", "Tukey HSD", "Setelah oven 1 jam vs Setelah baked")
a_bef = row("Q4", "Welch t (unit)", "Model A vs Model B, Sebelum oven")
a_bak = row("Q4", "Welch t (unit)", "Model A vs Model B, Setelah baked")
a_oven = row("Q4", "Welch t (unit)", "Model A vs Model B, Setelah oven 1 jam")
inter = row("Q5", "ANOVA dua arah (unit)", "Interaksi model x kondisi")
g3 = gt[gt.fakta.str.startswith("3.")].iloc[0]
planted = re.search(r"([\d.]+) g", g3.nilai_ditanam).group(1)
mde = re.search(r"MDE ±([\d.]+) g", g3.nilai_analisis).group(1)
capA = cap[(cap.model == "Model A") & (cap.condition == "before_oven")].iloc[0]
note = sens[sens.uji == "Kapabilitas Model A, Sebelum oven"].keputusan.iloc[0]
cpk_wo = re.findall(r"[\d.]+", note)[1]
assert cap.memenuhi_target.eq("Memenuhi").all()
n_pass, n_cc = int((cc.hasil == "PASS").sum()), len(cc)
sd_ = re.search(r"S\d+", gt[gt.fakta.str.startswith("4.")].iloc[0].nilai_ditanam).group(0)
n_files, n_raw, n_used = int(dq["file mesin dibaca"]), int(dq["baris data mentah"]), int(dq["baris dipakai"])
n_dirty = n_raw - n_used
pct = float(dq["persentase baris kotor"]) * 100

text = f"""[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 12: Process Comparison Analysis

**Status: Selesai.** Halaman project (Design dan Report) ada di [`design-and-report/index.html`](design-and-report/index.html). Dashboard ada di `project/code/3-presentation/streamlit/app.py` (belum dipublikasikan). Notebook di `project/results/3-presentation/analysis.ipynb`, one-sheet di `project/results/3-presentation/one_sheet.pdf`.

**Tujuan:** membandingkan kekuatan glue pada perekatan camera cover glass smartphone antar kondisi proses (sebelum oven, setelah oven 1 jam, setelah baked) dan antar model (Model A dan Model B), untuk memilih kondisi proses terbaik berdasarkan bukti.

| | |
|---|---|
| Kategori | Manufaktur smartphone |
| Tingkat | Mudah |
| Data | **Data simulasi** yang meniru format file mesin push test |
| Tools | DuckDB + SQL, Python (pandas, SciPy, statsmodels), Streamlit, Jupyter |

## 1. Problem

**Pertanyaan utama:** Apakah kekuatan glue berbeda signifikan antar kondisi proses dan antar model, dan kondisi mana yang memberi risiko NG paling kecil?

Rancangan memecahnya menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan). Daftar lengkap ada di bagian 2 halaman rancangan.

## 2. Data

- **Data simulasi.** Angka menggambarkan data buatan, bukan lini produksi. Parameter ground truth ada di `project/code/common.py` dan `project/docs/ground_truth.md`.
- {n_files} file CSV berformat mesin (`project/data/raw/machine_files/`, tidak di-commit; dibuat ulang oleh skrip 01, contoh kecil di `project/data/sample/`): 6 kombinasi model x kondisi, 10 sesi per kombinasi, 10 cover glass per sesi, dibuat Juli sampai September 2026.
- {f(n_raw)} baris data mentah, di antaranya {f(n_dirty)} baris kotor ({f(pct, 1)}%): baris ganda, gaya nol, dan gaya kosong. {f(n_used)} baris dipakai setelah cleaning.
- Tabel di DuckDB: `test_sessions`, `push_results`, `dim_condition`, dan `group_summary`. Kamus data di `project/docs/data_dictionary.md`.

## 3. Analysis

- **Efek oven terbukti.** Gaya setelah oven 1 jam rata-rata {f(q1.selisih_g)} g lebih tinggi dibanding sebelum oven (CI 95% {f(q1.ci_bawah_g)} s.d. {f(q1.ci_atas_g)} g, p {pv(q1.p_terkoreksi)}).
- **Setelah baked tidak berbeda dengan setelah oven 1 jam** (selisih {f(abs(tk.selisih_g))} g, p terkoreksi {pv(tk.p_terkoreksi)}).
- **Model A dan Model B berbeda kecil.** Sebelum oven, Model A lebih tinggi {f(a_bef.selisih_g)} g; setelah baked {f(a_bak.selisih_g)} g. Keduanya di bawah batas praktis {f(PRACTICAL_DIFF_G)} g. Setelah oven 1 jam tidak berbeda.
- **Interaksi model x oven tidak terdeteksi** (p {pv(inter.p_terkoreksi)}). Daya deteksi hanya ±{mde} g, sedangkan selisih yang ditanam {planted} g. Ini kesalahan perancangan (lihat Batasan).
- **Kapabilitas memenuhi target Cpk {f(CPK_TARGET, 2)}** pada semua kombinasi. Cpk Model A sebelum oven ({f(capA.cpk, 2)}) ditarik oleh satu sesi {sd_} yang sangat menyebar; tanpa sesi itu {f(cpk_wo, 2)}.
- **Tidak ada tren antar sesi** dan tidak ada perbedaan antar bonder atau operator.
- Cek silang SQL vs pandas dan ringkasan mesin: {n_pass} dari {n_cc} PASS.

## 4. Recommendation

Gunakan **setelah oven 1 jam** sebagai kondisi proses untuk kedua model. Verifikasi dengan data lini nyata sebelum diterapkan, dan selidiki lot glue pada sesi {sd_}.

## 5. Impact

Penurunan fail rate estimasi (estimated, asumsi sebaran normal): sekitar {f(rec.loc['Model A', 'penurunan_est_ppm'], 1)} ppm untuk Model A dan {f(rec.loc['Model B', 'penurunan_est_ppm'], 2)} ppm untuk Model B per 1 juta unit. Angka ini kecil karena kedua model sudah memenuhi target Cpk sebelum oven. Nilai utamanya adalah margin median: +{f(rec.loc['Model A', 'selisih_median_g'])} g (Model A) dan +{f(rec.loc['Model B', 'selisih_median_g'])} g (Model B).

## Batasan

- **Data adalah simulasi.** Hasil menunjukkan bahwa metode bekerja, bukan kondisi lini produksi.
- **Interaksi tidak terdeteksi.** Daya tidak dihitung sebelum data dibuat (kesalahan perancangan). Dicatat jujur, tidak diperbaiki dengan mengubah parameter setelah melihat hasil.
- Satu sesi ({sd_}) menentukan semua NG dan sangat memengaruhi Cpk Model A sebelum oven.
- Unit bersarang dalam sesi; uji per sesi dilaporkan sebagai pembanding. Residual tidak normal, sehingga Mann-Whitney juga dilaporkan.
- Asumsi (label di `project/docs/definitions.md`): batas praktis {f(PRACTICAL_DIFF_G)} g, target Cpk {f(CPK_TARGET, 2)}, estimasi ppm dengan sebaran normal, koreksi Bonferroni.
- Dashboard belum dipublikasikan.

## Menjalankan

Dari root repo (sekali jalan dari nol):

```bash
pip install -r project/requirements.txt
sh project/code/run_all.sh
# dashboard: cd project && streamlit run code/3-presentation/streamlit/app.py
```

`run_all.sh` menjalankan skrip berurutan menurut nomor: 01 generate, 02 parse dan load, 03 SQL views, 04 cek silang, 05 uji, 06 kapabilitas, 07 rekomendasi dan validasi, 08 one-sheet, 09 build notebook (dieksekusi dengan nbconvert), 10 bersihkan notebook, 11 README, lalu `design-and-report/src/build_report.py`.

## Struktur repository

```
index.html                    pengalihan ke design-and-report/
README.md                     dokumen ini (dibuat oleh 11_build_readme.py)
design-and-report/
  index.html                  halaman project (Design + Report)
  src/                        page_v1.html (pane Design), report.css, report_lib.py, build_report.py
project/
  code/
    common.py                 path dan parameter (blok GT hanya dibaca 01 dan 07)
    run_all.sh
    1-data-preparation/python/   01_generate_machine_files.py, 02_parse_load.py
    2-analysis/python/           03_sql_views.py, 04_crosscheck.py, 05_stats.py, 06_capability.py, 07_recommend_validate.py
    2-analysis/sql/              01_group_views.sql, 02_session_views.sql
    3-presentation/python/       08_one_sheet.py, 09_build_notebook.py, 10_finalize_notebook.py, 11_build_readme.py
    3-presentation/streamlit/    app.py (dashboard 4 halaman)
  results/
    1-data-preparation/       cleaning_log.csv, data_quality.csv
    2-analysis/               CSV hasil analisis
    3-presentation/           analysis.ipynb, one_sheet.pdf, one_sheet.png
  data/
    raw/                      60 file CSV simulasi (tidak di-commit, dibuat ulang oleh skrip 01)
    sample/                   3 contoh file mesin
    README.md                 sumber dan catatan data
  docs/                       analysis_plan.md, definitions.md, data_dictionary.md, ground_truth.md
  requirements.txt
  pushtest.duckdb             database (tidak di-commit, dibuat ulang dari skrip)
```
"""
(ROOT.parent / "README.md").write_text(text, encoding="utf-8")
print("ditulis: README.md")
