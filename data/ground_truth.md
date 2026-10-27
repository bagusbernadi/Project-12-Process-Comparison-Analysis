# Ground truth (fakta yang sengaja ditanam di data simulasi)

Data ini adalah simulasi. Parameter ada di `scripts/common.py` (blok GT) dan hanya dibaca oleh `01_generate_machine_files.py` dan `07_recommend_validate.py`. Analisis (02–06) tidak membacanya.

| # | Fakta yang ditanam | Parameter |
|---|---|---|
| 1 | Setelah oven 1 jam ±10% lebih kuat dari sebelum oven (rata-rata, dua model) | kenaikan relatif Model A 5%, Model B 15% |
| 2 | Model B ±5% lebih lemah dari Model A (rata-rata tiga kondisi) | rata-rata dasar A 7.000 g, B 6.490 g |
| 3 | Efek oven lebih besar di Model B (interaksi) | selisih kenaikan setelah oven 623,5 g (B − A) |
| 4 | Satu sesi (S037, Model A sebelum oven) sangat menyebar dengan 2 unit di bawah 2.000 g | sd 1.600 g; unit 1.850 g dan 1.960 g |
| 5 | Sekitar 2–3% data kotor | 8 baris ganda, 5 gaya nol, 2 gaya kosong (15 baris) |

Catatan kalibrasi: fakta 3 dirancang tanpa perhitungan daya. Setelah data dibuat, daya deteksi interaksi ternyata rendah (MDE ±554 g, selisih yang ditanam 624 g; lihat ground_truth_check.csv dan 7.6). Ini kesalahan perancangan, dicatat jujur, dan tidak diperbaiki dengan mengubah parameter setelah melihat hasil uji.
