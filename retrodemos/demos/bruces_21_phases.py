"""Bruce's 21's script: a shuffled deck cycle, then a mock deal. See
bruces_21.py's module docstring for the sprite/table background, and
docs/bruces-21.md for the demo overview.

Both phases' exact timings and the deal script's shape (hole card, a
random 0-2 "hit" cards, a reveal, a maybe-one dealer card) are judgement
calls filling in what the spec left as "deals and reveals hands as if
playing a round of 21" -- there's no real hand evaluation anywhere here,
just a plausible-looking sequence of face-up/face-down cards appearing
and disappearing on a loop. Retune the constants at the top of each class
without touching the choreography logic, same convention led_phases.py
uses.
"""

from __future__ import annotations

import pygame

from retrodemos.demos.bruces_21_table import RANKS, SUITS, CardTable
from retrodemos.framework.phase import Phase
from retrodemos.framework.ticker import Ticker


class DeckCyclePhase(Phase):
    """Shuffles the full 52-card face deck plus both card backs into one
    54-item list and flips through it one at a time, showing off the
    sprite art (docs/bruces-21.md: "shuffles and flips through the full
    face deck and both card backs")."""

    display: CardTable

    TICK = 0.12

    def reset(self) -> None:
        # back_for_slot, not back: the raw backs are 64x82 (BACKS.png's
        # own native size) vs. every card's 48x66, so cycling the raw
        # size in made the card visibly jump size twice a lap
        # (playtesting, 2026-08-26: "card sizes change mid way through").
        items: list[pygame.Surface] = list(self.display.deck.all_cards())
        items.append(self.display.deck.back_for_slot(0))
        items.append(self.display.deck.back_for_slot(1))
        self.rng.shuffle(items)
        self._items = items
        self._index = 0
        self._ticker = Ticker(self.TICK)
        self.display.mode = "cycle"
        self.display.center = self._items[0]

    def update(self, dt: float) -> bool:
        for _ in range(self._ticker.advance(dt)):
            self._index += 1
            if self._index >= len(self._items):
                return True
            self.display.center = self._items[self._index]
        return False

    def draw(self, surface: pygame.Surface) -> None:
        self.display.draw(surface)


# ---- Auto-deal script -- one action per scripted step, each held for a
# duration before the next fires. "pause" performs no action, just holds
# the table as-is. See class docstring above for how much of this is
# invented vs. spec'd. ----
DEAL_TICK = 0.35
PAUSE_SHORT = 0.6
PAUSE_LONG = 2.2
HOLE_CARD_BACK = 0  # which of the two back designs covers the dealer's hole card


class AutoDealPhase(Phase):
    """Deals a mock round: dealer gets a face-down hole card then one
    face-up, player gets two face-up, an optional "hit" or two follows,
    then the hole card flips face-up and the dealer may take one more --
    all appearance only, no hand values are ever computed."""

    display: CardTable

    def reset(self) -> None:
        self.display.mode = "deal"
        self.display.dealer_hand = []
        self.display.player_hand = []
        self._hole_card = self._draw_card()
        self._steps = self._build_steps()
        self._step_index = -1
        self._wait = 0.0
        self._advance()

    def _draw_card(self) -> pygame.Surface:
        return self.display.deck.card(self.rng.choice(SUITS), self.rng.choice(RANKS))

    def _build_steps(self) -> list[tuple[str, float]]:
        steps: list[tuple[str, float]] = [
            ("dealer_back", DEAL_TICK),
            ("player_card", DEAL_TICK),
            ("dealer_card", DEAL_TICK),
            ("player_card", DEAL_TICK),
            ("pause", PAUSE_SHORT),
        ]
        for _ in range(self.rng.choice((0, 1, 1, 2))):  # weighted toward exactly one hit
            steps.append(("player_card", DEAL_TICK))
        steps.append(("pause", PAUSE_SHORT))
        steps.append(("reveal_hole", DEAL_TICK))
        if self.rng.random() < 0.5:
            steps.append(("dealer_card", DEAL_TICK))
        steps.append(("pause", PAUSE_LONG))
        return steps

    def _advance(self) -> None:
        self._step_index += 1
        if self._step_index >= len(self._steps):
            return
        action, hold = self._steps[self._step_index]
        self._do_action(action)
        self._wait = hold

    def _do_action(self, action: str) -> None:
        if action == "dealer_back":
            self.display.dealer_hand.append(self.display.deck.back_for_slot(HOLE_CARD_BACK))
        elif action == "dealer_card":
            self.display.dealer_hand.append(self._draw_card())
        elif action == "player_card":
            self.display.player_hand.append(self._draw_card())
        elif action == "reveal_hole":
            self.display.dealer_hand[0] = self._hole_card
        elif action == "pause":
            pass
        else:  # pragma: no cover -- defensive, every step above is one of these
            raise ValueError(f"unknown deal step: {action!r}")

    def update(self, dt: float) -> bool:
        if self._step_index >= len(self._steps):
            return True
        self._wait -= dt
        if self._wait <= 0:
            self._advance()
        return self._step_index >= len(self._steps)

    def draw(self, surface: pygame.Surface) -> None:
        self.display.draw(surface)
