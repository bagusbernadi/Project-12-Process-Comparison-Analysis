# Rencana analisis (ditetapkan sebelum melihat hasil)

Pertanyaan utama: apakah kekuatan glue berbeda signifikan antar kondisi proses (sebelum oven, setelah oven 1 jam, setelah baked) dan antar model (Model A dan Model B), dan kondisi mana yang memberi risiko NG paling kecil?

## KPI

| KPI | Rumus | Catatan |
|---|---|---|
| Median gaya | median(force_g) per kombinasi | ukuran pusat utama, tahan terhadap outlier |
| Simpangan baku | stddev sampel (ddof = 1) | sebaran |
| Cpk (satu sisi, LSL 2.000 g) | (mean − LSL) / (3 × sd) | target minimal 1,33 (asumsi, lihat definitions.md) |
| Fail rate | jumlah NG / n, NG = gaya < 2.000 g | aktual |
| Effect size | Cohen's d = selisih rata-rata / sd gabungan | |

## Aturan uji

- Alpha 0,05 dua arah.
- Perbandingan dua kelompok: Welch t per cover glass (uji utama) dan Mann-Whitney U (sensitivitas).
- Tiga kondisi: ANOVA satu arah, lalu Tukey HSD.
- Dua faktor: ANOVA dua arah model x kondisi, dengan sensitivitas ANOVA pada rata-rata sesi.
- Banyak perbandingan dalam satu keluarga: koreksi Bonferroni (Q3, Q4).
- Selisih dianggap bermakna praktis bila minimal 500 g (asumsi).
- Asumsi Cpk dan ppm: sebaran normal. Dicek ulang dengan fail rate aktual dan tanpa sesi outlier.

## Hipotesis dan kriteria keputusan

Pertanyaan dijawab dari data, bukan dari fakta yang ditanam. Hasil yang bertentangan dengan harapan ditulis apa adanya.
