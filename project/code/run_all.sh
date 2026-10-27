#!/bin/sh
# Jalankan dari root repo: sh project/code/run_all.sh
# Urutan = urutan eksekusi (ketergantungan data). Untuk uji dari nol, hapus dulu:
#   rm -f project/pushtest.duckdb; rm -rf project/data/raw/machine_files project/results/*/
set -e
PY="python3 -I"
$PY project/code/1-data-preparation/python/01_generate_machine_files.py
$PY project/code/1-data-preparation/python/02_parse_load.py
$PY project/code/2-analysis/python/03_sql_views.py
$PY project/code/2-analysis/python/04_crosscheck.py
$PY project/code/2-analysis/python/05_stats.py
$PY project/code/2-analysis/python/06_capability.py
$PY project/code/2-analysis/python/07_recommend_validate.py
$PY project/code/3-presentation/python/08_one_sheet.py
python3 project/code/3-presentation/python/09_build_notebook.py
(cd project/results/3-presentation && python3 -m nbconvert --to notebook --execute --inplace analysis.ipynb --ExecutePreprocessor.timeout=900 >/dev/null 2>&1)
$PY project/code/3-presentation/python/10_finalize_notebook.py
$PY project/code/3-presentation/python/11_build_readme.py
$PY design-and-report/src/build_report.py
