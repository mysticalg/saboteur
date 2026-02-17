"""Generate pre-rendered sprite PNG assets with OpenAI Images API.

Usage:
  OPENAI_API_KEY=... python scripts/generate_openai_sprites.py
"""

from __future__ import annotations

import base64
import json
import os
import urllib.request
from pathlib import Path

OUT_DIR = Path("assets/generated")
MODEL = "gpt-image-1"

SPRITES: dict[str, dict[str, str]] = {
    "player.png": {
        "size": "1024x1024",
        "prompt": "single full-body stealth operative sprite, side-on platformer style, transparent background, dramatic pre-rendered lighting, no text",
    },
    "guard.png": {
        "size": "1024x1024",
        "prompt": "single full-body security guard sprite, side-on platformer style, transparent background, pre-rendered game art, no text",
    },
    "ninja.png": {
        "size": "1024x1024",
        "prompt": "single full-body elite ninja enemy sprite, side-on platformer style, transparent background, pre-rendered game art, no text",
    },
    "dog.png": {
        "size": "1024x1024",
        "prompt": "single guard dog sprite, side-on platformer style, transparent background, pre-rendered game art, no text",
    },
    "terminal.png": {
        "size": "1024x1024",
        "prompt": "single sci-fi hacking terminal object sprite, side-on platformer style, transparent background, pre-rendered game art",
    },
    "shuriken.png": {
        "size": "1024x1024",
        "prompt": "single shuriken weapon sprite, centered, transparent background, pre-rendered game art",
    },
    "ladder.png": {
        "size": "1024x1024",
        "prompt": "single metal ladder module sprite for platform game, transparent background, pre-rendered game art",
    },
    "train.png": {
        "size": "1536x1024",
        "prompt": "single side-view futuristic train car sprite for stealth platform game, transparent background, pre-rendered game art",
    },
    "dinghy.png": {
        "size": "1024x1024",
        "prompt": "single inflatable dinghy boat sprite, side view, transparent background, pre-rendered game art",
    },
}


def generate_image(api_key: str, prompt: str, size: str) -> bytes:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "background": "transparent",
        "quality": "high",
    }
    request = urllib.request.Request(
        url="https://api.openai.com/v1/images/generations",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    b64 = data["data"][0]["b64_json"]
    return base64.b64decode(b64)


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for filename, spec in SPRITES.items():
        print(f"Generating {filename}...")
        png_bytes = generate_image(api_key=api_key, prompt=spec["prompt"], size=spec["size"])
        (OUT_DIR / filename).write_bytes(png_bytes)

    print(f"Done. Wrote {len(SPRITES)} sprite files to {OUT_DIR}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
