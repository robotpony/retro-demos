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

A demo can be a single continuous behaviour, or a scripted sequence of stages that loops (LED's power-up -> numbers -> snake -> explosion -> words script is the first example). `framework/phase.py` has both halves of the shared unit for the second kind:

- `Phase`: one stage. `update(dt) -> bool` returns True when the stage is finished, `draw(surface)` renders it, `reset()` sets it up to run (called once on construction, and again every time the sequence is about to run it).
- `PhaseSequence`: the sequencer. Takes a list of `Phase`s, tracks the current index, and drives it: `update`/`draw` delegate to the current phase, and when a phase's `update` returns True, `PhaseSequence` advances to the next one (looping back to the first after the last) and calls its `reset()`.

A scripted demo builds its phase list once, in its own `__init__`, wraps it in a `PhaseSequence`, and delegates its own `update`/`draw`/`reset` to that sequence — the demo class itself carries no phase-index bookkeeping (see `LedDemo` in `retrodemos/demos/led.py`). Reuse both classes as-is for any other demo whose spec describes multiple stages rather than one continuous behaviour (Dooley, Bruce's 21, and Tank Status Window all look like candidates per their specs); only the individual `Phase` subclasses -- the actual choreography -- are demo-specific.

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

## Future framework polish

Not scheduled against the build order; tracked here so they aren't lost, and so LED II/Title don't reinvent them narrowly for their own demo when the LED polish pass lands. All three surfaced from LED's own future-polish list (`docs/led.md`) on 2026-08-24.

- **LED intensity, not just on/off.** Partly done (2026-08-24): `led_grid.py` has `lerp_color` and `DotMatrixDisplay.render_raw` now accepts either a plain set (fully lit, backward compatible) or a `dict[cell, float]` of per-cell brightness, blended between `DOT_UNLIT`/`DOT_LIT`. LED II's `RipplePhase` fireworks use it (via `graph_walk.Burst`'s per-node fade). Still open: `SevenSegmentDisplay` (LED's own renderer) has no equivalent yet -- LED's power-up flicker and `ExplosionPhase` still snap on/off -- and Title's dot-matrix needs, once built, should get the same treatment `DotMatrixDisplay` already has rather than reinventing it.
- **Timing momentum (speed up, hold, ease down).** Phase timing right now is either a fixed interval or (LED's power-up sweep) a one-directional speed-up with no ease-out. A shared easing helper alongside `framework/ticker.py`'s `Ticker` would let any phase's pacing feel less mechanical without each phase hand-rolling its own curve.
- **Rudimentary synthesized audio.** Short sine-tone beeps with simple envelopes, timed to animation beats (flicker, sweep, snake step, explosion). No audio exists anywhere in the framework yet. Note this is a distinct question from the "Out of scope" item above: that one rules out *real* audio playback for CD Player specifically (it doesn't actually play music to simulate a CD deck); a small synthesized-beep capability for sound effects is narrower and different, but is still a new project decision, not a foregone one -- confirm scope with Bruce before building rather than treating it as pre-approved.

## Open questions

Tracked in `demos.md` and each demo's own doc, not duplicated here. One remains: Tank Status Window's button icons will be a custom monochrome pixel set (confirmed, not Unicode emoji), but the specific icons are deferred until its build slot (order 9).

## Status

Framework scaffold and build orders 1-2 (LED, LED II) are all done. `retrodemos/framework/` has canvas, keys, `Demo` base, runtime, `led_grid.py` (seven-segment renderer + dot-matrix renderer + both displays' adjacency-graph builders + `lerp_color` for brightness blending), `phase.py` (`Phase` + `PhaseSequence`), `ticker.py` (fixed-interval tick accumulator), and `graph_walk.py` (`Snake`, `bfs_rings`, and `Burst` -- generic graph-crawl/radiating-particle-burst primitives; `Snake`/`bfs_rings` were extracted once LED II's phases needed the identical logic LED's `SnakePhase`/`ExplosionPhase` already had over a different graph, `Burst` was built directly here for LED II's fireworks). LED (`led.py`/`led_phases.py`) and LED II (`led_ii.py`/`led_ii_phases.py`) each run a full 5-phase script on this shared machinery; LED II's snake and fireworks were retuned bigger/richer on request (2026-08-24) -- see its phases' docstrings for the specific before/after. `--list` also got fixed while LED II was built: it was listing every module in `demos/`, including helper modules with no `DEMO_CLASS` (a latent bug since LED's own `led_phases.py`, made visibly worse by LED II's second phases module), not just runnable demos. 83 tests passing (`tests/`).

LED II's choreography (unlike LED's) has no source spec from Bruce; it's a deliberate structural echo of LED's script, confirmed with Bruce before building rather than assumed, with its own tuned constants for the much larger dot grid. `docs/led-ii.md` flags two of its content choices (the "1991" credit, the marquee default text) as reused from LED by assumption, not verified facts about LED II -- worth a look before considering LED II's polish pass done.

`framework/led_grid.py` still only has the seven-segment and dot-matrix renderers; Title's bit-pattern-column content and Dooley's dot-matrix-plus-colour-side-column need aren't built yet -- extend `DotMatrixDisplay` for Title (same grid style), and note Dooley's per-cell colour need will likely require extending it further rather than reusing it as-is.

## Next step

Build order 3: Title. Same framework, generated content instead of text -- reuse `DotMatrixDisplay` (per PLAN.md's "LED grid module" section) for its bit-pattern-column display, per `docs/title.md`.
