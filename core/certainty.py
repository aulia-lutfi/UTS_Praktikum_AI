# """Perhitungan Certainty Factor (CF) model MYCIN."""


# def combine(cf1: float, cf2: float) -> float:
#     """Gabungkan dua CF untuk hipotesis yang sama (evidence ganda)."""
#     if cf1 >= 0 and cf2 >= 0:
#         return cf1 + cf2 * (1 - cf1)
#     if cf1 < 0 and cf2 < 0:
#         return cf1 + cf2 * (1 + cf1)
#     penyebut = 1 - min(abs(cf1), abs(cf2))
#     if penyebut == 0:  # +1 dan -1 saling meniadakan
#         return 0.0
#     return (cf1 + cf2) / penyebut


# def rule_cf(premise_cfs: list[float], rule_cf_value: float) -> float:
#     """CF kesimpulan = min(CF semua premis) x CF rule (premis AND)."""
#     if not premise_cfs:
#         return 0.0
#     return min(premise_cfs) * rule_cf_value

"""Perhitungan Certainty Factor (CF) model MYCIN."""


def combine(cf1: float, cf2: float) -> float:
    """Gabungkan dua CF untuk hipotesis yang sama (evidence ganda)."""
    if cf1 >= 0 and cf2 >= 0:
        return cf1 + cf2 * (1 - cf1)
    if cf1 < 0 and cf2 < 0:
        return cf1 + cf2 * (1 + cf1)
    penyebut = 1 - min(abs(cf1), abs(cf2))
    if penyebut == 0:  # +1 dan -1 saling meniadakan
        return 0.0
    return (cf1 + cf2) / penyebut


def rule_cf(premise_cfs: list[float], rule_cf_value: float) -> float:
    """CF kesimpulan = min(CF semua premis) x CF rule (premis AND)."""
    if not premise_cfs:
        return 0.0
    # Jika ada premis yang CF-nya <= 0 (tidak terjadi), rule gugur
    if any(cf <= 0 for cf in premise_cfs):
        return 0.0
    return min(premise_cfs) * rule_cf_value