"""Working memory: fakta sementara, asal fakta, dan jejak inferensi."""


class WorkingMemory:
    """Menyimpan fakta (gejala + hasil antara + kesimpulan) selama satu konsultasi."""

    def __init__(self):
        self.facts: dict[str, float] = {}        # fakta -> CF
        self.sources: dict[str, list[str]] = {}  # fakta -> ['user'] atau [id rule, ...]
        self.trace: list[dict] = []              # jejak penalaran berurutan
        self.fired: set[str] = set()             # rule yang sudah dieksekusi

    def add_fact(self, name: str, cf: float, source: str = "user") -> None:
        """Tambah/perbarui fakta dan catat asalnya."""
        self.facts[name] = cf
        self.sources.setdefault(name, [])
        if source not in self.sources[name]:
            self.sources[name].append(source)

    def has(self, name: str) -> bool:
        return name in self.facts

    def log(self, step: dict) -> None:
        self.trace.append(step)

    def rules_used(self) -> list[str]:
        """ID rule yang dieksekusi, sesuai urutan eksekusi."""
        return [s["rule"] for s in self.trace]
