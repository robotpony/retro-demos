# Bruce's Windows

**Source:** `WINDOW1.png`
**Mode:** Functionally interactive (exception to the automated-only rule; this is the reference for the shared UI chrome)
**Build:** Done (`retrodemos/demos/bruces_windows.py`)

## What it shows

Windows 3.1-style chrome: a title bar reading "Window Title," a "Dialog" box titled "Welcome to Bruce's Windows" with a "Got it" button, and a status bar reading "This is a status a bar..." (a genuine quirk in the source -- an extra "a" before "bar", not "This is a status bar..." as this doc originally paraphrased it; kept verbatim, not "corrected").

`WINDOW1.png` (200x200) is a single coherent screenshot, unlike Title/Dooley/CD Player's source images -- no bundled calibration bands to untangle. Every text label is pixel-verified: extracted as the literal set of black pixels within its tight bounding box (see `docs/pixel-archaeology.md`), not decomposed into a reusable font -- every label here is fixed content, not `--text`-overridable, so there's no reason to build one. The status bar's own icon grid (12 columns -- 6 green, 6 red -- x4 rows, 2px squares on a 3px pitch) is also pixel-verified, since its exact pattern is content, not just decoration.

The window chrome itself (borders, bevels, the corner boxes, the status bar's icon-grid box, the resize grip) is approximated with a consistent raised/sunken-rect helper rather than matched pixel-for-pixel -- the same "decorative backdrop, not carried content" tier Dooley's RGB-spinner/grid area and CD Player's overall panel layout got.

## Behaviour

Renders the window and dialog on load. No auto-looping animation. The demo's canvas (320x240) is larger than the window itself (200x200) so there's visible room to drag it around; the rest of the canvas is a plain invented desktop-teal backdrop (`WINDOW1.png` shows only the window, no surrounding desktop).

## Interaction

- Title bar is draggable (clamped to the canvas bounds).
- "Got it" button closes the dialog; once closed it stays closed until `R` (restart).

Needed `framework/runtime.py`'s new mouse-coordinate rescaling (added the same day, see its own docstring) -- the first demo that needed mouse events at all; every future interactive demo (Cinqtris's About button next) gets it for free.

## Assets

Custom-drawn chrome to match `WINDOW1.png`. Per `PLAN.md`, this chrome is not extracted into the shared framework; CD Player and Tank Status Window draw their own window-style borders independently.

## Open questions

- Scope of interactivity beyond drag and "Got it" (e.g. a working close/minimize box, whether the dialog is modal) is unspecified. Treat drag + "Got it" as the baseline -- built exactly that and nothing more.
- The window chrome's exact border/bevel pixel geometry isn't independently re-verified beyond the text and icon-grid content (see "What it shows" above) -- fine for a backdrop, worth tightening if this demo ever needs to be pixel-exact everywhere.
- This demo's role is expected to grow: see `PLAN.md`'s "Future: the unified desktop (end state)" section (logged 2026-08-24) -- Bruce's Windows' chrome becomes the desktop shell that every other demo eventually runs inside, as its own window, rather than staying a single title-bar-plus-dialog demo forever. Not scheduled yet; every other demo needs to be built first.
