"""Orchestrateur de rendu : JSON -> validation -> contexte -> HTML -> PDF + PNG.

build_html() est testable sans WeasyPrint (utile en local/Windows).
render_pdf() ajoute le rendu PDF + l'aperçu PNG (dépend de WeasyPrint, en cloud).
"""
from __future__ import annotations

import json
import pathlib

import jinja2
from jsonschema import validate

from . import charts, condense, derive

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
SCHEMA = json.loads((ROOT / "schema" / "brief.schema.json").read_text(encoding="utf-8"))
P = derive.PALETTE

# Teintes claires (fond de tuile) + texte assorti, par sens.
TINT = {
    "up":      ("#E4F0E8", P["up"]),
    "down":    ("#F6E4E2", P["down"]),
    "neutre":  ("#EEEBE4", P["neutral"]),
    "warn":    ("#F6ECD8", P["warn"]),
}


def validate_payload(data: dict) -> None:
    validate(data, SCHEMA)


def _sens(biais: str | None) -> str:
    b = (biais or "").lower()
    if b in ("haussier", "long", "detente", "détente"):
        return "up"
    if b in ("baissier", "short"):
        return "down"
    if b in ("attente", "neutre", "range", ""):
        return "neutre"
    return "warn"


def _tier_color(tier) -> str:
    return {1: P["down"], 2: P["warn"], 3: P["muted"]}.get(tier or 3, P["muted"])


def _pills(data: dict) -> list[dict]:
    vol = data.get("volatilite", {}) or {}
    crb = data.get("courbe", {}) or {}
    out = []

    def add(metric, label, value, disp):
        col, sym = derive.dashboard_state(metric, value)
        out.append({"label": label, "disp": disp, "color": col, "sym": sym})

    if vol.get("vix") is not None:
        add("vix", "VIX", vol["vix"], derive.fmt(vol["vix"], 1))
    if crb.get("spread_2s10s") is not None:
        add("2s10s", "2s10s", crb["spread_2s10s"], f"{derive.fmt_signed(crb['spread_2s10s'], 0)} pb")
    if crb.get("spread_oat_bund") is not None:
        add("oat", "OAT-Bund", crb["spread_oat_bund"], f"{derive.fmt(crb['spread_oat_bund'], 0)} pb")
    for ca in data.get("cross_asset", []) or []:
        if ca["label"].lower() in ("brent", "pétrole", "petrole"):
            add("brent", "Brent", ca["pct"], derive.fmt_pct(ca["pct"], 1))
            break
    return out


def build_context(data: dict) -> dict:
    rails = [{"n": n, "svg": charts.rail(n)} for n in data["niveaux"]]
    secteurs = []
    for s in data.get("secteurs", []) or []:
        bg, fg = TINT[_sens(s.get("biais"))]
        secteurs.append({"s": s, "bg": bg, "fg": fg})
    playbook = [{"r": r, "bg": TINT[_sens(r["biais"])][0]} for r in data.get("playbook", []) or []]
    agenda = [{"a": a, "tc": _tier_color(a.get("tier", 3))} for a in data.get("agenda", []) or []]
    return dict(
        d=data, P=P, rails=rails, pills=_pills(data),
        secteurs=secteurs, playbook=playbook, agenda=agenda,
        svg_curve=charts.yield_curve(data.get("courbe", {}) or {}),
        svg_cross=charts.cross_asset_bars(data.get("cross_asset", []) or []),
        svg_vix=charts.vix_gauge(data.get("volatilite", {}) or {}),
    )


def _env() -> jinja2.Environment:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES)),
        autoescape=True,  # échappe les données ; les SVG sont marqués |safe
    )
    env.filters["fmt"] = derive.fmt
    env.filters["pct"] = derive.fmt_pct
    env.filters["signed"] = derive.fmt_signed
    return env


def build_html(data: dict) -> str:
    return _env().get_template("brief.html.j2").render(**build_context(data))


def render_pdf(data: dict, out_dir: str | pathlib.Path) -> pathlib.Path:
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    html = build_html(data)
    (out / "brief.html").write_text(html, encoding="utf-8")

    from weasyprint import HTML  # importé tardivement (absent en local Windows)
    HTML(string=html, base_url=str(ROOT)).write_pdf(str(out / "brief.pdf"))

    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(str(out / "brief.pdf"))
        pdf[0].render(scale=2.2).to_pil().save(str(out / "preview.png"))
    except Exception as exc:  # l'aperçu est un bonus, jamais bloquant
        print("preview PNG ignoré:", exc)

    (out / "condense.txt").write_text(condense.build_condense(data), encoding="utf-8")
    return out
