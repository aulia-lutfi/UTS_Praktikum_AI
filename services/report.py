"""Export hasil konsultasi ke TXT, CSV, dan PDF."""
import csv
import io


def _nama_gejala(sid: str, nama_gejala: dict | None) -> str:
    return f"{sid} - {nama_gejala[sid]}" if nama_gejala and sid in nama_gejala else sid


def export_txt(record: dict, nama_gejala: dict | None = None, refs: dict | None = None) -> str:
    """Laporan teks. `nama_gejala` (opsional): {id: nama} agar gejala terbaca."""
    baris = [
        "LAPORAN DIAGNOSIS - SISTEM PAKAR PENYAKIT IKAN AIR TAWAR",
        "=" * 56,
        f"Waktu      : {record.get('timestamp', '-')}",
        f"Jenis ikan : {record.get('ikan', '-')}",
        "",
        "Gejala (CF input):",
    ]
    for sid, cf in record.get("gejala", {}).items():
        baris.append(f"  - {_nama_gejala(sid, nama_gejala)}: {cf}")
    baris.append("")
    hasil = record.get("hasil", [])
    if not hasil:
        baris.append("Hasil: tidak ada diagnosis pasti dari gejala yang dimasukkan.")
    for i, h in enumerate(hasil, 1):
        baris.append(f"{i}. {h.get('nama', h.get('id'))}  (kepercayaan {h.get('cf', 0) * 100:.0f}%)")
        if h.get("pengobatan"):
            baris.append(f"   Pengobatan : {h['pengobatan']}")
        if h.get("pencegahan"):
            baris.append(f"   Pencegahan : {h['pencegahan']}")
    if refs:
        baris += ["", "Rujukan (buka tautan untuk membaca sumber):"]
        for rid in sorted({r for h in hasil for r in h.get("sumber_ids", [])}):
            if rid in refs:
                baris.append(f"  - {refs[rid]['singkat']}: {refs[rid]['url']}")
    baris += ["", f"Rule dipakai: {', '.join(record.get('rules_dipakai', [])) or '-'}",
              "", "Catatan: hasil ini alat bantu awal, bukan pengganti ahli kesehatan ikan."]
    return "\n".join(baris)


def export_csv(record: dict) -> str:
    """CSV: satu baris per penyakit hasil diagnosis."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["timestamp", "ikan", "penyakit_id", "penyakit", "cf_persen", "gejala", "rules_dipakai"])
    gejala = "; ".join(f"{k}:{v}" for k, v in record.get("gejala", {}).items())
    rules = "; ".join(record.get("rules_dipakai", []))
    hasil = record.get("hasil", []) or [{"id": "", "nama": "(tidak ada diagnosis)", "cf": 0}]
    for h in hasil:
        w.writerow([record.get("timestamp", ""), record.get("ikan", ""), h.get("id", ""),
                    h.get("nama", ""), round(h.get("cf", 0) * 100, 1), gejala, rules])
    return buf.getvalue()


def export_pdf(record: dict, nama_gejala: dict | None = None, refs: dict | None = None) -> bytes:
    """Laporan PDF (fpdf2, font bawaan Helvetica -> karakter dibatasi Latin-1)."""
    from fpdf import FPDF

    def bersih(teks) -> str:
        return str(teks).encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def tulis(teks, ukuran=11, gaya=""):
        pdf.set_font("Helvetica", gaya, ukuran)
        pdf.multi_cell(0, 6, bersih(teks), new_x="LMARGIN", new_y="NEXT")

    tulis("Laporan Diagnosis Penyakit Ikan Air Tawar", 15, "B")
    pdf.ln(2)
    tulis(f"Waktu: {record.get('timestamp', '-')}")
    tulis(f"Jenis ikan: {record.get('ikan', '-')}")
    pdf.ln(2)
    tulis("Gejala (CF input)", 12, "B")
    for sid, cf in record.get("gejala", {}).items():
        tulis(f"- {_nama_gejala(sid, nama_gejala)}: {cf}")
    pdf.ln(2)
    tulis("Hasil diagnosis", 12, "B")
    hasil = record.get("hasil", [])
    if not hasil:
        tulis("Tidak ada diagnosis pasti dari gejala yang dimasukkan.")
    for i, h in enumerate(hasil, 1):
        tulis(f"{i}. {h.get('nama', h.get('id'))} - kepercayaan {h.get('cf', 0) * 100:.0f}%", 11, "B")
        if h.get("pengobatan"):
            tulis(f"Pengobatan: {h['pengobatan']}")
        if h.get("pencegahan"):
            tulis(f"Pencegahan: {h['pencegahan']}")
    if refs:
        pdf.ln(2)
        tulis("Rujukan", 12, "B")
        for rid in sorted({r for h in hasil for r in h.get("sumber_ids", [])}):
            if rid in refs:
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(0, 5, bersih(f"- {refs[rid]['singkat']}: {refs[rid]['url']}"),
                               new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    tulis(f"Rule dipakai: {', '.join(record.get('rules_dipakai', [])) or '-'}")
    pdf.ln(2)
    tulis("Catatan: hasil ini alat bantu awal, bukan pengganti ahli kesehatan ikan.", 9, "I")
    return bytes(pdf.output())
