"""Penyimpanan riwayat konsultasi ke file JSON."""
import json
import os
from datetime import date, datetime
from pathlib import Path


class HistoryService:
    """Menyimpan dan menyaring record konsultasi (format record: lihat README Bagian 2.2)."""

    def __init__(self, path: str):
        self.path = Path(path)

    def all(self) -> list[dict]:
        """Semua record, urut dari yang terlama. File belum ada -> daftar kosong."""
        if not self.path.exists():
            return []
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("isi bukan daftar")
            return data
        except (json.JSONDecodeError, ValueError, OSError):
            # File rusak: simpan salinannya agar tidak hilang, lalu mulai dari kosong.
            try:
                os.replace(self.path, self.path.with_suffix(".json.corrupt"))
            except OSError:
                pass
            return []

    def save(self, record: dict) -> None:
        """Tambahkan satu record (penulisan atomik)."""
        data = self.all()
        data.append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)

    def filter(self, ikan=None, penyakit=None, tanggal=None) -> list[dict]:
        """Saring riwayat.

        ikan     : nama ikan persis (mis. "lele")
        penyakit : ID atau potongan nama penyakit (tanpa beda huruf besar/kecil)
        tanggal  : datetime.date atau teks "YYYY-MM-DD"
        """
        if isinstance(tanggal, datetime):
            tanggal = tanggal.date()
        if isinstance(tanggal, date):
            tanggal = tanggal.isoformat()

        hasil = []
        for rec in self.all():
            if ikan and rec.get("ikan") != ikan:
                continue
            if tanggal and not str(rec.get("timestamp", "")).startswith(tanggal):
                continue
            if penyakit:
                kunci = penyakit.lower()
                cocok = any(
                    kunci == h.get("id", "").lower() or kunci in h.get("nama", "").lower()
                    for h in rec.get("hasil", [])
                )
                if not cocok:
                    continue
            hasil.append(rec)
        return hasil
