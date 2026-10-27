[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 12: Process Comparison Analysis

**Status: Selesai di branch (belum digabung ke main).** Halaman project (Design dan Report) ada di [`design-and-report/index.html`](design-and-report/index.html). Dashboard, notebook, dan one-sheet belum dibuat.

**Tujuan:** membandingkan kekuatan glue pada perekatan camera cover glass smartphone antar kondisi proses (sebelum oven, setelah oven 1 jam, setelah baked) dan antar model (Model A dan Model B), untuk memilih kondisi proses terbaik berdasarkan bukti.

| | |
|---|---|
| Kategori | Manufaktur smartphone |
| Tingkat | Mudah |
| Data | **Data simulasi** yang meniru format file mesin push test |
| Tools | DuckDB + SQL, Python (pandas, SciPy, statsmodels) |

## 1. Problem

**Pertanyaan utama:** Apakah kekuatan glue berbeda signifikan antar kondisi proses dan antar model, dan kondisi mana yang memberi risiko NG paling kecil?

Rancangan memecahnya menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan). Daftar lengkap ada di bagian 2 halaman rancangan.

## 2. Data

- **Data simulasi.** Angka menggambarkan data buatan, bukan lini produksi. Parameter ground truth ada di `scripts/common.py` dan `data/ground_truth.md`.
- 60 file CSV berformat mesin (`data/machine_files/`): 6 kombinasi model x kondisi, 10 sesi per kombinasi, 10 cover glass per sesi, dibuat Juli sampai September 2026.
- 615 baris data mentah, di antaranya 15 baris kotor (2,4%): baris ganda, gaya nol, dan gaya kosong. 600 baris dipakai setelah cleaning.
- Tabel di DuckDB: `test_sessions`, `push_results`, `dim_condition`, dan `group_summary`. Kamus data di `docs/data_dictionary.md`.

## 3. Analysis

- **Efek oven terbukti.** Gaya setelah oven 1 jam rata-rata 747 g lebih tinggi dibanding sebelum oven (CI 95% 552 s.d. 943 g, p < 0,001).
- **Setelah baked tidak berbeda dengan setelah oven 1 jam** (selisih 183 g, p terkoreksi 0,13).
- **Model A dan Model B berbeda kecil.** Sebelum oven, Model A lebih tinggi 344 g; setelah baked 307 g. Keduanya di bawah batas praktis 500 g. Setelah oven 1 jam tidak berbeda.
- **Interaksi model x oven tidak terdeteksi.** Daya deteksi hanya ±554 g, sedangkan selisih yang ditanam 624 g. Ini kesalahan perancangan (lihat Batasan).
- **Kapabilitas memenuhi target Cpk 1,33** pada semua kombinasi. Cpk Model A sebelum oven (1,46) ditarik oleh satu sesi S037 yang sangat menyebar; tanpa sesi itu 1,93.
- **Tidak ada tren antar sesi** dan tidak ada perbedaan antar bonder atau operator.
- Cek silang SQL vs pandas dan ringkasan mesin: 28 dari 28 PASS.

## 4. Recommendation

Gunakan **setelah oven 1 jam** sebagai kondisi proses untuk kedua model. Verifikasi dengan data lini nyata sebelum diterapkan, dan selidiki lot glue pada sesi S037.

## 5. Impact

Penurunan fail rate estimasi (estimated, asumsi sebaran normal): sekitar 5,6 ppm untuk Model A dan 0,03 ppm untuk Model B per 1 juta unit. Angka ini kecil karena kedua model sudah memenuhi target Cpk sebelum oven. Nilai utamanya adalah margin median: +551 g (Model A) dan +847 g (Model B).

## Batasan

- **Data adalah simulasi.** Hasil menunjukkan bahwa metode bekerja, bukan kondisi lini produksi.
- **Interaksi tidak terdeteksi.** Daya tidak dihitung sebelum data dibuat (kesalahan perancangan). Dicatat jujur, tidak diperbaiki dengan mengubah parameter setelah melihat hasil.
- Satu sesi (S037) menentukan semua NG dan sangat memengaruhi Cpk Model A sebelum oven.
- Unit bersarang dalam sesi; uji per sesi dilaporkan sebagai pembanding. Residual tidak normal, sehingga Mann-Whitney juga dilaporkan.
- Asumsi (label di `docs/definitions.md`): batas praktis 500 g, target Cpk 1,33, estimasi ppm dengan sebaran normal, koreksi Holm.
- Dashboard (Streamlit), notebook, dan one-sheet belum dibuat. Repositori belum digabung ke main.

## Menjalankan

Dari root repo, urutan berikut (sekali jalan dari nol):

```bash
pip install -r requirements.txt
python scripts/01_generate_machine_files.py
python scripts/02_parse_load.py
python scripts/03_sql_views.py
python scripts/04_crosscheck.py
python scripts/05_stats.py
python scripts/06_capability.py
python scripts/07_recommend_validate.py
python design-and-report/src/build_report.py
```

## Struktur repository

```
index.html                    pengalihan ke design-and-report/
README.md                     dokumen ini
requirements.txt
design-and-report/
  index.html                  halaman project (Design + Report)
  src/                        page_v1.html (pane Design), report.css, report_lib.py, build_report.py
scripts/
  common.py                   path dan parameter (blok GT hanya dibaca 01 dan 07)
  01_generate_machine_files.py
  02_parse_load.py
  03_sql_views.py
  04_crosscheck.py
  05_stats.py
  06_capability.py
  07_recommend_validate.py
sql/
  01_group_views.sql
  02_session_views.sql
data/
  machine_files/              60 file CSV simulasi (di-commit)
  ground_truth.md             fakta yang ditanam
docs/
  analysis_plan.md, definitions.md, data_dictionary.md
outputs/                      CSV hasil analisis dan log cleaning
pushtest.duckdb               database (tidak di-commit, dibuat ulang dari skrip)
```
