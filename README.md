# Play now: https://mysticalg.github.io/saboteur/saboteur.html

# Saboteur II — Shadow Operative

Saboteur II is a fast, retro-style browser platformer built with plain HTML5 canvas and vanilla JavaScript.
You infiltrate a hostile facility, dodge hazards, fight enemies, collect mission items, and escape through the rooftop helipad.

## Features

- Pixel-art inspired, side-view action gameplay
- Multiple building floors with ladders, platforms, hazards, and moving elements
- Built-in sound effects generated with the Web Audio API
- Keyboard-based movement and combat
- New command console UI with pause/help/sound controls and tooltips
- Expanded HUD readability (cooldown bar, clearer status indicators)
- Extra atmospheric effects (rain layer, polished frame styling)
- Play instantly in the browser (no install required)

## How to play

Use the hosted game link above, or open `saboteur.html` in your browser.

### Controls

- **Left / Right Arrow**: Move
- **Shift**: Sprint
- **Up Arrow / Space**: Jump
- **Down Arrow**: Crouch
- **Up / Down Arrow on ladder**: Climb ladder slowly
- **Z / X / C on ladder**: Ladder action keys
- **P**: Pause / Resume
- **H**: Toggle quick help overlay
- **M**: Mute / unmute sound effects

## Run locally

Because this project is a static HTML game, you can run it in two simple ways:

1. **Directly open the file**
   - Double-click `saboteur.html`
2. **Serve with a local web server (recommended)**
   - From the project folder, run:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000/saboteur.html`.

## Project structure

- `saboteur.html` — main game (logic, rendering, audio, input)
- `index.html` — repository landing page

## Contributing

Issues and pull requests are welcome. Keep changes lightweight and performance-focused so gameplay remains smooth and responsive.
