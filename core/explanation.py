"""Fasilitas penjelasan: WHY, HOW, dan diagram reasoning tree."""


def why(symptom_id: str, rules: list[dict], diseases: dict | None = None) -> str:
    """WHY: kenapa gejala ini ditanyakan (rule mana yang memakainya).

    Bila `diseases` diberikan, ikut menyebut penyakit yang ditentukan gejala ini
    (langsung atau lewat fakta hasil antara).
    """
    used = [r["id"] for r in rules if symptom_id in r["IF"]]
    if not used:
        return "Gejala ini belum dipakai oleh rule mana pun."
    teks = f"Gejala ini ditanyakan karena dipakai pada rule: {', '.join(used)}"
    if diseases:
        sasaran, antrean, dilihat = set(), {r["THEN"] for r in rules if symptom_id in r["IF"]}, set()
        while antrean:
            f = antrean.pop()
            if f in dilihat:
                continue
            dilihat.add(f)
            if f in diseases:
                sasaran.add(diseases[f].get("nama") or diseases[f].get("name") or f)
            antrean |= {r["THEN"] for r in rules if f in r["IF"]}
        if sasaran:
            teks += f". Membantu menilai: {', '.join(sorted(sasaran))}"
    return teks


def _ancestor_steps(fact: str, wm, rule_map: dict, visited: set, urut: list) -> None:
    """Telusuri mundur: kumpulkan rule yang berkontribusi pada `fact`, premis lebih dulu."""
    for src in wm.sources.get(fact, []):
        if src == "user" or src in visited or src not in rule_map:
            continue
        visited.add(src)
        for premise in rule_map[src]["IF"]:
            _ancestor_steps(premise, wm, rule_map, visited, urut)
        urut.append(src)


def how(disease_id: str, wm, rules: list[dict]) -> list[str]:
    """HOW: rantai penalaran berurutan dari fakta awal sampai kesimpulan."""
    rule_map = {r["id"]: r for r in rules}
    trace_by_rule = {s["rule"]: s for s in wm.trace}
    urut: list[str] = []
    _ancestor_steps(disease_id, wm, rule_map, set(), urut)
    lines = []
    for src in urut:
        rule, step = rule_map[src], trace_by_rule.get(src)
        if step is None:
            continue
        lines.append(
            f"{src}: IF {' AND '.join(rule['IF'])} THEN {rule['THEN']} "
            f"(CF rule {rule['CF']}, CF hasil {step['cf_hasil']})"
        )
    return lines


def reasoning_graph(disease_id: str, wm, rules: list[dict], labels: dict | None = None) -> str:
    """Reasoning tree dalam format DOT (untuk st.graphviz_chart). Opsional."""
    labels = labels or {}
    rule_map = {r["id"]: r for r in rules}
    urut: list[str] = []
    _ancestor_steps(disease_id, wm, rule_map, set(), urut)

    def esc(text: str) -> str:
        return str(text).replace('"', "'")

    def fact_label(f: str) -> str:
        cf = wm.facts.get(f)
        nama = labels.get(f, f)
        return f"{nama}\\nCF {cf:.2f}" if cf is not None else nama

    baris = ["digraph G {", "rankdir=LR;", 'bgcolor="transparent";',
             'node [fontname="Helvetica", fontcolor="#E8EEF6", color="#6FA8DC"];',
             'edge [color="#9FB3CC"];']
    fakta = set()
    for rid in urut:
        r = rule_map[rid]
        baris.append(f'"{rid}" [shape=ellipse, style=filled, fillcolor="#1B2D47", '
                     f'label="{rid}\\nCF rule {r["CF"]}"];')
        for p in r["IF"]:
            fakta.add(p)
            baris.append(f'"{esc(p)}" -> "{rid}";')
        fakta.add(r["THEN"])
        baris.append(f'"{rid}" -> "{esc(r["THEN"])}";')
    for f in sorted(fakta):
        warna = "#2F5E8F" if f == disease_id else "#0F1F3A"
        baris.append(f'"{esc(f)}" [shape=box, style="rounded,filled", fillcolor="{warna}", '
                     f'label="{esc(fact_label(f))}"];')
    baris.append("}")
    return "\n".join(baris)
