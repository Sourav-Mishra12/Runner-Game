# PIXEL ERA

**RUN. EXPLORE. SURVIVE.**

PIXEL ERA is a local Pygame arcade runner. Dodge ground and flying enemies, collect coins, discover four environments, and use temporary power-ups to extend your run. A compact profile stores your high score, coins, milestones, settings, and statistics in your local application data folder.

## Run

Requires Python 3.10+ and Pygame:

```bash
pip install pygame
python main.py
```

## Controls

- **Space / W / Up**: jump
- **Escape**: pause or resume
- **Mouse**: select menu buttons
- **Left / Right**: adjust music and sound volume in Settings
- **R** while paused: restart
- **M** while paused: return to the menu

## Project layout

```text
main.py                 Entry point
pixel_era/game.py       Game loop, states, gameplay and procedural visuals
pixel_era/save_manager.py  Local JSON profile with safe defaults
pixel_era/systems/parallax.py  Cached layered scenery and atmosphere
assets/environments/    Optional per-world sky and parallax PNG layers
graphics/               Replaceable player, enemy and background art
audio/                  Replaceable music and sound effects
fonts/                  Replaceable game font
```

All artwork has a procedural fallback, and audio is optional. The game remains playable if an asset is missing. Profile data is stored at `%LOCALAPPDATA%/PixelEra/save.json` on Windows (or `~/.local/share/PixelEra/save.json` when `LOCALAPPDATA` is unavailable).

### Background artwork

There are **2 existing background image files** used as blended sky layers: `graphics/Sky.png` (day layer) and `graphics/background_2.png` (late/night layer). Replace either file with another PNG using the same filename to use your own art. For per-world layers, add PNG files such as `assets/environments/day/trees.png` or `assets/environments/night/clouds.png`; see `assets/environments/README.md` for the supported layer names. Missing art is replaced by cached procedural scenery. `graphics/ground.png` is a ground texture, not one of the two sky backgrounds.

## Current features

- Responsive single-jump controls, landing feedback, and animated original sprites
- Four parallax environments with moving clouds, mountains, trees, and foreground
- Gradual day, sunset, twilight, night, and dawn sky colors, with stars and a moon
- Occasional cosmetic rain, fog, snow, flocks, lightning, wind, and bonus coin events
- Preset obstacle patterns and optional jump-for-coins risk/reward sequences
- Fairly spaced ground and flying hazards, coin lines/arcs/steps, and timed power-ups
- Shield, coin magnet, slow time, and score multiplier effects
- Combo feedback, difficulty ramp, score and coin tracking
- Main menu, shop, records, achievements, settings, pause, and results screens
- Persistent local high score, coins, selected cosmetic, achievements, settings, and run statistics

The shop uses placeholder cosmetic unlocks. Original assets can be replaced in `graphics/`, `audio/`, and `fonts/` without changing gameplay code.
