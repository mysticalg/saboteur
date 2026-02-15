#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller

rm -rf build dist
python3 -m PyInstaller --noconfirm --clean --windowed --name Saboteur game.py

if [[ ! -d "dist/Saboteur.app" ]]; then
  echo "Build failed: dist/Saboteur.app not found" >&2
  exit 1
fi

if command -v create-dmg >/dev/null 2>&1; then
  rm -f dist/Saboteur.dmg
  create-dmg \
    --volname "Saboteur" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "Saboteur.app" 200 190 \
    --hide-extension "Saboteur.app" \
    --app-drop-link 600 185 \
    "dist/Saboteur.dmg" \
    "dist/Saboteur.app"
  echo "Built DMG at dist/Saboteur.dmg"
else
  echo "create-dmg not installed; .app available at dist/Saboteur.app"
fi
