"""Tests for Bruce's 21: the sprite sheet slicing (Deck), the table
layout/rendering (CardTable), and the two script phases."""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.bruces_21 import Bruces21Demo
from retrodemos.demos.bruces_21_phases import AutoDealPhase, DeckCyclePhase
from retrodemos.demos.bruces_21_table import (
    BACK_H,
    BACK_W,
    CARD_H,
    CARD_W,
    HEIGHT,
    RANKS,
    SUITS,
    WIDTH,
    CardTable,
    Deck,
)


def test_deck_has_all_52_unique_cards():
    deck = Deck()
    cards = deck.all_cards()
    assert len(cards) == 52
    # Every (suit, rank) combination is present and sized correctly.
    for suit in SUITS:
        for rank in RANKS:
            card = deck.card(suit, rank)
            assert card.get_size() == (CARD_W, CARD_H)


def test_deck_has_two_distinct_back_designs():
    deck = Deck()
    back0, back1 = deck.back(0), deck.back(1)
    assert back0.get_size() == (BACK_W, BACK_H) == back1.get_size()
    # Not the same design -- pattern back vs. wordmark back.
    pixels0 = [tuple(back0.get_at((x, y))) for x in range(BACK_W) for y in range(BACK_H)]
    pixels1 = [tuple(back1.get_at((x, y))) for x in range(BACK_W) for y in range(BACK_H)]
    assert pixels0 != pixels1


def test_back_for_slot_matches_card_footprint():
    deck = Deck()
    assert deck.back_for_slot(0).get_size() == (CARD_W, CARD_H)
    assert deck.back_for_slot(1).get_size() == (CARD_W, CARD_H)


def test_card_table_cycle_mode_draws_center_card():
    deck = Deck()
    table = CardTable(deck)
    table.center = deck.card("hearts", "A")
    surface = pygame.Surface((WIDTH, HEIGHT))
    table.draw(surface)  # should not raise


def test_card_table_deal_mode_draws_both_hands():
    deck = Deck()
    table = CardTable(deck)
    table.mode = "deal"
    table.dealer_hand = [deck.back_for_slot(0), deck.card("clubs", "K")]
    table.player_hand = [deck.card("spades", "A"), deck.card("hearts", "2")]
    surface = pygame.Surface((WIDTH, HEIGHT))
    table.draw(surface)  # should not raise


def test_deck_cycle_phase_visits_all_54_items_then_finishes():
    deck = Deck()
    table = CardTable(deck)
    phase = DeckCyclePhase(table, random.Random(0))
    seen = []
    finished = False
    for _ in range(200):
        finished = phase.update(DeckCyclePhase.TICK)
        seen.append(table.center)
        if finished:
            break
    assert finished
    assert len(seen) == 54  # 52 cards + 2 backs


def test_auto_deal_phase_deals_at_least_the_opening_four_cards():
    deck = Deck()
    table = CardTable(deck)
    phase = AutoDealPhase(table, random.Random(0))
    assert len(table.dealer_hand) == 1  # the face-down hole card, dealt in reset()
    assert len(table.player_hand) == 0
    for _ in range(3):
        phase.update(phase._wait + 0.001)
    assert len(table.dealer_hand) == 2
    assert len(table.player_hand) == 2


def test_auto_deal_phase_reveals_the_hole_card_and_eventually_finishes():
    deck = Deck()
    table = CardTable(deck)
    phase = AutoDealPhase(table, random.Random(1))
    hole_card = phase._hole_card
    finished = False
    for _ in range(50):
        finished = phase.update(phase._wait + 0.001)
        if finished:
            break
    assert finished
    assert table.dealer_hand[0] is hole_card  # hole card was face-down, then revealed


def test_auto_deal_phase_never_exceeds_max_hand_slots():
    from retrodemos.demos.bruces_21_table import MAX_HAND

    for seed in range(20):
        deck = Deck()
        table = CardTable(deck)
        phase = AutoDealPhase(table, random.Random(seed))
        for _ in range(50):
            if phase.update(phase._wait + 0.001):
                break
        assert len(table.dealer_hand) <= MAX_HAND
        assert len(table.player_hand) <= MAX_HAND


def test_demo_native_size_matches_table_layout():
    demo = Bruces21Demo()
    assert demo.NATIVE_SIZE == (WIDTH, HEIGHT)


def test_demo_loops_between_both_phases_across_many_frames():
    demo = Bruces21Demo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    seen_phases = set()
    for _ in range(3000):
        demo.update(0.05)
        demo.draw(surface)
        seen_phases.add(type(demo._sequence.current).__name__)
    assert seen_phases == {"DeckCyclePhase", "AutoDealPhase"}


def test_demo_reset_restarts_the_sequence():
    demo = Bruces21Demo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    for _ in range(200):
        demo.update(0.05)
        demo.draw(surface)
    demo.reset()
    assert demo._sequence.index == 0
    assert isinstance(demo._sequence.current, DeckCyclePhase)
