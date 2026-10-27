"""03 - Menjalankan semua file SQL (code/2-analysis/sql/*.sql) untuk membuat view, lalu mengekspor ringkasan ke results/2-analysis/."""
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import DB_PATH, RES_ANA, SQL_DIR

con = duckdb.connect(str(DB_PATH))
for f in sorted(SQL_DIR.glob("*.sql")):
    con.execute(f.read_text(encoding="utf-8"))
    print("dijalankan:", f.name)

con.execute(f"COPY (SELECT * FROM v_group_summary) TO '{RES_ANA / 'group_summary.csv'}' (HEADER, DELIMITER ',')")
con.execute(f"COPY (SELECT * FROM v_session_summary) TO '{RES_ANA / 'session_summary.csv'}' (HEADER, DELIMITER ',')")
print(con.execute("SELECT model, condition, n, median_g, sd_g, ng_count FROM v_group_summary").df().to_string(index=False))
con.close()
