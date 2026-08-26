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

## The unified desktop (end state) -- built 2026-08-25

Logged 2026-08-24, spec settled and built the next day. Bruce's Windows is now the **root interface of `retrodemos` itself**: `python -m retrodemos` with no name opens `retrodemos/demos/desktop.py`, a 1024x576 shell with one icon per built demo, each opening as its own draggable/closable window (`framework/window_chrome.py`). The original title-bar+dialog+status-bar exhibit (`bruces_windows.py`) is now just one of those icons -- "the actual Window demo from the PNG" -- not the whole experience. Icon glyphs (new pixel art, no source to measure against) were mocked up and confirmed with Bruce first, same workflow every other invented-content piece in this project got.

All eight planned demos now have an icon in `desktop.py`'s `_DEMO_ENTRIES` list (LED, LED II, Title, CD Player, Bruce's Windows, Cinqtris, Bruce's 21, Tank Status Window).

### Settled design (confirmed with Bruce, 2026-08-25)

- **Entry point**: `python -m retrodemos` with no name now opens the desktop (replacing `--list`'s text dump as the no-argument default; `--list` stays available as an explicit flag). `python -m retrodemos <name>` keeps working exactly as it does today -- standalone, full-window, no desktop chrome -- for dev/testing and for anyone who just wants one demo.
- **Canvas**: 1024x576. Desktop background is new invented content (WINDOW1.png shows only the window, no desktop behind it) -- reuse or restyle the existing invented desktop-teal.
- **Icons**: one per demo (LED, LED II, Title, CD Player, and "Bruce's Windows" itself as the exhibit). Simple monochrome pixel glyphs, no border box, label below each -- new pixel art, not archaeology; mock these up and get sign-off before wiring them in (same workflow as CD Player's prototype pass). Click/double-click opens that demo's window; the icon disables/hides while its window is open and re-enables when it closes. One instance per demo at a time.
- **Window chrome for opened demos**: the lighter Dialog archetype (black ring + raised bevel + sunken-bevel title bar, no corner boxes/status bar/resize grip -- those would look disproportionate on short-and-wide demos like Title or LED II). A close button is grafted onto the title bar's right end regardless (a small raised-bevel box with CD Player's own X glyph, reused) -- WINDOW1.png's Dialog archetype had no close control at all, so this is new, not sourced.
- **Title bar text**: needs a real pixel alphabet (A-Z at minimum, "LED II"/"CD Player" don't fit in digits-only fonts) -- hand-designed, no source to extract from, built the same `_DOT_GLYPH_ROWS`-style way as every other font in this project so it stays visually consistent.
- **Interactivity**: every opened window is draggable (title bar), closable (the new close button), and comes to front on click -- reuses the drag pattern `bruces_windows.py` already built, generalized to N windows instead of one.
- **Window sizing**: native 1:1 pixel size per demo, no scaling/padding -- authentic to how differently-sized these programs actually were.
- **`bruces_windows.py` refactor**: drops its own 320x240 canvas and internal drag logic once the desktop handles dragging for every window uniformly -- goes back to a plain 200x200 static render (its "Got it" closes-the-dialog logic stays; that's the exhibit's own content, not chrome). Opened from the desktop like any other demo, wrapped in the same generic window chrome as everything else.

### How it's built

- **`framework/window_chrome.py`**: `bevel_rect`/`black_ring` (moved out of `bruces_windows.py`, now byte-exact-verified primitives with a second real caller) plus `render_window_chrome(content, title)`, which wraps any demo's `draw()` output in the Dialog archetype + a close button and returns `title_bar`/`close_button`/`content` hit-test rects in the composed surface's own local coordinates.
- **`framework/pixel_font.py`**: the hand-designed 5x7 upper-case A-Z/0-9 alphabet, `text_cells()` laying out arbitrary title text the same way `DotMatrixDisplay.text_dots` does.
- **`retrodemos/demos/desktop.py`**: `DesktopDemo` owns `_open` (key -> `_OpenWindow`, each caching its own chrome geometry once at open time since it only depends on content size + title) and `_order` (z-order list, last = focused/topmost). Click routing checks, in order: an open window's close button, its title bar (starts a drag + focuses), its content area (focuses + forwards the click into the wrapped demo's own `handle_event`, translated to that demo's native coordinates via the `content` rect), then the icon row (opens a fresh instance, or just focuses if that demo's already open). Every open demo's `update(dt)` runs every frame regardless of focus -- background windows keep animating, not paused.
- **`__main__.py`**: `DESKTOP_DEMO_NAME = "desktop"`; no name given resolves to it before dispatch, so it's both the default and launchable by name like any other demo.

### Still open

- The shared quit/pause/restart keybindings (`framework/keys.py`) apply globally to the whole desktop, not per-window -- this wasn't a deliberate per-window design, just what building nothing special for it defaults to; revisit if it turns out to feel wrong once there's more than one or two demos open at a time (e.g. R currently restarts the whole desktop, closing every open window, not just the focused one).
- `framework/window_chrome.py`'s two primitives (`bevel_rect`, `black_ring`) are extracted and shared. CD Player's own two window frames now route through `bevel_rect` (2026-08-25, its second pixel-accuracy pass) -- its inner controls (readout, buttons) still don't, since those use different border styles (sunken, and a 3-sided highlight) than that helper provides. A future Tank Status Window's own chrome hasn't been revisited for the same question.
- All 8 planned demos (of the original 9; Dooley was cut) now have desktop icons.
- The top menu bar's dropdown (2026-08-25) has exactly 3 fixed items (About / Close All Windows / Quit) -- no per-app menus (a "File"/"Edit" a real focused app might contribute) exist yet, and nothing generalizes CD Player's `chrome=False` multi-window handling beyond its own hardcoded special case (see `desktop.py`'s module docstring) -- revisit both if a second demo ever needs either.

Follow-up review the same day: `WINDOW1.png` turned out to show two distinct window archetypes (Main Window: outer frame, sunken body-panel bevel, title bar, corner boxes, status bar; Dialog: black ring + raised bevel, title bar only, no other chrome -- see `docs/bruces-windows.md`) built from two measured, reusable border-style primitives that together reconstruct the whole window byte-exact against the source. That review also settled the unified-desktop spec, built the next day -- see "The unified desktop (end state)" above for the full account. `bruces_windows.py` itself dropped its own 320x240 canvas and drag logic once the desktop took that over generically, back to a plain 200x200 static render.

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

Build order 5 (Bruce's Windows) is done (2026-08-25), the first interactive demo. `WINDOW1.png` is a single coherent screenshot (unlike Title/Dooley/CD Player's source images), so no calibration-band untangling was needed; every text label (window title, dialog title, its two body lines, the button label, the status bar text) is pixel-verified -- extracted as the literal set of black pixels within its own tight bounding box, not decomposed into a reusable font, since every label here is fixed content. Caught and fixed one extraction bug along the way: an overly-tight search bound truncated the status text's "T" (its crossbar and stem), initially reading "his is a status a bar..." instead of the source's actual (and genuinely typo'd) "This is a status a bar...". Window chrome took two follow-up review passes the same day (request: identify the reusable window building blocks, since the first pass at bevel geometry wasn't accurate). First pass corrected the bevel direction (was backwards -- dark top/left instead of light top/left for "raised") but still approximated with guessed styles per element. Second pass measured every element's edge profile outside-in on all four sides via connected-component analysis (not eyeballed) and found the truth is simpler than either guess: the whole chrome is built from just **two** primitives -- a single 1px bevel (`_bevel_rect`, raised or sunken, used almost everywhere) and a plain black divider ring (`_black_ring`, used only between the Dialog's and the "Got it" button's own two nested opposite-direction bevels) -- plus a mitered-corner detail (the two corners where a bevel's two colours would collide are left unset, not closed) that a naive `pygame.draw.rect` gets wrong at every element. Confirmed against the source directly: `_render_window()` now reconstructs all 40,000 pixels of `images/WINDOW1.png` byte-exact, verified by a real reconstruct-and-diff test (`tests/test_bruces_windows.py`), the same bar LED-family fonts were held to. `WINDOW1.png` also turned out to show two distinct window archetypes, not one window with a popup bolted on: a **Main Window** (outer frame, a sunken body-panel bevel framing everything below the title bar -- the "content sits inside it" depth cue -- title bar, two raised corner boxes, a status bar) and a lighter-weight **Dialog** (black ring + raised bevel, floating above the body, same title-bar style, no corner boxes/status bar/resize grip) -- see `docs/bruces-windows.md`'s "Two window archetypes" section for the full inventory. Needed one new piece of shared framework, not just this demo's own code: `runtime.py` now rescales mouse event `pos`/`rel` from window-pixel space to native-canvas space before a demo ever sees them (`_to_native_space`), since no prior demo needed mouse input at all -- this benefits Cinqtris's About button next for free. The demo's own canvas (320x240) is bigger than the window (200x200) so there's visible room to drag it; the surrounding desktop backdrop is an invented flat teal, since `WINDOW1.png` shows only the window itself. The two border-style helpers aren't extracted into `framework/` yet -- written generically enough to lift out once a second window-drawing demo needs them, not done speculatively ahead of that. 141 tests passing (`tests/`).

CD Player got a second and third pixel-accuracy pass (2026-08-25), after Bruce playtested it and flagged it as far from pixel perfect -- worth logging in detail since each pass caught something the previous one missed. The **first** pass fixed real box-border and digit-font mistakes (an invented bevel that isn't in the source; fabricated "6 has no top bar, 9 has no bottom bar" quirks -- the readout turned out to be an all-segments-lit test pattern, not a real per-digit calibration strip) but still composited everything into one merged panel. Reviewing the source image again against that render showed the **real** structure: Band A is a genuine main player window (close button, "cd" logo, wide readout box, 5 transport buttons) sitting beside a taller, genuinely separate equalizer window (own close button, own "cd" logo, 6 sliders) -- not one panel, and not 4 sliders or 6 transport buttons as the first pass had. The **second** pass rebuilt the layout around that: two window frames (routed through `framework/window_chrome.py`'s `bevel_rect`, its first non-Bruce's-Windows caller), the dot-matrix spectrum moved *inside* the main readout box instead of a separate meter panel underneath, 5 buttons, 6 sliders. The **third** pass caught two more misses: the meter's "dots" are a genuine 2px NW-SE diagonal glint, not a single pixel (confirmed against the source at high zoom, byte-exact once fixed); and the main and equalizer windows are truly separate and independently draggable in the source -- clicking one reveals/reorders the other -- so CD Player became the project's second interactive demo, reusing `desktop.py`'s own per-window position/z-order pattern scoped to just its two windows. A **fourth** pass, this time playtesting the actual desktop shell rather than the standalone demo, found three more real bugs: the transport button icons were positioned with the wrong offset (up to 4px too far down, clipping most of the glyph -- a quick re-measure of each icon's own tight bounding box fixed it); opening CD Player from the desktop nested its two hand-drawn windows inside a *third*, generic desktop-chrome wrapper, reading as a window inside a window; and the equalizer showed by default instead of starting hidden until revealed. The nesting fix needed a real `desktop.py` extension, not just a `cd_player.py` fix: `_OpenWindow` gained a `chrome=False` mode, skipping the generic wrapper entirely and reading `close_rect`/`button_rects` straight off the demo instance for hit-testing instead of a chrome-supplied rect dict -- CD Player's main and equalizer panels now open as genuine independent top-level desktop windows (`_open_cd_player_main`/`_reveal_cd_player_eq`, hardcoded special cases, not a generalized "multi-window demo" abstraction, since this is the first and only demo that's needed one). Transport buttons also gained an invented press animation (inverted highlight, 1px nudge) and working close buttons. 181 tests passing (`tests/`).

A macOS-style top menu bar (2026-08-25, same session as CD Player's fourth pass) was added to the desktop shell itself, not any one demo: a white strip across the full width, exactly 2px padding + one line of `framework/pixel_font.py` text + 2px padding tall, a new ⌘ glyph at the left with a functional dropdown (About shows a small info panel, Close All Windows clears every open window, Quit ends the run), and the focused window's name (or "HELP" with nothing focused) after it. Both glyph and text render in the desktop's own teal with a 1px black drop shadow -- teal alone or white alone both read poorly against the plain white bar. Quit needed one small, genuinely new piece of framework: `Demo.want_quit`, a poll-based flag `runtime.run()` checks every frame, since until now only Esc/Q (handled by `handle_shared_keys` before any demo ever sees the event) could end a run -- no demo previously had a way to ask the runtime to stop itself. Windows are clamped below the bar (can't be dragged or opened underneath it); `ICON_ORIGIN` and `CASCADE_BASE` shifted down by the bar's height to match. 192 tests passing (`tests/`).

A short follow-up the same day swapped the drop shadow for a bold weight instead (`_draw_bold`: every lit cell gets a second one a column to its right, since a 1px-stroke font has no separate bold glyph set to switch to) once seen live -- cleaner against the white bar than the shadow was. The "HELP" text (shown when nothing is focused) is now itself clickable, opening a panel of condensed `README.md` content (`_HELP_LINES`, paraphrased -- `pixel_font` has no punctuation beyond an apostrophe, so quoting verbatim wasn't an option); the same panel machinery now serves both it and About (`_panel_rect`/`_draw_panel`, generalized from what was `_about_panel_rect`/`_draw_about_panel`). Separately, playtesting flagged that an open demo's icon disappearing "is weird" -- icons now stay visible always and just dim (disabled, not hidden) while their window is open, matching how a disabled control looks everywhere else; clicking a disabled icon is a no-op. Bruce's Windows' icon is disabled outright regardless of open state (`_PERMANENTLY_DISABLED`) -- a demo *of* windowing chrome reads as redundant now that the desktop itself is a real windowing system, parked rather than removed since a use for it may still turn up. 198 tests passing (`tests/`).

Build order 6 (Cinqtris) is done (2026-08-25). `CT_ANI.png` (128x145) turned out to be a sprite sheet, not a screenshot of the finished title screen -- same surprise every other demo's source image has held: three animation strips (wordmark, equalizer, "MADMAX") stacked vertically for storage, no layout mockup to build from. `docs/cinqtris.md`'s own three-cells-across sketch didn't survive contact with the source either. Design went through several review rounds with Bruce before any code was written, using a live HTML/canvas mockup (not a static PNG) to iterate quickly on layout and animation together -- confirmed valuable enough to note as a pattern worth reusing for a future demo with real interaction/animation to settle before building. Settled: a vertical stack (wordmark directly above the equalizer, not the original three-cell row), both rendered at matching width since both are 128 native px in the source and meant to line up; the wordmark's own 2px source margin cropped to exactly 1px top/bottom, kept local to the wordmark and not applied elsewhere; the equalizer's real sunken-bevel border (initially stripped out by mistake, then restored once re-checked against the source) with a divider between columns; both elements explicitly centred. The "10-segment equalizer" the spec's own name promised turned out to be 7 segments in the source -- kept as measured, not padded out to match the name. MADMAX's original spec (a button opening an About popup) was descoped during review in favour of a click-anywhere slide animation across the screen and off the far edge, reusing the source's 4 unique letter shapes laid out horizontally instead of the source's own stacked 2x3 grid -- the one real adaptation, everything else is a direct lift. No `Phase`/`PhaseSequence` (same reasoning CD Player's and Dooley's continuous designs used). Icon (a small equalizer-bars glyph, matching the demo's own visual identity directly) mocked up and confirmed before wiring into `desktop.py`'s `_DEMO_ENTRIES`, same workflow as the other five. 210 tests passing (`tests/`).

## Next step

Build order 7 (Bruce's 21) is done (2026-08-25). `CARDS.png` (672x264) reconstructed byte-exact as a clean 14x4 grid of 48x66 tiles -- no gaps, no border padding -- with rows for the four suits and columns A-K in the first 13, but the 14th column turned out to be non-card splash art (a "21"/MADMAX title card, a portrait, a "bruce's blackJack V.01" logo, and a blank), out of scope for this pass; `BACKS.png` (128x164) is a 2x2 grid of 64x82 tiles, two distinct designs each duplicated top and bottom. The real decision this demo forced: every prior demo hand-encodes its source pixels as literal data and never loads a PNG at runtime, but transcribing 52 detailed card faces by hand risked subtle errors with no upside -- confirmed with Bruce to load `CARDS.png`/`BACKS.png` directly via `pygame.image.load` + `subsurface` instead, the first (and likely only) demo built this way. `convert_alpha()` isn't used, since `Deck` is built in `Demo.__init__`, before `runtime.run()` sets up a display surface; plain unconverted surfaces blit fine at this sprite count. Uses `Phase`/`PhaseSequence` (`DeckCyclePhase` shuffles all 52 cards plus both backs into a flip-through cycle; `AutoDealPhase` scripts a mock deal -- dealer hole card, up-cards, a random 0-2 "hit", a reveal, maybe one more dealer card -- with no hand values ever computed, per the spec's "visual only" note and Bruce's own "build it as a demo, not a game"). `bruces_21_table.py` holds the sprite loader (`Deck`) and the shared `CardTable` display the two phases in `bruces_21_phases.py` drive, split out from `bruces_21.py` itself to avoid an import cycle between the demo module and its phases -- the same shape `led_grid.py` has relative to `led.py`/`led_phases.py`. Table layout (felt-green background, DEALER/PLAYER labels via `pixel_font`, fanned hands) is new, invented content, the same situation Cinqtris's wordmark+equalizer layout was in. Icon (a card outline with a diamond pip, matching the other icons' abstraction level) wired into `desktop.py`'s `_DEMO_ENTRIES` and screenshotted to confirm it reads at native size, same as the other invented-content icons. 223 tests passing (`tests/`).

Build order 8 (Tank Status Window) is done (2026-08-25) -- the eighth and last of the originally planned demos (Dooley, at order 4, was cut). `WIN1.png` (273x350) reconstructed close to byte-exact: a red/black outer frame, a title bar with a flat minimize box and a bevelled dropdown box, an 83x84 red/black dot-matrix grid, a smaller 83x9 secondary strip, and 11 blank grey buttons -- all measured, not guessed (the button count in particular: the spec's own "row of blank grey buttons" undercounted it as roughly 8 by eye; a real pixel scan found 11). The dot geometry (2x2px on a 3px pitch) and on-colour ((191, 0, 0)) are pixel-identical to `led_grid.DOT_LIT`/`DotMatrixDisplay`'s own -- confirmed by direct comparison -- but `DotMatrixDisplay` itself isn't reused: its bezel is a different shape and its `ROWS = 9` doesn't fit an 84-row grid. What legitimately carries over: `led_grid.dot_grid_adjacency` for the explosion topology, `framework/window_chrome.py`'s `bevel_rect`/`black_ring` for the button row and dropdown box (the source's own chrome there really is that exact combination), and -- a genuine surprise -- `led_grid.DOT_FONT` turned out to be the *wrong* font to reach for a status readout despite matching the strip's row count exactly: it's digits/space/hyphen only (built for LED II's numeric marquee), no letters, so `framework/pixel_font.py`'s A-Z alphabet went in instead. The single biggest surprise: `WIN1.png`'s own grid is a lit-everywhere test pattern, not a captured frame of real gameplay, so literally none of "tanks, walls, bullets, explosions" came from the source -- the spec's own open question ("scripted/looping vs. real game logic") was already resolved in the spec itself, in favour of scripted/looping. Built as three `Phase`s (`PatrolPhase`, `EngagePhase`, `ResetPhase`) over a shared `TankDisplay` (`tank_status_window_grid.py`, split out from `tank_status_window.py` to avoid an import cycle with `tank_status_window_phases.py`, the same shape `bruces_21_table.py` has): tanks patrol fixed lanes, trade a handful of scripted shots whose impacts are small `graph_walk.Burst`s, then a bigger centred Burst reads as the round ending before the loop restarts. One real bug caught before it shipped: `Burst.burned_out` requires `add_sparks()` to have been called at least once (even with `spark_count=0`) -- omitting it left every burst "expanding forever" from the caller's point of view, silently hanging `EngagePhase`/`ResetPhase` past their own end conditions; caught by watching a full loop run for longer than the scripted duration should allow, not by a passing-too-fast test. Icon (a small tank-turret glyph) added to `desktop.py`'s `_DEMO_ENTRIES`. 236 tests passing (`tests/`) -- all 8 planned demos are now built.

## Playtesting round, 2026-08-26 (first pass across three shipped demos)

With all 8 demos built, playtesting moved to checking them against each other/the sources more critically rather than one at a time in isolation. Three demos got real fixes in one session:

- **Tank Status Window**: opening it from the desktop nested `WIN1.png`'s own frame inside a second, generic wrapper window -- the same bug CD Player's own windows hit first, fixed the same way (`desktop.py`'s new `_CHROMELESS` set, a smaller-scoped version of the `chrome=False` mechanism CD Player needed its own hardcoded special case for). The button row bled past the window's right edge and the title text was off -- both were "simplified, not measured" approximations from the original build; replaced with a full reconstruct-and-diff pass against `WIN1.png` (previously only spot-checked), now 95,546/95,550 pixels exact. One genuine quirk found along the way: the 4th button renders flat in the source, not raised like the other 10. Animation speed increased 15% (`_SPEED = 1/1.15` in `tank_status_window_phases.py`, scaling every duration uniformly rather than hand-retuning each one).
- **LED**: `NumbersPhase`'s scroll speed increased 50% (`SCROLL_INTERVAL = 0.4/1.5`) -- both this and Tank Status Window's fix settled the same reading of "N% faster": the rate increases N%, so a duration is divided by `1 + N/100`, not multiplied by `1 - N/100`.
- **CD Player**: transport button icons were still off-centre after the 2026-08-25 fix (that pass solved clipping, not centring) -- `icon_offset` values now come from matching each icon's own black-pixel bounding box in `_ICON_ROWS` against its measured bounding box in `CDPLAYER.png`, not eyeballed. More substantially, the readout's two dot areas were swapped in purpose: the big dot-matrix area (previously a generic invented "spectrum meter") now scrolls a marquee -- the current fake track's title, then "0123456789" as a lighter-weight nod to "run the other LED demos on it" that doesn't require hosting a second Demo's update loop inside a differently-shaped display -- and the small dot swatch beside "1AR" (previously a static copy of the source's own all-lit calibration pattern) now animates as a real per-column frequency bar meter, reusing simulated levels the same way the old meter did.

237 tests passing (`tests/`).
