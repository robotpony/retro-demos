"""Seven-segment digit rendering, shared by the LED-family demos (LED, LED
II, Title, Dooley -- see PLAN.md's "LED grid module" section).

Segment geometry and colours were reverse-engineered pixel-by-pixel from
images/LED-thumb.png and worked out interactively with Bruce: the segment
shapes and bezel border are matched exactly against the source (verified by
reconstructing LED-thumb.png byte-for-byte from this geometry); the lit
colour was brightened past the source on request, and the unlit "ghost"
colour has no source ground truth at all (the source only ever shows a
fully-lit "8"), so it's invented at the same proportion below full
brightness the source's single red used relative to white.

This module currently implements only the seven-segment digit renderer --
what the LED demo needs. The dot-matrix grid needed by LED II, Title, and
Dooley isn't built yet; it lands with those demos, per PLAN.md's build order.
"""

from __future__ import annotations

import pygame

LIT = (255, 0, 0)
UNLIT = (64, 0, 0)
BG = (0, 0, 0)
BEZEL_DARK = (128, 128, 128)
BEZEL_LIGHT = (255, 255, 255)
BEZEL_CORNER = (192, 192, 192)

# One digit cell is 17px wide (its own horizontal pitch) and 25px tall.
# Segment pixel sets are local to a cell: x=0 is the leftmost column (f/e's
# outer edge), y=0 is the cell's top row.
CELL_W = 17
CELL_H = 25

# Bottom half is a deliberate vertical mirror of the top half: a's wide/clean
# row sits toward the border, its chamfered row (with f/b's tips) sits
# toward centre, next to g. d mirrors that in reversed order: chamfered row
# (with e/c's tips) toward centre, wide/clean row toward the border. Each
# vertical segment (f/b/e/c) gets exactly two tip rows, one per neighbouring
# horizontal segment -- never a third, which is what caused stray/duplicate
# lit pixels in an earlier pass.
SEGMENTS: dict[str, set[tuple[int, int]]] = {
    "a": {(x, 3) for x in range(2, 10)} | {(x, 4) for x in range(3, 9)},
    "f": {(0, 4)} | {(x, y) for y in range(5, 10) for x in (0, 1)} | {(0, 10)},
    "b": {(11, 4)} | {(x, y) for y in range(5, 10) for x in (10, 11)} | {(11, 10)},
    "g": {(x, y) for y in (11, 12) for x in range(2, 10)},
    "e": {(0, 13)} | {(x, y) for y in range(14, 20) for x in (0, 1)} | {(0, 20)},
    "c": {(11, 13)} | {(x, y) for y in range(14, 20) for x in (10, 11)} | {(11, 20)},
    "d": {(x, 20) for x in range(3, 9)} | {(x, 21) for x in range(2, 10)},
}
DOT_PIXELS = {(13, 20), (13, 21), (14, 20), (14, 21)}
ALL_SEGMENT_PIXELS: set[tuple[int, int]] = set().union(*SEGMENTS.values())

DIGIT_SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc",
    "5": "afgcd", "6": "afgecd", "7": "abc", "8": "abcdefg", "9": "abcdfg",
    " ": "", "-": "g",
}

# The 6 outer segments in ring order (clockwise around the hexagon,
# excluding the middle crossbar g) -- used for the power-up "calibration"
# sweep.
RING_ORDER = ("a", "b", "c", "d", "e", "f")

# Segments that share a physical corner within one digit cell, i.e. a snake
# or explosion could plausibly hop between them. f/g/e meet at one corner,
# b/g/c at the other, so each of those triples is fully connected rather
# than just adjacent pairs.
_INTRA_DIGIT_ADJACENCY = {
    ("a", "f"), ("a", "b"),
    ("f", "g"), ("f", "e"), ("g", "e"),
    ("b", "g"), ("b", "c"), ("g", "c"),
    ("e", "d"), ("c", "d"),
}

Node = tuple[int, str]  # (digit_index, segment_name)


def segment_adjacency(digit_count: int) -> dict[Node, set[Node]]:
    """Build the adjacency graph over every (digit_index, segment_name) node
    in a display of `digit_count` cells: segments sharing a corner within one
    cell, plus each cell's b/c (right side) to the next cell's f/e (left
    side), since those sit side by side. Used for the snake and explosion
    phases to find plausible paths/spread across the whole display."""
    graph: dict[Node, set[Node]] = {}

    def add_edge(u: Node, v: Node) -> None:
        graph.setdefault(u, set()).add(v)
        graph.setdefault(v, set()).add(u)

    for i in range(digit_count):
        for s1, s2 in _INTRA_DIGIT_ADJACENCY:
            add_edge((i, s1), (i, s2))
        if i + 1 < digit_count:
            add_edge((i, "b"), (i + 1, "f"))
            add_edge((i, "c"), (i + 1, "e"))
    return graph


class SevenSegmentDisplay:
    """A fixed-width row of seven-segment digit cells with a sunken bezel border."""

    def __init__(self, digit_count: int, *, margin: int = 5, border: int = 1) -> None:
        self.digit_count = digit_count
        self.margin = margin
        self.border = border
        # Sized off the digit body's right edge (segment c, local x=11), not
        # the trailing decimal dot (local x=13-14): the dot is a small,
        # low-profile mark on only the bottom two rows, and earlier sizing
        # off its overhang left the actual digit body sitting 6px from the
        # border on the right against 3px on the left.
        last_body_right_x = border + margin + (digit_count - 1) * CELL_W + 11
        self.width = last_body_right_x + margin + border + 1
        self.height = CELL_H + border * 2

    def render(self, surface: pygame.Surface, text: str) -> None:
        """Draw `text` onto surface, which must be exactly (self.width,
        self.height). Extra characters are dropped; short text is
        right-padded with spaces (blank digits). Characters outside
        DIGIT_SEGMENTS render as a blank digit."""
        text = text[: self.digit_count].ljust(self.digit_count)
        lit_segments = {i: set(DIGIT_SEGMENTS.get(ch, "")) for i, ch in enumerate(text)}
        self.render_raw(surface, lit_segments)

    def render_raw(
        self,
        surface: pygame.Surface,
        lit_segments: dict[int, set[str]] | None = None,
        lit_dots: set[int] | None = None,
    ) -> None:
        """Draw directly from a per-digit set of lit segment names (e.g.
        {2: {"a", "g"}} lights just those two segments on digit index 2),
        for choreography that isn't a fixed character -- the power-up,
        snake, and explosion phases all draw this way. Digits/dots not
        mentioned render fully unlit (dim ghost)."""
        lit_segments = lit_segments or {}
        lit_dots = lit_dots or set()
        surface.fill(BG)
        self._draw_bezel(surface)
        for i in range(self.digit_count):
            origin_x = self.border + self.margin + i * CELL_W
            self._draw_digit(surface, origin_x, lit_segments.get(i, set()), i in lit_dots)

    def _draw_bezel(self, surface: pygame.Surface) -> None:
        w, h = self.width, self.height
        for x in range(w):
            surface.set_at((x, 0), BEZEL_DARK)
            surface.set_at((x, h - 1), BEZEL_LIGHT)
        for y in range(h):
            surface.set_at((0, y), BEZEL_LIGHT)
            surface.set_at((w - 1, y), BEZEL_DARK)
        surface.set_at((0, 0), BEZEL_CORNER)
        surface.set_at((w - 1, h - 1), BEZEL_CORNER)

    def _draw_digit(
        self, surface: pygame.Surface, origin_x: int, lit_segment_names: set[str], dot_lit: bool
    ) -> None:
        lit_pixels: set[tuple[int, int]] = (
            set().union(*(SEGMENTS[s] for s in lit_segment_names)) if lit_segment_names else set()
        )
        for (x, y) in ALL_SEGMENT_PIXELS:
            color = LIT if (x, y) in lit_pixels else UNLIT
            surface.set_at((origin_x + x, self.border + y), color)
        dot_color = LIT if dot_lit else UNLIT
        for (dx, dy) in DOT_PIXELS:
            surface.set_at((origin_x + dx, self.border + dy), dot_color)
