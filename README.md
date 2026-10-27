# Sistem Pakar Diagnosis Penyakit Ikan Air Tawar (Lele, Nila, Gurame)

Sistem pakar berbasis aturan (rule-based) dengan Python dan Streamlit. Pengguna memilih gejala fisik dan perilaku ikan,
sistem menalar dengan **forward chaining** dan **Certainty Factor (CF)**, lalu menampilkan nama penyakit, tingkat
kepercayaan, penjelasan penalaran, penanganan langkah demi langkah, pencegahan, dan **tautan ke sumber rujukan**.

> Hasil adalah alat bantu awal, bukan pengganti ahli kesehatan ikan. Dosis berasal dari literatur; verifikasi ke
> penyuluh perikanan, BPBAT, atau dokter hewan ikan. Dosis antibiotik sengaja tidak dicantumkan.

## Cara menjalankan
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
python -m pytest -v          # pengujian (opsional, perlu pytest)
```

## Fitur dan pemetaan ke kriteria tugas
| Kriteria | Lokasi |
|---|---|
| Knowledge base IF-THEN (+ jenis, sumber, CF) | `data/rules/`, `data/diseases/`, `data/symptoms/`, `core/knowledge_base.py` |
| Dokumentasi sumber pengetahuan | `data/references/references.json`, `docs/DAFTAR_PUSTAKA.md`, tab Database Penyakit |
| Inference engine: forward + backward chaining, trace | `core/inference_engine.py` |
| Working memory | `core/working_memory.py` |
| UI input/output, validasi | `ui/`, `app.py`, `ui/theme.py` |
| Explanation: WHY, HOW, rule, reasoning tree | `core/explanation.py`, tab Diagnosa |
| Certainty Factor (user CF, rule CF, gabungan) | `core/certainty.py` |
| Akuisisi pengetahuan (tambah/ubah/hapus rule + validasi, simpan JSON) | tab Kelola Rule |
| Reporting dan logging (TXT/CSV/PDF, riwayat, statistik, rule terbanyak) | `services/`, tab Riwayat, Statistik |
| Pencarian dan filter, database penyakit | tab Database Penyakit, Riwayat |
| Pengujian 11 kasus uji + unit test | `tests/test_cases.py` |

## Penyakit dalam knowledge base
White Spot (Ich), MAS/Aeromonas, Columnaris, Saprolegniasis, Streptococcosis (nila), cacing insang (monogenea), Argulus.
Setiap penyakit memuat: penyebab, penularan, gejala, cara konfirmasi, penanganan langkah demi langkah, pencegahan,
pembatasan penyebaran, kapan memanggil ahli, dan rujukan bertaut. Butir bertanda "praktik umum" belum punya sumber
tertaut dan perlu divalidasi pakar. Nilai CF pada rule adalah estimasi heuristik tim.

## Struktur
```
app.py  config.py  core/  services/  ui/  data/  tests/  docs/  .streamlit/config.toml
```

## Yang masih harus dilengkapi tim
- Buka dan cek rujukan berstatus "WAJIB dicek anggota" (lihat `docs/DAFTAR_PUSTAKA.md`).
- Validasi nilai CF dan isi penanganan dengan pakar (dosen/penyuluh/dokter hewan ikan).
- Screenshot aplikasi di README, laporan PDF (min. 10 halaman), video demo 5-7 menit, dan commit dari semua anggota di GitHub.
