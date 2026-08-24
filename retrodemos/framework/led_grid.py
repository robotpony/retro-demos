"""Cell-grid rendering shared by the LED-family demos (LED, LED II, Title,
Dooley -- see PLAN.md's "LED grid module" section): the seven-segment digit
renderer (`SevenSegmentDisplay`, LED's), the dot-matrix renderer
(`DotMatrixDisplay`, LED II's), and the bit-column renderer
(`BitColumnDisplay`, Title's).

Every renderer's geometry and colours were reverse-engineered pixel-by-pixel
from its source screenshot (`images/LED-thumb.png`, `images/LED-II-thumb.png`,
`images/TITLE.png` -- see `docs/pixel-archaeology.md` for method): shapes and
bezel borders are matched exactly against the source (verified by
reconstructing each source image byte-for-byte, or pixel-exact-diffed against
it, from this geometry). LED-thumb.png and LED-II-thumb.png show their
display fully lit (a lit "8", every dot lit) with no unlit/ghost colour or
letterform ground truth, so those are invented, not measured -- see each
renderer's own docstring for what was invented and why. TITLE.png is
different: its two 0-255 reference ramps ARE the actual content-generation
rule (see BitColumnDisplay), not just a lit/unlit calibration image, and
there's no invented colour -- every colour BitColumnDisplay uses is measured.

Title turned out not to be a DotMatrixDisplay extension after all, despite
that being the plan (see PLAN.md's now-corrected note): its bit-pattern area
has no bezel, no gap between columns (unlike DotMatrixDisplay's dots, gapped
on both axes), and content that's directly computable from a byte value
rather than drawn from a font -- different enough pixel-for-pixel that
extending DotMatrixDisplay would have meant bending its dot-grid model
around a shape it doesn't describe. Dooley's colour side-column is still an
open question for whether it fits DotMatrixDisplay or needs its own renderer
too; decide that when building it, from its own source image, not by
assumption from Title's outcome.
"""

from __future__ import annotations

import pygame

LIT = (255, 0, 0)
UNLIT = (64, 0, 0)
BG = (0, 0, 0)
BEZEL_DARK = (128, 128, 128)
BEZEL_LIGHT = (255, 255, 255)
BEZEL_CORNER = (192, 192, 192)

# LED II's dot colour, unlike LED's LIT above, is left at the value actually
# measured in LED-II-thumb.png (191, 0, 0) rather than brightened -- LED's
# brightening was a specific request from Bruce for that demo, not an
# established house style, so the default here is the faithful one unless
# told otherwise. DOT_UNLIT has no source ground truth (see module
# docstring) and reuses the same 64/255 dimness-below-full-brightness ratio
# LED's own invented UNLIT used, applied to DOT_LIT instead of LIT.
DOT_LIT = (191, 0, 0)
DOT_UNLIT = (48, 0, 0)


def lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    """Blend from colour `a` (t=0) to `b` (t=1), clamped to that range.
    Shared brightness primitive for any grid cell that needs to vary
    intensity rather than just switch on/off -- DotMatrixDisplay.render_raw
    is the first user (LED II's RipplePhase fireworks)."""
    t = max(0.0, min(1.0, t))
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
    )


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


def scroll_window(loop_text: str, offset: int, width: int) -> str:
    """Return the `width`-character slice of `loop_text` visible at
    `offset`, wrapping around the end back to the start.

    `loop_text` should already carry any trailing padding needed to put a
    visible gap between repeats (e.g. `text + " " * width`) -- this
    function only handles the windowing, not the gap. Shared by any
    scrolling-content phase across the LED-family demos; LED's own
    `NumbersPhase` (`led_phases.py`) was the first user, before this was
    pulled out here as a second one (LED II) needed the identical logic.
    """
    if not loop_text:
        return " " * width
    offset %= len(loop_text)
    return (loop_text[offset:] + loop_text)[:width]


# Each glyph is 5 columns x 7 rows, local coordinates (x=0..4, y=0..6).
# Digits, space, and "-" only -- matching the seven-segment font's current
# limitation above (see SevenSegmentDisplay's DIGIT_SEGMENTS): a full
# alphabet isn't built, since nothing has needed one yet. There's no
# source ground truth for these shapes (LED-II-thumb.png shows only a
# fully-lit calibration block, see module docstring), so they're an
# original 5x7 dot-matrix font design in the well-worn LED-sign style, not
# a reverse-engineered one -- reviewed visually, not diffed against a
# source.
_DOT_GLYPH_ROWS: dict[str, tuple[str, ...]] = {
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}
GLYPH_W = 5
GLYPH_H = 7
GLYPH_GAP = 1  # blank column between characters

DOT_FONT: dict[str, set[tuple[int, int]]] = {
    ch: {(x, y) for y, row in enumerate(rows) for x, pixel in enumerate(row) if pixel == "#"}
    for ch, rows in _DOT_GLYPH_ROWS.items()
}

DotNode = tuple[int, int]  # (col, row)


def dot_grid_adjacency(cols: int, rows: int) -> dict[DotNode, set[DotNode]]:
    """Build the 4-neighbour adjacency graph over every (col, row) cell in a
    `cols` x `rows` grid -- the dot-grid analogue of segment_adjacency
    above. Used with framework/graph_walk.py the same way segment_adjacency
    is: a Snake or Burst walks this graph to find plausible paths/spread
    across a display.

    Purely topological -- nothing here assumes DotMatrixDisplay's dot
    pitch/size, so it's reused as-is for BitColumnDisplay's bit grid too
    (Title's phases, `dot_grid_adjacency(width, BitColumnDisplay.ROWS)`),
    not just LED II's dot grid; a (col, row) cell is a (col, row) cell
    regardless of what it renders as."""
    graph: dict[DotNode, set[DotNode]] = {}
    for row in range(rows):
        for col in range(cols):
            neighbours: set[DotNode] = set()
            if col > 0:
                neighbours.add((col - 1, row))
            if col < cols - 1:
                neighbours.add((col + 1, row))
            if row > 0:
                neighbours.add((col, row - 1))
            if row < rows - 1:
                neighbours.add((col, row + 1))
            graph[(col, row)] = neighbours
    return graph


class DotMatrixDisplay:
    """A fixed-width row of round dot cells with a sunken bezel border,
    LED II's marquee display.

    Geometry (each dot a 2x2px square on a 3px pitch, i.e. a 1px gap
    between dots) and colours were reverse-engineered from
    images/LED-II-thumb.png. The bezel is its own shape, not shared with
    SevenSegmentDisplay's: a 1px corner-grey outer frame plus a 1px
    light/dark inner bevel edge on the left/right sides only (full height),
    versus a 1px dark/light bevel top/bottom -- an asymmetric border,
    verified by reconstructing LED-II-thumb.png byte-for-byte from this
    geometry, not "fixed" to be symmetric (see docs/pixel-archaeology.md's
    note on not smoothing over a source's genuine quirks).
    """

    ROWS = 9
    DOT_SIZE = 2
    PITCH = 3  # DOT_SIZE + 1px gap

    def __init__(self, cols: int, *, margin: int = 2, h_border: int = 2, v_border: int = 1) -> None:
        self.cols = cols
        self.margin = margin
        self.h_border = h_border
        self.v_border = v_border
        self.char_count = (cols + GLYPH_GAP) // (GLYPH_W + GLYPH_GAP)
        # -1: the last dot in a row/column doesn't need a trailing gap pixel.
        self.width = h_border * 2 + margin * 2 + cols * self.PITCH - 1
        self.height = v_border * 2 + margin * 2 + self.ROWS * self.PITCH - 1

    def render(self, surface: pygame.Surface, text: str) -> None:
        """Draw `text` onto surface, which must be exactly (self.width,
        self.height). Extra characters are dropped; short text is
        right-padded with spaces. Characters outside DOT_FONT render as a
        blank cell (see DOT_FONT's limitation)."""
        text = text[: self.char_count].ljust(self.char_count)
        lit_cells, _ = self.text_dots(text)
        self.render_raw(surface, lit_cells)

    def text_dots(self, text: str) -> tuple[set[tuple[int, int]], int]:
        """Lay out `text` at its natural width -- unclipped and unpadded,
        unlike render()/render_raw(), which are always exactly self.cols
        wide. Returns the lit dot-cells (row-centred within self.ROWS the
        same way render() is) plus the text's total dot-column width.

        This is the building block for a smoothly-scrolling marquee (see
        led_ii_phases.py's MarqueePhase), which needs per-dot motion rather
        than render()'s per-character one; render() itself is written in
        terms of this method rather than duplicating the glyph layout."""
        row_offset = (self.ROWS - GLYPH_H) // 2
        dots: set[tuple[int, int]] = set()
        for i, ch in enumerate(text):
            glyph = DOT_FONT.get(ch, DOT_FONT[" "])
            col_offset = i * (GLYPH_W + GLYPH_GAP)
            for gx, gy in glyph:
                dots.add((col_offset + gx, row_offset + gy))
        # -1: the last character doesn't need a trailing gap column.
        width = max(len(text) * (GLYPH_W + GLYPH_GAP) - GLYPH_GAP, 1)
        return dots, width

    def render_raw(
        self,
        surface: pygame.Surface,
        lit_cells: set[tuple[int, int]] | dict[tuple[int, int], float] | None = None,
    ) -> None:
        """Draw directly from (col, row) dot-grid coordinates, for
        choreography that isn't a fixed character -- e.g. a power-up sweep
        or a graph-walk effect over the dot grid.

        `lit_cells` is either a set (every named cell fully lit, DOT_LIT --
        most callers) or a dict mapping cell to a 0..1 intensity, blended
        between DOT_UNLIT and DOT_LIT via lerp_color, for effects that vary
        brightness rather than just switching cells on/off (e.g. LED II's
        RipplePhase fireworks). A cell absent from either form renders
        fully unlit."""
        if lit_cells is None:
            intensity: dict[tuple[int, int], float] = {}
        elif isinstance(lit_cells, dict):
            intensity = lit_cells
        else:
            intensity = {cell: 1.0 for cell in lit_cells}
        surface.fill(BG)
        self._draw_bezel(surface)
        origin_x = self.h_border + self.margin
        origin_y = self.v_border + self.margin
        for row in range(self.ROWS):
            for col in range(self.cols):
                color = lerp_color(DOT_UNLIT, DOT_LIT, intensity.get((col, row), 0.0))
                x0 = origin_x + col * self.PITCH
                y0 = origin_y + row * self.PITCH
                for dx in range(self.DOT_SIZE):
                    for dy in range(self.DOT_SIZE):
                        surface.set_at((x0 + dx, y0 + dy), color)

    def _draw_bezel(self, surface: pygame.Surface) -> None:
        w, h = self.width, self.height
        # Outer corner-grey frame (col 0 and col w-1) plus the inner
        # light/dark bevel edge (col 1 and col w-2), all full height.
        for y in range(h):
            surface.set_at((0, y), BEZEL_CORNER)
            surface.set_at((w - 1, y), BEZEL_CORNER)
            surface.set_at((1, y), BEZEL_LIGHT)
            surface.set_at((w - 2, y), BEZEL_DARK)
        # Top/bottom bevel edges, for the columns the loop above doesn't
        # already own.
        for x in range(2, w - 2):
            surface.set_at((x, 0), BEZEL_DARK)
            surface.set_at((x, h - 1), BEZEL_LIGHT)
        # The two diagonal chamfer pixels where the inner bevel column
        # meets the opposite top/bottom edge -- present at the top-left and
        # bottom-right only, an asymmetry the source itself has.
        surface.set_at((1, 0), BEZEL_CORNER)
        surface.set_at((w - 2, h - 1), BEZEL_CORNER)


# Title's two reference colour pairs, measured directly from TITLE.png's
# two 0-255 ramps (not invented -- see module docstring). RED matches
# DOT_LIT above exactly (both are the same LED-family red at (191, 0, 0));
# GREEN/BLUE/CYAN are new. Bit off -> the first colour, bit on -> the second.
BIT_COLUMN_COLORS: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
    "red-green": ((191, 0, 0), (0, 255, 0)),
    "blue-cyan": ((0, 0, 191), (0, 255, 255)),
}


class BitColumnDisplay:
    """Title's LED bit-pattern display: each column is one byte value
    (0-255), rendered as its own 8 bits top-to-bottom (bit 7/MSB at the
    top, bit 0/LSB at the bottom), one pixel-row per bit with a 1px gap
    between rows, colour-coded per bit (off -> one colour, on -> another).

    Reverse-engineered from images/TITLE.png's two reference strips, which
    turned out to be more than a calibration image (see
    docs/pixel-archaeology.md): both strips show every column x's own
    value x as its rendered bits, i.e. the *rule* ("column x's bits are
    x's own bits") is directly legible from the source, not just its
    colours -- verified by checking exactly this rule against all 256
    columns x 8 rows x 2 colour pairs with zero mismatches, rather than
    reconstructing a fixed image and diffing it (there's no single fixed
    image to target; the source itself already varies by column).

    Unlike SevenSegmentDisplay/DotMatrixDisplay, there's no bezel and no
    gap between columns (TITLE.png's bit-pattern area runs edge to edge) --
    a genuinely different pixel model from the other two renderers, not a
    parameterization of either.

    render_values() is the byte-value-driven API render_raw() feeds into --
    what the source image itself encodes, and what Title's scrolling
    content phase draws with. render_raw() addresses individual (col, bit)
    cells directly, same role DotMatrixDisplay.render_raw plays for LED
    II: choreography that isn't a value-per-column mapping, e.g. a snake or
    a firework burst crawling individual bits (see title_phases.py). A
    (col, bit) cell here is exactly the kind of thing `dot_grid_adjacency`
    already builds a 4-neighbour graph over -- reused as-is for Title's bit
    grid rather than duplicated, since neither function cares whether the
    grid it's walking represents dots or bits.
    """

    ROWS = 8
    ROW_PITCH = 2  # 1px lit row + 1px gap

    def __init__(self, width: int, *, colors: tuple[tuple[int, int, int], tuple[int, int, int]]) -> None:
        self.width = width
        self.height = self.ROWS * self.ROW_PITCH - 1  # no trailing gap row
        self.off_color, self.on_color = colors

    def render_values(self, surface: pygame.Surface, values: list[int]) -> None:
        """Draw one byte value per column. `values` must have exactly
        `self.width` entries, each 0-255 (out-of-range bits beyond bit 7
        are simply never read, so a larger int just shows its low byte)."""
        lit_cells = {
            (x, row)
            for x, value in enumerate(values)
            for row in range(self.ROWS)
            if (value >> (self.ROWS - 1 - row)) & 1
        }
        self.render_raw(surface, lit_cells)

    def render_raw(
        self,
        surface: pygame.Surface,
        lit_cells: set[tuple[int, int]] | dict[tuple[int, int], float] | None = None,
    ) -> None:
        """Draw directly from (col, row) bit-grid coordinates, row 0 = bit
        7 (MSB) through row 7 = bit 0 (LSB) -- the same indexing
        render_values() derives from a byte value, just addressed directly
        instead of computed from one.

        `lit_cells` is either a set (every named cell fully on) or a dict
        mapping cell to a 0..1 intensity, blended between off_color and
        on_color via lerp_color -- mirrors DotMatrixDisplay.render_raw's
        two accepted shapes exactly."""
        if lit_cells is None:
            intensity: dict[tuple[int, int], float] = {}
        elif isinstance(lit_cells, dict):
            intensity = lit_cells
        else:
            intensity = {cell: 1.0 for cell in lit_cells}
        surface.fill(BG)
        for row in range(self.ROWS):
            y = row * self.ROW_PITCH
            for x in range(self.width):
                color = lerp_color(self.off_color, self.on_color, intensity.get((x, row), 0.0))
                surface.set_at((x, y), color)
