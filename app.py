"""Entry point Streamlit. Hanya merakit tab; isi tiap tab ada di folder ui/."""
import streamlit as st

from config import DATA_DIR, HISTORY_PATH
from core.inference_engine import InferenceEngine
from core.knowledge_base import KnowledgeBase, KnowledgeBaseError
from services.history import HistoryService
from ui import theme, tab_database, tab_diagnosa, tab_kelola_rule, tab_riwayat, tab_statistik

st.set_page_config(page_title="Sistem Pakar Penyakit Ikan", page_icon="🐟", layout="wide")
theme.inject_css()

try:
    kb = KnowledgeBase(DATA_DIR)
except KnowledgeBaseError as e:
    st.error(f"Knowledge base gagal dimuat: {e}")
    st.stop()

# --- BAGIAN PERINGATAN SUDAH DIHAPUS / DISEMBUNYIKAN ---
# if kb.problems:
#     with st.expander(f"Peringatan knowledge base ({len(kb.problems)})"):
#         for p in kb.problems:
#             st.warning(p)
# -------------------------------------------------------

theme.hero(kb)
engine = InferenceEngine(kb.rules)
history = HistoryService(HISTORY_PATH)

NAMA_TAB = ["Diagnosa", "Database Penyakit", "Kelola Rule", "Riwayat", "Statistik"]
MODUL = [tab_diagnosa, tab_database, tab_kelola_rule, tab_riwayat, tab_statistik]

for tab, modul in zip(st.tabs(NAMA_TAB), MODUL):
    with tab:
        try:
            modul.render(kb, engine, history)
        except Exception as e:  # satu tab error tidak menjatuhkan tab lain
            st.error(f"Tab ini mengalami error: {e}")

st.caption("Hasil sistem adalah alat bantu awal, bukan pengganti ahli kesehatan ikan. "
           "Dosis pada rujukan berasal dari literatur; verifikasi ke penyuluh perikanan, BPBAT, atau dokter hewan ikan.")