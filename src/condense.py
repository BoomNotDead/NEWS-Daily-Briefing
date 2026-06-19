"""Construit le condensé (Discord / Telegram) — version « lisible par un débutant ».

Texte aéré, 1 info par ligne, emojis-signal, explications en français simple.
Dérivé du MÊME JSON que le PDF (jamais une troncature du brief long).
"""
from __future__ import annotations

from .derive import fmt

# Emoji par actif (le condensé est de la messagerie : emojis OK).
EMOJI = {
    "CAC 40": "🇫🇷", "CAC40": "🇫🇷", "DAX": "🇩🇪",
    "EUR/USD": "💶", "Brent": "🛢", "Pétrole": "🛢", "Or": "🥇",
    "US 10 ans": "🇺🇸", "US10Y": "🇺🇸", "Nasdaq": "💻", "S&P 500": "🇺🇸",
}

SEP = "────────────"


def _u(unit: str | None) -> str:
    return f" {unit}" if unit else ""


def build_condense(data: dict, max_len: int = 4096) -> str:
    c = data.get("condense", {}) or {}
    m = data.get("meta", {}) or {}
    v = data.get("volatilite", {}) or {}
    L: list[str] = []

    L.append(f"📊 TRADING BRIEF MATIN — {m.get('date_str', '')} · {m.get('heure', '8h')}")
    L.append("")
    L.append("🎯 L'IDÉE DU JOUR")
    L.append((c.get("idee") or "").strip())

    if c.get("pourquoi"):
        L += ["", "💡 POURQUOI ?", c["pourquoi"].strip()]
    if c.get("evenement"):
        L += ["", "📅 L'ÉVÉNEMENT DU JOUR", c["evenement"].strip()]

    L += ["", SEP, "", "📈 NIVEAUX CLÉS"]
    for n in data.get("niveaux", []):
        e = EMOJI.get(n["actif"], "•")
        dec = n.get("decimals", 0)
        unit = n.get("unit", "")
        spot = f"{fmt(n['spot'], dec)}{_u(unit)}"
        zone = f"{fmt(n['sup1'], dec)} – {fmt(n['res1'], dec)}{_u(unit)}"
        L.append(f"{e} {n['actif']} : {spot}  ·  zone {zone}")

    if v.get("vix") is not None:
        etat = "bas, marché plutôt calme" if v["vix"] < 20 else "élevé, prudence"
        L += ["", f"😨 Stress du marché (indice VIX) : {fmt(v['vix'], 1)} → {etat}."]

    L += ["", SEP, "", "🗺 LE PLAN"]
    if c.get("plan_avant"):
        L.append(f"• Avant l'événement : {c['plan_avant'].strip()}")
    if c.get("plan_apres"):
        L.append(f"• Après : {c['plan_apres'].strip()}")
    if c.get("a_surveiller"):
        L.append(f"• À surveiller : {c['a_surveiller'].strip()}")

    if c.get("overnight"):
        L += ["", f"📊 Cette nuit : {c['overnight'].strip()}"]
    if c.get("inflation"):
        L.append(f"Inflation US : {c['inflation']}.")

    L += ["", "📎 Newsletter complète (PDF + graphiques) en pièce jointe.",
          "⚠️ Analyse, pas un conseil en investissement."]

    text = "\n".join(L)
    if len(text) > max_len:                       # garde-fou (rare)
        text = text[: max_len - 1].rstrip() + "…"
    return text
