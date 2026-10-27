"""Statistik penggunaan sistem dari riwayat konsultasi."""
from collections import Counter


def statistik(history: list[dict]) -> dict:
    """Ringkasan riwayat.

    Mengembalikan dict:
      total_konsultasi : jumlah record
      penyakit_terbanyak : [(nama, jumlah)] urut menurun; yang dihitung adalah
                           diagnosis utama (CF tertinggi) tiap konsultasi
      rule_terbanyak   : [(id_rule, jumlah)] urut menurun
      ikan_terbanyak   : [(ikan, jumlah)] urut menurun
      tanpa_diagnosis  : jumlah konsultasi tanpa hasil
    """
    penyakit, rules, ikan = Counter(), Counter(), Counter()
    tanpa = 0
    for rec in history:
        ikan[rec.get("ikan", "?")] += 1
        rules.update(rec.get("rules_dipakai", []))
        hasil = rec.get("hasil", [])
        if hasil:
            utama = max(hasil, key=lambda h: h.get("cf", 0))
            penyakit[utama.get("nama", utama.get("id", "?"))] += 1
        else:
            tanpa += 1
    return {
        "total_konsultasi": len(history),
        "penyakit_terbanyak": penyakit.most_common(),
        "rule_terbanyak": rules.most_common(),
        "ikan_terbanyak": ikan.most_common(),
        "tanpa_diagnosis": tanpa,
    }
