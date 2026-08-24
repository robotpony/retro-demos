# Pixel archaeology

How to reverse-engineer a source screenshot (`images/*.png`) into exact,
verifiable rendering code. Worked out building the LED demo's seven-segment
font; the same method applies to LED II, Title, and Dooley, since they're
each their own pixel font/grid extracted from a source image the same way.

## Environment setup (pygame-ce, headless)

Every inspection/prototype script needs this preamble:

```python
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
pygame.init()
pygame.display.set_mode((1, 1))  # <-- required even headless
```

The `set_mode` call matters: `pygame.image.load(...).convert_alpha()` (and
other format-conversion calls) raise `pygame.error: No convert format has
been set` without a display surface existing first, even under the dummy
driver. Skip `convert_alpha()` if you don't need alpha, but for pixel-colour
inspection it's simplest to always include the `set_mode` call.

Run scripts through the project venv (`.venv/bin/python`), not system
Python — pygame-ce is only installed there.

## The reconstruct-and-diff technique

Don't hand-derive pixel geometry from a glance or a manually-counted ASCII
dump — it's slow and error-prone. Building the LED font this way produced
several wrong tile boundaries, a wrong column offset, and a wrong segment
attribution before switching to this method instead:

1. **Find a "clean" ground-truth tile.** Real screenshots often repeat a
   unit (a digit cell, a dot-matrix column) many times. Extract each repeat
   as a pixel array and compare them for exact equality. The repeats that
   match each other exactly are the ground truth; edges sometimes have a
   one-off quirk (LED-thumb.png's first digit sits 1px tighter than the
   rest) — don't "fix" those, just don't use them as the reference tile.
2. **Write the rendering code from that one verified tile**, as explicit
   pixel-coordinate sets, not visual guesses.
3. **Reconstruct the full original image from the rendering code** and diff
   it pixel-by-pixel against the source. Zero differences is the bar, not
   "looks about right."
4. Only once the reconstruction is byte-exact, decompose it further (e.g.
   into named segments) by attributing pixels to logical groups, and
   **re-verify** the union of those groups still equals the ground-truth
   tile exactly — an `assert` in the script, not a visual check.

This caught a real bug fast: a segment-decomposition mistake gave one
vertical segment three tip-rows instead of two. It was invisible in the
source (LED-thumb.png only ever shows a fully-lit "8") and only showed up
as duplicate "stray dot" pixels once other digits were rendered.

## Verify pixel claims programmatically, not by eye

Small pixel-art images (every native resolution in this project is under
~200x30px) are genuinely hard to read reliably once resized, compressed, or
glanced at. This bit twice: an aggregate min/max bounding-box scan reported
symmetric padding when a per-row scan showed it wasn't (a small decimal dot
was skewing the aggregate), and a multi-frame choreography review was
misread by eye — rows that were actually correct looked wrong, and vice
versa — until the underlying state was printed and checked directly.

**Rule of thumb:** a claim about exact pixel position, colour, or symmetry
needs code to check it (`get_at`, aggregate scans done *per-row/column*,
`assert`), not narration from a screenshot. Screenshots are for the human's
aesthetic sign-off and macro "does the shape/motion read correctly" checks,
not for verifying exact pixel facts.

## Reviewing animated/choreographed content

A single static PNG (used for the font/shape design itself) isn't enough
once a demo has behaviour over time. For a scripted sequence (see
`retrodemos/demos/led_phases.py`), build a labeled contact sheet: capture
several frames per phase at key moments (start, mid-transition, end), stack
them into one tall image with a text label per row, scale up (e.g. 4x
nearest-neighbour) for legibility, and review that as one artifact instead
of running the real demo blind. `pygame.font.SysFont` works fine for labels
even headless.

## pygame-ce notes

- This project uses **pygame-ce** (the community fork), not classic
  `pygame` — a drop-in match for everything used so far.
- `pygame.image.tostring` is deprecated; use `pygame.image.tobytes`.
- `pygame.transform.scale(surface, size)` is nearest-neighbour by default,
  which is exactly what's wanted for crisp pixel-art upscaling (also what
  `framework/canvas.py` uses for the real display scaling).
- The headless test suite already handles all of the above (see
  `tests/conftest.py`); one-off inspection/prototype scripts need to set it
  up themselves, as shown above.
