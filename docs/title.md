# Title

**Source:** `TITLE.png`
**Mode:** Automated attract-mode

## What it shows

LED bit-pattern demo. Two pattern sets at the bottom, read column by column left to right; each column is a set of bits representing a vertical line with a value 0-255.

## Behaviour

Two strips (red/green, blue/cyan), 256 columns wide, each column showing one byte value's own 8 bits top-to-bottom (MSB at top), colour-coded per bit. `TITLE.png` itself turned out to encode the exact rendering rule, not just a calibration image: both strips show the static "column x displays value x" identity ramp, verified pixel-exact against all 256 columns x 8 rows x 2 colour pairs (see `docs/pixel-archaeology.md` and `framework/led_grid.py`'s `BitColumnDisplay`).

Runs a scripted sequence on a loop, mirroring LED and LED II's own five-beat structure -- confirmed with Bruce (2026-08-24), since (like LED II) Title had no source spec of its own pinning down a script: power-up (random bit flicker across both strips, then a column sweep that speeds up), a scrolling main-content phase (both strips' value-per-column mapping scroll over time, in opposite directions at different speeds, starting each time from offset 0 -- the exact identity ramp `TITLE.png` itself shows), a "snake" that crawls each strip's bit grid independently, a firework burst on both strips together, then a held "1991" credit. Unlike LED/LED II, Title has no font to hold that credit with (a `BitColumnDisplay` column is a byte value, not a glyph cell), so `WordsPhase` encodes "1991" as its own literal ASCII byte values (0x31, 0x39, 0x39, 0x31) in four centred columns on an otherwise blank field -- the same composition as LED/LED II's held credit, expressed in Title's own vocabulary of bytes rather than borrowing a font it doesn't have. See `retrodemos/demos/title_phases.py` for each phase's choreography.

The snake and fireworks phases address individual `(column, bit)` cells directly via `BitColumnDisplay.render_raw` (new alongside the existing byte-value-driven `render_values`) and `framework/graph_walk.py`'s `Snake`/`Burst` over `led_grid.dot_grid_adjacency(width, ROWS)` -- the same primitives LED II's phases use, over a bit grid instead of a dot grid. `dot_grid_adjacency` is purely `(col, row)` topology with no dot-specific assumptions, so it's reused as-is rather than duplicated for a "bit grid" variant.

Two dot-matrix panels above the bit-pattern strips in `TITLE.png` (fully-lit red and blue) are calibration reference only, the same role LED-thumb.png's lit "8" and LED-II-thumb.png's fully-lit grid play -- not part of the rendered demo. They pin down the red/blue colours (both measured directly, not invented).

## Interaction

None beyond the shared quit/pause controls.

## Assets

Shares the LED rendering framework with `led.md`, `led-ii.md`, and `dooley.md` -- though its `BitColumnDisplay` (`framework/led_grid.py`) is its own renderer, not an extension of `DotMatrixDisplay`: no bezel, no gap between columns, and content computed directly from a byte value rather than drawn from a font. Extending `DotMatrixDisplay` was the original plan (see `PLAN.md`), but Title's actual pixel model turned out different enough that forcing it in would have meant bending `DotMatrixDisplay`'s dot-grid shape around geometry it doesn't describe. `title.py`'s `TitleDisplays` composes the two `BitColumnDisplay` strips into the one unit every phase drives together, since (unlike LED/LED II, one display each) Title's script runs over two strips at once.

## Future polish (out of scope for now)

- The scroll speed/direction split between the two strips, and the snake/fireworks sizing constants, are invented choreography details, not confirmed with Bruce -- flag for review, same as LED II's assumed defaults.
- The timing-momentum and synthesized-beep polish items tracked in `PLAN.md`'s "Future framework polish" apply here too, once built.
