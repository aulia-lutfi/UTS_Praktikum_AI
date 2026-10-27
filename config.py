"""Konstanta bersama untuk seluruh aplikasi."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = str(BASE_DIR / "data")
HISTORY_PATH = str(BASE_DIR / "data" / "history.json")

DAFTAR_IKAN = ["lele", "nila", "gurame"]

# Tingkat keyakinan pengguna terhadap tiap gejala -> nilai CF
KEYAKINAN = {"Tidak yakin": 0.4, "Cukup yakin": 0.6, "Yakin": 0.8, "Sangat yakin": 1.0}
KEYAKINAN_DEFAULT = "Yakin"

# Diagnosis dengan CF di bawah ambang ini ditandai "keyakinan rendah"
CF_MINIMUM = 0.30
