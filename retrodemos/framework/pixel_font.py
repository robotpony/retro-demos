"""A hand-designed 5x7 pixel alphabet (A-Z, 0-9, apostrophe, space), for
window titles on the desktop shell's generic window chrome
(`framework/window_chrome.py`).

Unlike every other font in this project (LED's seven-segment digits,
`led_grid.DOT_FONT`'s 5x7 digits, Dooley's since-removed 3x5 digits, CD
Player's segment font), this one has no source image to extract from --
`WINDOW1.png` only ever shows the fixed strings "Window Title" and
"Dialog", not a full alphabet, and window titles on the desktop need
arbitrary demo names ("LED II", "CD Player", ...). Built new, in the same
`"#"`/`"."` row-string convention every other font table in this project
uses, so it stays visually and structurally consistent even though it
isn't measured.

Display convention: window titles render upper-case only (this font has
no lower-case glyphs) -- a deliberate simplification, not an oversight;
see `framework/window_chrome.py`.
"""

from __future__ import annotations

_GLYPH_ROWS: dict[str, tuple[str, ...]] = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".####"),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
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
    "'": (".#...", ".#...", ".....", ".....", ".....", ".....", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}

GLYPH_W = 5
GLYPH_H = 7
GLYPH_GAP = 1  # blank column between characters

#: char -> set of lit (x, y) cells within its own GLYPH_W x GLYPH_H box.
WINDOW_FONT: dict[str, set[tuple[int, int]]] = {
    ch: {(x, y) for y, row in enumerate(rows) for x, pixel in enumerate(row) if pixel == "#"}
    for ch, rows in _GLYPH_ROWS.items()
}


def text_cells(text: str) -> tuple[set[tuple[int, int]], int]:
    """Lay out `text` (upper-cased; characters missing from WINDOW_FONT
    render as a blank cell) at its natural width. Returns the lit
    (x, y) cells and the text's total pixel width -- same shape as
    `led_grid.DotMatrixDisplay.text_dots`, so a caller composites this the
    same way."""
    cells: set[tuple[int, int]] = set()
    for i, ch in enumerate(text.upper()):
        glyph = WINDOW_FONT.get(ch, WINDOW_FONT[" "])
        col_offset = i * (GLYPH_W + GLYPH_GAP)
        for gx, gy in glyph:
            cells.add((col_offset + gx, gy))
    width = max(len(text) * (GLYPH_W + GLYPH_GAP) - GLYPH_GAP, 1)
    return cells, width
