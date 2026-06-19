"""Graphiques en SVG inline, générés de façon déterministe.

Chaque fonction renvoie une chaîne SVG (width=100%) prête à injecter dans le
HTML. Formes simples uniquement (rect/line/circle/polyline/text) -> compatible
WeasyPrint, net à toute échelle, identique chaque matin.
"""
from __future__ import annotations

from .derive import PALETTE, fmt, fmt_pct, level_color, rail_ratio, clamp


def _svg(w: int, h: int, body: str) -> str:
    return (
        f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" font-family="DejaVu Sans, sans-serif">{body}</svg>'
    )


def rail(item: dict) -> str:
    """Rail support/résistance : segment [sup2..res2] + zone + marqueur spot."""
    spot, s2, r2 = item["spot"], item["sup2"], item["res2"]
    s1, r1 = item["sup1"], item["res1"]
    dec = item.get("decimals", 0)
    color = level_color(item.get("biais"))
    w, h = 320, 30
    x0, x1, y = 8, 312, 19

    def X(v):
        return x0 + (x1 - x0) * rail_ratio(v, s2, r2)

    b = []
    b.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{PALETTE["rule"]}" stroke-width="3" stroke-linecap="round"/>')
    b.append(f'<line x1="{X(s1):.1f}" y1="{y}" x2="{X(r1):.1f}" y2="{y}" stroke="{PALETTE["neutral"]}" stroke-width="3" stroke-linecap="round"/>')
    b.append(f'<line x1="{X(s1):.1f}" y1="{y-6}" x2="{X(s1):.1f}" y2="{y+6}" stroke="{PALETTE["up"]}" stroke-width="2"/>')
    b.append(f'<line x1="{X(r1):.1f}" y1="{y-6}" x2="{X(r1):.1f}" y2="{y+6}" stroke="{PALETTE["down"]}" stroke-width="2"/>')
    b.append(f'<circle cx="{X(spot):.1f}" cy="{y}" r="5.5" fill="{color}" stroke="{PALETTE["paper"]}" stroke-width="2"/>')
    b.append(f'<text x="{x0}" y="10" font-size="8" fill="{PALETTE["muted"]}">{fmt(s2, dec)}</text>')
    b.append(f'<text x="{x1}" y="10" font-size="8" fill="{PALETTE["muted"]}" text-anchor="end">{fmt(r2, dec)}</text>')
    return _svg(w, h, "".join(b))


def yield_curve(courbe: dict) -> str:
    """Courbe des taux US (points discrets 2Y/5Y/10Y)."""
    pts = courbe.get("points") or []
    if not pts:
        return ""
    w, h = 320, 120
    padl, padr, padt, padb = 26, 12, 16, 24
    vals = [p["v"] for p in pts]
    vmin, vmax = min(vals), max(vals)
    if vmax == vmin:
        vmax = vmin + 0.5
    pad = (vmax - vmin) * 0.18 or 0.1
    vmin -= pad
    vmax += pad
    n = len(pts)

    def X(i):
        return padl + (w - padl - padr) * (i / (n - 1) if n > 1 else 0.5)

    def Y(v):
        return padt + (h - padt - padb) * (1 - (v - vmin) / (vmax - vmin))

    b = []
    poly = " ".join(f"{X(i):.1f},{Y(p['v']):.1f}" for i, p in enumerate(pts))
    b.append(f'<polyline points="{poly}" fill="none" stroke="{PALETTE["navy"]}" stroke-width="2"/>')
    for i, p in enumerate(pts):
        b.append(f'<circle cx="{X(i):.1f}" cy="{Y(p["v"]):.1f}" r="3" fill="{PALETTE["navy"]}"/>')
        b.append(f'<text x="{X(i):.1f}" y="{h-10}" font-size="8" text-anchor="middle" fill="{PALETTE["muted"]}">{p["t"]}</text>')
        b.append(f'<text x="{X(i):.1f}" y="{Y(p["v"])-7:.1f}" font-size="8" text-anchor="middle" fill="{PALETTE["ink"]}">{fmt(p["v"], 2)}</text>')
    return _svg(w, h, "".join(b))


def cross_asset_bars(items: list) -> str:
    """Barres divergentes des variations overnight (autour de zéro)."""
    items = (items or [])[:7]
    if not items:
        return ""
    rowh, w = 22, 320
    h = len(items) * rowh + 8
    cx, maxlen = 116, 150
    maxabs = max((abs(i["pct"]) for i in items), default=1) or 1
    b = [f'<line x1="{cx}" y1="4" x2="{cx}" y2="{h-4}" stroke="{PALETTE["rule"]}" stroke-width="1"/>']
    for k, it in enumerate(items):
        yc = 8 + k * rowh + 8
        pct = it["pct"]
        length = abs(pct) / maxabs * maxlen
        up = pct >= 0
        color = PALETTE["up"] if up else PALETTE["down"]
        bx = cx if up else cx - length
        b.append(f'<text x="4" y="{yc+3:.1f}" font-size="9" fill="{PALETTE["ink"]}">{it["label"]}</text>')
        b.append(f'<rect x="{bx:.1f}" y="{yc-5:.1f}" width="{length:.1f}" height="10" rx="2" fill="{color}"/>')
        vx = cx + length + 4 if up else cx - length - 4
        anchor = "start" if up else "end"
        b.append(f'<text x="{vx:.1f}" y="{yc+3:.1f}" font-size="8.5" text-anchor="{anchor}" fill="{color}">{fmt_pct(pct, 2)}</text>')
    return _svg(w, h, "".join(b))


def vix_gauge(vol: dict) -> str:
    """Jauge VIX segmentée par régime (calme/normal/stress/panique)."""
    vix = (vol or {}).get("vix")
    if vix is None:
        return ""
    w, h = 320, 44
    x0, x1, y, maxv = 8, 312, 22, 40
    segs = [(0, 15, PALETTE["up"]), (15, 20, PALETTE["amber2"]),
            (20, 30, PALETTE["warn"]), (30, 40, PALETTE["down"])]

    def X(v):
        return x0 + (x1 - x0) * clamp(v, 0, maxv) / maxv

    b = []
    for a, c, col in segs:
        b.append(f'<rect x="{X(a):.1f}" y="{y}" width="{X(c)-X(a):.1f}" height="8" fill="{col}"/>')
    mx = X(vix)
    b.append(f'<polygon points="{mx-4:.1f},{y-3} {mx+4:.1f},{y-3} {mx:.1f},{y+2}" fill="{PALETTE["ink"]}"/>')
    b.append(f'<text x="{mx:.1f}" y="{y-6}" font-size="9" font-weight="bold" text-anchor="middle" fill="{PALETTE["ink"]}">VIX {fmt(vix, 1)}</text>')
    for v, t in [(7.5, "calme"), (17.5, "normal"), (25, "stress"), (35, "panique")]:
        b.append(f'<text x="{X(v):.1f}" y="{y+19}" font-size="7.5" text-anchor="middle" fill="{PALETTE["muted"]}">{t}</text>')
    return _svg(w, h, "".join(b))
