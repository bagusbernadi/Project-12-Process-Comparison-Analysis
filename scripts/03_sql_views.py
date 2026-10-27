"""03 - Menjalankan semua file SQL (sql/*.sql) untuk membuat view, lalu mengekspor ringkasan ke outputs/."""
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DB_PATH, OUT_DIR, SQL_DIR

con = duckdb.connect(str(DB_PATH))
for f in sorted(SQL_DIR.glob("*.sql")):
    con.execute(f.read_text(encoding="utf-8"))
    print("dijalankan:", f.name)

con.execute(f"COPY (SELECT * FROM v_group_summary) TO '{OUT_DIR / 'group_summary.csv'}' (HEADER, DELIMITER ',')")
con.execute(f"COPY (SELECT * FROM v_session_summary) TO '{OUT_DIR / 'session_summary.csv'}' (HEADER, DELIMITER ',')")
print(con.execute("SELECT model, condition, n, median_g, sd_g, ng_count FROM v_group_summary").df().to_string(index=False))
con.close()
