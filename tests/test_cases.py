"""Pengujian sistem pakar. Jalankan: `python -m pytest -v` atau `python -m tests.test_cases`."""
import json
import shutil
import tempfile
from pathlib import Path

import pytest

from config import DATA_DIR
from core.certainty import combine, rule_cf
from core.explanation import how, why
from core.inference_engine import InferenceEngine
from core.knowledge_base import KnowledgeBase, KnowledgeBaseError
from services.history import HistoryService
from services.report import export_csv, export_pdf, export_txt
from services.stats import statistik

FIXTURE = Path(__file__).parent / "fixtures" / "mini_rules.json"


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(DATA_DIR)


@pytest.fixture(scope="module")
def engine(kb):
    return InferenceEngine(kb.rules)


def diagnosa(engine, kb, ikan, gejala):
    wm = engine.forward_chain(gejala, ikan)
    return engine.get_diagnoses(wm, list(kb.diseases)), wm


# ------------------------------------------------------------ test case tabel BAB V
# (id, ikan, gejala {id: CF}, penyakit utama yang diharapkan atau None, keterangan)
TEST_CASES = [
    (1, "lele", {"G01": 1.0, "G09": 1.0, "G08": 1.0}, "P01", "White Spot"),
    (2, "nila", {"G04": 1.0, "G07": 1.0}, "P07", "Streptococcosis"),
    (3, "gurame", {"G02": 1.0, "G05": 1.0, "G08": 1.0}, "P02", "MAS / Aeromonas"),
    (4, "lele", {"G08": 1.0}, None, "Tidak ada diagnosis pasti"),
    (5, "nila", {"G01": 1.0, "G09": 1.0, "G08": 1.0, "G04": 1.0, "G07": 1.0}, "P07", "Dua penyakit"),
    (6, "lele", {"G13": 1.0, "G03": 1.0}, "P03", "Columnaris"),
    (7, "gurame", {"G06": 1.0, "G02": 1.0}, "P04", "Saprolegniasis"),
    (8, "lele", {"G03": 1.0, "G53": 1.0, "G10": 1.0}, "P06", "Cacing insang"),
    (9, "lele", {"G50": 1.0, "G52": 1.0}, "P08", "Argulus"),
    (10, "lele", {"G04": 1.0, "G07": 1.0}, None, "Gejala nila dipakai pada lele"),
    (11, "lele", {}, None, "Input kosong"),
]


@pytest.mark.parametrize("tc", TEST_CASES, ids=[f"TC{t[0]}" for t in TEST_CASES])
def test_kasus(engine, kb, tc):
    _, ikan, gejala, harapan, _ = tc
    hasil, _wm = diagnosa(engine, kb, ikan, gejala)
    if harapan is None:
        assert hasil == []
    else:
        assert hasil and hasil[0][0] == harapan


# ------------------------------------------------------------ nilai CF
def test_rumus_cf():
    assert rule_cf([0.8, 0.6], 0.5) == pytest.approx(0.3)
    assert combine(0.6, 0.56) == pytest.approx(0.824)
    assert combine(0.5, -0.5) == pytest.approx(0.0)
    assert combine(1.0, -1.0) == 0.0


def test_cf_berantai(engine, kb):
    # R01: min(0.8, 1.0) x 0.7 = 0.56 ; R02: min(0.56, 0.6) x 0.8 = 0.448
    hasil, wm = diagnosa(engine, kb, "lele", {"G01": 0.8, "G09": 1.0, "G08": 0.6})
    assert wm.facts["dugaan_parasit_kulit"] == pytest.approx(0.56)
    r02 = next(s for s in wm.trace if s["rule"] == "R02")
    assert r02["cf_hasil"] == pytest.approx(0.448)


def test_evidence_ganda_digabung(engine, kb):
    hasil, _ = diagnosa(engine, kb, "lele", {"G01": 1.0, "G09": 1.0, "G08": 1.0})
    # R02 (0.56) + R03 (0.6) -> 0.824 ; R04 tidak aktif (butuh G10)
    assert dict(hasil)["P01"] == pytest.approx(0.824)


def test_dua_penyakit_terurut(engine, kb):
    hasil, _ = diagnosa(engine, kb, "nila",
                        {"G01": 1.0, "G09": 1.0, "G08": 1.0, "G04": 1.0, "G07": 1.0})
    ids = [d for d, _ in hasil]
    assert ids[:2] == ["P07", "P01"]
    assert hasil[0][1] >= hasil[1][1]


def test_gejala_tumpang_tindih(engine, kb):
    hasil, _ = diagnosa(engine, kb, "lele", {"G03": 1.0, "G13": 1.0, "G53": 1.0, "G10": 1.0})
    assert {"P03", "P06"} <= {d for d, _ in hasil}


def test_rule_bertingkat_menunggu_premis_final(engine, kb):
    # dugaan_parasit_kulit hanya dari R01; R02 harus jalan setelah R01
    _, wm = diagnosa(engine, kb, "lele", {"G01": 1.0, "G09": 1.0, "G08": 1.0})
    urut = [s["rule"] for s in wm.trace]
    assert urut.index("R01") < urut.index("R02")


# ------------------------------------------------------------ explanation
def test_how_dan_why(engine, kb):
    _, wm = diagnosa(engine, kb, "lele", {"G01": 1.0, "G09": 1.0, "G08": 1.0})
    baris = how("P01", wm, kb.rules)
    ids = [b.split(":")[0] for b in baris]
    assert ids.index("R01") < ids.index("R02")   # premis ditelusuri lebih dulu
    assert "R03" in ids                          # evidence kedua untuk P01
    assert "R01" in why("G01", kb.rules)
    assert how("P03", wm, kb.rules) == []


def test_fixture_mini_rules():
    rules = json.loads(FIXTURE.read_text(encoding="utf-8"))
    eng = InferenceEngine(rules)
    wm = eng.forward_chain({"G01": 0.8, "G09": 1.0, "G08": 0.6}, "lele")
    assert wm.facts["P01"] == pytest.approx(0.448)


# ------------------------------------------------------------ knowledge base
def test_kb_valid(kb):
    assert kb.problems == []
    assert len(kb.rules) >= 20
    assert len(kb.diseases) == 10


@pytest.fixture
def kb_salinan():
    tmp = Path(tempfile.mkdtemp())
    shutil.copytree(DATA_DIR, tmp / "data")
    yield KnowledgeBase(str(tmp / "data")), tmp / "data"
    shutil.rmtree(tmp, ignore_errors=True)


def test_validasi_rule(kb):
    assert kb.validate_rule({"id": "R100", "IF": ["G01"], "THEN": "P01", "CF": 0.5}) == []
    assert kb.validate_rule({"id": "R01", "IF": ["G01"], "THEN": "P01", "CF": 0.5})  # ID ganda
    assert kb.validate_rule({"id": "R100", "IF": ["G01"], "THEN": "P01", "CF": 1.5})  # CF salah
    assert kb.validate_rule({"id": "R100", "IF": ["GXX"], "THEN": "P01", "CF": 0.5})  # premis salah
    assert kb.validate_rule({"id": "R100", "IF": [], "THEN": "P01", "CF": 0.5})
    assert kb.validate_rule({"id": "R100", "THEN": "P01", "CF": 0.5})                 # field hilang
    assert kb.validate_rule({"id": "R100", "IF": ["G09", "G01"], "THEN": "dugaan_parasit_kulit",
                             "CF": 0.4})                                               # duplikat isi


def test_crud_dan_simpan(kb_salinan):
    kb, data_dir = kb_salinan
    n = len(kb.rules)
    kb.add_rule({"id": "R100", "IF": ["G10", "G15"], "THEN": "P06", "CF": 0.4, "ikan": ["lele"]})
    kb.update_rule("R01", {**kb.get_rule("R01"), "CF": 0.9})
    kb.delete_rule("R15")
    kb.save()
    assert (data_dir / "rules" / "rules_custom.json").exists()
    kb2 = KnowledgeBase(str(data_dir))
    assert len(kb2.rules) == n
    assert kb2.get_rule("R01")["CF"] == 0.9
    assert kb2.get_rule("R100") and kb2.get_rule("R15") is None
    assert kb2.get_rule("R100") in json.loads((data_dir / "rules" / "rules_custom.json").read_text())


def test_crud_error(kb_salinan):
    kb, _ = kb_salinan
    with pytest.raises(ValueError):
        kb.add_rule({"id": "R01", "IF": ["G01"], "THEN": "P01", "CF": 0.5})
    with pytest.raises(KeyError):
        kb.delete_rule("R999")


def test_id_ganda_antar_file(kb_salinan):
    _, data_dir = kb_salinan
    sym = json.loads((data_dir / "symptoms" / "symptoms_a.json").read_text())
    (data_dir / "symptoms" / "symptoms_x.json").write_text(json.dumps({"G01": sym["G01"]}))
    with pytest.raises(KnowledgeBaseError):
        KnowledgeBase(str(data_dir))


def test_json_rusak(kb_salinan):
    _, data_dir = kb_salinan
    (data_dir / "rules" / "rules_a.json").write_text("{rusak")
    with pytest.raises(KnowledgeBaseError):
        KnowledgeBase(str(data_dir))


# ------------------------------------------------------------ services
@pytest.fixture
def record():
    return {"timestamp": "2026-10-26T14:30:00", "ikan": "lele",
            "gejala": {"G01": 0.8, "G09": 1.0},
            "hasil": [{"id": "P01", "nama": "White Spot (Ich)", "cf": 0.62,
                       "pengobatan": "Perbaiki air", "pencegahan": "Karantina"}],
            "rules_dipakai": ["R01", "R02"]}


def test_history_filter(tmp_path, record):
    h = HistoryService(str(tmp_path / "h.json"))
    assert h.all() == []
    h.save(record)
    h.save({**record, "ikan": "nila", "timestamp": "2026-10-27T08:00:00",
            "hasil": [{"id": "P07", "nama": "Streptococcosis (nila)", "cf": 0.7}]})
    assert len(h.all()) == 2
    assert len(h.filter(ikan="lele")) == 1
    assert len(h.filter(penyakit="strep")) == 1
    assert len(h.filter(penyakit="P01")) == 1
    assert len(h.filter(tanggal="2026-10-27")) == 1
    assert h.filter(ikan="gurame") == []


def test_history_file_rusak(tmp_path, record):
    p = tmp_path / "h.json"
    p.write_text("{rusak")
    h = HistoryService(str(p))
    assert h.all() == []
    h.save(record)
    assert len(h.all()) == 1


def test_statistik(record):
    s = statistik([record, record, {**record, "hasil": [], "rules_dipakai": []}])
    assert s["total_konsultasi"] == 3
    assert s["penyakit_terbanyak"][0] == ("White Spot (Ich)", 2)
    assert s["rule_terbanyak"][0][1] == 2
    assert s["tanpa_diagnosis"] == 1
    assert statistik([])["total_konsultasi"] == 0


def test_export(record):
    txt = export_txt(record, {"G01": "Bintik putih"})
    assert "White Spot" in txt and "62%" in txt and "Bintik putih" in txt
    rows = export_csv(record).strip().splitlines()
    assert len(rows) == 2 and "White Spot" in rows[1]
    pdf = export_pdf(record)
    assert pdf[:4] == b"%PDF"


# ------------------------------------------------------------ backward chaining & rujukan
def test_backward_chaining(engine, kb):
    ok = engine.backward_chain("P01", {"G01": 1.0, "G09": 1.0, "G08": 1.0}, "lele")
    maju = diagnosa(engine, kb, "lele", {"G01": 1.0, "G09": 1.0, "G08": 1.0})[0]
    assert ok["terbukti"] and ok["cf"] == pytest.approx(dict(maju)["P01"])   # sama dengan forward
    kurang = engine.backward_chain("P01", {"G01": 1.0, "G09": 1.0}, "lele")
    assert "G08" in kurang["kurang"]["R02"]                                  # gejala yang perlu ditanyakan
    assert not engine.backward_chain("P07", {"G04": 1.0, "G07": 1.0}, "lele")["terbukti"]  # P07 hanya untuk nila/gurame


def test_rujukan_lengkap(kb):
    assert len(kb.references) >= 30
    for pid, p in kb.diseases.items():
        assert (p.get("name") or p.get("nama")), pid
        assert p.get("references") or p.get("sumber"), pid
    for ref in kb.references.values():
        assert ref["url"].startswith("http")


def test_why_menyebut_penyakit(kb):
    assert "White Spot" in why("G01", kb.rules, kb.diseases)


def test_export_memuat_tautan(record):
    rec = {**record, "hasil": [{**record["hasil"][0], "sumber_ids": ["uf_fa006"]}]}
    refs = {"uf_fa006": {"singkat": "UF/IFAS FA006", "url": "https://ask.ifas.ufl.edu/publication/FA006"}}
    assert "https://ask.ifas.ufl.edu/publication/FA006" in export_txt(rec, None, refs)
    assert export_pdf(rec, None, refs)[:4] == b"%PDF"


# ------------------------------------------------------------ runner mandiri
if __name__ == "__main__":
    _kb = KnowledgeBase(DATA_DIR)
    _eng = InferenceEngine(_kb.rules)
    sesuai = 0
    print(f"{'TC':<4}{'Ikan':<8}{'Diharapkan':<12}{'Hasil sistem':<28}Sesuai?")
    for tc_id, ikan, gejala, harapan, ket in TEST_CASES:
        hasil, _ = diagnosa(_eng, _kb, ikan, gejala)
        utama = hasil[0][0] if hasil else None
        ok = utama == harapan
        sesuai += ok
        teks = ", ".join(f"{d} {cf:.0%}" for d, cf in hasil) or "tidak ada diagnosis"
        print(f"{tc_id:<4}{ikan:<8}{str(harapan):<12}{teks:<28}{'Ya' if ok else 'Tidak'}  ({ket})")
    print(f"\nAkurasi = {sesuai}/{len(TEST_CASES)} = {sesuai / len(TEST_CASES) * 100:.0f}%")


# ------------------------------------------------------------ konsistensi rule <-> penyakit <-> rujukan
SUMBER_PENYAKIT = {
    "P07": {"anshary2014", "hardi2011", "ugm_strep_pcr"},
    "P08": {"uf_fa184"},
}


def test_rule_strep_ke_p07(kb):
    for rid in ("R50", "R51", "R52", "R53"):
        r = kb.get_rule(rid)
        assert r["THEN"] == "P07", rid
        assert r["ikan"] == ["nila", "gurame"], rid
        assert set(r["sumber"]) <= SUMBER_PENYAKIT["P07"], rid


def test_rule_argulus_ke_p08(kb):
    for rid in ("R58", "R59", "R60", "R61"):
        r = kb.get_rule(rid)
        assert r["THEN"] in ("P08", "dugaan_ektoparasit_besar"), rid
        assert r["ikan"] == ["lele", "gurame"], rid
        assert r["sumber"] == ["uf_fa184"], rid
    assert any(r["THEN"] == "P08" for r in kb.rules)       # P08 kini punya rule


def test_p07_p08_ikan_sesuai_penyakit(kb):
    for pid in ("P07", "P08"):
        species = {s.lower() for s in kb.diseases[pid]["species"]}
        for r in kb.rules:
            if r["THEN"] == pid:
                assert set(r["ikan"]) <= species, (r["id"], pid)


def test_sumber_rule_sesuai_penyakit(kb):
    """Rule penyakit P07/P08 hanya boleh mengutip rujukan yang membahas penyakit itu."""
    for r in kb.rules:
        if r["THEN"] in SUMBER_PENYAKIT:
            assert set(r["sumber"]) <= SUMBER_PENYAKIT[r["THEN"]], r["id"]
    for r in kb.rules:   # fa184 = Argulus, tidak boleh dipakai untuk MAS
        if r["id"] in ("R05", "R06", "R07", "R08"):
            assert "uf_fa184" not in r["sumber"]


def test_diagnosis_p07_p08(engine, kb):
    hasil, _ = diagnosa(engine, kb, "gurame", {"G04": 1.0, "G07": 1.0})
    assert hasil[0][0] == "P07"
    hasil, _ = diagnosa(engine, kb, "lele", {"G50": 1.0, "G52": 1.0})
    assert hasil[0][0] == "P08"
    hasil, _ = diagnosa(engine, kb, "lele", {"G04": 1.0, "G07": 1.0})
    assert hasil == []                                    # strep tidak untuk lele
    hasil, _ = diagnosa(engine, kb, "nila", {"G50": 1.0, "G52": 1.0})
    assert hasil == []                                    # argulus tidak untuk nila
