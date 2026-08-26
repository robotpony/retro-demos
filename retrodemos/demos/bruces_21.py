"""Bruce's 21: an automated card-table attract loop -- a shuffled cycle
through the full face deck and both card backs, then a scripted mock deal
"as if" playing a round of 21, no real scoring. See `docs/bruces-21.md`
for the demo overview, `bruces_21_table.py` for the sprite loader and
table layout, and `bruces_21_phases.py` for the two phases' choreography.

`CARDS.png` (672x264) is a clean 14x4 grid of 48x66 tiles (confirmed
byte-exact by reconstruct-and-diff -- no gaps, no border padding between
cells). Rows are the four suits (hearts, diamonds, clubs, spades); the
first 13 columns are A-K. The 14th column is not a playing card at all --
it holds four pieces of splash/credit art (a "21"/MADMAX title card, a
portrait, a "bruce's blackJack V.01" logo card, and one blank) left over
from the original program's own title screen. Out of scope for this demo
(the spec only calls for the face deck and the two backs); revisit if a
title-card flourish is ever wanted, the same way Cinqtris's wordmark
came from its own sprite sheet.

`BACKS.png` (128x164) is a 2x2 grid of 64x82 tiles: two distinct designs
(a blue/orange quartered-circle pattern, and a "Bruce's 21" wordmark
card) each duplicated top and bottom -- the two rows aren't byte-identical
(minor dithering differences) but read as the same design; only the top
row is used here.

Unlike every other demo so far, this one loads its source PNGs at
runtime (`pygame.image.load` + `subsurface`) rather than hand-encoding
pixel data -- confirmed with Bruce (2026-08-25): 52 detailed card faces
plus 2 backs is too much art to transcribe by hand without risking subtle
errors, and blitting the real sprite pixels is byte-exact by construction
rather than by verification. `convert_alpha()`/`convert()` are avoided
since `Deck` is built in `Demo.__init__`, before `runtime.run()` has
called `pygame.display.set_mode()` -- both conversions raise without a
display surface already existing (see `docs/pixel-archaeology.md`'s
environment-setup note); plain unconverted surfaces blit fine here, and
at this sprite count/frequency the lack of format conversion costs
nothing visible.

Card-back art (64x82) doesn't share cards' 48x66 footprint, so a hand
slot showing a face-down card uses `Deck.back_for_slot`, a version
scaled down to match; the deck-cycle phase shows backs at their native
82px height instead, since nothing there needs to align to a card-sized
slot.

Uses `Phase`/`PhaseSequence` (like LED/LED II/Title): the spec describes
two distinct stages -- deck cycle, then auto-deal -- not one continuous
behaviour, matching `PLAN.md`'s "Build order" placement for this demo.

Felt-green background, the DEALER/PLAYER labels, and the whole table
layout (hand fan spacing, canvas size) are invented -- there's no
finished-screen source image for this demo, only its sprite sheets, the
same situation Cinqtris's wordmark+equalizer layout was in.
"""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.bruces_21_phases import AutoDealPhase, DeckCyclePhase
from retrodemos.demos.bruces_21_table import NATIVE_SIZE, CardTable, Deck
from retrodemos.framework.demo import Demo
from retrodemos.framework.phase import PhaseSequence


class Bruces21Demo(Demo):
    NATIVE_SIZE = NATIVE_SIZE

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self._deck = Deck()
        self._table = CardTable(self._deck)
        self._rng = random.Random()
        self._sequence = PhaseSequence([
            DeckCyclePhase(self._table, self._rng),
            AutoDealPhase(self._table, self._rng),
        ])

    def reset(self) -> None:
        self._sequence.reset()

    def update(self, dt: float) -> None:
        self._sequence.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._sequence.draw(surface)


DEMO_CLASS = Bruces21Demo
