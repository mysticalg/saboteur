# Saboteur Replica (Python / pygame)

A full-featured **Saboteur-style ninja action game** implemented in Python.

This version now includes:
- Multi-zone compound map (7 connected zones)
- Classic mission items (bomb + keycard/codes + extra collectibles)
- Ninja enemies, guards, dog patrols
- Melee fighting moves (punch, kick, flying kick)
- Thrown shuriken combat for player and ninjas
- Bomb timer, terminal defuse, and extraction objective

## Install & Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python game.py
```

## Controls

- Move: `A / D` or arrow keys
- Jump: `Space`
- Throw shuriken: `Z`
- Punch: `X`
- Kick: `C`
- Flying kick: `V`
- Interact/defuse: `E`
- Restart after win/loss: `R`

## Mission Flow

1. Collect the `time_bomb` to arm the mission timer.
2. Collect the `keycard` (codes).
3. Collect all remaining mission items.
4. Defuse at the terminal.
5. Reach the extraction pad.

You fail if health reaches 0 or the timer expires.
