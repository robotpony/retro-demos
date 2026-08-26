# Tank Status Window

**Source:** `WIN1.png`
**Mode:** Automated attract-mode

## What it shows

A window titled "Tank Status Window" containing a large red/black dot-matrix grid, a smaller secondary dot-matrix strip beneath it, and a row of blank grey buttons along the bottom. In the source image the grid is a uniform solid block (no game state visible) and the buttons carry no icon art at all.

## Behaviour

An automated, single-player COMBAT (Atari 2600 style) game plays itself within the grid. Tanks, walls, and bullets are recreated and animated, but rendered in the same red/black dot-matrix style as `WIN1.png` rather than as full-colour sprites.

## Interaction

None beyond the shared quit/pause controls. The bottom-row buttons are placeholder monochrome icons that visually support the demo; they are decorative, not required to be functional.

## Assets

No existing sprite sheet; the dot-matrix rendering is custom-drawn.

## Open questions

- ~~**Simulation fidelity.**~~ Resolved during the build (2026-08-25): scripted/looping, not real collision/AI. Three phases loop (patrol, engage, reset); see `retrodemos/demos/tank_status_window_phases.py`'s module docstring.
- The bottom-row buttons render as 11 blank bevelled buttons (measured count and chrome style, reusing `framework/window_chrome.py`'s `black_ring`+`bevel_rect`); they stay decorative/unwired, per the spec's own Interaction note. A future custom monochrome icon set for them is still open if ever wanted.

## Notes (build, 2026-08-25)

`WIN1.png`'s grid is a lit-everywhere test pattern, not a captured frame of real play -- there's no "game state" to recreate, only the dot pitch/size/colour and the two grids' exact dimensions (83x84 main, 83x9 secondary). Everything that moves (tanks, walls, bullets, explosions) is invented content, scripted to read as a plausible round rather than simulated. See `retrodemos/demos/tank_status_window_grid.py` and `tank_status_window_phases.py`'s module docstrings for the full account, including what's pixel-exact (window size, grid dimensions, button count, the title text and icon glyphs) versus simplified (the outer frame/bevel widths).
