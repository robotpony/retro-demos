# Tank Status Window

**Source:** `WIN1.png`
**Mode:** Automated attract-mode

## What it shows

A window titled "Tank Status Window" containing a large red/black dot-matrix grid, a smaller secondary dot-matrix strip beneath it, and a row of blank grey buttons along the bottom. In the source image the grid is a uniform solid block (no game state visible) and the buttons carry no icon art at all.

## Behaviour

An automated, single-player COMBAT (Atari 2600 style) game plays itself within the grid. Tanks, walls, and bullets are recreated and animated, but rendered in the same red/black dot-matrix style as `WIN1.png` rather than as full-colour sprites.

## Interaction

None beyond the shared quit/pause controls, plus one desktop-only control: `WIN1.png` has no close button of its own (only minimize and dropdown boxes), so on the desktop shell the minimize box doubles as this window's close control -- confirmed working 2026-08-26, not a new fix. The bottom-row buttons carry decorative black icons and press themselves at random (`tank_status_window.py`'s `_ButtonRowAnimator`); they don't respond to clicks and don't do anything beyond that ambient animation.

## Assets

No existing sprite sheet; the dot-matrix rendering is custom-drawn.

## Open questions

- ~~**Simulation fidelity.**~~ Resolved during the build (2026-08-25): scripted/looping, not real collision/AI. Three phases loop (patrol, engage, reset); see `retrodemos/demos/tank_status_window_phases.py`'s module docstring.
- ~~**Bottom-row icons.**~~ Resolved 2026-08-26: each button now shows one of 6 invented black pictograms, cycled by index (`tank_status_window_grid.py`'s `_BUTTON_ICONS`).

## Notes (build, 2026-08-25)

`WIN1.png`'s grid is a lit-everywhere test pattern, not a captured frame of real play -- there's no "game state" to recreate, only the dot pitch/size/colour and the two grids' exact dimensions (83x84 main, 83x9 secondary). Everything that moves (tanks, walls, bullets, explosions) is invented content, scripted to read as a plausible round rather than simulated. See `retrodemos/demos/tank_status_window_grid.py` and `tank_status_window_phases.py`'s module docstrings for the full account, including what's pixel-exact (window size, grid dimensions, button count, the title text and icon glyphs) versus simplified (the outer frame/bevel widths).

## Notes (playtesting, 2026-08-26 -- reconstruct-and-diff pass)

The first build wasn't actually 1:1 with the source despite the above: opening it from the desktop nested `WIN1.png`'s own frame inside a second, generic wrapper window (fixed the same way CD Player's own windows were -- `desktop.py`'s `_CHROMELESS` set, no generic chrome); the button row bled past the window's right edge (11 buttons at a guessed size/pitch, not the source's own measured 23px pitch); and the title text was centred by formula rather than placed at its own measured origin. All three geometry issues led to a full reconstruct-and-diff pass against `WIN1.png` (previously only spot-checked) -- now 95,546 of 95,550 pixels match exactly, the remaining 4 being a one-row source scanline artifact deliberately not reproduced (see `tank_status_window_grid.py`'s module docstring). Also caught a real quirk in the process: the 4th button (0-indexed 3) renders flat in the source, not raised like the other 10. Animation speed also increased 15% per playtesting request.

## Notes (playtesting, 2026-08-26 -- built-demo pass)

A second playtesting round, this time on the running demo rather than a raw reconstruct-and-diff, made several further changes:

- **Right edge.** The reconstruct-and-diff pass had faithfully kept the source's own asymmetric border (3px of black on the right versus 1px on the other three sides), but on the built demo that read as a stray extra line rather than a border. Widened deliberately, departing from the source on purpose -- see `tank_status_window_grid.py`'s `RED_X1`.
- **Status text** now crossfades between "PATROL"/"ENGAGE"/"RESET" instead of snapping (`_TankSceneBase._start_status_transition`/`_update_status`, shared by all three phases).
- **Tank sprites** were redesigned bigger and blockier, reading more like an Atari Combat tank (hull, treads, centred barrel); the enemy tank's copy is now vertically flipped so its barrel points down, toward the player it actually fires at, instead of sharing the player's up-pointing orientation.
- **EngagePhase** is now a best-of-3 match (score per side, shown as dots on each tank's own side of the secondary strip) instead of a fixed shot count, with faster and more randomized tank movement during the exchange.
- **ResetPhase**'s round-ending burst grew (wider radius, longer fade) and gained a `graph_walk.Rocket` launch trail, the same "climb, then ignite" fireworks shape LED II's and Title's own explosion phases use.
- **Every phase runs longer** (patrol and the post-blast hold both extended; the engage phase's own length now follows from how long its best-of-3 match takes to resolve, rather than a fixed shot count).
- **Bottom-row buttons** gained 6 cycled invented icon glyphs and an ambient, non-functional press animation (`tank_status_window.py`'s `_ButtonRowAnimator`) -- one button presses itself at random intervals; nothing is clickable.
- **Minimize-doubles-as-close** was confirmed already working, not a new fix.
