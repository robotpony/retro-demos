# CD Player

**Source:** `CDPLAYER.png`
**Mode:** Interactive -- two draggable windows, simulated audio
**Build:** Done (`retrodemos/demos/cd_player.py`)

## What it shows

`CDPLAYER.png` (384x78) turned out not to be one coherent screenshot, the
same surprise Title's and Dooley's source images held: it bundles three
stacked reference bands. Band A (x0-284, y0-31) is the **main player
window**: close button, "cd" logo, a wide readout box (spectrum dots, a
3-digit counter, a "repeat/shuffle/1AR" status cluster), and 5 transport
buttons. A companion **equalizer window** sits beside it (x287-383,
y0-53, taller than the main window since it isn't split at y31 the way
the main window is): its own close button, own "cd" logo, and a 6-band
slider bank. Band B (y32-53, x0-247) is a sprite/reference strip below
the main window, not part of any real window -- icon and digit-shape
reference only, same role Dooley's own reference material played. Band C
(y56-77) is a separate full-width level-meter strip, reference for the
meter's colours, pitch, and dot shape, not a UI element of its own.

Getting here took three playtesting-driven review passes on 2026-08-25,
each catching a real mistake the previous one missed:

1. **First pass** fixed real box-border and digit-font mistakes (an
   invented bevel that isn't in the source; "6 has no top bar, 9 has no
   bottom bar" quirks that turned out to be fabricated -- the readout is
   actually an all-segments-lit test pattern, not a per-digit
   calibration strip) but still composited everything into one loosely-
   arranged panel, not the two actual windows the source shows.
2. **Second pass** rebuilt the layout around the real structure: two
   window frames side by side, each with its own close button and "cd"
   logo, the dot-matrix spectrum living *inside* the main readout box
   (not a separate meter panel underneath), 5 transport buttons (not 6 --
   the extra "eject" icon only exists in Band B's reference capture,
   never in the real window), and 6 sliders (not 4).
3. **Third pass** fixed two more misses: the meter's "dots" are a
   genuine 2px NW-SE diagonal glint, not a single pixel (confirmed
   against both the spectrum area and Band C directly); and the main and
   equalizer windows are truly separate in the source -- dragging one
   reveals/reorders the other -- so the demo needed to become interactive
   rather than draw them as one fixed composite.
4. **Fourth pass** (playtesting the desktop shell) found three more real
   problems, not cosmetic ones: the transport button icons were
   positioned using the wrong offset (up to 4px too far down, clipping
   most of the glyph); the two windows, when opened from the desktop,
   were nested inside a *third*, generic wrapper window, reading as a
   window inside a window; and the equalizer was visible by default
   instead of hidden until revealed. All three fixed -- icon offsets
   re-measured directly, the two windows now open as genuine independent
   top-level desktop windows (`desktop.py`'s `_open_cd_player_main`/
   `_reveal_cd_player_eq`), and the equalizer starts closed. Transport
   buttons also gained a press animation (inverted highlight + 1px
   nudge) on click -- invented, no source data exists for a pressed
   state -- and their close buttons now actually close their window.
5. **Fifth pass** (2026-08-26 playtesting) found the transport icons
   still off-centre even after the fourth pass's fix -- that pass solved
   clipping but not centring; icon offsets are now each icon's own
   black-pixel bounding box matched against the source's, not eyeballed.
   The readout's two dot areas were also reconsidered: the big dot-matrix
   area (previously a generic level meter) now scrolls a marquee -- the
   current fake track's title, then "0123456789" as a lighter-weight nod
   to LED's own number-scroll phase -- and the small dot swatch beside
   "1AR" (previously a static copy of the source's own all-lit test
   pattern) now animates as a real per-column frequency bar meter.

Every piece is pixel-verified against Band A directly for the two real
windows (not Band B, which is reference material only -- confirmed by
finding Band A's own transport buttons use a different border style than
Band B's copies of the same icons):

- **Window frames**: a raised bevel (white top/left, grey bottom/right),
  no black ring -- routed through `framework/window_chrome.py`'s
  `bevel_rect`, the first non-Bruce's-Windows caller of that module.
- **Readout box**: sunken (reversed bevel), black fill.
- **Numeric LED readout**: pixel-verified segment geometry (11x21 per
  cell, the hexagonal tapered-end shape real LED segments have), single
  colour (measured red), 3 digits at a 12px pitch.
- **Dot-matrix spectrum + level meter**: pixel-verified 2px NW-SE
  diagonal dot shape at a 3px pitch, red/green, colours used directly
  from the source; now drives a scrolling track-title marquee rather
  than a generic level meter (2026-08-26, see Behaviour).
- **Status cluster** ("repeat/shuffle/1AR" text): no pixel font was
  built for this one-off text; it's copied verbatim as a lit/unlit pixel
  mask, the same approach as the icons. The small dense dot swatch next
  to it is no longer part of that static mask -- it's a live per-column
  frequency bar meter now (2026-08-26).
- **Transport buttons**: sunken sub-panel, each button a light 3-sided
  highlight (top/left/right) inside it -- a different style than the
  window frame's own bevel, and different again from Band B's flat-grey
  copies of the same icons.
- **Slider bank**: track + tick geometry pixel-verified from the
  equalizer window directly; no thumb/handle is visible in the source (a
  blank calibration state), so the demo's slider levels are invented
  content.
- **"cd" logo**: pixel-verified glyph, the literal same glyph reused by
  both windows.

## Behaviour

Simulated playback only, no real audio, one continuous loop (no
`Phase`/`PhaseSequence` -- see `cd_player.py`'s module docstring for why,
same reasoning Dooley's continuous design used):

- The time counter increments each second; after `TRACK_LENGTH` (180s) it
  wraps to the next track, wrapping the track number after `TRACK_COUNT`
  (12).
- Playback pauses for `PAUSE_DURATION` (3s) every `PAUSE_EVERY` (25s) of
  play, and the transport buttons pick out "play" or "pause" (its icon
  picked out in red) to match.
- The small dot-matrix EQ swatch (beside "1AR") fakes a per-column
  frequency reading (summed sine curves, invented, not a real audio
  analysis) that goes quiet while paused.
- The big dot-matrix area scrolls a marquee: the current fake track's
  title ("TRACK 01", no real metadata exists), then "0123456789" as a
  nod to LED's own number-scroll phase, looping between the two.

## Interaction

The main and equalizer windows are each draggable (click and hold
anywhere on a window's body that isn't a button or the close control)
and clicking either brings it in front of the other. This is the second
interactive demo in the project after Bruce's Windows.

- **The equalizer starts hidden.** Clicking the main window's body
  (not a transport button, not the close control) reveals it.
- **Close buttons work.** Each window's own "X" closes just that
  window.
- **Transport buttons animate on press**: the highlight inverts and the
  icon nudges 1px, both invented (no pressed-state reference exists in
  the source) -- they don't yet control playback (see Open questions).

On the desktop shell, CD Player's icon opens only the main window as a
genuine top-level desktop window -- not wrapped in the desktop's own
generic chrome, since that window already draws its own complete chrome
and a second wrapper around it read as a window inside a window
(2026-08-25 playtesting). The equalizer, once revealed, opens as its own
independent top-level window too. Standalone (`python -m retrodemos
cd_player`), `CDPlayerDemo` re-implements the same position/z-order/
reveal/close bookkeeping at a smaller scale so the two windows behave
identically without the desktop shell around them.

## Assets

Its window frames route through `framework/window_chrome.py`'s
`bevel_rect` (added 2026-08-25); its inner controls (readout, transport
buttons) are still custom-drawn, since those use different border
styles than that shared helper provides. No sprite sheet exists;
everything is pixel-verified coordinate/glyph data extracted from
`CDPLAYER.png`, same method as the LED-family renderers
(`docs/pixel-archaeology.md`).

## Notes

No real audio files are bundled or played, by design.

## Open questions

- Whether the fake waveform should look more musical (recognizable peaks
  tied to a "song" rather than pure summed sine curves) is unresolved --
  built simple for now.
- Transport buttons animate on press but don't change playback (stop
  doesn't stop, prev/next don't change track) -- whether they should is
  unresolved; the simulation currently drives itself.
- The equalizer's sliders have no thumb/handle reference in the source
  and aren't draggable yet -- only its close button is interactive.
