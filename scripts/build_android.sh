#!/usr/bin/env bash
set -euo pipefail

if ! command -v buildozer >/dev/null 2>&1; then
  python3 -m pip install --upgrade pip
  python3 -m pip install buildozer cython==0.29.36
fi

if [[ ! -f buildozer.spec ]]; then
  buildozer init
  sed -i 's/^title = .*/title = Saboteur/' buildozer.spec
  sed -i 's/^package.name = .*/package.name = saboteur/' buildozer.spec
  sed -i 's/^source.include_exts = .*/source.include_exts = py,png,jpg,kv,atlas,ttf,wav,ogg/' buildozer.spec
  sed -i 's|^requirements = .*|requirements = python3,pygame|' buildozer.spec
  sed -i 's/^orientation = .*/orientation = landscape/' buildozer.spec
  sed -i 's/^fullscreen = .*/fullscreen = 1/' buildozer.spec
  sed -i 's|^#android.permissions =.*|android.permissions = INTERNET|' buildozer.spec
fi

buildozer android debug
echo "APK output under bin/"
