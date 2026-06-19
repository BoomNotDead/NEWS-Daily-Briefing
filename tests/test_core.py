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
assert all(s.startswith("<svg") for s in rails)
print(f"[ok] {len(rails)} rails support/résistance")

yc = charts.yield_curve(data["courbe"])
ca = charts.cross_asset_bars(data["cross_asset"])
gauge = charts.vix_gauge(data["volatilite"])
assert yc.startswith("<svg") and ca.startswith("<svg") and gauge.startswith("<svg")
print("[ok] courbe des taux / barres cross-asset / jauge VIX")

txt = condense.build_condense(data)
assert "TRADING BRIEF" in txt and "CAC 40" in txt and "L'IDÉE DU JOUR" in txt
assert len(txt) <= 4096
print(f"[ok] condensé généré ({len(txt)} caractères)")

# Écrit des sorties de debug pour inspection visuelle.
dbg = ROOT / "_debug"
dbg.mkdir(exist_ok=True)
(dbg / "condense.txt").write_text(txt, encoding="utf-8")
preview = ["<!doctype html><meta charset='utf-8'>",
           "<body style='font-family:sans-serif;max-width:360px;margin:20px'>"]
preview.append("<h4>Rails</h4>")
preview += [f"<div style='margin:6px 0'><b>{n['actif']}</b>{r}</div>"
            for n, r in zip(data["niveaux"], rails)]
preview += ["<h4>Courbe des taux</h4>", yc,
            "<h4>Cross-asset</h4>", ca,
            "<h4>Jauge VIX</h4>", gauge, "</body>"]
(dbg / "charts.html").write_text("".join(preview), encoding="utf-8")
print(f"[ok] debug écrit dans {dbg}")
print("\nTOUS LES TESTS PASSENT.")
