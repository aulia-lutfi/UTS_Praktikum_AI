"""Tab Diagnosa: input gejala, hasil, CF, WHY, dan HOW."""
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from config import CF_MINIMUM, DAFTAR_IKAN, KEYAKINAN, KEYAKINAN_DEFAULT
from core.explanation import how, reasoning_graph, why

KUNCI_PILIHAN = "gejala_dipilih_v3"
KUNCI_HASIL = "hasil_diagnosa_v3"


def _tampilkan_referensi(referensi: list, prefix: str = "diag"):
    """Helper untuk menampilkan referensi dengan tombol PDF atau Link Web."""
    if not referensi:
        return
    st.markdown("**Referensi Jurnal & Sumber Resmi:**")
    for i, ref in enumerate(referensi):
        if isinstance(ref, dict):
            judul = ref.get('title', 'Sumber')
            url = ref.get('url', '#')
            
            if url.endswith(".pdf"):
                if os.path.exists(url):
                    with open(url, "rb") as f:
                        st.download_button(
                            label=f"📄 Unduh PDF: {judul}",
                            data=f,
                            file_name=os.path.basename(url),
                            mime="application/pdf",
                            key=f"{prefix}_pdf_{i}_{url}"
                        )
                else:
                    st.warning(f"⚠️ File PDF tidak ditemukan: {url}")
            elif url.startswith("http"):
                st.link_button(f"🔗 Buka Sumber: {judul}", url=url)
            else:
                st.write(f"• {judul} ({url})")
        else:
            st.write(f"• {ref}")


def _toggle(sid: str) -> None:
    pilihan = st.session_state.setdefault(KUNCI_PILIHAN, {})
    if st.session_state.get(f"chk_v3_{sid}"):
        pilihan.setdefault(sid, KEYAKINAN_DEFAULT)
    else:
        pilihan.pop(sid, None)
        st.session_state.pop(f"select_v3_{sid}", None)


def _set_level(sid: str) -> None:
    st.session_state.setdefault(KUNCI_PILIHAN, {})[sid] = st.session_state[f"select_v3_{sid}"]


def _reset() -> None:
    st.session_state[KUNCI_PILIHAN] = {}
    st.session_state.pop(KUNCI_HASIL, None)
    for k in list(st.session_state.keys()):
        if str(k).startswith(("chk_v3_", "select_v3_")):
            del st.session_state[k]


def _form_gejala(kb) -> None:
    pilihan = st.session_state.setdefault(KUNCI_PILIHAN, {})
    cari = st.text_input("Cari gejala", placeholder="mis. insang, nafsu makan", key="diag_cari_input").strip().lower()
    if pilihan:
        st.caption(f"{len(pilihan)} gejala dipilih.")
    
    labels = list(KEYAKINAN.keys()) if isinstance(KEYAKINAN, dict) else list(KEYAKINAN)
    
    tab_fisik, tab_perilaku = st.tabs(["📌 Pengamatan Fisik", "🐟 Perubahan Perilaku"])
    
    kategori_map = {
        "Fisik": tab_fisik,
        "Perilaku": tab_perilaku
    }

    for kategori, tab_obj in kategori_map.items():
        with tab_obj:
            st.caption(f"Centang gejala {kategori.lower()} untuk memilih tingkat keyakinan pengamatan Anda:")
            ada = False
            for sid, s in kb.symptoms.items():
                s_nama = s.get("nama") or s.get("name") or sid
                s_kat = s.get("kategori") or s.get("category") or "Fisik"
                
                if s_kat != kategori or (cari and cari not in s_nama.lower()):
                    continue
                ada = True
                kol1, kol2 = st.columns([3, 1.5])
                
                is_checked = sid in pilihan
                
                kol1.checkbox(
                    f"[{sid}] {s_nama}", 
                    value=is_checked, 
                    key=f"chk_v3_{sid}",
                    on_change=_toggle, 
                    args=(sid,), 
                    help=why(sid, kb.rules)
                )
                
                with kol2:
                    if is_checked:
                        current_val = pilihan.get(sid, KEYAKINAN_DEFAULT)
                        current_idx = labels.index(current_val) if current_val in labels else labels.index(KEYAKINAN_DEFAULT)
                        
                        st.selectbox(
                            "Tingkat Keyakinan", 
                            options=labels, 
                            index=current_idx,
                            key=f"select_v3_{sid}", 
                            on_change=_set_level, 
                            args=(sid,),
                            label_visibility="collapsed"
                        )
                        
            if not ada:
                st.caption("Tidak ada gejala yang cocok.")


def _jalankan(kb, engine, history, ikan: str, fakta: dict) -> None:
    wm = engine.forward_chain(fakta, ikan)
    diagnosis = engine.get_diagnoses(wm, list(kb.diseases))
    
    hasil_list = []
    for d, cf in diagnosis:
        dis = kb.diseases.get(d, {})
        d_nama = dis.get("name") or dis.get("nama") or d
        d_treat = dis.get("treatments") or dis.get("pengobatan") or []
        if isinstance(d_treat, list):
            d_treat_str = "; ".join(d_treat)
        else:
            d_treat_str = str(d_treat)
            
        d_prev = dis.get("prevention") or dis.get("pencegahan") or ""
        
        hasil_list.append({
            "id": d,
            "nama": d_nama,
            "cf": round(cf, 3),
            "pengobatan": d_treat_str,
            "pencegahan": d_prev
        })

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "ikan": ikan,
        "gejala": fakta,
        "hasil": hasil_list,
        "rules_dipakai": wm.rules_used(),
    }
    
    labels = {}
    for k, v in kb.symptoms.items():
        labels[k] = v.get("nama") or v.get("name") or k
    for k, v in kb.diseases.items():
        labels[k] = v.get("name") or v.get("nama") or k

    st.session_state[KUNCI_HASIL] = {
        "record": record,
        "trace": list(wm.trace),
        "how": {d: how(d, wm, kb.rules) for d, _ in diagnosis},
        "graph": {d: reasoning_graph(d, wm, kb.rules, labels) for d, _ in diagnosis},
    }
    try:
        history.save(record)
    except OSError as e:
        st.warning(f"Riwayat tidak dapat disimpan: {e}")


def _tampilkan_hasil(kb) -> None:
    data = st.session_state.get(KUNCI_HASIL)
    if not data:
        return
    record = data["record"]
    st.divider()
    st.header("Hasil diagnosis")
    hasil = record["hasil"]
    if not hasil:
        st.info("Tidak ada diagnosis pasti dari gejala yang dipilih. Tambahkan gejala lain "
                "atau konsultasikan dengan ahli kesehatan ikan.")
    else:
        utama = hasil[0]
        st.success(f"Ikan Anda kemungkinan terkena **{utama['nama']} ({str(record['ikan']).capitalize()})** "
                   f"(kepercayaan {utama['cf'] * 100:.0f}%)")
        
        for i, h in enumerate(hasil, 1):
            with st.container(border=True):
                kol1, kol2 = st.columns([3, 1])
                kol1.subheader(f"{i}. {h['nama']} ({str(record['ikan']).capitalize()})")
                kol2.metric("Kepercayaan", f"{h['cf'] * 100:.0f}%")
                st.progress(min(max(h["cf"], 0.0), 1.0))
                
                if h["cf"] < CF_MINIMUM:
                    st.caption("Keyakinan rendah: anggap sebagai dugaan awal saja.")
                
                penyakit = kb.diseases.get(h["id"], {})
                desc = penyakit.get("symptoms_desc") or penyakit.get("penyebab")
                if desc:
                    st.write(f"**Penyebab / Gejala Utama:** {desc}")
                st.write(f"**Rekomendasi pengobatan:** {h['pengobatan']}")
                st.write(f"**Pencegahan penyebaran:** {h['pencegahan']}")
                
                # Panggil fungsi referensi di sini
                rujukan_list = penyakit.get("references") or penyakit.get("sumber") or []
                _tampilkan_referensi(rujukan_list, prefix=f"diag_{h['id']}")

                with st.expander("Bagaimana kesimpulan ini didapat? (HOW)", expanded=True):
                    for n, baris in enumerate(data["how"].get(h["id"], []), 1):
                        st.write(f"{n}. {baris}")
                    g_chart = data["graph"].get(h["id"])
                    if g_chart:
                        st.graphviz_chart(g_chart)

    with st.expander("Jejak forward chaining (trace)"):
        if data["trace"]:
            df = pd.DataFrame(data["trace"])
            if "IF" in df.columns:
                df["IF"] = df["IF"].apply(lambda x: " AND ".join(x) if isinstance(x, list) else str(x))
            st.dataframe(df, hide_index=True)
        else:
            st.write("Tidak ada rule yang dieksekusi.")

def _render_backward_chaining(kb, engine, ikan, fakta):
    """Menampilkan UI untuk Backward Chaining (Goal-Driven)."""
    st.markdown("---")
    st.subheader("🎯 Uji Hipotesis (Backward Chaining)")
    st.caption("Pilih penyakit yang ingin diuji. Sistem akan menelusuri mundur (Goal-Driven) untuk membuktikan apakah gejala yang ada cukup, dan memberi tahu gejala apa yang kurang.")
    
    # Pilih penyakit sebagai Goal
    opsi_penyakit = {pid: f"{pid} - {p.get('name', p.get('nama', pid))}" for pid, p in kb.diseases.items()}
    goal = st.selectbox("Pilih Hipotesis Penyakit:", options=list(opsi_penyakit.keys()), format_func=lambda x: opsi_penyakit[x], key="bc_goal")
    
    if st.button("Uji Hipotesis", type="secondary", key="btn_bc"):
        if not fakta:
            st.warning("Pilih minimal satu gejala di atas terlebih dahulu untuk diuji.")
            return
            
        # Panggil fungsi backward_chain dari inference_engine.py
        hasil = engine.backward_chain(goal, fakta, ikan)
        
        st.markdown(f"### Hasil Uji: **{opsi_penyakit[goal]}**")
        
        if hasil["terbukti"]:
            st.success(f"✅ **Hipotesis Terbukti!** Gejala yang Anda berikan cukup untuk mendiagnosis **{opsi_penyakit[goal]}** dengan tingkat kepercayaan **{hasil['cf']*100:.1f}%**.")
        else:
            st.error("❌ **Hipotesis Belum Terbukti.** Gejala yang Anda berikan belum cukup untuk menyimpulkan penyakit ini.")
            
        with st.expander("Lihat Alur Penalaran (Reasoning Trace)", expanded=True):
            for baris in hasil["trace"]:
                st.code(baris, language="text")
                
        if hasil["kurang"]:
            st.warning("**Gejala yang masih kurang (perlu ditanyakan/diperiksa):**")
            for rule_id, gejala_kurang in hasil["kurang"].items():
                nama_gejala = [kb.symptoms.get(g, {}).get("nama", g) for g in gejala_kurang]
                st.write(f"- Rule **{rule_id}** membutuhkan: {', '.join(nama_gejala)}")


def render(kb, engine, history) -> None:
    ikan = st.selectbox("Jenis ikan", DAFTAR_IKAN, index=None, placeholder="Pilih jenis ikan", key="diag_ikan_v3")
    _form_gejala(kb)

    kol1, kol2 = st.columns([1, 5])
    if kol1.button("Diagnosa (Forward Chaining)", type="primary", key="btn_diag_submit"):
        raw_pilihan = st.session_state.get(KUNCI_PILIHAN, {})
        fakta = {sid: KEYAKINAN[lbl] for sid, lbl in raw_pilihan.items() if lbl in KEYAKINAN}

        if ikan is None:
            st.warning("Pilih jenis ikan terlebih dahulu.")
        elif not fakta:
            st.warning("Pilih minimal satu gejala.")
        else:
            _jalankan(kb, engine, history, ikan, fakta)
            
    kol2.button("Reset", on_click=_reset, key="btn_diag_reset")

    # --- LOGIKA TAMPILAN HASIL ---
    raw_pilihan = st.session_state.get(KUNCI_PILIHAN, {})
    fakta_saat_ini = {sid: KEYAKINAN[lbl] for sid, lbl in raw_pilihan.items() if lbl in KEYAKINAN}

    # Jika ada gejala yang dipilih dan jenis ikan sudah dipilih, tampilkan Tab
    if fakta_saat_ini and ikan:
        tab_hasil, tab_uji = st.tabs(["📋 Hasil Diagnosis (Forward)", "🎯 Uji Hipotesis (Backward)"])
        
        with tab_hasil:
            _tampilkan_hasil(kb)      # <-- HANYA DIPANGGIL SEKALI DI SINI
            
        with tab_uji:
            _render_backward_chaining(kb, engine, ikan, fakta_saat_ini)
    else:
        # Jika belum ada gejala/ikan, tampilkan pesan kosong
        st.info("Silakan pilih jenis ikan dan gejala, lalu klik 'Diagnosa' untuk melihat hasil.")