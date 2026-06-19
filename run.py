"""Point d'entrée : lit le JSON, valide, rend le PDF + aperçu, publie sur les 2 canaux.

Usage : python run.py [chemin_du_brief.json]   (défaut : brief.json)
Variables d'env : DISCORD_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
"""
from __future__ import annotations

import json
import pathlib
import sys

from src import publish, render


def main() -> int:
    brief_path = sys.argv[1] if len(sys.argv) > 1 else "brief.json"
    data = json.loads(pathlib.Path(brief_path).read_text(encoding="utf-8"))

    # Garde-fou : on ne publie JAMAIS un brief invalide / à moitié cassé.
    render.validate_payload(data)

    out = render.render_pdf(data, "out")
    print(f"PDF généré : {(out / 'brief.pdf').exists()} · aperçu : {(out / 'preview.png').exists()}")

    text = (out / "condense.txt").read_text(encoding="utf-8")
    ok_d = publish.post_discord(out, text)
    ok_t = publish.post_telegram(out, text)
    print(f"\nRÉSULTAT : discord={ok_d} · telegram={ok_t}")

    # Archivage (trace) sous artifacts/<date>/.
    try:
        day = (data.get("meta", {}) or {}).get("date_str", "jour").replace(" ", "_")
        arch = pathlib.Path("artifacts") / day
        arch.mkdir(parents=True, exist_ok=True)
        for name in ("brief.pdf", "preview.png", "condense.txt"):
            src = out / name
            if src.exists():
                (arch / name).write_bytes(src.read_bytes())
        (arch / "brief.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print("archivage ignoré :", exc)

    return 0 if (ok_d or ok_t) else 2


if __name__ == "__main__":
    sys.exit(main())
