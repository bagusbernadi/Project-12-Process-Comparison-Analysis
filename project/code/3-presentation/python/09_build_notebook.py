# Membangun results/3-presentation/analysis.ipynb P12 (membaca results/*/*.csv). Dijalankan dengan nbconvert setelah dibangun (lihat run_all.sh).
import sys, pathlib, nbformat as nbf
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from common import RES_PRES
nb = nbf.v4.new_notebook()
C, M = nbf.v4.new_code_cell, nbf.v4.new_markdown_cell
nb.cells = [
M("# Project 12: Process Comparison Analysis\n\n**DATA SIMULASI.** Notebook ini membaca hasil dari `results/` dan menampilkan langkah utama. "
  "Perhitungan lengkap ada di `code/1-data-preparation` dan `code/2-analysis` (skrip 01–07)."),
M("## Data dan cleaning"),
C("import pandas as pd\npd.read_csv('../1-data-preparation/cleaning_log.csv')"),
M("## Kondisi proses dan model (Q1–Q4)"),
C("g = pd.read_csv('../2-analysis/group_summary.csv')\ng[['model','condition_label','n','median_g','sd_g','fail_rate']]"),
C("t = pd.read_csv('../2-analysis/test_results.csv')\nt[t.pertanyaan.isin(['Q1','Q2'])][['pertanyaan','perbandingan','uji','selisih_g','ci_bawah_g','ci_atas_g','p_terkoreksi','keputusan']]"),
M("## Kapabilitas (Cpk) dan NG"),
C("pd.read_csv('../2-analysis/capability.csv')[['model','condition_label','median_g','sd_g','cpk','cpk_lo','fail_rate']]"),
M("## Rekomendasi"),
C("pd.read_csv('../2-analysis/recommendation.csv')"),
M("## Validasi terhadap fakta yang ditanam\nFakta yang ditanam hanya dipakai skrip validasi (07). Interaksi model x oven tidak terdeteksi: daya kurang (lihat 7.6 di report)."),
C("pd.read_csv('../2-analysis/ground_truth_check.csv')"),
M("## Kesimpulan\n- Efek oven terbukti. Setelah oven 1 jam menjadi kondisi rekomendasi.\n- Interaksi model x oven tidak terdeteksi.\n- Data simulasi: hasil membuktikan metode, bukan kondisi lini."),
]
for i, c in enumerate(nb.cells, 1):
    c.id = f"cell-{i:02d}"
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
path = RES_PRES / "analysis.ipynb"
nbf.write(nb, path); print("ditulis:", path)
