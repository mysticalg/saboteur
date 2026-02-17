# Saboteur Replica (Python / pygame)

> **Engine note:** The original version is **Python + pygame**, and this repo now also includes a lightweight **Godot 4** port under `godot/`.

A full-featured **Saboteur-style ninja action game** implemented in Python with a massive traversable map. The game supports optional pre-rendered sprite overrides generated through OpenAI Images.

This version now includes:
- Massive multi-layer complex (shore entry, basement lines, ladders, one-way floors)
- Stealth traversal options (bush hiding, swim approach, moving train corridor)
- Classic mission items (bomb + codes + extra collectibles)
- Ninja enemies, guards, and dog patrols
- Melee + shuriken combat
- 60 FPS animation pass (character bob/sway + spinning shuriken + terminal flicker)
- 1-hour mission timer, terminal defuse, and extraction objective

## Run with Godot (new)

A minimal Godot 4 playable port is available in `godot/` with the same core mission loop: collect bomb + codes, defuse at terminal, then extract before time runs out.

```bash
cd godot
godot4 --path .
```

If your executable is named `godot` instead of `godot4`, use that binary.

## Install & Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python game.py
```

## Controls

### Splash / Options
- Start mission: `Enter` (or `Space`) from splash
- Open options: `O` from splash
- In options: `B` opens browser to OpenAI sign-in/key page, `K` edits/saves API key, `G` generates sprites
- Toggle OpenAI sprite mode in options: `Left/Right`, `Enter`, or `Space`
- Back from options: `Esc`, `Backspace`, or `O`

### In Mission
- Move: `A / D` or arrow keys
- Jump: `Space`
- Throw shuriken: `Z`
- Punch: `X`
- Kick: `C`
- Flying kick: `V`
- Interact/defuse: `E`
- Return to splash menu: `Esc`
- Restart after win/loss: `R`

## Mission Flow

1. Collect the `time_bomb` to arm the mission timer.
2. Collect the `keycard` (codes).
3. Collect all remaining mission items.
4. Defuse at the terminal.
5. Reach the extraction pad.

You fail if health reaches 0 or the timer expires.


## Playability checks

- The project includes an automated level-connectivity test that validates there is a route from the spawn side to extraction.
- Core simulation logic is covered by unit tests for collision and bomb mission rules.


## Do I need to plug in to OpenAI for sprites?

Short answer: **No, not to play the game.**

- The game runs without OpenAI and will use built-in procedural sprites by default/fallback.
- You only need an OpenAI API key if you want to **generate new PNG sprite files** via `scripts/generate_openai_sprites.py`.
- Once PNGs are generated into `assets/generated/`, the game can load them locally (no live API call while playing).
- The in-game browser flow assists sign-in and key creation; OpenAI image API still uses an API key for generation.

## OpenAI pre-rendered sprite pipeline

You can generate high-detail sprite PNGs with OpenAI and drop them into `assets/generated/`.
When present, the game automatically loads these files instead of the procedural fallback art:

- `player.png`
- `guard.png`
- `ninja.png`
- `dog.png`
- `terminal.png`
- `shuriken.png`
- `ladder.png`
- `train.png`
- `dinghy.png`

Generate them with:

```bash
OPENAI_API_KEY=your_key_here python scripts/generate_openai_sprites.py
```

Then run the game normally:

```bash
python game.py
```
