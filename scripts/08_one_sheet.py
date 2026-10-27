# One-sheet infografik P12 (PNG dan PDF) dari outputs/*.csv. Data simulasi. Jalankan dari root repo.
import pathlib, textwrap, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
cap = pd.read_csv(OUT / "capability.csv")
rec = pd.read_csv(OUT / "recommendation.csv")
t = pd.read_csv(OUT / "test_results.csv")
sens = pd.read_csv(OUT / "sensitivity.csv")
cpk_note = sens[sens.uji == "Kapabilitas Model A, Sebelum oven"].keputusan.iloc[0]  # "Cpk 1.46 dengan outlier; 1.93 tanpa"
q1 = t[(t.pertanyaan == "Q1") & (t.uji == "Welch t (unit)") & (t.perbandingan == "Setelah oven vs Sebelum oven")].iloc[0]
fmt = lambda v, d=0: f"{float(v):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

fig = plt.figure(figsize=(11, 8.5), dpi=150)
fig.text(0.05, 0.93, "Glue push test: kondisi proses mana yang paling kuat?", fontsize=22, weight="bold", color="#174EA6")
fig.text(0.05, 0.895, "Project 12 · DATA SIMULASI yang meniru format mesin push test (60 file, 600 cover glass)", fontsize=12, color="#5F6368")

# Grafik median per kondisi
ax = fig.add_axes([0.08, 0.14, 0.52, 0.66])
conds = ["before_oven", "after_oven", "after_baked"]
labels = ["Sebelum oven", "Setelah oven 1 jam", "Setelah baked"]
x = range(3); w = 0.38
for i, (m, col) in enumerate([("Model A", "#1A73E8"), ("Model B", "#E8710A")]):
    vals = [float(cap[(cap.model == m) & (cap.condition == c)].median_g.iloc[0]) for c in conds]
    bars = ax.bar([p + (i - 0.5) * w for p in x], vals, w, color=col, label=m)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 60, fmt(v), ha="center", fontsize=9)
ax.axhline(2000, color="#D93025", ls="--", lw=1); ax.text(-0.45, 2120, "batas bawah 2.000 g", color="#D93025", fontsize=8, ha="left", bbox=dict(facecolor="white", edgecolor="none", pad=1))
ax.set_xticks(list(x)); ax.set_xticklabels(labels); ax.set_ylabel("median gaya lepas (g)")
ax.set_ylim(0, 9000); ax.legend(frameon=False, loc="upper left")
ax.set_title("Median gaya lepas per kondisi dan model", fontsize=10, loc="left")
ax.spines[["top", "right"]].set_visible(False)

# Kartu kanan
ax2 = fig.add_axes([0.66, 0.14, 0.31, 0.66]); ax2.axis("off")
rA = rec[rec.model == "Model A"].iloc[0]; rB = rec[rec.model == "Model B"].iloc[0]
txt = (
    "Rekomendasi\n\n"
    f"Gunakan setelah oven 1 jam untuk kedua model.\n\n"
    f"Efek oven: +{fmt(q1.selisih_g)} g (CI 95% {fmt(q1.ci_bawah_g)} s.d. {fmt(q1.ci_atas_g)} g, p < 0,001).\n\n"
    f"Selisih median setelah oven 1 jam vs sebelum oven:\n"
    f"• Model A: +{fmt(rA.selisih_median_g)} g\n"
    f"• Model B: +{fmt(rB.selisih_median_g)} g\n\n"
    f"Cpk sebelum oven Model A: {cpk_note.replace('.', ',')} (sesi S037 menarik Cpk).\n\n"
    "Interaksi model x oven tidak terdeteksi (daya kurang; lihat 7.6 di report)."
)
txt = "\n".join(textwrap.fill(line, 40) if line else "" for line in txt.split("\n"))
ax2.text(0, 1, txt, va="top", fontsize=10.5, color="#202124")
fig.text(0.05, 0.05, "Data simulasi. Angka dari outputs/*.csv. Parameter ground truth hanya dipakai skrip validasi (07).", fontsize=8.5, color="#5F6368")
png, pdf = OUT / "one_sheet.png", OUT / "one_sheet.pdf"
fig.savefig(png, metadata={"Software": "matplotlib"}); fig.savefig(pdf, metadata={"CreationDate": None, "Creator": "matplotlib"})
print("ditulis:", png.name, pdf.name)
