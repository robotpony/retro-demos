# Tank Status Window

**Source:** `WIN1.png`
**Mode:** Automated attract-mode

## What it shows

A window titled "Tank Status Window" containing a large red/black dot-matrix grid, a smaller secondary dot-matrix strip beneath it, and a row of blank grey buttons along the bottom. In the source image the grid is a uniform solid block (no game state visible) and the buttons carry no icon art at all.

## Behaviour

An automated, single-player COMBAT (Atari 2600 style) game plays itself within the grid. Tanks, walls, and bullets are recreated and animated, but rendered in the same red/black dot-matrix style as `WIN1.png` rather than as full-colour sprites.

## Interaction

None beyond the shared quit/pause controls, plus one desktop-only control added 2026-08-26: `WIN1.png` has no close button of its own (only minimize and dropdown boxes), so on the desktop shell the minimize box doubles as this window's close control. The bottom-row buttons are placeholder monochrome icons that visually support the demo; they are decorative, not required to be functional.

## Assets

No existing sprite sheet; the dot-matrix rendering is custom-drawn.

## Open questions

- ~~**Simulation fidelity.**~~ Resolved during the build (2026-08-25): scripted/looping, not real collision/AI. Three phases loop (patrol, engage, reset); see `retrodemos/demos/tank_status_window_phases.py`'s module docstring.
- The bottom-row buttons render as 11 blank bevelled buttons (measured count and chrome style, reusing `framework/window_chrome.py`'s `black_ring`+`bevel_rect`); they stay decorative/unwired, per the spec's own Interaction note. A future custom monochrome icon set for them is still open if ever wanted.

## Notes (build, 2026-08-25)

`WIN1.png`'s grid is a lit-everywhere test pattern, not a captured frame of real play -- there's no "game state" to recreate, only the dot pitch/size/colour and the two grids' exact dimensions (83x84 main, 83x9 secondary). Everything that moves (tanks, walls, bullets, explosions) is invented content, scripted to read as a plausible round rather than simulated. See `retrodemos/demos/tank_status_window_grid.py` and `tank_status_window_phases.py`'s module docstrings for the full account, including what's pixel-exact (window size, grid dimensions, button count, the title text and icon glyphs) versus simplified (the outer frame/bevel widths).

## Notes (playtesting, 2026-08-26)

The first build wasn't actually 1:1 with the source despite the above: opening it from the desktop nested `WIN1.png`'s own frame inside a second, generic wrapper window (fixed the same way CD Player's own windows were -- `desktop.py`'s `_CHROMELESS` set, no generic chrome); the button row bled past the window's right edge (11 buttons at a guessed size/pitch, not the source's own measured 23px pitch); and the title text was centred by formula rather than placed at its own measured origin. All three geometry issues led to a full reconstruct-and-diff pass against `WIN1.png` (previously only spot-checked) -- now 95,546 of 95,550 pixels match exactly, the remaining 4 being a one-row source scanline artifact deliberately not reproduced (see `tank_status_window_grid.py`'s module docstring). Also caught a real quirk in the process: the 4th button (0-indexed 3) renders flat in the source, not raised like the other 10. Animation speed also increased 15% per playtesting request.
