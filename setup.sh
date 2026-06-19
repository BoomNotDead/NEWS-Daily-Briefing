#!/usr/bin/env bash
# Script de setup de l'environnement cloud (Routine Claude). Tourne une fois,
# puis l'image est mise en cache. Installe les libs système de WeasyPrint,
# les polices, puis les dépendances Python.
set -euo pipefail

apt-get update
apt-get install -y --no-install-recommends \
  libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libgdk-pixbuf-2.0-0 \
  libffi-dev libcairo2 fontconfig fonts-dejavu-core

# Paquets listés en clair (le script de setup peut tourner avant le clone du repo).
pip install "weasyprint>=62,<64" "jinja2>=3.1" "jsonschema>=4" "pypdfium2>=4" "pillow>=10" "requests>=2.31"

echo "setup_render OK"
