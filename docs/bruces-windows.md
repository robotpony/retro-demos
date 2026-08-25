# Bruce's Windows

**Source:** `WINDOW1.png`
**Mode:** Functionally interactive (exception to the automated-only rule; this is the reference for the shared UI chrome)
**Build:** Done (`retrodemos/demos/bruces_windows.py`)

## Two window archetypes, one screenshot

Reviewed carefully on request (2026-08-25) with an eye toward reusable building blocks for a future windowing system. `WINDOW1.png` shows **two distinct window types**, not one window with a popup bolted on:

**Main Window** (the outer frame, the whole 200x200 canvas)
- Outer frame: 1px black, 1px white, a 2px background margin
- Title bar ("Window Title"), framed by its own sunken bevel (grey top/left, white bottom/right)
- Two corner boxes flanking the title bar, each a simple raised bevel (white top/left, grey bottom/right) -- undecorated, no icon inside
- Body: plain background panel
- Status bar: a text field, an icon grid, and a resize grip, each its own component (below)

**Dialog** (nested inside the Main Window's body, a lighter-weight type)
- Border: plain 1px black + 1px white -- no background margin the way the Main Window's outer frame has
- Title bar ("Dialog"), same cyan + sunken-bevel-frame style as the Main Window's
- Body: text lines directly on the panel background
- **No corner boxes, no status bar, no resize grip** -- the defining structural difference from the Main Window type

**Shared sub-components, each its own border style** (not one generic bevel -- see below):
- Button ("Got it"): a triple-ring frame (grey, black, white, outside-in, uniform on all sides)
- Status text field: a single grey rule inside + single white rule outside, background gaps between
- Status icon grid: same grey-inside/white-outside style, containing a pixel-verified 12x4 green/red cell grid (6 green columns, 6 red, 2px squares on a 3px pitch)
- Resize grip: diagonal grey/white checkerboard triangle, no border box, bottom-right corner only

## What it shows

Windows 3.1-style chrome: a title bar reading "Window Title," a "Dialog" box titled "Welcome to Bruce's Windows" with a "Got it" button, and a status bar reading "This is a status a bar..." (a genuine quirk in the source -- an extra "a" before "bar", not "This is a status bar..." as this doc originally paraphrased it; kept verbatim, not "corrected").

`WINDOW1.png` (200x200) is a single coherent screenshot, unlike Title/Dooley/CD Player's source images -- no bundled calibration bands to untangle. Every text label is pixel-verified: extracted as the literal set of black pixels within its tight bounding box (see `docs/pixel-archaeology.md`), not decomposed into a reusable font -- every label here is fixed content, not `--text`-overridable, so there's no reason to build one.

**Fixed on review (2026-08-25):** the first build pass collapsed all four border styles above into one generic raised/sunken-rect helper, and got the bevel direction backwards in the process (dark top/left instead of light top/left for "raised"). Every border is now measured by sampling its edge profile (background -> border colours -> content) outside-in on all four sides -- caught the direction bug, the button's actual triple-ring style, the status field/icon box's actual double-rule style, and a sunken bevel framing both cyan title bars that the first pass missed entirely. See `retrodemos/demos/bruces_windows.py`'s module docstring for the four styles' exact geometry (`_bevel_rect`, `_ring_frame`, `_double_rule_rect`).

## Behaviour

Renders the window and dialog on load. No auto-looping animation. The demo's canvas (320x240) is larger than the window itself (200x200) so there's visible room to drag it around; the rest of the canvas is a plain invented desktop-teal backdrop (`WINDOW1.png` shows only the window, no surrounding desktop).

## Interaction

- Title bar is draggable (clamped to the canvas bounds).
- "Got it" button closes the dialog; once closed it stays closed until `R` (restart).

Needed `framework/runtime.py`'s new mouse-coordinate rescaling (added the same day, see its own docstring) -- the first demo that needed mouse events at all; every future interactive demo (Cinqtris's About button next) gets it for free.

## Assets

Custom-drawn chrome to match `WINDOW1.png`. Per `PLAN.md`, this chrome is not extracted into the shared framework yet; CD Player and Tank Status Window draw their own window-style borders independently. The four border-style helpers (`_bevel_rect`, `_ring_frame`, `_double_rule_rect`, plus the outer-frame logic) are written generically enough to lift into `framework/` once a second window-drawing demo needs them -- not done speculatively ahead of that, same reasoning `graph_walk.py`'s primitives were each pulled out only once a second real caller needed the identical logic.

## Open questions

- Scope of interactivity beyond drag and "Got it" (e.g. a working close/minimize box, whether the dialog is modal) is unspecified. Treat drag + "Got it" as the baseline -- built exactly that and nothing more.
- Whether/when to extract the Main-Window-vs-Dialog archetype split and the four border-style helpers into a reusable `framework/` module is undecided -- see "Assets" above and `PLAN.md`'s "Future: the unified desktop" section. The desktop shell itself is explicitly TBD.
- This demo's role is expected to grow: see `PLAN.md`'s "Future: the unified desktop (end state)" section (logged 2026-08-24) -- Bruce's Windows' chrome becomes the desktop shell that every other demo eventually runs inside, as its own window, rather than staying a single title-bar-plus-dialog demo forever. Not scheduled yet; every other demo needs to be built first.
