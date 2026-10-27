"""Tab Kelola Rule: tambah, ubah, dan hapus rule (akuisisi pengetahuan)."""
import streamlit as st

from config import DAFTAR_IKAN


def _pesan() -> None:
    pesan = st.session_state.pop("kr_pesan", None)
    if pesan:
        st.success(pesan)


def _selesai(pesan: str) -> None:
    st.session_state["kr_pesan"] = pesan
    st.rerun()


def _opsi_premis(kb) -> list[str]:
    return [*kb.symptoms, *kb.intermediate_facts()]


def _fmt(kb):
    def f(x: str) -> str:
        if x in kb.symptoms:
            s_nama = kb.symptoms[x].get("nama") or kb.symptoms[x].get("name") or x
            return f"[{x}] {s_nama}"
        if x in kb.diseases:
            d_nama = kb.diseases[x].get("name") or kb.diseases[x].get("nama") or x
            return f"[{x}] {d_nama}"
        return f"[{x}] (Fakta Antara)"
    return f


def _tabel(kb) -> None:
    st.dataframe([{"ID": r["id"], "IF": " AND ".join(r["IF"]), "THEN": r["THEN"], "CF": r["CF"],
                   "Ikan": ", ".join(r.get("ikan", ["semua"]))} for r in kb.rules],
                 hide_index=True, use_container_width=True)


def _form_tambah(kb) -> None:
    st.subheader("Tambah rule")
    rid = st.text_input("ID rule", value=kb.next_rule_id(), key="kr_add_id")
    premis = st.multiselect("IF (semua premis harus terpenuhi)", _opsi_premis(kb),
                            format_func=_fmt(kb), key="kr_add_if")
    jenis = st.radio("THEN berupa", ["Penyakit", "Fakta antara"], horizontal=True, key="kr_add_jenis")
    if jenis == "Penyakit":
        then = st.selectbox("Penyakit", list(kb.diseases), format_func=_fmt(kb), key="kr_add_then_p")
    else:
        then = st.text_input("Nama fakta antara (mis. dugaan_infeksi_x)", key="kr_add_then_f").strip()
    cf = st.slider("CF rule", 0.05, 1.0, 0.7, 0.05, key="kr_add_cf")
    ikan = st.multiselect("Berlaku untuk ikan", DAFTAR_IKAN, default=DAFTAR_IKAN, key="kr_add_ikan")
    if st.button("Simpan rule baru", key="kr_add_btn"):
        rule = {"id": rid.strip(), "IF": premis, "THEN": then, "CF": cf, "ikan": ikan}
        err = kb.validate_rule(rule)
        if err:
            for e in err:
                st.error(e)
            return
        kb.add_rule(rule)
        kb.save()
        _selesai(f"Rule {rule['id']} ditambahkan.")


def _form_ubah(kb) -> None:
    st.subheader("Ubah rule")
    if not kb.rules:
        st.info("Belum ada rule.")
        return
    rid = st.selectbox("Pilih rule", [r["id"] for r in kb.rules], key="kr_edit_pilih")
    r = kb.get_rule(rid)
    k = f"kr_edit_{rid}"
    opsi = _opsi_premis(kb)
    premis = st.multiselect("IF", sorted(set(opsi) | set(r["IF"])), default=r["IF"],
                            format_func=_fmt(kb), key=f"{k}_if")
    then = st.text_input("THEN (ID penyakit atau fakta antara)", value=r["THEN"], key=f"{k}_then").strip()
    cf = st.slider("CF rule", 0.05, 1.0, float(r["CF"]), 0.05, key=f"{k}_cf")
    ikan = st.multiselect("Berlaku untuk ikan", DAFTAR_IKAN, default=r.get("ikan", DAFTAR_IKAN),
                          key=f"{k}_ikan")
    if st.button("Simpan perubahan", key=f"{k}_btn"):
        baru = {"id": rid, "IF": premis, "THEN": then, "CF": cf, "ikan": ikan}
        try:
            kb.update_rule(rid, baru)
        except ValueError as e:
            for pesan in str(e).split("; "):
                st.error(pesan)
            return
        kb.save()
        _selesai(f"Rule {rid} diperbarui.")


def _form_hapus(kb) -> None:
    st.subheader("Hapus rule")
    if not kb.rules:
        return
    rid = st.selectbox("Pilih rule", [r["id"] for r in kb.rules], key="kr_del_pilih")
    r = kb.get_rule(rid)
    bergantung = kb.rules_depending_on(r["THEN"])
    if bergantung:
        st.warning(f"Fakta '{r['THEN']}' dipakai sebagai premis oleh rule: {', '.join(bergantung)}.")
    yakin = st.checkbox(f"Saya yakin menghapus {rid}", key=f"kr_del_yakin_{rid}")
    if st.button("Hapus rule", disabled=not yakin, key="kr_del_btn"):
        kb.delete_rule(rid)
        kb.save()
        _selesai(f"Rule {rid} dihapus.")


def render(kb, engine, history) -> None:
    _pesan()
    st.write(f"Total rule: **{len(kb.rules)}**. Perubahan langsung disimpan ke file JSON.")
    _tabel(kb)
    tambah, ubah, hapus = st.tabs(["Tambah", "Ubah", "Hapus"])
    with tambah:
        _form_tambah(kb)
    with ubah:
        _form_ubah(kb)
    with hapus:
        _form_hapus(kb)