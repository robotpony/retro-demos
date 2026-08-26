# Cinqtris

**Source:** `CT_ANI.png`
**Mode:** Automated attract-mode, with one interactive control
**Build:** Done (`retrodemos/demos/cinqtris.py`)

## What it shows

An animated "CINQTRIS" wordmark stacked directly above an 8-bar cascading
equalizer, both the same width and centred -- not the three-cells-across
layout originally sketched here. `CT_ANI.png` (128x145) turned out to be
a sprite sheet, not a screenshot of the finished title screen, same
surprise every other demo's source image has held: it bundles three
separate animation strips (wordmark, equalizer, "MADMAX"), stacked
vertically for storage, with no layout mockup to follow. The vertical
stack, matching widths, and click-to-slide MADMAX interaction below were
worked out with Bruce over several review rounds (2026-08-25) before
building, using a live HTML/canvas mockup to iterate quickly.

`CT_PRTS.png` (the palette/font/board-texture sheet) went unused in the
end -- everything the built demo needed came directly from `CT_ANI.png`.

## Assets

- **Wordmark**: 8 letters x 16x16, pixel-verified. Letter *shape* is
  identical across all 3 sampled frames in the source; only a 3-colour
  band (yellow/olive/green, 4px each) cycles per frame, scrolling upward
  with wraparound -- not three different letter bitmaps.
- **Equalizer**: 14-frame rise-and-fall sequence (frames 0-7 red-to-green
  rising, 8-13 falling back), 7 segments per bar, pixel-verified. The
  spec originally here said "10-segment"; the source only ever shows 7.
  Also pixel-verified: a real sunken bevel border (grey top/left, white
  bottom/right) framing the whole strip, with a divider between columns
  -- missed in an early pass, since it reads as background chrome rather
  than part of "the bars."
- **MADMAX**: 4 unique 7x7 letter shapes (M, A, D, X), pixel-verified.
  The source lays "MAD"/"MAX" out as a stacked 2x3 grid in two
  colour-swapped frames (not hover/press states, just a colour flash);
  this demo re-lays the same shapes out as one horizontal row
  (M-A-D-M-A-X) instead, since a left-to-right slide needs a horizontal
  strip -- the one real adaptation, not a straight lift.

## Behaviour

One continuous loop, no `Phase`/`PhaseSequence` (same reasoning CD
Player's continuous design used -- nothing here suggested discrete
narrative beats):

- The wordmark cycles its 3 colour frames on a fixed interval.
- The equalizer's 8 bars each cycle the full 14-frame sequence, staggered
  by 1 frame per bar, for a cascading-wave look.
- Both timings are invented (no timing data exists in a static sprite
  sheet); tuned by eye during the mockup review.

## Interaction

Clicking anywhere on the demo triggers a one-shot animation: "MADMAX"
slides in from the left, passes over the equalizer, and exits off the
right edge, then resets to hidden. Ignored while already sliding. This
replaces the originally-specified About-popup button -- deliberately
descoped during design review in favour of the slide, not yet reinstated.

## Open questions

- Whether MADMAX should still open an About popup (the original spec)
  in addition to or instead of the slide is unresolved -- currently just
  the slide.
- Slide speed (currently 90 native px/sec) and both cycle intervals are
  first-guess defaults, not tuned against any reference.
