# Bruce's Windows

**Source:** `WINDOW1.png`
**Mode:** Functionally interactive (exception to the automated-only rule; this is the reference for the shared UI chrome)
**Build:** Done (`retrodemos/demos/bruces_windows.py`) -- chrome is byte-exact against the source (see "What it shows" below); its reusable bevel primitives now live in `framework/window_chrome.py`

## Two window archetypes, one screenshot

Reviewed carefully on request (2026-08-25) with an eye toward reusable building blocks for a future windowing system. `WINDOW1.png` shows **two distinct window types**, not one window with a popup bolted on:

**Main Window** (the outer frame, the whole 200x200 canvas)
- Outer frame: 1px black, then a raised bevel (white top/left, grey bottom/right) right at the window's own edge
- A sunken bevel (`BODY_BEVEL_RECT`) frames the whole space between the title bar and the status row -- this is the "content sits inside the window" depth cue
- Title bar ("Window Title"), framed by its own sunken bevel
- Two corner boxes flanking the title bar, each a raised bevel, 17x17 -- undecorated, no icon inside
- Status bar: a text field and an icon grid, each a sunken bevel inset into the open background below the body panel, plus a resize grip (bottom-right corner, no border box)

**Dialog** (nested inside the Main Window's body, a lighter-weight type)
- Border: a black ring, then a **raised** bevel just inside it -- the dialog floats above the body, opposite direction from the body panel's own sunken bevel
- Title bar ("Dialog"), same sunken-bevel-plus-cyan style as the Main Window's
- Body: text lines directly on the panel background
- **No corner boxes, no status bar, no resize grip** -- the defining structural difference from the Main Window type
- The "Got it" button nests the *same* raised-inside-sunken pattern the dialog itself uses: a sunken bevel (the well), a black ring, then a raised bevel (the button face) -- not the uniform three-colour "ring frame" an earlier pass guessed

**The chrome is built from just two primitives**, not a different style per element:
- A single 1px bevel (`bevel_rect`): white top/left + grey bottom/right for raised, swapped for sunken. Every bordered element above uses this, including the status text field and icon grid (an earlier pass guessed a "double rule with a gap" for those; it's the exact same touching bevel as everything else).
- A plain black divider ring (`black_ring`), used only between the Dialog's and the button's two opposite-direction bevels.

Both now live in `framework/window_chrome.py` (moved 2026-08-25, once the desktop shell -- `PLAN.md`'s "Future: the unified desktop" -- became a second real caller for them), alongside a new generic `render_window_chrome()` that wraps *any* demo's content in the lighter Dialog archetype plus a close button (new, not in the source -- WINDOW1.png's own Dialog has no close control) and a title drawn in a new hand-built pixel alphabet (`framework/pixel_font.py`, since the source only ever shows the fixed strings "Window Title"/"Dialog", not a usable A-Z set).

One more finding that took two passes to catch: every outline is **mitered, not closed** -- at the two corners where an element's two bevel colours would collide (top-right, bottom-left), the source leaves the pixel unset (background shows through) rather than picking one colour to win. A naive closed rectangle draws both of those corners wrong.

## What it shows

Windows 3.1-style chrome: a title bar reading "Window Title," a "Dialog" box titled "Welcome to Bruce's Windows" with a "Got it" button, and a status bar reading "This is a status a bar..." (a genuine quirk in the source -- an extra "a" before "bar", not "This is a status bar..." as this doc originally paraphrased it; kept verbatim, not "corrected").

`WINDOW1.png` (200x200) is a single coherent screenshot, unlike Title/Dooley/CD Player's source images -- no bundled calibration bands to untangle. Every text label is pixel-verified: extracted as the literal set of black pixels within its tight bounding box (see `docs/pixel-archaeology.md`), not decomposed into a reusable font -- every label here is fixed content, not `--text`-overridable, so there's no reason to build one.

**The whole 200x200 window is now reconstructed byte-exact against the source** -- `tests/test_bruces_windows.py` diffs every pixel of `_render_window()`'s output against `images/WINDOW1.png` and asserts zero mismatches, the same reconstruct-and-diff bar `docs/pixel-archaeology.md` sets for fonts, now applied to an entire chrome layout. Getting there took two review passes: the first pass approximated the chrome with one generic bevel helper and had the bevel direction backwards; the second measured every element's edge profile outside-in on all four sides (rather than eyeballing) and found the geometry described in "Two window archetypes" above, plus the mitered-corner detail. See `retrodemos/demos/bruces_windows.py`'s module docstring for the full account.

## Behaviour

Renders the window and dialog on load. No auto-looping animation. Runs at a plain 200x200 (`WINDOW_SIZE`) -- this demo used to own a bigger 320x240 canvas with its own internal draggable-window simulation, but that moved to `framework/window_chrome.py` as the desktop shell's own generic responsibility (2026-08-25) once the desktop's spec was settled; see "Assets" below.

## Interaction

- "Got it" button closes the dialog; once closed it stays closed until `R` (restart).
- No drag when launched standalone (`python -m retrodemos bruces_windows`) -- opened from the eventual desktop shell, it gets the same draggable/closable chrome every other demo's window does, via `framework/window_chrome.py`'s generic wrapper.

`framework/runtime.py`'s mouse-coordinate rescaling (added building this demo, see its own docstring) was the first demo that needed mouse events at all; every interactive demo since (and the desktop shell) gets it for free.

## Assets

Custom-drawn chrome to match `WINDOW1.png`, reverse-engineered here first. The two border-style primitives (`bevel_rect`, `black_ring`) and the generic `render_window_chrome()` wrapper now live in `framework/window_chrome.py` (moved 2026-08-25, once the desktop shell became a second real caller for the same bevel logic -- same reasoning `graph_walk.py`'s primitives were each pulled out only once a second real caller needed the identical logic). `bruces_windows.py` keeps its own pixel-verified text-glyph tables and `_render_window()` (this exhibit's exact screenshot layout, which the generic wrapper doesn't reproduce) plus the "Got it" interactivity, which is this exhibit's own content, not chrome.

## Open questions

- Scope of interactivity beyond "Got it" (e.g. a working close/minimize box, whether the dialog is modal) is unspecified. Treat "Got it" as the baseline for this exhibit's own content -- drag/close are now the desktop shell's job, not this demo's.
- This demo's role has already started to change: see `PLAN.md`'s "Future: the unified desktop (end state)" section (spec settled 2026-08-25) -- Bruce's Windows becomes the root interface of `retrodemos` itself (a 1024x576 icon-driven desktop), and this file's own exhibit becomes just one of the icons you can open from it, not the whole experience. The desktop shell itself (icon rendering, click handling, multi-demo embedding, `__main__.py` wiring) isn't built yet.
