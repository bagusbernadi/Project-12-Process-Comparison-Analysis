"""Path dan parameter bersama.

Parameter GT (ground truth) hanya dipakai oleh 01_generate_machine_files.py dan
07_recommend_validate.py (skrip validasi). Skrip analisis (02-06) tidak membacanya.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # folder project/
MACHINE_DIR = ROOT / "data" / "raw" / "machine_files"   # data mentah simulasi (tidak di-commit)
DB_PATH = ROOT / "pushtest.duckdb"
SQL_DIR = ROOT / "code" / "2-analysis" / "sql"
RES_PREP = ROOT / "results" / "1-data-preparation"
RES_ANA = ROOT / "results" / "2-analysis"
RES_PRES = ROOT / "results" / "3-presentation"
for _d in (MACHINE_DIR, RES_PREP, RES_ANA, RES_PRES):
    _d.mkdir(parents=True, exist_ok=True)


def result(name):
    """Path file hasil: dicari di folder hasil per tahap."""
    for d in (RES_PREP, RES_ANA, RES_PRES):
        if (d / name).exists():
            return d / name
    raise FileNotFoundError(name)


SEED = 20260927
LSL_G = 2000.0          # batas bawah spesifikasi (g)
USL_G = 20000.0         # batas atas (g), tidak dipakai untuk risiko NG
ALPHA = 0.05
PRACTICAL_DIFF_G = 500.0  # selisih minimum yang dianggap bermakna secara praktis (asumsi)
CPK_TARGET = 1.33         # target Cpk (asumsi, sesuai rancangan)

MODELS = ["Model A", "Model B"]
CONDITIONS = ["before_oven", "after_oven", "after_baked"]
COND_LABEL = {
    "before_oven": "Sebelum oven",
    "after_oven": "Setelah oven 1 jam",
    "after_baked": "Setelah baked",
}
COND_SEQ = {"before_oven": 1, "after_oven": 2, "after_baked": 3}
COND_OVEN_MIN = {"before_oven": 0, "after_oven": 60, "after_baked": 60}

SESSIONS_TOTAL = 60       # 6 kombinasi x 10 sesi
UNITS_PER_SESSION = 10
START_DATE = "2026-07-01"
N_DAYS = 92               # Juli sampai akhir September 2026

# Ground truth: fakta yang sengaja ditanam di data simulasi (hanya skrip 01 dan 07)
GT = {
    "base_g": {"Model A": 7000.0, "Model B": 6490.0},          # rata-rata sebelum oven per model
    "oven_effect": {                                             # kenaikan relatif terhadap sebelum oven
        "Model A": {"before_oven": 0.0, "after_oven": 0.05, "after_baked": 0.08},
        "Model B": {"before_oven": 0.0, "after_oven": 0.15, "after_baked": 0.12},
    },
    "session_sd_g": 180.0,     # sebaran antar sesi
    "unit_sd_g": 850.0,        # sebaran antar cover glass dalam sesi
    "outlier_session": "S037",  # sesi dengan sebaran sangat besar
    "outlier_sd_g": 1600.0,
    "outlier_low_g": [1850.0, 1960.0],  # 2 unit di bawah 2.000 g
}

# Data kotor yang disisipkan (jumlah baris tambahan; ±2-3% dari 600 baris)
DIRT = {
    "duplicate_rows": 8,
    "zero_force_rows": 5,
    "empty_force_rows": 2,
    "empty_condition_sessions": ["S011", "S045"],
    "alt_name_sessions": ["S004", "S016", "S028"],
}
