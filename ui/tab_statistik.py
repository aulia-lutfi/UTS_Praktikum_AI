"""Tab Statistik: ringkasan penggunaan sistem."""
import pandas as pd
import streamlit as st

from services.stats import statistik


def _bar(judul: str, pasangan: list, kolom: str) -> None:
    st.subheader(judul)
    if not pasangan:
        st.caption("Belum ada data.")
        return
    df = pd.DataFrame(pasangan[:10], columns=[kolom, "Jumlah"]).set_index(kolom)
    st.bar_chart(df)


def render(kb, engine, history) -> None:
    s = statistik(history.all())
    if s["total_konsultasi"] == 0:
        st.info("Belum ada data konsultasi untuk dihitung.")
        return
    a, b, c = st.columns(3)
    a.metric("Total konsultasi", s["total_konsultasi"])
    b.metric("Tanpa diagnosis", s["tanpa_diagnosis"])
    c.metric("Penyakit terbanyak",
             s["penyakit_terbanyak"][0][0] if s["penyakit_terbanyak"] else "-")
    _bar("Penyakit paling sering terdiagnosa", s["penyakit_terbanyak"], "Penyakit")
    _bar("Rule paling sering dipakai", s["rule_terbanyak"], "Rule")
    _bar("Jenis ikan yang dikonsultasikan", s["ikan_terbanyak"], "Ikan")
