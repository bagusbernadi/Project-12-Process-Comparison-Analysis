[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 12: Process Comparison Analysis

**Status: Design (rancangan).** Halaman rancangan ada di [`index.html`](index.html). Analisis, dashboard, dan angka hasil belum dikerjakan, sehingga bagian Analysis, Recommendation, dan Impact di bawah masih kosong.

**Tujuan:** membangun analisis statistik dan dashboard yang membandingkan kekuatan glue pada perekatan camera cover glass smartphone antar kondisi proses dan antar model (Model A dan Model B), sehingga kondisi proses terbaik dapat dipilih berdasarkan bukti.

| | |
|---|---|
| Kategori | Manufaktur smartphone |
| Tingkat | Mudah |
| Data | Data simulasi meniru format file mesin push test |
| Tools | DuckDB + SQL, Python (pandas, SciPy, statsmodels), Jupyter Notebook, Streamlit + Plotly |

## 1. Problem

**Pertanyaan utama:** Apakah kekuatan glue berbeda signifikan antar kondisi proses (sebelum oven, setelah oven, setelah baked) dan antar model, dan kondisi mana yang memberi risiko NG paling kecil?

Rancangan memecahnya menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan) dalam tema kondisi proses, model, variasi dan kapabilitas, waktu, rekomendasi, dan validitas. Daftar lengkap ada di bagian 2 halaman rancangan.

## 2. Data

- Data simulasi meniru format file CSV mesin push test: baris ringkasan sesi, koma desimal, uji destruktif, batas contoh 2.000–20.000 g. Generator Python akan disertakan.
- Ukuran: 2 model × 3 kondisi, ±60 sesi × ±10 unit.
- Rencana tabel: `test_sessions`, `push_results`, `dim_condition`, `group_summary`.

## 3. Analysis

Belum dikerjakan. Rencana langkah (12 langkah, tahap A sampai D) ada di bagian 6 halaman rancangan. Semua angka nanti dihitung dari data dengan SQL dan dicek silang.

Fakta yang sengaja ditanam di data simulasi (ground truth):
1. setelah oven ±10% lebih kuat.
2. Model B ±5% lebih lemah.
3. efek oven lebih besar di Model B.
4. satu sesi dengan sebaran besar dan 2 unit NG.
5. 2–3% data kotor.

## 4. Recommendation

Belum dikerjakan. Output yang direncanakan: kondisi proses terbaik per model.

## 5. Impact

Belum dikerjakan. Rumus yang akan dipakai (semua hasil diberi label `estimated`):

```
Penurunan fail rate = fail rate kondisi lama − fail rate kondisi baru
```

## Batasan yang sudah diketahui

- Sampel per sesi kecil.
- Pola belum tentu penyebab.
- Uji destruktif membatasi jumlah sampel.

## Struktur repository

```
index.html   Halaman rancangan project (bisa dibuka di browser atau lewat GitHub Pages)
README.md    Dokumen ini
```

Folder `docs/`, `data/`, `scripts/`, `sql/`, `notebooks/`, `dashboard/`, dan `outputs/` ditambahkan saat pengerjaan dimulai.
