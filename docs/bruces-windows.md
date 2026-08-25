# Bruce's Windows

**Source:** `WINDOW1.png`
**Mode:** Functionally interactive (exception to the automated-only rule; this is the reference for the shared UI chrome)
**Build:** Done (`retrodemos/demos/bruces_windows.py`) -- chrome is byte-exact against the source (see "What it shows" below)

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
- A single 1px bevel (`_bevel_rect`): white top/left + grey bottom/right for raised, swapped for sunken. Every bordered element above uses this, including the status text field and icon grid (an earlier pass guessed a "double rule with a gap" for those; it's the exact same touching bevel as everything else).
- A plain black divider ring (`_black_ring`), used only between the Dialog's and the button's two opposite-direction bevels.

One more finding that took two passes to catch: every outline is **mitered, not closed** -- at the two corners where an element's two bevel colours would collide (top-right, bottom-left), the source leaves the pixel unset (background shows through) rather than picking one colour to win. A naive closed rectangle draws both of those corners wrong.

## What it shows

Windows 3.1-style chrome: a title bar reading "Window Title," a "Dialog" box titled "Welcome to Bruce's Windows" with a "Got it" button, and a status bar reading "This is a status a bar..." (a genuine quirk in the source -- an extra "a" before "bar", not "This is a status bar..." as this doc originally paraphrased it; kept verbatim, not "corrected").

`WINDOW1.png` (200x200) is a single coherent screenshot, unlike Title/Dooley/CD Player's source images -- no bundled calibration bands to untangle. Every text label is pixel-verified: extracted as the literal set of black pixels within its tight bounding box (see `docs/pixel-archaeology.md`), not decomposed into a reusable font -- every label here is fixed content, not `--text`-overridable, so there's no reason to build one.

**The whole 200x200 window is now reconstructed byte-exact against the source** -- `tests/test_bruces_windows.py` diffs every pixel of `_render_window()`'s output against `images/WINDOW1.png` and asserts zero mismatches, the same reconstruct-and-diff bar `docs/pixel-archaeology.md` sets for fonts, now applied to an entire chrome layout. Getting there took two review passes: the first pass approximated the chrome with one generic bevel helper and had the bevel direction backwards; the second measured every element's edge profile outside-in on all four sides (rather than eyeballing) and found the geometry described in "Two window archetypes" above, plus the mitered-corner detail. See `retrodemos/demos/bruces_windows.py`'s module docstring for the full account.

## Behaviour

Renders the window and dialog on load. No auto-looping animation. The demo's canvas (320x240) is larger than the window itself (200x200) so there's visible room to drag it around; the rest of the canvas is a plain invented desktop-teal backdrop (`WINDOW1.png` shows only the window, no surrounding desktop).

## Interaction

- Title bar is draggable (clamped to the canvas bounds).
- "Got it" button closes the dialog; once closed it stays closed until `R` (restart).

Needed `framework/runtime.py`'s new mouse-coordinate rescaling (added the same day, see its own docstring) -- the first demo that needed mouse events at all; every future interactive demo (Cinqtris's About button next) gets it for free.

## Assets

Custom-drawn chrome to match `WINDOW1.png`. Per `PLAN.md`, this chrome is not extracted into the shared framework yet; CD Player and Tank Status Window draw their own window-style borders independently. The two border-style helpers (`_bevel_rect`, `_black_ring`) are written generically enough to lift into `framework/` once a second window-drawing demo needs them -- not done speculatively ahead of that, same reasoning `graph_walk.py`'s primitives were each pulled out only once a second real caller needed the identical logic.

## Open questions

- Scope of interactivity beyond drag and "Got it" (e.g. a working close/minimize box, whether the dialog is modal) is unspecified. Treat drag + "Got it" as the baseline -- built exactly that and nothing more.
- Whether/when to extract the Main-Window-vs-Dialog archetype split and the two border-style helpers into a reusable `framework/` module is undecided -- see "Assets" above and `PLAN.md`'s "Future: the unified desktop" section. The desktop shell itself is explicitly TBD.
- This demo's role is expected to grow: see `PLAN.md`'s "Future: the unified desktop (end state)" section (logged 2026-08-24) -- Bruce's Windows' chrome becomes the desktop shell that every other demo eventually runs inside, as its own window, rather than staying a single title-bar-plus-dialog demo forever. Not scheduled yet; every other demo needs to be built first.
