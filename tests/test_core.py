"""Test local de la logique pure (sans WeasyPrint) : schéma, charts, condensé."""
import json
import pathlib
import sys

from jsonschema import validate

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import charts, condense  # noqa: E402

data = json.loads((ROOT / "sample_brief.json").read_text(encoding="utf-8"))
schema = json.loads((ROOT / "schema" / "brief.schema.json").read_text(encoding="utf-8"))

validate(data, schema)
print("[ok] schéma validé")

rails = [charts.rail(n) for n in data["niveaux"]]
assert all(s.startswith("data:image/png") for s in rails)
print(f"[ok] {len(rails)} rails support/résistance")

yc = charts.yield_curve(data["courbe"])
ca = charts.cross_asset_bars(data["cross_asset"])
gauge = charts.vix_gauge(data["volatilite"])
assert all(s.startswith("data:image/png") for s in (yc, ca, gauge))
print("[ok] courbe des taux / barres cross-asset / jauge VIX")

txt = condense.build_condense(data)
assert "TRADING BRIEF" in txt and "CAC 40" in txt and "L'IDÉE DU JOUR" in txt
assert len(txt) <= 4096
print(f"[ok] condensé généré ({len(txt)} caractères)")

# Écrit des sorties de debug pour inspection visuelle.
dbg = ROOT / "_debug"
dbg.mkdir(exist_ok=True)
(dbg / "condense.txt").write_text(txt, encoding="utf-8")
def _img(uri, w=320):
    return f"<img src='{uri}' style='width:{w}px;display:block;margin:4px 0'>"

preview = ["<!doctype html><meta charset='utf-8'>",
           "<body style='font-family:sans-serif;max-width:380px;margin:20px'>"]
preview.append("<h4>Rails</h4>")
preview += [f"<div style='margin:6px 0'><b>{n['actif']}</b>{_img(r, 160)}</div>"
            for n, r in zip(data["niveaux"], rails)]
preview += ["<h4>Courbe des taux</h4>", _img(yc),
            "<h4>Cross-asset</h4>", _img(ca),
            "<h4>Jauge VIX</h4>", _img(gauge), "</body>"]
(dbg / "charts.html").write_text("".join(preview), encoding="utf-8")
print(f"[ok] debug écrit dans {dbg}")

# Cas extrêmes (non-régression des bornes charts) : aucune exception, data URI non vide.
stress = [
    charts.vix_gauge({"vix": 85}),
    charts.cross_asset_bars([{"label": "X", "pct": -12.5}, {"label": "Y", "pct": 8.0}, {"label": "Z", "pct": None}]),
    charts.rail({"actif": "T", "spot": 9999, "sup1": 8380, "sup2": 8320, "res1": 8500, "res2": 8560}),
    charts.rail({"actif": "T", "spot": 100, "sup1": 8380, "sup2": 8320, "res1": 8500, "res2": 8560}),
    charts.yield_curve({"points": [{"t": "10Y", "v": 4.4}]}),
]
assert all(s.startswith("data:image/png") for s in stress)
print("[ok] cas extrêmes (VIX krach, ±12 %, prix hors zone, None, courbe 1 point)")
print("\nTOUS LES TESTS PASSENT.")
