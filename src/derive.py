"""Calculs et helpers déterministes (aucun LLM ici).

Tout ce qui est dérivé (positions, couleurs, formats, seuils) est calculé en
code pour garantir un rendu identique chaque matin.
"""
from __future__ import annotations

# Palette « newsletter premium » sur fond clair. La couleur ne sert qu'au SENS.
PALETTE = {
    "navy":    "#14304A",  # marque
    "ink":     "#2B2B2B",  # texte
    "muted":   "#6B7280",  # texte secondaire
    "rule":    "#D8D2C8",  # filets
    "paper":   "#FAF8F4",  # fond
    "tint":    "#F1EEE8",  # fond de carte héros
    "up":      "#1B7F4B",  # haussier
    "down":    "#C0392B",  # baissier
    "warn":    "#C8861A",  # alerte / neutre-vigilant
    "amber2":  "#E3B768",  # ambre clair (segments)
    "neutral": "#5B6B7B",  # neutre
}

MINUS = "−"  # vrai signe moins typographique


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def fmt(value, decimals: int = 0) -> str:
    """Format FR : espace fine pour les milliers, virgule décimale."""
    if value is None:
        return "—"
    s = f"{value:,.{decimals}f}"          # 12,345.67
    return s.replace(",", " ").replace(".", ",")  # -> 12 345,67


def fmt_signed(value, decimals: int = 2) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else (MINUS if value < 0 else "")
    return f"{sign}{fmt(abs(value), decimals)}"


def fmt_pct(value, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{fmt_signed(value, decimals)} %"


def level_color(biais: str | None) -> str:
    b = (biais or "").strip().lower()
    if b in ("haussier", "long", "detente", "détente"):
        return PALETTE["up"]
    if b in ("baissier", "short"):
        return PALETTE["down"]
    if b in ("neutre", "", "attente", "range"):
        return PALETTE["neutral"]
    return PALETTE["warn"]


def rail_ratio(value: float, low: float, high: float) -> float:
    if high == low:
        return 0.5
    return clamp((value - low) / (high - low), 0.0, 1.0)


# --- Pivot classique (si H/L/C de la veille dispo). Optionnel. ---
def pivot_points(high, low, close):
    if None in (high, low, close):
        return None
    pp = (high + low + close) / 3.0
    return {
        "pp": pp,
        "r1": 2 * pp - low,
        "s1": 2 * pp - high,
        "r2": pp + (high - low),
        "s2": pp - (high - low),
    }


# --- Dashboard de régime : seuils FIXES -> (couleur, symbole) ---
def dashboard_state(metric: str, value):
    """Couleur + symbole déterministes par métrique connue."""
    if value is None:
        return PALETTE["neutral"], "●"  # ●
    m = metric.lower()
    if "vix" in m:
        if value < 15:
            return PALETTE["up"], "●"
        if value < 20:
            return PALETTE["warn"], "▲"
        return PALETTE["down"], "▲"
    if "2s10s" in m or "pente" in m:
        return (PALETTE["up"], "▲") if value >= 0 else (PALETTE["down"], "▼")
    if "oat" in m:  # spread OAT-Bund : stress France
        if value < 60:
            return PALETTE["up"], "●"
        if value <= 80:
            return PALETTE["warn"], "●"
        return PALETTE["down"], "▲"
    # défaut : neutre, flèche selon signe
    return PALETTE["neutral"], ("▲" if value >= 0 else "▼")
