"""Tab Database Penyakit: telusuri penyakit, gejala terkait, dan rule-nya."""
import os
import streamlit as st


def _tampilkan_referensi(referensi: list):
    """Helper untuk menampilkan referensi dengan tombol PDF atau Link Web."""
    if not referensi:
        return
    st.markdown("**Sumber Rujukan / Jurnal:**")
    for i, ref in enumerate(referensi):
        if isinstance(ref, dict):
            judul = ref.get('title', 'Sumber')
            url = ref.get('url', '#')
            
            # Jika file PDF lokal
            if url.endswith(".pdf"):
                if os.path.exists(url):
                    with open(url, "rb") as f:
                        st.download_button(
                            label=f"📄 Unduh PDF: {judul}",
                            data=f,
                            file_name=os.path.basename(url),
                            mime="application/pdf",
                            key=f"db_pdf_{i}_{url}"
                        )
                else:
                    st.warning(f"⚠️ File PDF tidak ditemukan: {url}")
            # Jika Link Web
            elif url.startswith("http"):
                st.link_button(f"🔗 Buka Sumber: {judul}", url=url)
            else:
                st.write(f"• {judul} ({url})")
        else:
            st.write(f"• {ref}")


def render(kb, engine, history) -> None:
    st.write(f"Knowledge base berisi **{len(kb.diseases)} penyakit**, "
             f"**{len(kb.symptoms)} gejala**, dan **{len(kb.rules)} rule**.")
    cari = st.text_input("🔍 Cari penyakit atau gejala...", key="db_cari").strip().lower()

    st.subheader("Daftar Penyakit Terdaftar")
    ditemukan = 0
    for pid, p in kb.diseases.items():
        # Menyesuaikan pembacaan skema lama maupun skema baru
        nama = p.get("name") or p.get("nama") or pid
        spesies = p.get("species") or p.get("ikan_rentan") or []
        gejala_desc = p.get("symptoms_desc") or p.get("penyebab") or "-"
        pengobatan = p.get("treatments") or [p.get("pengobatan", "-")]
        pencegahan = p.get("prevention") or p.get("pencegahan") or "-"
        referensi = p.get("references") or []

        gejala_terkait = kb.related_symptoms(pid)
        teks_cari = f"{pid} {nama} {gejala_desc} {' '.join(spesies)}".lower()
        
        if cari and cari not in teks_cari:
            continue
            
        ditemukan += 1
        with st.expander(f"[{pid}] {nama}"):
            if spesies:
                st.write(f"**Komoditas Target:** {', '.join(spesies)}")
            st.write(f"**Gejala Utama / Indikasi:** {gejala_desc}")
            
            st.markdown("**Prosedur Pengobatan & Penanganan:**")
            if isinstance(pengobatan, list):
                for t in pengobatan:
                    st.write(f"- {t}")
            else:
                st.write(f"- {pengobatan}")

            st.write(f"**Pencegahan:** {pencegahan}")
            
            if gejala_terkait:
                nama_gejala = [kb.symptoms[g]["nama"] for g in gejala_terkait if g in kb.symptoms]
                st.write("**Gejala Terkait (Rule Base):** " + (", ".join(nama_gejala) or "-"))

            rule_terkait = [r for r in kb.rules if r["THEN"] == pid]
            if rule_terkait:
                st.write("**Rule yang Menyimpulkan Penyakit Ini:**")
                for r in rule_terkait:
                    st.code(f"{r['id']}: IF {' AND '.join(r['IF'])} THEN {r['THEN']} "
                            f"(CF {r['CF']}; ikan: {', '.join(r.get('ikan', ['semua']))})")
            
            # Panggil fungsi referensi
            _tampilkan_referensi(referensi)

    if not ditemukan:
        st.info("Tidak ada penyakit yang cocok dengan kata kunci pencarian.")

    st.markdown("---")
    st.subheader("Daftar Gejala Terdaftar")
    baris = [{"ID": sid, "Gejala": s.get("nama", s.get("name", sid)), "Kategori": s.get("kategori", "-"),
              "Dipakai Rule": ", ".join(r["id"] for r in kb.rules if sid in r["IF"])}
             for sid, s in kb.symptoms.items()
             if not cari or cari in s.get("nama", "").lower()]
    st.dataframe(baris, hide_index=True, use_container_width=True)