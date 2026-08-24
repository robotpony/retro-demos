# Plan

Execution plan for README priorities 2 through 7. Priority 1 (mini-specs) is done; see `demos.md` and `docs/`. This plan covers the shared interface design, build order, and tooling needed before any demo code is written.

## Repository layout

```
retro-demos/
  requirements.txt ......... pygame-ce, pytest

  retrodemos/
    __main__.py ............ `python -m retrodemos <name>` entry point, owns argparse

    framework/
      canvas.py ............ fixed native-res surface, scaled blit to the real window
      keys.py ............... shared event loop: quit / pause / restart handling
      demo.py ............... Demo base class every demo implements
      phase.py .............. Phase base class for demos that are a scripted, looping sequence of stages
      ticker.py ............. fixed-interval tick accumulator, for any Phase that advances in discrete steps
      led_grid.py ........... generic cell-grid renderer + scroll/cycle content helpers

    demos/
      led.py
      led_ii.py
      title.py
      dooley.py
      cd_player.py
      bruces_windows.py
      cinqtris.py
      bruces_21.py
      tank_status_window.py

  tests/
    test_smoke.py ........... headless launch test, one case per demo

  images/ ................... existing reference screenshots (unchanged)
  docs/ ...................... existing mini-specs (unchanged)
  demos.md
  README.md
  CLAUDE.md
  PLAN.md
```

`retrodemos` is a placeholder package name; rename freely, nothing depends on it yet.

## Shared framework

### Launcher and CLI

One entry point, `python -m retrodemos <name>`, owns argument parsing so no demo duplicates it. Flags apply uniformly:

- `--scale N` (default 3): integer scale factor from native pixel resolution to window size.
- `--fps N` (default 60): frame rate cap.
- `--fullscreen`: optional, off by default.

The launcher looks up `<name>` in `retrodemos/demos/`, instantiates its `Demo` subclass, and drives the loop.

### Demo interface

Every demo implements the same small interface, so the launcher can drive it generically and tests can drive it headlessly:

```python
class Demo:
    NATIVE_SIZE: tuple[int, int]   # native pixel resolution, before scaling

    def handle_event(self, event: pygame.event.Event) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...
```

The launcher owns the window, scaling, and the shared keybindings below; it calls `handle_event` only for events a demo cares about beyond those keys.

### Pixel scaling

Source screenshots are native-resolution pixel art (roughly 100 to 700px). Each demo renders to an offscreen surface at `NATIVE_SIZE`, and `framework/canvas.py` blits it scaled (nearest-neighbour, integer factor) to the real window. Keeps the pixel-art look crisp at any scale.

### Shared keybindings

| Key | Action |
|---|---|
| Esc / Q | Quit |
| Space | Pause / resume |
| R | Restart |

These are handled once, in the launcher, not per demo. Two demos layer their own interaction on top, documented in their own specs:

- **Bruce's Windows**: draggable title bar, "Got it" closes the dialog.
- **Cinqtris**: the "MADMAX" cell is a button that opens an About popup.

### Scripted sequences

A demo can be a single continuous behaviour, or a scripted sequence of stages that loops (LED's power-up -> numbers -> snake -> explosion -> words script is the first example). `framework/phase.py`'s `Phase` base class is the shared unit for the second kind: `update(dt) -> bool` returns True when a stage is finished, `draw(surface)` renders it, and the demo just holds a list of phases and an index, advancing and calling `reset()` on the next phase when the current one finishes. Reuse it for any other demo whose spec describes multiple stages rather than one continuous behaviour (Dooley, Bruce's 21, and Tank Status Window all look like candidates per their specs).

`framework/ticker.py`'s `Ticker` is a small companion: a fixed-interval tick accumulator (`advance(dt) -> int`, how many whole ticks fired) for any phase that advances in discrete steps rather than continuously, so each phase doesn't hand-roll its own dt-accumulation loop. It correctly catches up a slow frame instead of losing time; before it existed, LED's phases each wrote this by hand and did so inconsistently (see `retrodemos/demos/led_phases.py`'s history for the bug that motivated pulling it out).

### LED grid module

`framework/led_grid.py` is shared by Dooley, LED, LED II, and Title. It owns both the generic cell-grid renderer (lit/unlit or coloured cells, including seven-segment digits as a special case) and the common content-animation helpers (scroll text across the grid, cycle through a list of patterns). Each of the four demos configures its own grid dimensions and cell style, then calls a helper with its own content:

| Demo | Grid style | Content |
|---|---|---|
| LED | Seven-segment digits, single row | Built-in default string, overridable via `--text` |
| LED II | Dot-matrix, red | Same default/`--text` rule, scrolled |
| Title | Dot-matrix, bit-pattern columns (0-255 per column) | Generated pattern, not literal text |
| Dooley | Dot-matrix main display + colour-pixel side column | Scrolled text, with the side column cycling independently |

### Window chrome

Bruce's Windows' title bar, dialog, and status bar are drawn directly in `demos/bruces_windows.py`, not extracted into `framework/`. CD Player and Tank Status Window also show window-style borders in their source images, but each draws its own chrome independently rather than sharing Bruce's Windows' component. This was a decision, not an oversight: the three demos' chrome differs enough (a full OS-style window vs. a CD player's edge vs. a status window's border) that a shared abstraction would be built for one real caller and speculative for the other two. Revisit if a fourth chrome-bearing demo shows up.

This closes the "may double as the reference implementation" note in `docs/bruces-windows.md`; that doc has been updated to match.

## Build order

Framework first, then simplest demo first, so the framework gets validated early and complexity ramps up gradually.

| Order | Demo | Why here |
|---|---|---|
| 0 | Framework itself | Everything else depends on it |
| 1 | LED | Simplest: one grid, one content type, no interaction |
| 2 | LED II | Same framework, different grid style |
| 3 | Title | Same framework, generated content instead of text |
| 4 | Dooley | Same framework, two content streams (main display + side column) |
| 5 | CD Player | No shared grid or chrome reuse; several UI elements (sliders, meters, transport buttons) but no interaction or game logic |
| 6 | Bruce's Windows | First interactive demo (drag, button); validates the interaction pattern Cinqtris needs next |
| 7 | Cinqtris | Reuses the interaction pattern from Bruce's Windows for its About button; adds sprite art and pattern-cycling |
| 8 | Bruce's 21 | Sprite art plus phase-cycling (deck cycle, then auto-deal), no interaction |
| 9 | Tank Status Window | Most complex: scripted Combat-style animation (see `docs/tank-status-window.md`), reuses the LED grid's cell renderer at a larger scale, plus a placeholder button row |

Bruce's 21's slot wasn't explicit in the "simplest first" decision; it's placed by complexity (sprite art plus multi-phase cycling, no interaction) between Cinqtris and Tank Status Window. Move it if you'd rather it come earlier.

Per README priorities 3 and 4, each demo gets up to 1 day to build and iterate, plus up to 1 more day to polish. That's a ceiling, not a target. The framework itself isn't covered by that timebox; budget it separately since every demo depends on it being right.

## Testing

Headless smoke tests, one per demo: launch it with `SDL_VIDEODRIVER=dummy`, call `update`/`draw` for a fixed number of frames, and assert nothing raises. This is possible cheaply because every demo implements the same `Demo` interface; tests don't need a real display or a real event loop. It catches crashes and import errors, not visual regressions, matching what was asked for.

## Tooling

- **pygame-ce**, the actively maintained community fork, drop-in compatible with pygame.
- Standard **venv + pip**, dependencies pinned in `requirements.txt`.
- No build step; demos run directly from source.

Once the framework exists and these commands are real, `CLAUDE.md` should be updated with the actual run/test commands. It currently says no code exists yet, which is still true until this plan starts landing.

## Out of scope for now

- Real audio playback (CD Player is simulated only, per its spec).
- A full Combat rules engine for Tank Status Window (scripted/looping animation instead, per its spec).
- Shared window chrome beyond Bruce's Windows (see Window chrome above).
- `index.html` preview page (README priority 5). Revisit once demos exist to screenshot; format should follow `~/projects/peep`'s `--preview` output.

## Open questions

Tracked in `demos.md` and each demo's own doc, not duplicated here. One remains: Tank Status Window's button icons will be a custom monochrome pixel set (confirmed, not Unicode emoji), but the specific icons are deferred until its build slot (order 9).

## Status

Framework scaffold is done: `retrodemos/framework/` (canvas, keys, `Demo` base, runtime), the `retrodemos/__main__.py` launcher, `requirements.txt`, and `tests/test_smoke.py` (10 headless tests, all passing). `framework/led_grid.py` is deliberately not built yet; it lands with the LED demo (build order 1), the first demo that needs it.

## Next step

Build order 1: the LED demo. Write `retrodemos/framework/led_grid.py` (generic cell-grid renderer + scroll/cycle helpers) alongside it, per `docs/led.md`.
