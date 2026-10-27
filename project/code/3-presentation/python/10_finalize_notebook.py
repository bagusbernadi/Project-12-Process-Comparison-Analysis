# Membersihkan metadata waktu eksekusi notebook (nbconvert) agar hasil byte-identik antar jalan.
import sys, pathlib, nbformat
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from common import RES_PRES
p = RES_PRES / "analysis.ipynb"
nb = nbformat.read(p, as_version=4)
for c in nb.cells:
    c.get("metadata", {}).pop("execution", None)
nbformat.write(nb, p)
print("notebook dibersihkan:", p.name)
