# Sistem Pakar Diagnosis Penyakit Ikan Air Tawar

Sistem pakar berbasis aturan untuk membantu pembudidaya lele, nila, dan gurame menandai kemungkinan penyakit pada ikannya. Pengguna memilih gejala yang diamati beserta tingkat keyakinannya, sistem menalar dengan forward chaining dan Certainty Factor model MYCIN, lalu menampilkan kandidat penyakit yang diurutkan menurut tingkat kepercayaan disertai penjelasan bagaimana kesimpulan tersebut diperoleh.

Hasil yang ditampilkan bersifat indikasi awal, bukan pengganti pemeriksaan penyuluh perikanan atau dokter hewan ikan. Dosis dan prosedur penanganan di dalam basis pengetahuan diambil dari literatur dan masih memerlukan validasi pakar.

## Teknis

| Bagian | Rincian |
| --- | --- |
| Bahasa | Python 3.10 ke atas |
| Antarmuka | Streamlit dengan lima tab |
| Basis pengetahuan | Berkas JSON di `data/`, dimuat dan disimpan tanpa basis data eksternal |
| Metode inferensi | Forward chaining, satu arah, dengan penggabungan bukti |
| Dependensi | `streamlit`, `fpdf2`, `pandas` (lihat `requirements.txt`) |

## Menjalankan

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Pengujian memakai pytest:

```bash
pip install pytest
python -m pytest -v
```

## Struktur

```
app.py                  perakit antarmuka dan lima tab
config.py               daftar komoditas, tingkat keyakinan, ambang CF, lokasi data
core/
  knowledge_base.py     baca, gabung, validasi, CRUD, dan simpan JSON
  inference_engine.py   forward chaining dan backward chaining
  working_memory.py     fakta, sumber fakta, jejak penalaran, rule yang tereksekusi
  certainty.py          rumus rule CF dan combine
  explanation.py        WHY, HOW, dan grafik penalaran
services/
  history.py            penyimpanan dan penyaringan riwayat konsultasi
  report.py             ekspor TXT, CSV, dan PDF
  stats.py              agregasi statistik
ui/                     satu modul per tab, termasuk tema
data/
  symptoms/             gejala, dibagi per berkas
  diseases/             penyakit, gejala ringkas, pengobatan, pencegahan, rujukan
  rules/                aturan IF-THEN, dibagi per berkas
  references/           daftar pustaka ber-ID
  history.sample.json   contoh isi riwayat; history.json dibuat otomatis saat dipakai
tests/test_cases.py     11 kasus uji dan pengujian modul
docs/DAFTAR_PUSTAKA.md  susunan rujukan untuk laporan
```

## Isi basis pengetahuan

| Komponen | Jumlah | Keterangan |
| --- | --- | --- |
| Gejala | 20 | 14 kategori fisik, 6 kategori perilaku, ber-ID `G01` sampai dengan `G55` |
| Penyakit | 10 | `P01` sampai dengan `P10`, tiap entri memuat komoditas rentan, uraian gejala, langkah pengobatan, pencegahan, dan tautan rujukan |
| Aturan | 30 | 25 aturan menuju ID penyakit dan 5 aturan menuju fakta antara |
| Fakta antara | 5 | `dugaan_parasit_kulit`, `dugaan_infeksi_bakteri`, `dugaan_infeksi_jamur`, `dugaan_gangguan_insang`, `dugaan_ektoparasit_besar` |
| Rujukan | 22 | Entri ber-ID di `data/references/references.json` |
| Bobot CF aturan | 0.50 sampai 0.85 | Seluruhnya berjenis heuristik, hasil estimasi tim dari literatur |

Cakupan aturan per penyakit:

| ID | Penyakit | Komoditas rentan | Jumlah aturan |
| --- | --- | --- | --- |
| P01 | Bintik Putih (White Spot / Ichthyophthiriasis) | Lele, Nila, Gurame | 3 |
| P02 | Motile Aeromonas Septicemia (MAS) | Lele, Nila, Gurame | 3 |
| P03 | Columnaris | Lele, Nila | 3 |
| P04 | Saprolegniasis | Nila, Gurame, Lele | 3 |
| P05 | Trichodiniasis | Lele, Nila, Gurame | 1 |
| P06 | Infeksi Dactylogyrus / Gyrodactylus | Lele, Nila, Gurame | 3 |
| P07 | Streptococcosis | Nila, Gurame | 4 |
| P08 | Argulosis (kutu ikan) | Gurame, Lele | 3 |
| P09 | Jaundice (penyakit kuning lele) | Lele | 1 |
| P10 | Enteric Septicemia of Catfish (ESC) | Lele, Nila | 1 |

## Cara kerja inferensi

1. Gejala yang dicentang pengguna masuk ke working memory sebagai fakta awal dengan CF sesuai pilihan tingkat keyakinan: Tidak yakin 0.4, Cukup yakin 0.6, Yakin 0.8, Sangat yakin 1.0.
2. Aturan disaring dua kali, yaitu yang berlaku untuk komoditas terpilih dan yang premisnya mungkin tercapai dari fakta awal. Aturan untuk ikan lain tidak diuji.
3. Sebuah aturan baru dieksekusi ketika seluruh premisnya sudah tersedia dan tidak ada aturan lain yang masih bisa menaikkan nilai premis tersebut. Mekanisme ini membuat fakta antara selalu memakai nilai terbaik sebelum dipakai oleh aturan berikutnya. Bila tidak ada aturan yang memenuhi syarat, satu aturan dengan premis lengkap dijalankan lebih dahulu sebagai jalan keluar dari kemungkinan siklus antar aturan.
4. CF kesimpulan aturan dihitung dengan `min(CF seluruh premis) x CF aturan`. Bila penyakit yang sama sudah memiliki nilai, kedua bukti digabung mengikuti model MYCIN.

```python
def combine(cf1, cf2):
    if cf1 >= 0 and cf2 >= 0:
        return cf1 + cf2 * (1 - cf1)
    if cf1 < 0 and cf2 < 0:
        return cf1 + cf2 * (1 + cf1)
    penyebut = 1 - min(abs(cf1), abs(cf2))
    return 0.0 if penyebut == 0 else (cf1 + cf2) / penyebut
```

5. Hasil diurutkan dari CF tertinggi dan ditampilkan sebagai kandidat. Nilai di bawah 0.30 ditandai sebagai keyakinan rendah.
6. Setiap langkah perhitungan dicatat pada jejak penalaran, berisi iterasi, ID aturan, premis, CF premis, CF hasil, dan CF akumulasi. Jejak ini yang dipakai fitur penjelasan dan riwayat.
7. Riwayat konsultasi ditulis otomatis ke `data/history.json`. Berkas riwayat yang tidak terbaca akan dicadangkan sebagai `.json.corrupt` agar aplikasi tetap berjalan.

`backward_chain` tersedia pada `core/inference_engine.py` dan dipakai untuk membuktikan hipotesis tertentu serta menyusun daftar gejala yang masih kurang. Pada kondisi sekarang metode ini dijalankan oleh pengujian, belum dipanggil dari antarmuka.

## Tab antarmuka

| Tab | Fungsi |
| --- | --- |
| Diagnosa | Pilih komoditas, centang gejala yang terpisah pada kelompok fisik dan perilaku, tentukan tingkat keyakinan tiap gejala, lalu tampilkan kandidat penyakit beserta persen kepercayaan, alasan aturan memakai gejala, rantai penalaran, dan grafik penalaran |
| Database Penyakit | Ringkasan jumlah pengetahuan, pencarian penyakit dan gejala, rincian tiap penyakit termasuk langkah pengobatan dan tautan rujukan, daftar aturan yang menyimpulkan penyakit tersebut, serta tabel gejala beserta aturan yang memakai gejala itu |
| Kelola Rule | Tabel aturan dan form tambah, ubah, hapus. Aturan divalidasi sebelum disimpan dan hasilnya langsung ditulis kembali ke berkas JSON asalnya. Penghapusan fakta antara diberi peringatan bila masih dipakai aturan lain |
| Riwayat | Daftar konsultasi beserta penyaringan berdasarkan komoditas, penyakit, dan tanggal, rincian gejala dan hasil tiap konsultasi, serta unduhan TXT, CSV, dan PDF |
| Statistik | Total konsultasi, penyakit terbanyak, aturan paling sering dipakai, jumlah konsultasi tanpa diagnosis, dan grafik batang pendukung |

## Validasi basis pengetahuan

Muat dan simpan melewati `core/knowledge_base.py` dengan pemeriksaan berikut.

- ID aturan tidak boleh ganda di seluruh berkas rule.
- Field wajib `id`, `IF`, `THEN`, dan `CF` harus ada, `IF` tidak boleh kosong.
- Nilai CF aturan berada pada rentang 0 sampai 1 dan tidak nol.
- Setiap premis harus dikenal sebagai gejala, penyakit, atau fakta antara.
- ID rujukan pada field `sumber` harus ada di `data/references/references.json`.
- Penulisan berkas memakai berkas sementara lalu `os.replace`, sehingga data tidak rusak bila proses berhenti di tengah penyimpanan.

## Status dan pekerjaan yang belum selesai

- Rujukan antar modul belum selaras. Sebanyak 26 peringatan validasi muncul karena ID pada field `sumber` beberapa aturan, misalnya `nila_warmadewa` dan `anshary2014`, belum terdaftar di `references.json`. Kondisi ini membuat `test_kb_valid` dan `test_rujukan_lengkap` belum lolos.
- Nilai CF seluruhnya estimasi heuristik tim dan belum divalidasi pakar.
- Berkas `ui/components.py` adalah sisa versi antarmuka sebelumnya dan tidak dipanggil dari tab mana pun.
- Ekspor laporan menerima daftar rujukan sebagai parameter, tetapi tab Riwayat belum mengirimkannya, sehingga tautan pustaka belum muncul di berkas hasil ekspor.
- Panel peringatan validasi basis pengetahuan saat ini dinonaktifkan di `app.py`, sehingga masalah data tidak terlihat saat aplikasi berjalan.
- Dokumentasi tugas belum lengkap, yaitu tangkapan layar aplikasi, laporan, dan video demo.

## Alur kontribusi

Setiap modul dikerjakan pada branch sendiri, misalnya `feature/setup-config`, `feature/knowledge-data`, `feature/core-engine`, `feature/ui-interface`, dan `feature/services-and-testing`, lalu digabungkan ke `main` melalui pull request yang sudah direview. Simpan `main` sebagai acuan ketika memulai pekerjaan baru agar perubahan modul lain sudah ikut terpakai.
