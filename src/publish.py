"""Publication sur Discord (webhook) et Telegram (bot). Secrets via variables d'env.

Chaque canal est indépendant : un échec sur l'un ne bloque pas l'autre.
Rien ne lève d'exception vers l'appelant (on log + on réessaie une fois).
"""
from __future__ import annotations

import json
import os
import pathlib
import time

import requests

TITLE = "📊 Trading Brief Matin"
BRAND_COLOR = 0x14304A


def _retry(fn, tries: int = 2) -> bool:
    for i in range(tries):
        try:
            if fn():
                return True
        except Exception as exc:
            print(f"  tentative {i + 1} échec : {exc}")
        time.sleep(1.5 * (i + 1))
    return False


def post_discord(out: pathlib.Path, condense_text: str) -> bool:
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        print("[discord] DISCORD_WEBHOOK_URL absent — ignoré")
        return False
    png, pdf = out / "preview.png", out / "brief.pdf"

    def _do() -> bool:
        embed = {"title": TITLE, "description": condense_text[:4096], "color": BRAND_COLOR}
        files, opened = {}, []
        if png.exists():
            f = open(png, "rb"); opened.append(f)
            files["files[0]"] = ("preview.png", f, "image/png")
            embed["image"] = {"url": "attachment://preview.png"}
        if pdf.exists():
            f = open(pdf, "rb"); opened.append(f)
            files[f"files[{len(files)}]"] = ("brief.pdf", f, "application/pdf")
        try:
            r = requests.post(url, data={"payload_json": json.dumps({"embeds": [embed]})},
                              files=files or None, timeout=40)
        finally:
            for f in opened:
                f.close()
        print(f"[discord] HTTP {r.status_code}")
        return r.status_code in (200, 204)

    return _retry(_do)


def post_telegram(out: pathlib.Path, condense_text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        print("[telegram] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID absent — ignoré")
        return False
    base = f"https://api.telegram.org/bot{token}"
    png, pdf = out / "preview.png", out / "brief.pdf"
    results = []

    if png.exists():
        def _photo() -> bool:
            with open(png, "rb") as f:
                r = requests.post(f"{base}/sendPhoto",
                                  data={"chat_id": chat, "caption": TITLE},
                                  files={"photo": ("preview.png", f, "image/png")}, timeout=40)
            print(f"[telegram] sendPhoto {r.status_code}")
            return r.status_code == 200
        results.append(_retry(_photo))

    def _msg() -> bool:
        r = requests.post(f"{base}/sendMessage",
                          data={"chat_id": chat, "text": condense_text[:4096]}, timeout=40)
        print(f"[telegram] sendMessage {r.status_code}")
        return r.status_code == 200
    results.append(_retry(_msg))

    if pdf.exists():
        def _doc() -> bool:
            with open(pdf, "rb") as f:
                r = requests.post(f"{base}/sendDocument",
                                  data={"chat_id": chat},
                                  files={"document": ("brief.pdf", f, "application/pdf")}, timeout=60)
            print(f"[telegram] sendDocument {r.status_code}")
            return r.status_code == 200
        results.append(_retry(_doc))

    return all(results) if results else False
