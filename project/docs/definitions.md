# Definisi dan asumsi

Label: **[definisi]** = dari rancangan; **[asumsi]** = tidak ada di rancangan, ditetapkan di proyek ini dan diuji sensitivitasnya.

| Istilah | Label | Definisi / nilai | Sensitivitas |
|---|---|---|---|
| Gaya lepas (force_g) | [definisi] | gaya maksimum push test sampai cover glass lepas, dalam gram | |
| NG | [definisi] | gaya lepas di bawah batas bawah 2.000 g | |
| Batas bawah spesifikasi (LSL) | [definisi] | 2.000 g | |
| Cpk satu sisi | [definisi] | (mean − LSL) / (3 × sd), sd ddof = 1 | CI pendekatan normal (Bissell) |
| Fail rate | [definisi] | NG / n | CI Wilson |
| Estimasi ppm | [asumsi] | P(gaya < LSL) dengan distribusi normal dari mean dan sd kombinasi, × 1.000.000 | dibandingkan dengan fail rate aktual; dihitung ulang tanpa sesi S037 |
| Selisih praktis | [asumsi] | 500 g | diuji pada 250, 500, dan 1.000 g (sensitivity.csv) |
| Target Cpk | [asumsi] | 1,33 | hanya status; tidak mengubah angka |
| Sesi outlier | [asumsi] | sesi S037 (ditanam, lihat ground_truth.md) dianalisis dengan dan tanpa | Model A sebelum oven berubah dari Cpk 1,46 menjadi 1,93 |
| Koreksi banyak perbandingan | [asumsi] | Bonferroni untuk Q3 dan Q4 (p × jumlah uji, maksimal 1) | Dibandingkan dengan Holm: 2 dari 27 keputusan berubah (Q3 setelah baked vs setelah oven 1 jam, dan Q4 Mann-Whitney setelah baked), keduanya pada p sekitar 0,05; kesimpulan utama tidak berubah |
| Residual sesi (Q9, Q10) | [asumsi] | nilai minus rata-rata kombinasi model x kondisi | tanpa residual, tren tercampur kondisi |
| Daya interaksi (MDE) | [asumsi] | (z 1,96 + z 0,84) × SE selisih selisih; SE dari sd dan n kelompok | dihitung di 07, dibandingkan dengan selisih yang ditanam |

## Catatan

- Data simulasi: pola, tren, dan efek yang ditemukan menggambarkan simulasi, bukan lini produksi.
- Unit uji bersarang dalam sesi. Uji per cover glass (Welch, ANOVA) memperlakukan unit sebagai independen; uji per sesi dipakai sebagai pembanding.
