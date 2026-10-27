# Kamus data

Database: `pushtest.duckdb` (dibuat ulang oleh `code/1-data-preparation/python/02_parse_load.py`, tidak di-commit).

## test_sessions (1 baris = 1 sesi uji = 1 file mesin)

| Kolom | Tipe | Arti |
|---|---|---|
| session_id | VARCHAR, PK | kode sesi (S001–S060), dari ringkasan file |
| test_date | DATE | tanggal uji (dd/mm/yyyy di file) |
| model | VARCHAR | Model A atau Model B (CHECK) |
| condition | VARCHAR, FK | before_oven, after_oven, after_baked |
| condition_source | VARCHAR | "ringkasan" atau "nama file" (bila kolom Condition kosong) |
| program | VARCHAR | program mesin, DS20KG |
| bonder | VARCHAR | mesin bonder (BD-01 s.d. BD-03) |
| operator | VARCHAR | operator (OP-01 s.d. OP-04) |
| lsl_g | DOUBLE | batas bawah, 2.000 g |
| usl_g | DOUBLE | batas atas, 20.000 g (tidak dipakai untuk NG) |
| machine_cpk | DOUBLE | Cpk yang ditulis mesin, dibandingkan di 04 |
| fail_count | INTEGER | jumlah fail yang ditulis mesin, dibandingkan di 04 |
| source_file | VARCHAR | nama file CSV sumber |

## push_results (1 baris = 1 cover glass yang diuji)

| Kolom | Tipe | Arti |
|---|---|---|
| session_id | VARCHAR, FK | kode sesi |
| sample_no | INTEGER | nomor sampel dalam sesi (PK bersama session_id) |
| force_g | DOUBLE | gaya lepas dalam gram, > 0 (CHECK) |
| result | VARCHAR | OK atau NG, dihitung dari LSL (bukan dari file) |
| bonder | VARCHAR | salinan dari sesi |
| operator | VARCHAR | salinan dari sesi |

## dim_condition

| Kolom | Arti |
|---|---|
| condition | kode kondisi |
| label | label untuk pembaca (Sebelum oven, Setelah oven 1 jam, Setelah baked) |
| oven_minutes | lama oven (0 atau 60) |
| sequence | urutan proses (1, 2, 3) |

## group_summary (1 baris = 1 kombinasi model x kondisi)

model, condition, n, median_g, sd_g, cpk, fail_rate. Dibuat di `06_capability.py`.

## View SQL

- `v_push`: push_results + test_sessions + dim_condition.
- `v_group_summary`: ringkasan per kombinasi (n, median, Q1, Q3, mean, sd, min, max, NG, fail rate).
- `v_session_summary`: ringkasan per sesi.

## Aturan cleaning (lihat results/1-data-preparation/cleaning_log.csv)

- Koma desimal diubah menjadi titik.
- Label kondisi kosong di ringkasan diambil dari nama file.
- Baris gaya kosong dan gaya nol dibuang.
- Baris ganda (nomor sampel sama) dibuang; baris pertama dipakai.
- Result dihitung ulang dari LSL.
