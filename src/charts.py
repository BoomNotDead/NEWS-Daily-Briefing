"""Graphiques en matplotlib -> PNG (data URI base64), déterministes.

Rendu raster haute résolution embarqué dans le HTML via <img>. Robuste dans
WeasyPrint, qualité « publication », inspectable en local (PNG), et durci sur
les cas extrêmes (VIX de krach, prix hors zone support/résistance, valeurs nulles).
"""
from __future__ import annotations

import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .derive import PALETTE, fmt, fmt_pct, fmt_signed, level_color  # noqa: E402

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.unicode_minus": False,
})
DPI = 200
DEEP_RED = "#6E1810"


def _uri(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, transparent=True,
                bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def cross_asset_bars(items: list) -> str:
    items = [i for i in (items or []) if i.get("pct") is not None]
    items = sorted(items, key=lambda x: x["pct"], reverse=True)[:9]
    if not items:
        return ""
    labels = [i["label"] for i in items]
    vals = [i["pct"] for i in items]
    colors = [PALETTE["up"] if v >= 0 else PALETTE["down"] for v in vals]
    n = len(items)
    maxv = max((abs(v) for v in vals), default=1) or 1

    fig, ax = plt.subplots(figsize=(3.25, 0.25 * n + 0.12))
    y = list(range(n))
    ax.barh(y, vals, color=colors, height=0.6, zorder=3)
    ax.axvline(0, color=PALETTE["muted"], lw=0.8, zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8, color=PALETTE["ink"])
    ax.invert_yaxis()
    # Étiquette de valeur : à l'intérieur de la barre la plus longue (texte blanc)
    # pour ne jamais sortir du cadre ; à l'extérieur sinon.
    for yi, v in zip(y, vals):
        inside = abs(v) > 0.78 * maxv
        if inside:
            ax.text(v - (0.02 * maxv if v >= 0 else -0.02 * maxv), yi, fmt_pct(v, 2),
                    va="center", ha="right" if v >= 0 else "left", fontsize=7.2, color="white")
        else:
            off = 0.05 * maxv if v >= 0 else -0.05 * maxv
            ax.text(v + off, yi, fmt_pct(v, 2), va="center",
                    ha="left" if v >= 0 else "right", fontsize=7.2, color=colors[yi])
    ax.set_xlim(-maxv * 1.32, maxv * 1.32)
    ax.set_xticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    return _uri(fig)


def yield_curve(courbe: dict) -> str:
    pts = (courbe or {}).get("points") or []
    if not pts:
        return ""
    xs = list(range(len(pts)))
    ys = [p["v"] for p in pts]
    labels = [p["t"] for p in pts]

    fig, ax = plt.subplots(figsize=(3.25, 1.05))
    ax.plot(xs, ys, "-o", color=PALETTE["navy"], lw=1.8, ms=4.5, zorder=4)
    slope_up = len(ys) > 1 and ys[-1] >= ys[0]
    for x, yv in zip(xs, ys):
        ax.annotate(fmt(yv, 2), (x, yv), textcoords="offset points",
                    xytext=(0, 7 if slope_up else -11), ha="center",
                    fontsize=7, color=PALETTE["ink"])

    extra = []
    if courbe.get("bund10y") is not None:
        extra.append(("Bund 10a", courbe["bund10y"], PALETTE["up"]))
    if courbe.get("oat10y") is not None:
        extra.append(("OAT 10a", courbe["oat10y"], PALETTE["warn"]))
    for lab, val, col in extra:
        ax.axhline(val, color=col, lw=1, ls=(0, (4, 3)), zorder=2)
        ax.text(xs[-1], val, f"{lab} {fmt(val, 2)}", va="bottom", ha="right",
                fontsize=6.6, color=col)

    if courbe.get("spread_2s10s") is not None:
        ax.text(0.015, 0.04, f"Pente 2-10 ans : {fmt_signed(courbe['spread_2s10s'], 0)} pb",
                transform=ax.transAxes, fontsize=6.8, color=PALETTE["ink"], va="bottom")

    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=8, color=PALETTE["muted"])
    ax.set_ylabel("rendement %", fontsize=7, color=PALETTE["muted"])
    ax.grid(axis="y", color=PALETTE["rule"], lw=0.5, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(PALETTE["rule"])
    ax.tick_params(length=0, labelsize=7, colors=PALETTE["muted"])
    ax.margins(x=0.12, y=0.30)
    return _uri(fig)


def vix_gauge(vol: dict) -> str:
    vol = vol or {}
    vix = vol.get("vix")
    if vix is None:
        return ""
    # Échelle adaptative : un VIX de krach (65/80) reste lisible.
    maxv = max(40.0, vix * 1.12)
    bounds = [(0, 15, PALETTE["up"]), (15, 20, PALETTE["amber2"]),
              (20, 30, PALETTE["warn"]), (30, 50, PALETTE["down"]), (50, 80, DEEP_RED)]

    fig, ax = plt.subplots(figsize=(3.25, 0.72))
    for a, b, c in bounds:
        if a >= maxv:
            break
        ax.axvspan(a, min(b, maxv), ymin=0.40, ymax=0.68, color=c, lw=0)
    ax.axvline(19, ymin=0.40, ymax=0.68, color=PALETTE["ink"], lw=0.8, ls=(0, (2, 2)))
    cur = min(vix, maxv)
    ax.annotate(f"VIX {fmt(vix, 1)}", (cur, 0.68), xytext=(cur, 1.0),
                ha="center", fontsize=9, fontweight="bold", color=PALETTE["ink"],
                arrowprops=dict(arrowstyle="-|>", color=PALETTE["ink"], lw=1.4))
    zones = [(7.5, "calme"), (17.5, "normal"), (25, "stress"), (38, "panique")]
    if maxv > 52:
        zones.append((65, "extrême"))
    for x, t in zones:
        if x < maxv:
            ax.text(x, 0.30, t, ha="center", va="top", fontsize=6.4, color=PALETTE["muted"])
    ax.set_xlim(0, maxv)
    ax.set_ylim(0, 1.12)
    ax.axis("off")
    return _uri(fig)


def rail(item: dict) -> str:
    spot, s2, r2 = item["spot"], item["sup2"], item["res2"]
    s1, r1 = item["sup1"], item["res1"]
    # Convention couleur unique : supports/résistances en gris neutre,
    # marqueur coloré par le biais — ou rouge/vert si CASSURE (gap).
    below, above = spot < s2, spot > r2
    breached = below or above
    marker = PALETTE["down"] if below else (PALETTE["up"] if above else level_color(item.get("biais")))
    lo, hi = min(s2, spot), max(r2, spot)

    fig, ax = plt.subplots(figsize=(3.9, 0.17))
    ax.hlines(0, s2, r2, color=PALETTE["rule"], lw=3.4, zorder=1)
    ax.hlines(0, s1, r1, color=PALETTE["neutral"], lw=3.4, zorder=2)
    ax.vlines(s1, -0.55, 0.55, color=PALETTE["muted"], lw=1.5, zorder=3)
    ax.vlines(r1, -0.55, 0.55, color=PALETTE["muted"], lw=1.5, zorder=3)
    ax.plot([spot], [0], "o", color=marker, ms=7, mec="white", mew=1.2, zorder=5)
    if breached:  # chevron d'alerte dans le sens de la cassure
        ax.annotate("", xy=(spot, 0), xytext=(s1 if below else r1, 0),
                    arrowprops=dict(arrowstyle="-|>", color=marker, lw=1.4), zorder=4)
    pad = (hi - lo) * 0.05 or 1
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(-1.0, 1.0)
    ax.axis("off")
    return _uri(fig)
