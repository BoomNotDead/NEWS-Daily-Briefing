# Trading Brief Matin — moteur de newsletter (cloud)

Génère chaque matin une **newsletter PDF visuelle** (type publication payante) +
un **condensé lisible par un débutant**, et les publie sur **Discord** et **Telegram**.

Conçu pour tourner dans une **Routine Claude Code (cloud)** : Claude fait la
recherche + le raisonnement et produit un **JSON structuré** ; ce moteur s'occupe
du rendu déterministe (graphiques, mise en page) et de l'envoi. Rien ne tourne sur
ta machine.

## Comment ça marche

```
brief.json (produit par Claude)
   │
   ├─ validation (schema/brief.schema.json)   ← refuse un brief cassé
   ├─ calculs déterministes (src/derive.py)   ← couleurs, positions, formats
   ├─ graphiques SVG (src/charts.py)          ← rails, courbe, barres, jauge VIX
   ├─ template figé (templates/brief.html.j2) ← grille A4 paysage
   ├─ WeasyPrint → out/brief.pdf
   ├─ aperçu page 1 → out/preview.png
   └─ condensé → out/condense.txt
        │
        └─ publication (src/publish.py) → Discord + Telegram
```

## Lancer

```bash
bash setup.sh                 # une fois (libs système + pip)
python run.py brief.json      # rend + publie
```

## Variables d'environnement (secrets)

| Variable | Rôle |
|---|---|
| `DISCORD_WEBHOOK_URL` | webhook du salon Discord |
| `TELEGRAM_BOT_TOKEN`  | token du bot Telegram |
| `TELEGRAM_CHAT_ID`    | id du chat/canal Telegram |

Un canal dont les variables sont absentes est simplement ignoré (l'autre part quand même).

## Tester localement (sans WeasyPrint)

```bash
python tests/test_core.py     # schéma + graphiques + condensé
```

Le rendu PDF (WeasyPrint) se teste dans l'environnement cloud (Linux).

## Le format `brief.json`

Voir `sample_brief.json` (exemple complet commenté par l'usage) et
`schema/brief.schema.json` (contrat strict). Claude ne produit QUE des données :
aucune mise en page, aucun HTML, aucune couleur — tout ça est géré ici.
