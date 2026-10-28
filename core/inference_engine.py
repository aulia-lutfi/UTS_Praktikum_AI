# """Mesin inferensi forward chaining dengan Certainty Factor."""
# from core.certainty import combine, rule_cf
# from core.working_memory import WorkingMemory


# class InferenceEngine:
#     """Forward chaining: dari fakta (gejala) menuju kesimpulan (penyakit)."""

#     def __init__(self, rules: list[dict]):
#         # Sengaja menyimpan referensi (bukan salinan) agar perubahan rule
#         # lewat CRUD langsung terlihat oleh engine.
#         self.rules = rules

#     def _applicable(self, jenis_ikan: str) -> list[dict]:
#         return [r for r in self.rules if jenis_ikan in r.get("ikan", [jenis_ikan])]

#     @staticmethod
#     def _live_rules(rules: list[dict], known: set[str]) -> list[dict]:
#         """Rule yang premisnya mungkin terpenuhi (penutup transitif dari fakta awal)."""
#         reachable = set(known)
#         changed = True
#         while changed:
#             changed = False
#             for r in rules:
#                 if r["THEN"] not in reachable and all(p in reachable for p in r["IF"]):
#                     reachable.add(r["THEN"])
#                     changed = True
#         return [r for r in rules if all(p in reachable for p in r["IF"])]

#     def forward_chain(self, user_facts: dict[str, float], jenis_ikan: str) -> WorkingMemory:
#         """Jalankan inferensi dan kembalikan WorkingMemory berisi fakta + trace.

#         Sebuah rule baru dieksekusi saat premisnya sudah "final", yaitu tidak ada
#         rule lain yang masih bisa menambah CF premis tersebut. Ini mencegah CF
#         hasil antara yang belum lengkap dipakai oleh rule bertingkat.
#         """
#         wm = WorkingMemory()
#         for name, cf in user_facts.items():
#             wm.add_fact(name, cf, "user")

#         rules = self._applicable(jenis_ikan)
#         live = self._live_rules(rules, set(user_facts))
#         iteration = 0

#         while True:
#             pending = [r for r in live if r["id"] not in wm.fired]
#             if not pending:
#                 break
#             pending_outputs = {r["THEN"]: [] for r in pending}
#             for r in pending:
#                 pending_outputs[r["THEN"]].append(r["id"])

#             ready = [
#                 r for r in pending
#                 if all(wm.has(p) for p in r["IF"])
#                 and not any(
#                     any(rid != r["id"] for rid in pending_outputs.get(p, []))
#                     for p in r["IF"]
#                 )
#             ]
#             if not ready:
#                 # Cadangan (mis. siklus antar rule): eksekusi rule pertama yang premisnya ada.
#                 ready = [r for r in pending if all(wm.has(p) for p in r["IF"])][:1]
#             if not ready:
#                 break

#             iteration += 1
#             for rule in ready:
#                 premise = [wm.facts[c] for c in rule["IF"]]
#                 new_cf = rule_cf(premise, rule["CF"])
#                 old_cf = wm.facts.get(rule["THEN"])
#                 final_cf = combine(old_cf, new_cf) if old_cf is not None else new_cf
#                 wm.add_fact(rule["THEN"], final_cf, rule["id"])
#                 wm.fired.add(rule["id"])
#                 wm.log({
#                     "iterasi": iteration, "rule": rule["id"],
#                     "IF": list(rule["IF"]), "THEN": rule["THEN"],
#                     "cf_rule": rule["CF"], "cf_premis": [round(p, 3) for p in premise],
#                     "cf_hasil": round(new_cf, 3), "cf_akumulasi": round(final_cf, 3),
#                 })
#         return wm

#     def get_diagnoses(self, wm: WorkingMemory, disease_ids) -> list[tuple[str, float]]:
#         """Penyakit yang terdeteksi (CF > 0), urut dari CF tertinggi."""
#         hasil = [(d, wm.facts[d]) for d in disease_ids if d in wm.facts and wm.facts[d] > 0]
#         return sorted(hasil, key=lambda x: x[1], reverse=True)

#     def backward_chain(self, goal: str, user_facts: dict[str, float], jenis_ikan: str) -> dict:
#         """Backward chaining (goal-driven): uji apakah hipotesis `goal` didukung fakta.

#         Mulai dari goal (mis. ID penyakit), cari rule yang menyimpulkannya, lalu
#         buktikan premisnya secara rekursif (premis = gejala dari user atau fakta
#         hasil rule lain). Gejala yang belum diketahui dicatat sebagai pertanyaan
#         lanjutan (konteks WHY: \"ditanyakan karena rule X membutuhkannya\").

#         Mengembalikan dict: cf (0 bila belum terbukti), terbukti, trace (daftar
#         teks langkah), kurang (rule -> gejala yang belum diketahui).
#         """
#         rules = self._applicable(jenis_ikan)
#         trace: list[str] = []
#         kurang: dict[str, list[str]] = {}

#         def buktikan(fakta: str, kedalaman: int, jalur: tuple) -> float | None:
#             indent = "  " * kedalaman
#             if fakta in user_facts:
#                 trace.append(f"{indent}{fakta} diketahui dari user (CF {user_facts[fakta]:.2f})")
#                 return user_facts[fakta]
#             kandidat = [r for r in rules if r["THEN"] == fakta]
#             if not kandidat or fakta in jalur:
#                 trace.append(f"{indent}{fakta} tidak diketahui dan tidak ada rule yang menyimpulkannya")
#                 return None
#             hasil: float | None = None
#             for r in kandidat:
#                 trace.append(f"{indent}Goal {fakta}: coba {r['id']} (IF {' AND '.join(r['IF'])})")
#                 cfs, hilang = [], []
#                 for prem in r["IF"]:
#                     cf = buktikan(prem, kedalaman + 1, jalur + (fakta,))
#                     if cf is None:
#                         hilang.append(prem)
#                     else:
#                         cfs.append(cf)
#                 if hilang:
#                     kurang[r["id"]] = hilang
#                     trace.append(f"{indent}  {r['id']} gagal: premis belum terbukti -> {', '.join(hilang)}")
#                     continue
#                 cf_rule = rule_cf(cfs, r["CF"])
#                 trace.append(f"{indent}  {r['id']} terbukti, CF = min{[round(c, 2) for c in cfs]} x {r['CF']} = {cf_rule:.3f}")
#                 hasil = cf_rule if hasil is None else combine(hasil, cf_rule)
#             return hasil

#         cf = buktikan(goal, 0, ())
#         return {"cf": cf or 0.0, "terbukti": cf is not None and cf > 0, "trace": trace, "kurang": kurang}

"""Mesin inferensi forward chaining dengan Certainty Factor."""
from core.certainty import combine, rule_cf
from core.working_memory import WorkingMemory


class InferenceEngine:
    """Forward chaining: dari fakta (gejala) menuju kesimpulan (penyakit)."""

    def __init__(self, rules: list[dict]):
        # Sengaja menyimpan referensi (bukan salinan) agar perubahan rule
        # lewat CRUD langsung terlihat oleh engine.
        self.rules = rules

    def _applicable(self, jenis_ikan: str) -> list[dict]:
        return [r for r in self.rules if jenis_ikan in r.get("ikan", [jenis_ikan])]

    def forward_chain(self, user_facts: dict[str, float], jenis_ikan: str) -> WorkingMemory:
        """Jalankan inferensi dan kembalikan WorkingMemory berisi fakta + trace.

        Sebuah rule baru dieksekusi saat premisnya sudah "final", yaitu tidak ada
        rule lain yang masih bisa menambah CF premis tersebut. Ini mencegah CF
        hasil antara yang belum lengkap dipakai oleh rule bertingkat.
        """
        wm = WorkingMemory()
        for name, cf in user_facts.items():
            wm.add_fact(name, cf, "user")

        rules = self._applicable(jenis_ikan)
        
        while True:
            ready_rules = []
            
            for r in rules:
                if r["id"] in wm.fired:
                    continue
                
                # Syarat 1: Semua premis sudah ada di Working Memory
                if not all(wm.has(p) for p in r["IF"]):
                    continue
                
                # Syarat 2: Cek apakah ada rule LAIN yang belum dieksekusi 
                # yang bisa menghasilkan salah satu premis rule ini
                premis_belum_final = False
                for p in r["IF"]:
                    for other_r in rules:
                        if other_r["id"] not in wm.fired and other_r["THEN"] == p:
                            premis_belum_final = True
                            break
                    if premis_belum_final:
                        break
                
                if not premis_belum_final:
                    ready_rules.append(r)
            
            # Jika tidak ada rule yang siap, hentikan inferensi
            if not ready_rules:
                break
                
            # Eksekusi semua rule yang siap di iterasi ini
            for rule in ready_rules:
                premise = [wm.facts[c] for c in rule["IF"]]
                new_cf = rule_cf(premise, rule["CF"])
                
                # Jika rule gugur (CF 0), jangan masukkan ke WM
                if new_cf > 0:
                    old_cf = wm.facts.get(rule["THEN"])
                    final_cf = combine(old_cf, new_cf) if old_cf is not None else new_cf
                    wm.add_fact(rule["THEN"], final_cf, rule["id"])
                
                wm.fired.add(rule["id"])
                wm.log({
                    "rule": rule["id"],
                    "IF": list(rule["IF"]), "THEN": rule["THEN"],
                    "cf_rule": rule["CF"], "cf_premis": [round(p, 3) for p in premise],
                    "cf_hasil": round(new_cf, 3), 
                    "cf_akumulasi": round(wm.facts.get(rule["THEN"], 0), 3),
                })
                
        return wm

    def get_diagnoses(self, wm: WorkingMemory, disease_ids) -> list[tuple[str, float]]:
        """Penyakit yang terdeteksi (CF > 0), urut dari CF tertinggi."""
        hasil = [(d, wm.facts[d]) for d in disease_ids if d in wm.facts and wm.facts[d] > 0]
        return sorted(hasil, key=lambda x: x[1], reverse=True)

    def backward_chain(self, goal: str, user_facts: dict[str, float], jenis_ikan: str) -> dict:
        """Backward chaining (goal-driven): uji apakah hipotesis `goal` didukung fakta.

        Mulai dari goal (mis. ID penyakit), cari rule yang menyimpulkannya, lalu
        buktikan premisnya secara rekursif (premis = gejala dari user atau fakta
        hasil rule lain). Gejala yang belum diketahui dicatat sebagai pertanyaan
        lanjutan (konteks WHY: "ditanyakan karena rule X membutuhkannya").

        Mengembalikan dict: cf (0 bila belum terbukti), terbukti, trace (daftar
        teks langkah), kurang (rule -> gejala yang belum diketahui).
        """
        rules = self._applicable(jenis_ikan)
        trace: list[str] = []
        kurang: dict[str, list[str]] = {}

        def buktikan(fakta: str, kedalaman: int, jalur: tuple) -> float | None:
            indent = "  " * kedalaman
            if fakta in user_facts:
                trace.append(f"{indent}{fakta} diketahui dari user (CF {user_facts[fakta]:.2f})")
                return user_facts[fakta]
            
            # Cegah siklus (loop)
            if fakta in jalur:
                trace.append(f"{indent}{fakta} terdeteksi siklus, dihentikan.")
                return None
                
            kandidat = [r for r in rules if r["THEN"] == fakta]
            if not kandidat:
                trace.append(f"{indent}{fakta} tidak diketahui dan tidak ada rule yang menyimpulkannya")
                return None
            
            hasil: float | None = None
            for r in kandidat:
                trace.append(f"{indent}Goal {fakta}: coba {r['id']} (IF {' AND '.join(r['IF'])})")
                cfs, hilang = [], []
                
                for prem in r["IF"]:
                    cf = buktikan(prem, kedalaman + 1, jalur + (fakta,))
                    if cf is None:
                        hilang.append(prem)
                    else:
                        cfs.append(cf)
                        
                if hilang:
                    kurang[r["id"]] = hilang
                    trace.append(f"{indent}  {r['id']} gagal: premis belum terbukti -> {', '.join(hilang)}")
                    continue
                    
                cf_rule = rule_cf(cfs, r["CF"])
                trace.append(f"{indent}  {r['id']} terbukti, CF = {cf_rule:.3f}")
                if cf_rule > 0:
                    hasil = cf_rule if hasil is None else combine(hasil, cf_rule)
            
            return hasil

        cf = buktikan(goal, 0, ())
        return {"cf": cf or 0.0, "terbukti": cf is not None and cf > 0, "trace": trace, "kurang": kurang}