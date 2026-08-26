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


class Deck:
    """Loads CARDS.png/BACKS.png once and slices out every tile."""

    def __init__(self) -> None:
        cards_sheet = pygame.image.load(str(_IMAGES_DIR / "CARDS.png"))
        backs_sheet = pygame.image.load(str(_IMAGES_DIR / "BACKS.png"))

        self._cards: dict[tuple[str, str], pygame.Surface] = {}
        for row, suit in enumerate(SUITS):
            for col, rank in enumerate(RANKS):
                self._cards[(suit, rank)] = cards_sheet.subsurface(
                    (col * CARD_W, row * CARD_H, CARD_W, CARD_H)
                )

        self._backs: list[pygame.Surface] = [
            backs_sheet.subsurface((i * BACK_W, 0, BACK_W, BACK_H)) for i in range(BACK_DESIGNS)
        ]
        self._backs_for_slot: list[pygame.Surface] = [
            pygame.transform.scale(back, (CARD_W, CARD_H)) for back in self._backs
        ]

    def card(self, suit: str, rank: str) -> pygame.Surface:
        return self._cards[(suit, rank)]

    def all_cards(self) -> list[pygame.Surface]:
        return list(self._cards.values())

    def back(self, design: int) -> pygame.Surface:
        return self._backs[design]

    def back_for_slot(self, design: int) -> pygame.Surface:
        return self._backs_for_slot[design]


# ---- Table layout -- new design, invented (no finished-screen source
# image for this demo). Sized to fit a hand of up to MAX_HAND fanned
# cards, dealer row above, player row below. ----
MAX_HAND = 5
FAN_STEP = 20  # px of each fanned card left visible before the next overlaps it
HAND_ROW_W = CARD_W + (MAX_HAND - 1) * FAN_STEP

SIDE_MARGIN = 16
WIDTH = HAND_ROW_W + SIDE_MARGIN * 2

TOP_MARGIN = 12
LABEL_GAP = 3  # between a hand's label and its card row
ROW_GAP = 20  # between the dealer row and the player label
BOTTOM_MARGIN = 12

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
