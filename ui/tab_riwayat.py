"""Tab Riwayat: tampilkan riwayat konsultasi dengan filter dan unduh ulang."""
from datetime import datetime

import pandas as pd
import streamlit as st

from config import DAFTAR_IKAN
from services.report import export_csv, export_pdf, export_txt


def _nama_gejala(kb, gid: str) -> str:
    """Mengambil nama gejala dengan aman baik dari atribut 'nama' maupun 'name'."""
    s = kb.symptoms.get(gid, {})
    return s.get("nama") or s.get("name") or gid


def render(kb, engine, history) -> None:
    st.subheader("Riwayat Konsultasi")
    
    # Filter Riwayat
    c1, c2, c3 = st.columns(3)
    pilih_ikan = c1.selectbox("Jenis ikan", ["Semua"] + list(DAFTAR_IKAN), key="rw_ikan")
    
    opsi_penyakit = ["Semua"] + [
        f"{pid} - {p.get('name') or p.get('nama') or pid}" 
        for pid, p in kb.diseases.items()
    ]
    pilih_penyakit = c2.selectbox("Penyakit", opsi_penyakit, key="rw_penyakit")
    pilih_tgl = c3.date_input("Tanggal", value=None, key="rw_tgl")

    # Ambil data riwayat
    ikan_filter = None if pilih_ikan == "Semua" else pilih_ikan
    penyakit_filter = None
    if pilih_penyakit != "Semua":
        penyakit_filter = pilih_penyakit.split(" - ")[0]

    records = history.filter(ikan=ikan_filter, penyakit=penyakit_filter, tanggal=pilih_tgl)
    if not records:
        st.info("Tidak ada riwayat konsultasi yang cocok dengan filter.")
        return

    st.caption(f"Menampilkan {len(records)} record (paling baru di atas).")
    
    # Tampilkan daftar riwayat secara terbalik (terbaru di atas)
    for rec in reversed(records):
        ts = rec.get("timestamp", "-")
        ikan_str = str(rec.get("ikan", "-")).capitalize()
        hasil = rec.get("hasil", [])
        
        label_hasil = hasil[0]["nama"] if hasil else "Tanpa diagnosis"
        with st.expander(f"[{ts}] {ikan_str} — {label_hasil}"):
            st.write(f"**Jenis Ikan:** {ikan_str}")
            st.write(f"**Waktu:** {ts}")
            
            # Tampilkan Gejala yang Dicentang
            st.markdown("**Gejala yang Diberikan:**")
            gejala_dict = rec.get("gejala", {})
            if gejala_dict:
                for gid, cf_user in gejala_dict.items():
                    st.write(f"- [{gid}] {_nama_gejala(kb, gid)} (CF User: {cf_user})")
            else:
                st.write("- Tidak ada gejala.")

            # Tampilkan Hasil Diagnosis
            st.markdown("**Hasil Diagnosis:**")
            if hasil:
                for h in hasil:
                    st.write(f"- **{h.get('nama', h.get('id'))}** — Kepastian: {float(h.get('cf', 0))*100:.0f}%")
                    if h.get("pengobatan"):
                        st.write(f"  *Pengobatan:* {h['pengobatan']}")
            else:
                st.write("Tidak terdiagnosa penyakit.")

            # Tombol Unduh Laporan Per Record
            st.markdown("---")
            dict_nama_gejala = {k: _nama_gejala(kb, k) for k in kb.symptoms}
            k1, k2, k3 = st.columns(3)
            rec_id = str(ts).replace(":", "-").replace(" ", "_")
            
            k1.download_button("Unduh TXT", export_txt(rec, dict_nama_gejala), f"diagnosis_{rec_id}.txt", "text/plain", key=f"dl_txt_{rec_id}")
            k2.download_button("Unduh CSV", export_csv(rec), f"diagnosis_{rec_id}.csv", "text/csv", key=f"dl_csv_{rec_id}")
            try:
                pdf_data = export_pdf(rec, dict_nama_gejala)
            except ModuleNotFoundError as exc:
                if exc.name != "fpdf":
                    raise
                k3.warning(
                    "Ekspor PDF belum tersedia. Instal dependensi proyek dengan "
                    "`python -m pip install -r requirements.txt`, lalu jalankan ulang aplikasi."
                )
            else:
                k3.download_button(
                    "Unduh PDF", pdf_data, f"diagnosis_{rec_id}.pdf", "application/pdf",
                    key=f"dl_pdf_{rec_id}",
                )
