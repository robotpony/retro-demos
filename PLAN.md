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

A scripted demo builds its phase list once, in its own `__init__`, wraps it in a `PhaseSequence`, and delegates its own `update`/`draw`/`reset` to that sequence — the demo class itself carries no phase-index bookkeeping (see `LedDemo` in `retrodemos/demos/led.py`). Reuse both classes as-is for any other demo whose spec describes multiple stages rather than one continuous behaviour (Bruce's 21 and Tank Status Window both look like candidates per their specs); only the individual `Phase` subclasses -- the actual choreography -- are demo-specific.

`framework/ticker.py`'s `Ticker` is a small companion: a fixed-interval tick accumulator (`advance(dt) -> int`, how many whole ticks fired) for any phase that advances in discrete steps rather than continuously, so each phase doesn't hand-roll its own dt-accumulation loop. It correctly catches up a slow frame instead of losing time; before it existed, LED's phases each wrote this by hand and did so inconsistently (see `retrodemos/demos/led_phases.py`'s history for the bug that motivated pulling it out).

### LED grid module

`framework/led_grid.py` is shared by LED, LED II, and Title. The original plan (below, kept for history) was one generic cell-grid renderer for all of them; in practice each demo's source image turned out to need its own renderer shape closely matched to that image's actual pixel model, not a single grid abstraction bent to fit all three -- `SevenSegmentDisplay`, `DotMatrixDisplay`, and `BitColumnDisplay` are three distinct classes in the same module, not configurations of one class. (A fourth, `BevelCellDisplay`, was built for Dooley on 2026-08-24 and removed the same day when Dooley was cut from the project -- see the Status section below.)

| Demo | Grid style | Content |
|---|---|---|
| LED | Seven-segment digits, single row (`SevenSegmentDisplay`) | Built-in default string, overridable via `--text` |
| LED II | Dot-matrix, red, gapped both axes (`DotMatrixDisplay`) | Same default/`--text` rule, scrolled |
| Title | Bit-column, no bezel, no gap between columns, content computed directly from a byte value rather than a font (`BitColumnDisplay`) | Each column's own value (0-255) as its 8 bits; scrolled over time |

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
| 4 | CD Player | No shared grid or chrome reuse; several UI elements (sliders, meters, transport buttons) but no interaction or game logic |
| 5 | Bruce's Windows | First interactive demo (drag, button); validates the interaction pattern Cinqtris needs next |
| 6 | Cinqtris | Reuses the interaction pattern from Bruce's Windows for its About button; adds sprite art and pattern-cycling |
| 7 | Bruce's 21 | Sprite art plus phase-cycling (deck cycle, then auto-deal), no interaction |
| 8 | Tank Status Window | Most complex: scripted Combat-style animation (see `docs/tank-status-window.md`), reuses the LED grid's cell renderer at a larger scale, plus a placeholder button row |

Dooley (originally slotted at order 4, "same framework, two content streams") was built on 2026-08-24, then cut from the project the same day (see the Status section below) -- removed from this table rather than left as a gap.

Bruce's 21's slot wasn't explicit in the "simplest first" decision; it's placed by complexity (sprite art plus multi-phase cycling, no interaction) between Cinqtris and Tank Status Window. Move it if you'd rather it come earlier.

## Future: the unified desktop (end state)

Logged on request (2026-08-24), not scheduled against the build order above -- it needs every other demo built first. The end state of this project isn't eight standalone programs each launched with `python -m retrodemos <name>`; it's all of them running as windows inside one desktop, using Bruce's Windows' own chrome (`docs/bruces-windows.md`, `WINDOW1.png`) as the desktop shell. Picture Bruce's actual early-90s desktop: LED, LED II, Title, CD Player, Cinqtris, Bruce's 21, and Tank Status Window each in their own window, all running their attract-mode loops at once, the way several little utility programs might genuinely have been left open together.

This changes Bruce's Windows' own role: `docs/bruces-windows.md` currently describes it as "the reference for the shared UI chrome," a single title bar + dialog + status bar demo. It becomes the container demo instead (or in addition) -- a `python -m retrodemos desktop`-style mode (exact launch mechanism undecided) that composites every other demo's own `Demo.draw()` onto one canvas, each behind its own draggable Bruce's-Windows-style title bar.

Open questions, all deferred until the individual demos are done:
- Does each demo run at its own native resolution inside a same-sized window, or get uniformly scaled to fit the desktop?
- Do the shared quit/pause/restart keybindings (`framework/keys.py`) apply per-window (focused window only) or globally to every window at once?
- Is this a new launch mode of the existing CLI, or its own demo entry (`desktop.py`) that happens to embed the others?
- Window chrome is currently deliberately *not* shared (`PLAN.md`'s "Window chrome" section) since only Bruce's Windows needed it; a desktop hosting every demo is the "fourth chrome-bearing demo" that section already flags as the trigger to revisit that decision.

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
- **Snake-chase minigame, not just a wandering snake.** Title's `SnakePhase` was rebuilt 2026-08-24 (request: the scene ran too short and didn't cover enough horizontal ground) from a single unbiased `graph_walk.Snake` per strip into a chase minigame: two `graph_walk.ChaseSnake`s per strip, spawned a guaranteed quarter-width apart, hunt each other's head (target-weighted steps, biased toward whichever axis needs closing most) until one catches the other, flashes a few times, and hands off to the next phase. Ported to LED II's own `SnakePhase` the same day: the shared catch/win/flash bookkeeping was pulled out into `graph_walk.ChasePair` once both demos needed it (Title's `title_phases.py` now wraps it in `_TitleChase` for its two-strips-plus-quarter-width-spawn specifics; LED II's `led_ii_phases.py` uses it directly), with its own milder axis weighting (2:1, not Title's 4:1) tuned for this grid's 83x9 shape rather than reused verbatim. LED's own `SnakePhase` (the segment-graph one, not spatial the way a dot grid is) still uses the plain wandering `Snake` -- worth porting next time it's touched, though its "opposite quarters" spawn rule and distance function will need their own equivalent, not a verbatim copy.

## Open questions

Tracked in `demos.md` and each demo's own doc, not duplicated here. One remains: Tank Status Window's button icons will be a custom monochrome pixel set (confirmed, not Unicode emoji), but the specific icons are deferred until its build slot (order 8).

## Status

Framework scaffold and build orders 1-3 (LED, LED II, Title) are all done. `retrodemos/framework/` has canvas, keys, `Demo` base, runtime, `led_grid.py` (`SevenSegmentDisplay`, `DotMatrixDisplay`, `BitColumnDisplay`, each demo's adjacency-graph builder where it has one, `lerp_color` for brightness blending), `phase.py` (`Phase` + `PhaseSequence`), `ticker.py` (fixed-interval tick accumulator), and `graph_walk.py` (`Snake`, `bfs_rings`, and `Burst` -- generic graph-crawl/radiating-particle-burst primitives; `Snake`/`bfs_rings` were extracted once LED II's phases needed the identical logic LED's `SnakePhase`/`ExplosionPhase` already had over a different graph, `Burst` was built directly here for LED II's fireworks). LED (`led.py`/`led_phases.py`), LED II (`led_ii.py`/`led_ii_phases.py`), and Title (`title.py`/`title_phases.py`) each run a full 5-phase script on this shared machinery; LED II's snake and fireworks were retuned bigger/richer on request (2026-08-24) -- see its phases' docstrings for the specific before/after. Title was originally built as a single continuous behaviour, then rebuilt (same day, on request) into the same 5-beat script as its siblings once that was confirmed as what Title's spec should actually describe too; it needed `BitColumnDisplay.render_raw` added (alongside the existing `render_values`) so its snake/fireworks phases could address individual `(col, bit)` cells directly, and `TitleDisplays` (in `title.py`) to let one Phase drive both of Title's colour strips together, since Title (unlike LED/LED II) has two displays, not one. `--list` also got fixed while LED II was built: it was listing every module in `demos/`, including helper modules with no `DEMO_CLASS` (a latent bug since LED's own `led_phases.py`, made visibly worse by each demo's own phases module), not just runnable demos. LED II's `SnakePhase` was rebuilt 2026-08-24 into the same snake-chase minigame Title's got the same day -- see "Future framework polish" above for the `graph_walk.ChasePair` extraction this drove. 114 tests passing (`tests/`).

LED II's choreography (unlike LED's) has no source spec from Bruce; it's a deliberate structural echo of LED's script, confirmed with Bruce before building rather than assumed, with its own tuned constants for the much larger dot grid. `docs/led-ii.md` flags two of its content choices (the "1991" credit, the marquee default text) as reused from LED by assumption, not verified facts about LED II -- worth a look before considering LED II's polish pass done.

Title turned out not to fit `DotMatrixDisplay` after all, despite that being the plan going in (see "LED grid module" above for the corrected per-demo table): its source image (`TITLE.png`) has no bezel, no gap between columns, and content directly computable from a byte value rather than drawn from a font, so it got its own renderer (`BitColumnDisplay`) instead of a forced extension. `TITLE.png` also turned out to encode the actual rendering *rule* (column x shows value x's own bits), not just a lit/unlit calibration image like LED's and LED II's source images -- verified pixel-exact against all 256 columns x 8 rows x 2 colour pairs.

Dooley was built (2026-08-24: `BevelCellDisplay` renderer, LED strip + colour palette + RGB-spinner/grid area, verified byte-exact against the two content-bearing regions) then cut from the project the same day on request -- not going to work well as a demo. Demo code, tests, spec, and the `BevelCellDisplay` renderer were all removed; `DOOLEY1.png` moved to `demos.md`'s Excluded table. Not in the build order below any more, rather than left as a gap.

Build order 4 (CD Player) is done (2026-08-24), confirming the "no shared grid or chrome reuse" prediction: `cd_player.py` draws its own chrome directly, nothing from `led_grid.py`. `CDPLAYER.png` turned out to bundle three stacked reference bands rather than one screenshot (the same surprise Title's and Dooley's source images held) -- two differently-sized captures of the same widget vocabulary (transport buttons, "cd" logo, slider bank) plus a separate level-meter strip; built around the larger capture, confirmed with Bruce, since its long readout doubled as an 18-cell segment-font calibration strip (every segment shown in its own measured on/off colour, better ground truth than LED's own font had, plus two genuine quirks kept rather than corrected: this font's "6" has no top bar, "9" has no bottom bar). No `Phase`/`PhaseSequence` -- like Dooley, nothing about simulated CD playback suggested discrete narrative beats, so it's one continuous loop (time counter, periodic pauses, a fake sine-summed waveform) instead. 125 tests passing (`tests/`).

Build order 5 (Bruce's Windows) is done (2026-08-25), the first interactive demo. `WINDOW1.png` is a single coherent screenshot (unlike Title/Dooley/CD Player's source images), so no calibration-band untangling was needed; every text label (window title, dialog title, its two body lines, the button label, the status bar text) is pixel-verified -- extracted as the literal set of black pixels within its own tight bounding box, not decomposed into a reusable font, since every label here is fixed content. Caught and fixed one extraction bug along the way: an overly-tight search bound truncated the status text's "T" (its crossbar and stem), initially reading "his is a status a bar..." instead of the source's actual (and genuinely typo'd) "This is a status a bar...". Window chrome (borders, bevels, corner boxes, the resize grip) is approximated with a consistent bevel-rect helper, the same tier Dooley's/CD Player's non-content chrome got; the status bar's own icon grid (12x4 cells, pixel-verified) is content, not decoration, so it wasn't. Needed one new piece of shared framework, not just this demo's own code: `runtime.py` now rescales mouse event `pos`/`rel` from window-pixel space to native-canvas space before a demo ever sees them (`_to_native_space`), since no prior demo needed mouse input at all -- this benefits Cinqtris's About button next for free. The demo's own canvas (320x240) is bigger than the window (200x200) so there's visible room to drag it; the surrounding desktop backdrop is an invented flat teal, since `WINDOW1.png` shows only the window itself. 140 tests passing (`tests/`).

## Next step

Build order 6: Cinqtris. Reuses the interaction pattern Bruce's Windows just validated (mouse click via `runtime.py`'s coordinate rescaling) for its own "MADMAX" About-button popup; adds sprite art and pattern-cycling on top. Check `docs/cinqtris.md` and do its own pixel-archaeology pass before assuming anything carries over.
