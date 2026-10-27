"""04 - Cek silang (Q14): SQL vs pandas per kombinasi, dan ringkasan mesin vs hitung ulang per sesi.

Hasil ditulis ke results/2-analysis/crosscheck.csv. Jika ada FAIL, skrip berhenti dengan error.
"""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import DB_PATH, LSL_G, RES_ANA

con = duckdb.connect(str(DB_PATH), read_only=True)
push = con.execute("SELECT session_id, sample_no, force_g, result, model, condition FROM v_push").df()
sql_grp = con.execute("SELECT * FROM v_group_summary").df()
sess_db = con.execute("SELECT session_id, machine_cpk, fail_count FROM test_sessions").df()
n_sess_db = con.execute("SELECT COUNT(*) FROM test_sessions").fetchone()[0]
con.close()

rows = []


def check(name, sql_val, pd_val, tol=1e-6):
    diff = abs(float(sql_val) - float(pd_val))
    rows.append(dict(pemeriksaan=name, nilai_sql_atau_mesin=sql_val, nilai_pandas=pd_val,
                     selisih=round(diff, 9), hasil="PASS" if diff <= tol else "FAIL"))


# a. Jumlah baris dan sesi
check("jumlah baris push_results", len(push), len(push))
check("jumlah sesi test_sessions", n_sess_db, push.session_id.nunique())

# b. Per kombinasi: pandas dihitung ulang dari baris per cover glass
pd_grp = push.groupby(["model", "condition"]).agg(
    n=("force_g", "size"), median_g=("force_g", "median"), sd_g=("force_g", lambda x: x.std(ddof=1)),
    ng_count=("result", lambda x: int((x == "NG").sum()))).reset_index()
m = sql_grp.merge(pd_grp, on=["model", "condition"], suffixes=("_sql", "_pd"))
assert len(m) == len(sql_grp) == 6, "kombinasi tidak lengkap"
for _, r in m.iterrows():
    tag = f"{r.model} / {r.condition}"
    check(f"n {tag}", r.n_sql, r.n_pd, 0)
    check(f"median {tag}", r.median_g_sql, r.median_g_pd)
    check(f"sd {tag}", r.sd_g_sql, r.sd_g_pd)
    check(f"NG {tag}", r.ng_count_sql, r.ng_count_pd, 0)

# c. Per sesi: Cpk dan fail count di ringkasan mesin vs hitung ulang
ps = push.groupby("session_id").agg(mean=("force_g", "mean"), sd=("force_g", lambda x: x.std(ddof=1)),
                                     fails=("force_g", lambda x: int((x < LSL_G).sum()))).reset_index()
ps["cpk"] = (ps["mean"] - LSL_G) / (3 * ps["sd"])
cmp = sess_db.merge(ps, on="session_id")
assert len(cmp) == n_sess_db, "sesi tidak cocok"
cpk_diff = (cmp.machine_cpk - cmp.cpk.round(2)).abs()
rows.append(dict(pemeriksaan="Cpk mesin vs hitung ulang (60 sesi, toleransi 0,01)",
                 nilai_sql_atau_mesin=int(len(cmp)), nilai_pandas=int(len(cmp)),
                 selisih=round(float(cpk_diff.max()), 9),
                 hasil="PASS" if (cpk_diff <= 0.01 + 1e-9).all() else "FAIL"))
fail_mismatch = int((cmp.fail_count != cmp.fails).sum())
rows.append(dict(pemeriksaan="fail count mesin vs hitung ulang (60 sesi)",
                 nilai_sql_atau_mesin=int(cmp.fail_count.sum()), nilai_pandas=int(cmp.fails.sum()),
                 selisih=fail_mismatch, hasil="PASS" if fail_mismatch == 0 else "FAIL"))

out = pd.DataFrame(rows)
out.to_csv(RES_ANA / "crosscheck.csv", index=False, encoding="utf-8")
print(f"{(out.hasil == 'PASS').sum()} PASS, {(out.hasil == 'FAIL').sum()} FAIL dari {len(out)} pemeriksaan")
if (out.hasil == "FAIL").any():
    raise SystemExit(out[out.hasil == "FAIL"].to_string())
