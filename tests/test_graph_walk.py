"""Tests for the generic graph-walk primitives (framework/graph_walk.py):
Snake and bfs_rings, extracted from LED's phases once LED II's phases
needed the identical logic over a different (dot-grid) graph; Burst, built
directly here for LED II's fireworks-style RipplePhase; and ChaseMatch and
Rocket (2026-08-26), the best-of-N match wrapper and fireworks launch
trail built for LED II's and Title's snake-chase/fireworks phases.

Uses a plain 3x3 grid graph as a stand-in for either real caller's graph
shape, since none of Snake, bfs_rings, or Burst care what a node actually is.
"""

from __future__ import annotations

import random

from retrodemos.framework.graph_walk import Burst, ChaseMatch, ChasePair, ChaseSnake, Rocket, Snake, bfs_rings


def _grid_graph(width: int, height: int) -> dict[tuple[int, int], set[tuple[int, int]]]:
    graph: dict[tuple[int, int], set[tuple[int, int]]] = {}
    for y in range(height):
        for x in range(width):
            neighbours = set()
            if x > 0:
                neighbours.add((x - 1, y))
            if x < width - 1:
                neighbours.add((x + 1, y))
            if y > 0:
                neighbours.add((x, y - 1))
            if y < height - 1:
                neighbours.add((x, y + 1))
            graph[(x, y)] = neighbours
    return graph


def test_snake_starts_at_the_given_node():
    graph = _grid_graph(3, 3)
    snake = Snake(graph, start=(1, 1), max_length=3, rng=random.Random(0))
    assert snake.body == [(1, 1)]


def test_snake_grows_up_to_max_length_then_holds():
    graph = _grid_graph(3, 3)
    snake = Snake(graph, start=(1, 1), max_length=3, rng=random.Random(0))
    for _ in range(10):
        snake.advance()
        assert len(snake.body) <= 3
    assert len(snake.body) == 3


def test_snake_stays_on_graph_edges():
    graph = _grid_graph(3, 3)
    snake = Snake(graph, start=(0, 0), max_length=4, rng=random.Random(1))
    for _ in range(20):
        snake.advance()
        for a, b in zip(snake.body, snake.body[1:]):
            assert b in graph[a], f"{a} -> {b} isn't an edge in the graph"


def test_snake_avoids_immediately_reversing_when_another_option_exists():
    # On this 3-wide row, the middle node has two neighbours; the snake
    # should never double back to where it just came from while it can
    # still choose the other one.
    graph = _grid_graph(3, 1)
    snake = Snake(graph, start=(0, 0), max_length=2, rng=random.Random(0))
    snake.advance()  # body: [(1,0), (0,0)]
    assert snake.body == [(1, 0), (0, 0)]
    snake.advance()  # from (1,0), previous is (0,0) -- must go to (2,0)
    assert snake.body[0] == (2, 0)


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def test_chase_snake_grows_up_to_max_length_then_holds():
    graph = _grid_graph(9, 9)
    snake = ChaseSnake(graph, start=(0, 0), max_length=3, rng=random.Random(0), distance=_manhattan)
    for _ in range(10):
        snake.advance((8, 8))
        assert len(snake.body) <= 3
    assert len(snake.body) == 3


def test_chase_snake_stays_on_graph_edges():
    graph = _grid_graph(9, 9)
    snake = ChaseSnake(graph, start=(0, 0), max_length=4, rng=random.Random(1), distance=_manhattan)
    for _ in range(20):
        snake.advance((8, 8))
        for a, b in zip(snake.body, snake.body[1:]):
            assert b in graph[a], f"{a} -> {b} isn't an edge in the graph"


def test_chase_snake_with_full_chase_chance_always_closes_distance_on_target():
    # chase_chance=1.0 makes every step a greedy best-move, so distance to a
    # stationary target should never increase.
    graph = _grid_graph(9, 9)
    snake = ChaseSnake(graph, start=(0, 0), max_length=20, rng=random.Random(2), distance=_manhattan, chase_chance=1.0)
    target = (8, 8)
    previous_distance = _manhattan(snake.body[0], target)
    for _ in range(16):
        snake.advance(target)
        distance = _manhattan(snake.body[0], target)
        assert distance <= previous_distance
        previous_distance = distance
    assert snake.body[0] == target


def test_chase_snake_with_zero_chase_chance_behaves_like_plain_random_walk():
    # chase_chance=0.0 should never prefer the target -- just confirm it
    # still produces a valid walk (an unbiased Snake's own tests already
    # cover the "stays on graph edges" / "avoids reversing" behaviour this
    # shares via the same candidate-selection logic).
    graph = _grid_graph(9, 9)
    snake = ChaseSnake(graph, start=(4, 4), max_length=5, rng=random.Random(3), distance=_manhattan, chase_chance=0.0)
    for _ in range(20):
        snake.advance((0, 0))
        for a, b in zip(snake.body, snake.body[1:]):
            assert b in graph[a]


def test_chase_snake_avoids_immediately_reversing_when_another_option_exists():
    graph = _grid_graph(3, 1)
    snake = ChaseSnake(graph, start=(0, 0), max_length=2, rng=random.Random(0), distance=_manhattan, chase_chance=0.0)
    snake.advance((2, 0))  # body: [(1,0), (0,0)]
    assert snake.body == [(1, 0), (0, 0)]
    snake.advance((2, 0))  # from (1,0), previous is (0,0) -- must go to (2,0)
    assert snake.body[0] == (2, 0)


def _chase_pair(graph, start_a=(0, 0), start_b=(8, 8), max_length=20, seed=0, chase_chance=1.0, max_steps=200, flash_cycles=2):
    return ChasePair(graph, start_a, start_b, max_length, random.Random(seed), _manhattan, chase_chance, max_steps, flash_cycles)


def test_chase_pair_starts_unresolved_with_both_bodies_lit():
    graph = _grid_graph(9, 9)
    pair = _chase_pair(graph)
    assert not pair.resolved
    assert not pair.finished
    assert pair.lit_cells() == {(0, 0), (8, 8)}


def test_chase_pair_resolves_once_a_head_lands_on_the_other_bodys():
    graph = _grid_graph(9, 9)
    pair = _chase_pair(graph, chase_chance=1.0)
    for _ in range(50):
        if pair.resolved:
            break
        pair.step()
    assert pair.resolved
    assert pair.winner in (pair.a, pair.b)


def test_chase_pair_stops_stepping_once_resolved():
    graph = _grid_graph(9, 9)
    pair = _chase_pair(graph, chase_chance=1.0)
    while not pair.resolved:
        pair.step()
    steps_at_resolution = pair.steps_taken
    pair.step()  # no-op now
    assert pair.steps_taken == steps_at_resolution


def test_chase_pair_flash_tick_toggles_until_finished():
    graph = _grid_graph(9, 9)
    pair = _chase_pair(graph, chase_chance=1.0, flash_cycles=2)
    while not pair.resolved:
        pair.step()
    toggles = 0
    seen_both = set()
    while not pair.finished:
        pair.flash_tick()
        toggles += 1
        seen_both.add(pair.flash_on)
    assert toggles == 4  # 2 cycles * (on + off)
    assert seen_both == {True, False}


def test_chase_pair_lit_cells_only_shows_winner_while_flashing_on():
    graph = _grid_graph(9, 9)
    pair = _chase_pair(graph, chase_chance=1.0)
    while not pair.resolved:
        pair.step()
    assert pair.flash_on  # resolves with a visible flash
    assert pair.lit_cells() == set(pair.winner.body)
    pair.flash_tick()
    assert not pair.flash_on
    assert pair.lit_cells() == set()


def test_chase_pair_safety_net_forces_a_winner_at_max_steps():
    # chase_chance=0.0 means the snakes never actually pursue each other,
    # so max_steps is what has to end the pair, not a real catch.
    graph = _grid_graph(3, 1)
    pair = ChasePair(
        graph, start_a=(0, 0), start_b=(2, 0), max_length=1, rng=random.Random(0),
        distance=_manhattan, chase_chance=0.0, max_steps=10, flash_cycles=1,
    )
    for _ in range(10):
        pair.step()
    assert pair.resolved


def test_chase_pair_winner_index_matches_which_side_won():
    graph = _grid_graph(9, 9)
    pair = _chase_pair(graph, chase_chance=1.0)
    assert pair.winner_index is None
    while not pair.resolved:
        pair.step()
    expected = 0 if pair.winner is pair.a else 1
    assert pair.winner_index == expected


def _make_round_factory(graph, seed):
    counter = {"seed": seed}

    def factory():
        counter["seed"] += 1
        return _chase_pair(graph, seed=counter["seed"], chase_chance=1.0, flash_cycles=1)

    return factory


def _run_round_to_finish(pair):
    while not pair.resolved:
        pair.step()
    while not pair.finished:
        pair.flash_tick()


def test_chase_match_scores_a_round_and_starts_a_fresh_one():
    graph = _grid_graph(9, 9)
    match = ChaseMatch(_make_round_factory(graph, seed=0), wins_needed=3)
    first_round = match.round
    _run_round_to_finish(match.round)
    match.update()
    assert sum(match.score) == 1
    assert match.round is not first_round  # a fresh round started
    assert not match.round.resolved


def test_chase_match_is_idempotent_once_a_round_is_scored():
    graph = _grid_graph(9, 9)
    match = ChaseMatch(_make_round_factory(graph, seed=0), wins_needed=3)
    _run_round_to_finish(match.round)
    match.update()
    scored_after_first_call = match.score[:]
    match.update()  # no-op: the new round hasn't finished yet
    assert match.score == scored_after_first_call


def test_chase_match_finishes_once_a_side_reaches_wins_needed():
    graph = _grid_graph(9, 9)
    match = ChaseMatch(_make_round_factory(graph, seed=0), wins_needed=3)
    for _ in range(50):
        if match.finished:
            break
        _run_round_to_finish(match.round)
        match.update()
    assert match.finished
    assert match.match_winner in (0, 1)
    assert match.score[match.match_winner] == 3


def test_rocket_starts_at_start_and_ends_at_target():
    rocket = Rocket(start=(0, 10), target=(10, 0), duration=1.0)
    assert rocket.position() == (0, 10)
    assert not rocket.done
    rocket.age(1.0)
    assert rocket.done
    assert rocket.position() == (10, 0)


def test_rocket_position_is_partway_along_the_line_mid_flight():
    rocket = Rocket(start=(0, 0), target=(10, 0), duration=2.0)
    rocket.age(1.0)
    assert not rocket.done
    assert rocket.position() == (5, 0)


def test_bfs_rings_first_ring_is_just_the_start():
    graph = _grid_graph(3, 3)
    rings = bfs_rings(graph, start=(1, 1), max_ring=2)
    assert rings[0] == [(1, 1)]


def test_bfs_rings_respects_the_max_ring_cap():
    graph = _grid_graph(5, 5)
    rings = bfs_rings(graph, start=(2, 2), max_ring=1)
    assert len(rings) == 2  # ring 0 (start) and ring 1 (its neighbours) only


def test_bfs_rings_visits_every_node_reachable_within_the_cap():
    graph = _grid_graph(3, 3)
    rings = bfs_rings(graph, start=(0, 0), max_ring=4)
    visited = {node for ring in rings for node in ring}
    assert visited == set(graph.keys())


def _burst(graph, start=(2, 2), max_ring=2, fade_duration=0.5, spark_count=3, seed=0):
    return Burst(graph, start, max_ring, fade_duration, spark_count, random.Random(seed))


def test_burst_starts_with_nothing_ignited():
    graph = _grid_graph(5, 5)
    burst = _burst(graph)
    assert burst.intensities() == {}
    assert burst.is_expanding


def test_expand_next_ring_ignites_the_start_node_first():
    graph = _grid_graph(5, 5)
    burst = _burst(graph, start=(2, 2))
    burst.expand_next_ring()
    intensities = burst.intensities()
    assert (2, 2) in intensities
    assert 0.7 <= intensities[(2, 2)] <= 1.0  # default ignite_range


def test_is_expanding_becomes_false_once_every_ring_has_ignited():
    graph = _grid_graph(5, 5)
    burst = _burst(graph, start=(2, 2), max_ring=2)
    ring_count = len(bfs_rings(graph, (2, 2), 2))
    for _ in range(ring_count):
        assert burst.is_expanding
        burst.expand_next_ring()
    assert not burst.is_expanding


def test_add_sparks_ignites_spark_count_more_nodes():
    graph = _grid_graph(6, 6)
    burst = _burst(graph, start=(3, 3), max_ring=1, spark_count=5)
    while burst.is_expanding:
        burst.expand_next_ring()
    before = len(burst.intensities())
    burst.add_sparks()
    after = len(burst.intensities())
    # spark nodes might land on already-ignited ones, so this is a floor,
    # not an exact count, but at least one new node should light up given
    # a 6x6 graph and only ~5 nodes ignited by a max_ring=1 burst so far.
    assert after > before


def test_add_sparks_is_idempotent():
    graph = _grid_graph(5, 5)
    burst = _burst(graph, spark_count=4)
    while burst.is_expanding:
        burst.expand_next_ring()
    burst.add_sparks()
    first = dict(burst.intensities())
    burst.add_sparks()
    assert burst.intensities() == first


def test_intensity_fades_to_nothing_over_fade_duration():
    graph = _grid_graph(5, 5)
    burst = _burst(graph, start=(2, 2), fade_duration=1.0)
    burst.expand_next_ring()
    peak = burst.intensities()[(2, 2)]
    burst.age(0.5)
    assert 0 < burst.intensities()[(2, 2)] < peak
    burst.age(0.6)  # total age 1.1s, past fade_duration
    assert (2, 2) not in burst.intensities()


def test_burned_out_requires_sparks_added_and_full_fade():
    graph = _grid_graph(5, 5)
    burst = _burst(graph, start=(2, 2), max_ring=1, fade_duration=0.2, spark_count=2)
    while burst.is_expanding:
        burst.expand_next_ring()
    burst.age(1.0)  # rings fully faded, but sparks not added yet
    assert not burst.burned_out
    burst.add_sparks()
    assert not burst.burned_out  # sparks just ignited, still at peak brightness
    burst.age(1.0)
    assert burst.burned_out
