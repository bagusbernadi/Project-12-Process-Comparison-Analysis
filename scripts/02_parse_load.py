"""02 - Membaca file mesin, membersihkan data, mencatat perubahan, dan memuat 4 tabel ke DuckDB.

Aturan cleaning:
- koma desimal diubah menjadi titik;
- label kondisi dari ringkasan; bila kosong, diambil dari nama file (dicatat);
- baris gaya kosong dan gaya nol dibuang (dicatat);
- baris ganda (nomor sampel yang sama) dibuang, baris pertama dipakai (dicatat);
- result OK/NG dihitung ulang dari LSL, tidak dari file.
Constraint DuckDB menolak gaya <= 0, sesi tanpa model, dan sampel ganda.
"""
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import COND_LABEL, COND_OVEN_MIN, COND_SEQ, DB_PATH, LSL_G, MACHINE_DIR, OUT_DIR, USL_G
from common import CONDITIONS

from datetime import datetime


def cond_code(text):
    k = re.sub(r"[^a-z]", "", str(text).lower())
    if not k:
        return None
    if "sebelum" in k or "before" in k:
        return "before_oven"
    if "baked" in k:
        return "after_baked"
    if "oven" in k:
        return "after_oven"
    return None


def model_name(text):
    m = re.search(r"([AB])\s*$", str(text).strip())
    return f"Model {m.group(1)}" if m else None


def num(text):
    return float(str(text).strip().replace(",", "."))


def read_file(path):
    summary, rows, header = {}, [], False
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        if not header:
            if ln.startswith("Sample No"):
                header = True
                continue
            k, _, v = ln.partition(";")
            summary[k.strip()] = v.strip()
        else:
            n, _, v = ln.partition(";")
            rows.append((n.strip(), v.strip()))
    return summary, rows


CANON_STEM = {"SebelumOven", "SetelahOven", "SetelahBaked"}
sessions, pushes, log, naive = [], [], [], []
raw_total = 0
files = sorted(MACHINE_DIR.glob("*.csv"))

for path in files:
    summary, rows = read_file(path)
    sid = summary["Session ID"]
    fname_sid, _, stem = path.stem.partition("_")
    assert fname_sid == sid, f"ID sesi di nama file ({fname_sid}) beda dengan ringkasan ({sid})"
    name_cond = cond_code(stem.split("_", 1)[1] if "_" in stem else stem)
    cond = cond_code(summary.get("Condition", ""))
    src = "ringkasan"
    if cond is None:
        cond, src = name_cond, "nama file"
        log.append(dict(file=path.name, session_id=sid, baris=None, jenis="label kosong",
                        detail="kolom Condition di ringkasan kosong", tindakan=f"label diambil dari nama file: {COND_LABEL[cond]}"))
    if name_cond != cond:
        raise ValueError(f"label nama file dan ringkasan beda: {path.name}")
    model = model_name(summary["Model"])
    assert model is not None, path.name
    if not stem.split("_", 1)[1] in CANON_STEM:
        log.append(dict(file=path.name, session_id=sid, baris=None, jenis="nama file tidak seragam",
                        detail="ejaan label di nama file berbeda", tindakan="dibaca dengan pemetaan label; nama file tidak diubah"))
    d = datetime.strptime(summary["Test Date"], "%d/%m/%Y").date()
    sessions.append(dict(
        session_id=sid, test_date=d, model=model, condition=cond, condition_source=src,
        program=summary["Test Program"], bonder=summary["Bonder"], operator=summary["Operator"],
        lsl_g=num(summary["LSL (g)"]), usl_g=USL_G, machine_cpk=num(summary["Machine Cpk"]),
        fail_count=int(summary["Fail Count"]), source_file=path.name,
    ))
    seen = set()
    for n, v in rows:
        raw_total += 1
        ln = int(n)
        if v == "":
            log.append(dict(file=path.name, session_id=sid, baris=ln, jenis="gaya kosong",
                            detail="kolom gaya kosong", tindakan="dibuang"))
            continue
        f = num(v)
        naive.append(dict(session_id=sid, sample_no=ln, force_g=f))
        if f <= 0:
            log.append(dict(file=path.name, session_id=sid, baris=ln, jenis="gaya nol",
                            detail=f"gaya {v} g", tindakan="dibuang"))
            continue
        if ln in seen:
            log.append(dict(file=path.name, session_id=sid, baris=ln, jenis="baris ganda",
                            detail=f"nomor sampel {ln} muncul lebih dari sekali", tindakan="baris kedua dibuang"))
            continue
        seen.add(ln)
        pushes.append(dict(session_id=sid, sample_no=ln, force_g=f,
                           result="NG" if f < LSL_G else "OK",
                           bonder=summary["Bonder"], operator=summary["Operator"]))

sess = pd.DataFrame(sessions).sort_values("session_id").reset_index(drop=True)
push = pd.DataFrame(pushes).sort_values(["session_id", "sample_no"]).reset_index(drop=True)
nv = pd.DataFrame(naive)
log_df = pd.DataFrame(log, columns=["file", "session_id", "baris", "jenis", "detail", "tindakan"])
log_df = log_df.sort_values(["file", "jenis", "baris"], na_position="first", kind="mergesort").reset_index(drop=True)
log_df.to_csv(OUT_DIR / "cleaning_log.csv", index=False, encoding="utf-8")

dim = pd.DataFrame([dict(condition=c, label=COND_LABEL[c], oven_minutes=COND_OVEN_MIN[c], sequence=COND_SEQ[c])
                    for c in CONDITIONS]).sort_values("sequence").reset_index(drop=True)

# Ringkasan kualitas data (Q12)
dropped = log_df.groupby("jenis").size().to_dict()
n_raw = raw_total
n_clean = len(push)
dq = [
    ("file mesin dibaca", len(files), "file CSV di data/machine_files"),
    ("baris data mentah", n_raw, "termasuk baris kotor yang disisipkan"),
    ("baris gaya kosong", dropped.get("gaya kosong", 0), "dibuang"),
    ("baris gaya nol", dropped.get("gaya nol", 0), "dibuang"),
    ("baris ganda", dropped.get("baris ganda", 0), "dibuang (baris kedua)"),
    ("baris dipakai", n_clean, "masuk tabel push_results"),
    ("persentase baris kotor", (n_raw - n_clean) / n_raw, "(mentah - dipakai) / mentah"),
    ("sesi", len(sess), "tabel test_sessions"),
    ("sesi label dari nama file", int((sess.condition_source == "nama file").sum()), "kolom Condition di ringkasan kosong"),
    ("NG naif (tanpa cleaning)", int((nv.force_g < LSL_G).sum()), "termasuk gaya nol dan baris ganda"),
    ("NG bersih", int((push.result == "NG").sum()), "setelah cleaning"),
    ("rata-rata gaya naif (g)", float(nv.force_g.mean()), "tanpa cleaning"),
    ("rata-rata gaya bersih (g)", float(push.force_g.mean()), "setelah cleaning"),
]
dq_df = pd.DataFrame(dq, columns=["metrik", "nilai", "catatan"])
dq_df.to_csv(OUT_DIR / "data_quality.csv", index=False, encoding="utf-8")

# Muat ke DuckDB (ulang dari nol setiap kali dijalankan)
if DB_PATH.exists():
    DB_PATH.unlink()
con = duckdb.connect(str(DB_PATH))
con.execute("""
CREATE TABLE dim_condition (
  condition VARCHAR PRIMARY KEY, label VARCHAR NOT NULL, oven_minutes INTEGER, sequence INTEGER);
CREATE TABLE test_sessions (
  session_id VARCHAR PRIMARY KEY, test_date DATE NOT NULL,
  model VARCHAR NOT NULL CHECK (model IN ('Model A', 'Model B')),
  condition VARCHAR NOT NULL REFERENCES dim_condition(condition),
  condition_source VARCHAR, program VARCHAR, bonder VARCHAR, operator VARCHAR,
  lsl_g DOUBLE, usl_g DOUBLE, machine_cpk DOUBLE, fail_count INTEGER, source_file VARCHAR);
CREATE TABLE push_results (
  session_id VARCHAR NOT NULL REFERENCES test_sessions(session_id),
  sample_no INTEGER NOT NULL,
  force_g DOUBLE NOT NULL CHECK (force_g > 0),
  result VARCHAR NOT NULL CHECK (result IN ('OK', 'NG')),
  bonder VARCHAR, operator VARCHAR,
  PRIMARY KEY (session_id, sample_no));
""")
con.register("dim_df", dim)
con.register("sess_df", sess)
con.register("push_df", push)
con.execute("INSERT INTO dim_condition SELECT condition, label, oven_minutes, sequence FROM dim_df")
con.execute("INSERT INTO test_sessions SELECT session_id, test_date, model, condition, condition_source, program, "
            "bonder, operator, lsl_g, usl_g, machine_cpk, fail_count, source_file FROM sess_df")
con.execute("INSERT INTO push_results SELECT session_id, sample_no, force_g, result, bonder, operator FROM push_df "
            "ORDER BY session_id, sample_no")
print("sesi:", con.execute("SELECT COUNT(*) FROM test_sessions").fetchone()[0],
      "| push_results:", con.execute("SELECT COUNT(*) FROM push_results").fetchone()[0],
      "| baris kotor:", len(log_df))
con.close()
