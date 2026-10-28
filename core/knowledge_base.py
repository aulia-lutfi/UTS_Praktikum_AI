"""Knowledge base: muat, validasi, simpan, dan kelola (CRUD) rule."""
import json
import os
import re
from pathlib import Path

from config import DAFTAR_IKAN

CUSTOM_FILE = "rules_custom.json"
ID_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


class KnowledgeBaseError(Exception):
    """Kesalahan pada file/isi knowledge base."""


class KnowledgeBase:
    """Menggabungkan semua file JSON di data_dir/{symptoms,diseases,rules}/."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.symptoms: dict[str, dict] = {}
        self.diseases: dict[str, dict] = {}
        self.rules: list[dict] = []
        self.references: dict[str, dict] = {}   # id rujukan -> {sitasi, url, status, ...}
        self.problems: list[str] = []          # peringatan validasi saat load
        self._rule_origin: dict[str, Path] = {}  # id rule -> file asal
        self._rule_files: set[Path] = set()      # semua file rule yang dimuat
        self._dirty: set[Path] = set()           # file rule yang perlu ditulis ulang
        self.load()

    # ------------------------------------------------------------------ load
    @staticmethod
    def _read_json(path: Path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise KnowledgeBaseError(f"File JSON rusak: {path.name} ({e})") from e
        except OSError as e:
            raise KnowledgeBaseError(f"File tidak bisa dibaca: {path} ({e})") from e

    def _merge_dicts(self, subdir: str) -> dict[str, dict]:
        folder = self.data_dir / subdir
        if not folder.is_dir():
            raise KnowledgeBaseError(f"Folder tidak ditemukan: {folder}")
        hasil: dict[str, dict] = {}
        asal: dict[str, str] = {}
        for path in sorted(folder.glob("*.json")):
            data = self._read_json(path)
            if not isinstance(data, dict):
                raise KnowledgeBaseError(f"{path.name}: isi harus berupa objek JSON")
            for key, val in data.items():
                if key in hasil:
                    raise KnowledgeBaseError(
                        f"ID ganda '{key}' di {subdir}/: {asal[key]} dan {path.name}")
                hasil[key] = val
                asal[key] = path.name
        return hasil

    def load(self) -> None:
        """Muat ulang seluruh knowledge base dari disk."""
        self.symptoms = self._merge_dicts("symptoms")
        self.diseases = self._merge_dicts("diseases")
        self.references = self._merge_dicts("references")

        folder = self.data_dir / "rules"
        if not folder.is_dir():
            raise KnowledgeBaseError(f"Folder tidak ditemukan: {folder}")
        self.rules, self._rule_origin = [], {}
        self._rule_files, self._dirty = set(), set()
        for path in sorted(folder.glob("*.json")):
            data = self._read_json(path)
            if not isinstance(data, list):
                raise KnowledgeBaseError(f"{path.name}: isi harus berupa daftar rule")
            self._rule_files.add(path)
            for rule in data:
                rid = rule.get("id") if isinstance(rule, dict) else None
                if rid is None:
                    raise KnowledgeBaseError(f"{path.name}: ada rule tanpa field 'id'")
                if rid in self._rule_origin:
                    raise KnowledgeBaseError(
                        f"ID rule ganda '{rid}': {self._rule_origin[rid].name} dan {path.name}")
                self.rules.append(rule)
                self._rule_origin[rid] = path
        self.problems = self.validate_all() + self.validate_references()

    # ---------------------------------------------------------------- lookup
    def get_rule(self, rule_id: str) -> dict | None:
        return next((r for r in self.rules if r["id"] == rule_id), None)

    def intermediate_facts(self) -> list[str]:
        """Fakta hasil antara: THEN dari rule yang bukan penyakit."""
        return sorted({r["THEN"] for r in self.rules if r["THEN"] not in self.diseases})

    def rules_depending_on(self, fact: str) -> list[str]:
        """ID rule yang memakai `fact` sebagai premis."""
        return [r["id"] for r in self.rules if fact in r["IF"]]

    def next_rule_id(self) -> str:
        """ID rule berikutnya untuk rule custom (mulai R100 agar tidak bentrok rentang A/E)."""
        angka = [int(m.group(1)) for r in self.rules
                 if (m := re.fullmatch(r"R(\d+)", r["id"]))]
        return f"R{max([99] + angka) + 1}"

    def related_symptoms(self, disease_id: str) -> list[str]:
        """Semua gejala yang ikut menentukan sebuah penyakit (menelusuri rule bertingkat)."""
        hasil, antrean, dilihat = set(), [disease_id], set()
        while antrean:
            fakta = antrean.pop()
            if fakta in dilihat:
                continue
            dilihat.add(fakta)
            for r in self.rules:
                if r["THEN"] == fakta:
                    for p in r["IF"]:
                        if p in self.symptoms:
                            hasil.add(p)
                        else:
                            antrean.append(p)
        return sorted(hasil)

    # ------------------------------------------------------------ validation
    def _validate(self, rule: dict, ignore_id: str | None = None) -> list[str]:
        err: list[str] = []
        if not isinstance(rule, dict):
            return ["Rule harus berupa objek/dict."]
        for field in ("id", "IF", "THEN", "CF"):
            if field not in rule:
                err.append(f"Field wajib '{field}' tidak ada.")
        if err:
            return err

        rid, premis, then, cf = rule["id"], rule["IF"], rule["THEN"], rule["CF"]
        if not isinstance(rid, str) or not ID_PATTERN.match(rid):
            err.append("ID rule harus berupa huruf/angka/underscore tanpa spasi.")
        elif rid != ignore_id and any(r["id"] == rid for r in self.rules):
            err.append(f"ID rule '{rid}' sudah dipakai.")

        if not isinstance(premis, list) or not premis:
            err.append("IF harus berupa daftar premis yang tidak kosong.")
            premis = []
        elif len(set(premis)) != len(premis):
            err.append("IF berisi premis ganda.")

        if not isinstance(then, str) or not then.strip():
            err.append("THEN harus berupa teks (ID penyakit atau fakta hasil antara).")
        elif then in self.symptoms:
            err.append("THEN tidak boleh berupa gejala.")
        elif then in premis:
            err.append("THEN tidak boleh sama dengan salah satu premis.")

        if isinstance(cf, bool) or not isinstance(cf, (int, float)) or not 0 < cf <= 1:
            err.append("CF harus berupa angka lebih dari 0 dan maksimal 1.")

        ikan = rule.get("ikan")
        if ikan is not None:
            if (not isinstance(ikan, list) or not ikan
                    or any(i not in DAFTAR_IKAN for i in ikan)):
                err.append(f"'ikan' harus daftar tidak kosong berisi salah satu dari {DAFTAR_IKAN}.")

        # premis harus gejala atau fakta yang dihasilkan rule lain
        dihasilkan = {r["THEN"] for r in self.rules if r["id"] not in (rid, ignore_id)}
        for p in premis:
            if isinstance(p, str) and p not in self.symptoms and p not in dihasilkan:
                err.append(f"Premis '{p}' bukan gejala dan tidak dihasilkan rule lain.")

        # duplikat isi (IF + THEN sama dengan rule lain)
        if isinstance(then, str):
            for r in self.rules:
                if r["id"] in (rid, ignore_id):
                    continue
                if set(r["IF"]) == set(premis) and r["THEN"] == then:
                    err.append(f"Rule duplikat dengan {r['id']} (IF dan THEN sama).")
        return err

    def validate_references(self) -> list[str]:
        """Pastikan setiap id rujukan di penyakit/rule/langkah ada di references/."""
        masalah = []

        def cek(asal: str, ids) -> None:
            for rid in ids or []:
                if rid not in self.references:
                    masalah.append(f"{asal}: rujukan '{rid}' tidak ada di data/references/.")

        for pid, p in self.diseases.items():
            cek(pid, p.get("sumber"))
            detail = p.get("detail", {})
            for kunci in ("penularan", "siklus", "gejala_klinis", "konfirmasi",
                          "pencegahan_rinci", "cegah_penyebaran"):
                for it in detail.get(kunci, []):
                    cek(f"{pid}.{kunci}", it.get("r"))
            for bagian in detail.get("penanganan", []):
                for it in bagian.get("langkah", []):
                    cek(f"{pid}.penanganan", it.get("r"))
        for r in self.rules:
            cek(r.get("id", "?"), r.get("sumber"))
        return masalah

    def validate_rule(self, rule: dict) -> list[str]:
        """Daftar pesan error untuk rule baru (kosong jika valid)."""
        return self._validate(rule)

    def validate_all(self) -> list[str]:
        """Periksa seluruh rule yang sudah dimuat; kembalikan daftar peringatan."""
        masalah = []
        for r in self.rules:
            for e in self._validate(r, ignore_id=r.get("id")):
                masalah.append(f"{r.get('id', '?')}: {e}")
        return masalah

    # ------------------------------------------------------------------ CRUD
    def add_rule(self, rule: dict) -> None:
        err = self.validate_rule(rule)
        if err:
            raise ValueError("; ".join(err))
        custom = self.data_dir / "rules" / CUSTOM_FILE
        self.rules.append(rule)
        self._rule_origin[rule["id"]] = custom
        self._dirty.add(custom)

    def update_rule(self, rule_id: str, rule: dict) -> None:
        idx = next((i for i, r in enumerate(self.rules) if r["id"] == rule_id), None)
        if idx is None:
            raise KeyError(f"Rule '{rule_id}' tidak ditemukan.")
        err = self._validate(rule, ignore_id=rule_id)
        if err:
            raise ValueError("; ".join(err))
        asal = self._rule_origin.pop(rule_id)
        self.rules[idx] = rule
        self._rule_origin[rule["id"]] = asal
        self._dirty.add(asal)

    def delete_rule(self, rule_id: str) -> None:
        idx = next((i for i, r in enumerate(self.rules) if r["id"] == rule_id), None)
        if idx is None:
            raise KeyError(f"Rule '{rule_id}' tidak ditemukan.")
        del self.rules[idx]
        self._dirty.add(self._rule_origin.pop(rule_id))

    # ------------------------------------------------------------------ save
    def save(self) -> None:
        """Tulis ulang hanya file rule yang berubah (tiap rule kembali ke file asalnya)."""
        for path in sorted(self._dirty):
            isi = [r for r in self.rules if self._rule_origin.get(r["id"]) == path]
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(isi, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
            self._rule_files.add(path)
        self._dirty.clear()
