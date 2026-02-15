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

## Build installers

### Windows (.exe + installer)
On Windows with PowerShell:

```powershell
./scripts/build_windows.ps1
```

This creates:
- `dist/Saboteur/Saboteur.exe`
- `dist/Saboteur-Installer.exe` (if Inno Setup 6 is installed)

### macOS (.app + .dmg)
On macOS:

```bash
./scripts/build_macos.sh
```

This creates:
- `dist/Saboteur.app`
- `dist/Saboteur.dmg` (if `create-dmg` is installed)

### Android (.apk)
On Linux/macOS with Android dependencies:

```bash
./scripts/build_android.sh
```

This creates a debug APK in `bin/`.

### CI build artifacts
A GitHub Actions workflow is included at `.github/workflows/build-installers.yml`.
It builds Windows, macOS, and Android artifacts and uploads them to workflow artifacts.
