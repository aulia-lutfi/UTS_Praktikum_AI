"""Tab Diagnosa: input gejala, hasil, CF, WHY, dan HOW."""
from datetime import datetime

import pandas as pd
import streamlit as st

from config import CF_MINIMUM, DAFTAR_IKAN, KEYAKINAN, KEYAKINAN_DEFAULT
from core.explanation import how, reasoning_graph, why

KUNCI_PILIHAN = "gejala_dipilih_v3"
KUNCI_HASIL = "hasil_diagnosa_v3"


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


def _form_gejala(kb, cari: str = "") -> None:
    pilihan = st.session_state.setdefault(KUNCI_PILIHAN, {})
    cari = cari.strip().lower()
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
            gejala_kategori = []
            for sid, s in kb.symptoms.items():
                s_nama = s.get("nama") or s.get("name") or sid
                s_kat = s.get("kategori") or s.get("category") or "Fisik"
                if s_kat != kategori or (cari and cari not in s_nama.lower()):
                    continue
                gejala_kategori.append((sid, s_nama))

            if not gejala_kategori:
                st.caption("Tidak ada gejala yang cocok.")
                continue

            # Pisahkan daftar menjadi dua kolom agar tab fisik tidak terlalu panjang.
            kolom_gejala = st.columns(2)
            for kolom, daftar_kolom in zip(kolom_gejala, (gejala_kategori[::2], gejala_kategori[1::2])):
                with kolom:
                    for sid, s_nama in daftar_kolom:
                        is_checked = sid in pilihan
                        st.checkbox(
                            f"[{sid}] {s_nama}",
                            value=is_checked,
                            key=f"chk_v3_{sid}",
                            on_change=_toggle,
                            args=(sid,),
                            help=why(sid, kb.rules),
                        )

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
                                label_visibility="collapsed",
                            )


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
                
                rujukan_list = penyakit.get("references") or penyakit.get("sumber") or []
                if rujukan_list:
                    st.markdown("**Referensi Jurnal & Sumber Resmi:**")
                    if isinstance(rujukan_list, list):
                        for ref in rujukan_list:
                            if isinstance(ref, dict):
                                st.markdown(f"• **{ref.get('title', 'Sumber')}** — [🔗 Buka Sumber Jurnal]({ref.get('url', '#')})")
                            else:
                                st.write(f"• {ref}")

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


def render(kb, engine, history) -> None:
    kolom_ikan, kolom_cari = st.columns([1, 2], gap="medium")
    with kolom_ikan:
        ikan = st.selectbox("Jenis ikan", DAFTAR_IKAN, index=None, placeholder="Pilih jenis ikan",
                            key="diag_ikan_v3")
    with kolom_cari:
        cari = st.text_input("Cari gejala", placeholder="mis. insang, nafsu makan",
                             key="diag_cari_input")
    _form_gejala(kb, cari)

    kol1, kol2 = st.columns([1, 5])
    if kol1.button("Diagnosa", type="primary", key="btn_diag_submit"):
        raw_pilihan = st.session_state.get(KUNCI_PILIHAN, {})
        fakta = {sid: KEYAKINAN[lbl] for sid, lbl in raw_pilihan.items() if lbl in KEYAKINAN}

        if ikan is None:
            st.warning("Pilih jenis ikan terlebih dahulu.")
        elif not fakta:
            st.warning("Pilih minimal satu gejala.")
        else:
            _jalankan(kb, engine, history, ikan, fakta)
    kol2.button("Reset", on_click=_reset, key="btn_diag_reset")

    _tampilkan_hasil(kb)
