"""01 - Membuat 60 file CSV simulasi berformat mesin push test (data/machine_files/).

Ground truth dipakai di sini untuk membangkitkan data. Analisis (02-06) tidak membacanya.
Jalankan dari mana saja: python scripts/01_generate_machine_files.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (CONDITIONS, COND_LABEL, DIRT, GT, LSL_G, MACHINE_DIR, MODELS,
                    N_DAYS, SEED, SESSIONS_TOTAL, START_DATE, UNITS_PER_SESSION)

rng = np.random.default_rng(SEED)
COMBOS = [(m, c) for m in MODELS for c in CONDITIONS]          # 6 kombinasi
BONDERS = ["BD-01", "BD-02", "BD-03"]
OPERATORS = ["OP-01", "OP-02", "OP-03", "OP-04"]
NAME_TAG = {"before_oven": "SebelumOven", "after_oven": "SetelahOven", "after_baked": "SetelahBaked"}
ALT_NAME_TAG = {"before_oven": "sebelum oven", "after_oven": "AfterOven", "after_baked": "setelah baked"}


def fmt(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def sid(i):
    return f"S{i + 1:03d}"


# 1. Sesi, kombinasi, tanggal, mesin, dan nilai per cover glass
sessions = []
start = date.fromisoformat(START_DATE)
for i in range(SESSIONS_TOTAL):
    model, cond = COMBOS[i % len(COMBOS)]
    s = sid(i)
    base = GT["base_g"][model] * (1 + GT["oven_effect"][model][cond])
    sess_eff = rng.normal(0, GT["session_sd_g"])
    sd = GT["outlier_sd_g"] if s == GT["outlier_session"] else GT["unit_sd_g"]
    vals = rng.normal(base + sess_eff, sd, UNITS_PER_SESSION)
    if s == GT["outlier_session"]:
        vals[0], vals[1] = GT["outlier_low_g"]
    vals = np.round(vals, 1)
    d = start + timedelta(days=int(rng.integers(0, N_DAYS)))
    sessions.append(dict(
        sid=s, model=model, cond=cond, date=d,
        bonder=BONDERS[int(rng.integers(0, len(BONDERS)))],
        operator=OPERATORS[int(rng.integers(0, len(OPERATORS)))],
        vals=vals,
    ))

# 2. Data kotor tambahan (baris ekstra, tidak mengubah nilai asli)
extra = {x["sid"]: [] for x in sessions}
dup_idx = rng.choice(len(sessions), DIRT["duplicate_rows"], replace=False)
for k in dup_idx:                                    # baris ganda: salinan baris asli
    x = sessions[k]
    j = int(rng.integers(0, UNITS_PER_SESSION))
    extra[x["sid"]].append((j + 1, x["vals"][j], "dup"))
zero_idx = rng.choice(len(sessions), DIRT["zero_force_rows"], replace=False)
for k in zero_idx:                                   # gaya nol
    extra[sessions[k]["sid"]].append((UNITS_PER_SESSION + 1, 0.0, "zero"))
empty_idx = [k for k in rng.choice(len(sessions), DIRT["empty_force_rows"] + 3, replace=False)
             if k not in zero_idx][:DIRT["empty_force_rows"]]
for k in empty_idx:                                  # gaya kosong
    extra[sessions[k]["sid"]].append((UNITS_PER_SESSION + 2, None, "empty"))

# 3. Tulis file
for x in sessions:
    s, model, cond, vals = x["sid"], x["model"], x["cond"], x["vals"]
    n = len(vals)
    mean = float(np.mean(vals))
    sd = float(np.std(vals, ddof=1))
    cpk = (mean - LSL_G) / (3 * sd)
    fails = int(np.sum(vals < LSL_G))
    cond_text = "" if s in DIRT["empty_condition_sessions"] else COND_LABEL[cond]
    alt = s in DIRT["alt_name_sessions"]
    tag = (ALT_NAME_TAG if alt else NAME_TAG)[cond]
    name = f"{s}_{model.replace(' ', '')}_{tag}.csv"
    lines = [
        "Test Program;DS20KG",
        "Test Mode;Destructive",
        "Test Speed (mm/s);0,3",
        f"Session ID;{s}",
        f"Test Date;{x['date'].strftime('%d/%m/%Y')}",
        f"Model;{model}",
        f"Condition;{cond_text}",
        f"Bonder;{x['bonder']}",
        f"Operator;{x['operator']}",
        f"LSL (g);{fmt(LSL_G, 0)}",
        f"Sample Count;{n}",
        f"Average (g);{fmt(mean)}",
        f"Std Dev (g);{fmt(sd)}",
        f"Machine Cpk;{fmt(cpk, 2)}",
        f"Fail Count;{fails}",
        "Sample No;Force (g)",
    ]
    lines += [f"{j + 1};{fmt(v)}" for j, v in enumerate(vals)]
    for j, v, kind in extra[s]:
        lines.append(f"{j};" + ("" if v is None else fmt(v)))
    (MACHINE_DIR / name).write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"{len(sessions)} file ditulis ke {MACHINE_DIR}")
print("baris ekstra (data kotor):", sum(len(v) for v in extra.values()))
