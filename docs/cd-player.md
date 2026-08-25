# CD Player

**Source:** `CDPLAYER.png`
**Mode:** Automated attract-mode
**Build:** Done (`retrodemos/demos/cd_player.py`)

## What it shows

`CDPLAYER.png` (384x78) turned out not to be one coherent screenshot, the
same surprise Title's and Dooley's source images held: it bundles three
stacked reference bands. Band A (y0-28) and Band B (y30-53) are two
differently-sized captures of the same widget vocabulary (transport
buttons, a "cd" logo, a slider bank); Band C (y56-77) is a separate
full-width level-meter strip. Built around Band B (confirmed with Bruce,
2026-08-24) since it's the larger, more detailed capture, and its long
18-cell readout doubles as a segment-shape calibration strip.

A 2026-08-25 re-verification (connected-component style, same method that
caught Bruce's Windows' bevel bugs) found the first pass had two real
mistakes, both now fixed:

- The 18-cell readout isn't a calibration strip spelling "0123456789" --
  every cell has all seven segments lit (a segment-test pattern,
  alternating red/green per position for visibility, matching Band A's
  own all-lit "888"). There's no source data for individual digit shapes,
  so the "6 has no top bar, 9 has no bottom bar" quirks the first pass
  claimed were fabricated, not measured. The font now uses the standard
  closed 6/9 forms instead, with the segment geometry itself (each
  segment's exact tapered pixel shape) still pixel-measured from that
  all-lit pattern.
- Every box border in the source -- readout, meter, transport buttons --
  is a flat single-tone grey outline, not a two-tone raised/sunken bevel.
  The first pass invented a bevel that isn't there.

- **Numeric LED readout**: pixel-verified segment geometry (11x21 per
  cell, with the hexagonal tapered-end shape real LED segments have),
  single colour (Band A's own measured red), showing track number + time.
- **Transport buttons**: all 6 icons (prev, next, stop, pause, play, close)
  pixel-verified glyphs extracted from Band B.
- **Level meter**: 1px dots on a 3px pitch, red/green, colours used
  directly from the source (no invented dimness needed -- Band C already
  shows both).
- **Slider bank**: track + tick geometry pixel-verified from Band B; no
  thumb/handle is visible in the source (a blank calibration state), so
  the demo's slider levels and thumb positions are invented content.
- **"cd" logo**: pixel-verified glyph from Band B.
- Overall panel layout (where each piece sits relative to the others)
  isn't a measurement -- Band B's own pieces aren't laid out as one
  coherent window, so composing them into a single CD Player face was
  this build's own design call.

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
- The level meter fakes a waveform (summed sine curves, invented, not a
  real audio analysis) that goes quiet while paused.

## Interaction

None beyond the shared quit/pause controls.

## Assets

No shared framework renderer -- `cd_player.py` draws its own chrome
directly (digit font, icons, meter, sliders, logo), matching
`PLAN.md`'s "Window chrome" reasoning for why CD Player, Bruce's Windows,
and Tank Status Window each draw their own borders independently rather
than sharing one. No sprite sheet exists; everything is pixel-verified
coordinate/glyph data extracted from `CDPLAYER.png`, same method as the
LED-family renderers (`docs/pixel-archaeology.md`).

## Notes

No real audio files are bundled or played, by design.

## Open questions

- Whether the fake waveform should look more musical (recognizable peaks
  tied to a "song" rather than pure summed sine curves) is unresolved --
  built simple for now.
