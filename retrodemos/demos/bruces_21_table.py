"""Bruce's 21's sprite loader and shared render target -- the `Deck` that
slices CARDS.png/BACKS.png into surfaces, and the `CardTable` display the
two phases in `bruces_21_phases.py` drive (the role `SevenSegmentDisplay`/
`TitleDisplays` play for their own demos). Split out from `bruces_21.py`
itself so that module and `bruces_21_phases.py` can both import from here
without an import cycle between the demo module and its own phases --
the same shape `led_grid.py` has relative to `led.py`/`led_phases.py`.

See `bruces_21.py`'s module docstring for the full account of the source
images' geometry and the runtime-image-loading decision.
"""

from __future__ import annotations

from pathlib import Path

import pygame

from retrodemos.framework.pixel_font import GLYPH_H, text_cells

_IMAGES_DIR = Path(__file__).resolve().parents[2] / "images"

# ---- CARDS.png geometry (measured, byte-exact -- see bruces_21.py) ----
CARD_W, CARD_H = 48, 66
SUITS = ("hearts", "diamonds", "clubs", "spades")  # row order in CARDS.png
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")  # column order

# ---- BACKS.png geometry (measured -- see bruces_21.py) ----
BACK_W, BACK_H = 64, 82
BACK_DESIGNS = 2  # only the top row's two designs are used

# Every card and both backs have the same rounded-corner cut: a 3px "L"
# notch per corner, measured identically across a dozen sampled cards
# (see bruces_21.py's module docstring) -- position-based, not
# colour-based, since CARDS.png and BACKS.png fill that notch with two
# different flat greys ((192,192,192) vs (198,198,198)), neither of
# which is meant to be part of the card art. Playtesting (2026-08-26):
# blitting the tiles as opaque rectangles left those grey corners
# showing over the felt instead of rounding into it.
_TRANSPARENT = (0, 0, 0, 0)


def _punch_rounded_corners(tile: pygame.Surface) -> None:
    w, h = tile.get_size()
    for x, y in ((0, 0), (1, 0), (0, 1)):
        tile.set_at((x, y), _TRANSPARENT)
    for x, y in ((w - 1, 0), (w - 2, 0), (w - 1, 1)):
        tile.set_at((x, y), _TRANSPARENT)
    for x, y in ((0, h - 1), (1, h - 1), (0, h - 2)):
        tile.set_at((x, y), _TRANSPARENT)
    for x, y in ((w - 1, h - 1), (w - 2, h - 1), (w - 1, h - 2)):
        tile.set_at((x, y), _TRANSPARENT)


def _alpha_copy(source: pygame.Surface) -> pygame.Surface:
    """A copy with a real per-pixel alpha channel -- subsurfaces of an
    image loaded without convert_alpha() share the source file's own
    format, which has no alpha to punch a transparent notch into."""
    tile = pygame.Surface(source.get_size(), pygame.SRCALPHA)
    tile.blit(source, (0, 0))
    return tile


class Deck:
    """Loads CARDS.png/BACKS.png once and slices out every tile."""

    def __init__(self) -> None:
        cards_sheet = pygame.image.load(str(_IMAGES_DIR / "CARDS.png"))
        backs_sheet = pygame.image.load(str(_IMAGES_DIR / "BACKS.png"))

        self._cards: dict[tuple[str, str], pygame.Surface] = {}
        for row, suit in enumerate(SUITS):
            for col, rank in enumerate(RANKS):
                tile = _alpha_copy(cards_sheet.subsurface((col * CARD_W, row * CARD_H, CARD_W, CARD_H)))
                _punch_rounded_corners(tile)
                self._cards[(suit, rank)] = tile

        self._backs: list[pygame.Surface] = []
        for i in range(BACK_DESIGNS):
            tile = _alpha_copy(backs_sheet.subsurface((i * BACK_W, 0, BACK_W, BACK_H)))
            _punch_rounded_corners(tile)
            self._backs.append(tile)

        # Scaled to card size for a hand slot; corners punched fresh at
        # that size rather than scaling the 64x82 tile's own notch down,
        # so the cut stays the same crisp 3px "L" every card has, not
        # whatever a nearest-neighbour resize of it happens to produce.
        self._backs_for_slot: list[pygame.Surface] = []
        for back in self._backs:
            slot_tile = pygame.transform.scale(back, (CARD_W, CARD_H))
            _punch_rounded_corners(slot_tile)
            self._backs_for_slot.append(slot_tile)

    def card(self, suit: str, rank: str) -> pygame.Surface:
        return self._cards[(suit, rank)]

    def all_cards(self) -> list[pygame.Surface]:
        return list(self._cards.values())

    def back(self, design: int) -> pygame.Surface:
        return self._backs[design]

    def back_for_slot(self, design: int) -> pygame.Surface:
        return self._backs_for_slot[design]


# ---- Table layout -- new design, invented (no finished-screen source
# image for this demo). Sized to fit a hand of up to MAX_HAND cards,
# dealer row above, player row below. Playtesting (2026-08-26): this
# deck's own art isn't corner-indexed like a real card (a small rank+suit
# mark tucked in the corner) -- CARDS.png draws one giant rank glyph
# filling most of the card, with the suit pip in the corners -- so any
# real overlap hides the rank behind the next card. FAN_STEP is now
# CARD_W itself (no overlap at all) instead of a partial-overlap fan,
# and the whole table grew to match ("the field needs to be larger,
# show as a standard 21 table").
MAX_HAND = 5
FAN_STEP = CARD_W  # cards sit edge to edge, not fanned/overlapping
HAND_ROW_W = CARD_W + (MAX_HAND - 1) * FAN_STEP

SIDE_MARGIN = 24
WIDTH = HAND_ROW_W + SIDE_MARGIN * 2

TOP_MARGIN = 24
LABEL_GAP = 3  # between a hand's label and its card row
ROW_GAP = 40  # between the dealer row and the player label
BOTTOM_MARGIN = 24

DEALER_LABEL_Y = TOP_MARGIN
DEALER_ROW_Y = DEALER_LABEL_Y + GLYPH_H + LABEL_GAP
PLAYER_LABEL_Y = DEALER_ROW_Y + CARD_H + ROW_GAP
PLAYER_ROW_Y = PLAYER_LABEL_Y + GLYPH_H + LABEL_GAP
HEIGHT = PLAYER_ROW_Y + CARD_H + BOTTOM_MARGIN

FELT = (0, 92, 58)  # invented felt green
LABEL_COLOR = (255, 255, 255)


def _draw_label(surface: pygame.Surface, text: str, y: int) -> None:
    cells, width = text_cells(text)
    x0 = (WIDTH - width) // 2
    for x, y_off in cells:
        surface.set_at((x0 + x, y + y_off), LABEL_COLOR)


def _draw_hand(surface: pygame.Surface, hand: list[pygame.Surface], y: int) -> None:
    if not hand:
        return
    row_w = CARD_W + (len(hand) - 1) * FAN_STEP
    x0 = (WIDTH - row_w) // 2
    for i, card in enumerate(hand):
        surface.blit(card, (x0 + i * FAN_STEP, y))


class CardTable:
    """The shared render target `DeckCyclePhase`/`AutoDealPhase` drive.
    `mode` picks which of the two phases' content is on screen; each
    phase owns the fields it writes to."""

    def __init__(self, deck: Deck) -> None:
        self.deck = deck
        self.mode = "cycle"  # "cycle" (DeckCyclePhase) | "deal" (AutoDealPhase)
        self.center: pygame.Surface | None = None
        self.dealer_hand: list[pygame.Surface] = []
        self.player_hand: list[pygame.Surface] = []

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(FELT)
        if self.mode == "cycle":
            if self.center is not None:
                cx = (WIDTH - self.center.get_width()) // 2
                cy = (HEIGHT - self.center.get_height()) // 2
                surface.blit(self.center, (cx, cy))
            return
        _draw_label(surface, "DEALER", DEALER_LABEL_Y)
        _draw_hand(surface, self.dealer_hand, DEALER_ROW_Y)
        _draw_label(surface, "PLAYER", PLAYER_LABEL_Y)
        _draw_hand(surface, self.player_hand, PLAYER_ROW_Y)


NATIVE_SIZE = (WIDTH, HEIGHT)
