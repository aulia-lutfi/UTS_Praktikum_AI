"""Komponen UI bersama: detail penyakit lengkap dengan tautan rujukan."""
import html

import streamlit as st

LABEL_STATUS = {
    "dibaca": "isi dibaca tim",
    "ditemukan": "ditemukan di pencarian",
    "perlu_dicek": "perlu dicek anggota",
}


def _tautan(kb, ids) -> str:
    """Rangkaian tautan Markdown ke rujukan (hanya id yang dikenal)."""
    out = []
    for rid in ids or []:
        ref = kb.references.get(rid)
        if ref:
            out.append(f"[{ref['singkat']}]({ref['url']})")
    return " &middot; ".join(out)


def _baris(kb, item) -> str:
    """Satu butir pengetahuan -> teks Markdown + sumbernya."""
    teks = item["t"] if isinstance(item, dict) else str(item)
    if not isinstance(item, dict):
        return teks
    tail = ""
    if item.get("r"):
        tail += f" <span class='meta'>Sumber: {_tautan(kb, item['r'])}</span>"
    if item.get("praktik"):
        tail += " <span class='praktik'>praktik umum, perlu validasi pakar</span>"
    return teks + tail


def daftar(kb, items) -> None:
    """Tampilkan daftar butir sebagai bullet."""
    if items:
        st.markdown("\n".join(f"- {_baris(kb, it)}" for it in items), unsafe_allow_html=True)


def daftar_rujukan(kb, ids) -> None:
    """Daftar sitasi lengkap + lencana status verifikasi."""
    for rid in ids:
        ref = kb.references.get(rid)
        if not ref:
            continue
        st.markdown(
            f"<span class='ref {ref['status']}'>{LABEL_STATUS.get(ref['status'], ref['status'])}</span> "
            f"{html.escape(ref['sitasi'])} <a href='{ref['url']}' target='_blank' rel='noopener'>Buka sumber</a>"
            + (f"<br><span class='meta'>Catatan: {html.escape(ref['catatan'])}</span>" if ref.get("catatan") else ""),
            unsafe_allow_html=True)


def detail_penyakit(kb, pid: str, key: str = "") -> None:
    """Halaman rinci satu penyakit: gejala, konfirmasi, penanganan langkah demi langkah, rujukan."""
    p = kb.diseases[pid]
    d = p.get("detail")
    st.markdown(
        f"<span class='chip'>{html.escape(p.get('kategori', ''))}</span>"
        f"<span class='chip'><i>{html.escape(p.get('nama_ilmiah', ''))}</i></span>"
        + "".join(f"<span class='chip'>{i}</span>" for i in p.get("ikan_rentan", [])),
        unsafe_allow_html=True)
    if not d:
        st.write(f"**Penyebab:** {p.get('penyebab', '-')}")
        st.write(f"**Pengobatan:** {p.get('pengobatan', '-')}")
        st.write(f"**Pencegahan:** {p.get('pencegahan', '-')}")
        return
    st.write(d["ringkasan"])
    t_ringkas, t_gejala, t_tangani, t_cegah, t_rujuk = st.tabs(
        ["Penularan dan siklus", "Gejala dan konfirmasi", "Penanganan langkah demi langkah",
         "Pencegahan dan pembatasan", "Rujukan"])
    with t_ringkas:
        st.markdown("**Cara penularan**")
        daftar(kb, d.get("penularan"))
        if d.get("siklus"):
            st.markdown("**Daur hidup parasit**")
            daftar(kb, d["siklus"])
    with t_gejala:
        st.markdown("**Gejala klinis**")
        daftar(kb, d.get("gejala_klinis"))
        st.markdown("**Penyakit yang mirip**")
        daftar(kb, d.get("diagnosis_banding"))
        st.markdown("**Cara memastikan diagnosis**")
        daftar(kb, d.get("konfirmasi"))
    with t_tangani:
        for n, bagian in enumerate(d.get("penanganan", []), 1):
            with st.expander(f"{n}. {bagian['judul']}", expanded=(n == 1)):
                daftar(kb, bagian["langkah"])
        st.markdown("**Kapan harus memanggil ahli**")
        daftar(kb, d.get("kapan_ke_ahli"))
        for w in d.get("peringatan", []):
            st.warning(w)
    with t_cegah:
        st.markdown("**Pencegahan**")
        daftar(kb, d.get("pencegahan_rinci"))
        st.markdown("**Mencegah penyebaran ke ikan lain**")
        daftar(kb, d.get("cegah_penyebaran"))
    with t_rujuk:
        st.caption("Lencana hijau: isi sumber dibaca tim. Biru: ditemukan lewat pencarian, isi lengkap belum dibaca. "
                   "Kuning: berasal dari daftar pustaka awal dan wajib dibuka dan dicek anggota sebelum dikumpulkan.")
        daftar_rujukan(kb, p.get("sumber", []))
        semua = {r for b in d.get("penanganan", []) for it in b["langkah"] for r in it.get("r", [])}
        tambahan = [r for r in semua if r not in p.get("sumber", [])]
        if tambahan:
            st.markdown("**Rujukan tambahan yang dipakai pada langkah penanganan**")
            daftar_rujukan(kb, sorted(tambahan))
