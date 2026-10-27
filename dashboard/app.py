"""Dashboard Project 12 (Streamlit). Membaca outputs/*.csv. DATA SIMULASI.
Jalankan dari root repo: streamlit run dashboard/app.py
"""
import pathlib
import pandas as pd
import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
COND = {"before_oven": "Sebelum oven", "after_oven": "Setelah oven 1 jam", "after_baked": "Setelah baked"}

st.set_page_config(page_title="Project 12: Glue push test", layout="wide")
st.warning("DATA SIMULASI. Angka meniru format mesin push test, bukan lini produksi.")
grp = pd.read_csv(OUT / "group_summary.csv")
cap = pd.read_csv(OUT / "capability.csv")
rec = pd.read_csv(OUT / "recommendation.csv")
tests = pd.read_csv(OUT / "test_results.csv")
sens = pd.read_csv(OUT / "sensitivity.csv")

page = st.sidebar.radio("Halaman", ["Ringkasan", "Kondisi proses", "Kapabilitas dan NG", "Validasi"])

if page == "Ringkasan":
    st.title("Kondisi proses mana yang paling kuat?")
    q1 = tests[(tests.pertanyaan == "Q1") & (tests.uji == "Welch t (unit)") & (tests.perbandingan == "Setelah oven vs Sebelum oven")].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Efek oven (median selisih, g)", f"{q1.selisih_g:,.0f}".replace(",", "."))
    c2.metric("CI 95% (g)", f"{q1.ci_bawah_g:,.0f} s.d. {q1.ci_atas_g:,.0f}".replace(",", "."))
    c3.metric("Rekomendasi", "Setelah oven 1 jam")
    st.write("Gunakan **setelah oven 1 jam** untuk kedua model. Verifikasi dengan data lini nyata sebelum diterapkan.")
    st.dataframe(rec, width="stretch", hide_index=True)

elif page == "Kondisi proses":
    st.title("Median gaya lepas per kondisi")
    p = cap.copy(); p["kondisi"] = p.condition.map(COND)
    st.bar_chart(p, x="kondisi", y="median_g", color="model", horizontal=False)
    st.dataframe(grp, width="stretch", hide_index=True)

elif page == "Kapabilitas dan NG":
    st.title("Kapabilitas (Cpk) dan fail rate")
    st.dataframe(cap, width="stretch", hide_index=True)
    st.caption("Target Cpk 1,33. Batas bawah 2.000 g. Cpk Model A sebelum oven ditarik satu sesi (S037).")

else:
    st.title("Validasi terhadap fakta yang ditanam")
    gt = pd.read_csv(OUT / "ground_truth_check.csv")
    st.dataframe(gt, width="stretch", hide_index=True)
    st.subheader("Sensitivitas batas praktis")
    st.dataframe(sens, width="stretch", hide_index=True)
