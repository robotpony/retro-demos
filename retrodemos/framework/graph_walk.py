"""Generic walks over an adjacency graph (`dict[Node, set[Node]]`), shared
by any Phase that crawls or radiates across a LED-family grid.

Node is opaque here -- LED's segment graph (`led_grid.segment_adjacency`,
`Node = (digit_index, segment_name)`) and LED II's dot graph
(`led_grid.dot_grid_adjacency`, `Node = (col, row)`) are the two current
graphs this walks, but neither `Snake`, `bfs_rings`, nor `Burst` know or
care which kind of node they're holding, only that the graph maps a node to
its neighbours.

`Snake` and `bfs_rings` were pulled out of `retrodemos/demos/led_phases.py`'s
`SnakePhase` and `ExplosionPhase` once LED II's phases needed the identical
logic over a different graph -- see PLAN.md's "Future framework polish"
history for why this wasn't built speculatively ahead of a second caller.
`Burst` (built directly here, for LED II's RipplePhase) generalizes
`bfs_rings` into an actual particle effect: per-node randomized brightness
that fades over time, plus a scatter of extra spark nodes -- LED's own
ExplosionPhase doesn't use it yet, but could adopt it later. `ChaseSnake`
(built directly here, for Title's snake-chase minigame -- see
`retrodemos/demos/title_phases.py`'s SnakePhase) generalizes `Snake` the same
way: same growing-body-then-holds-length shape, but each step is weighted
toward a target node supplied fresh per call rather than picked uniformly at
random, so two of them can hunt each other. `ChasePair` (also built here)
was pulled out of Title's own `SnakePhase` once LED II's snake-chase needed
the identical catch/win/flash bookkeeping over its own (differently-shaped)
dot grid -- the two callers' Phases now differ only in grid shape, spawn
positions, and timing constants, not in the chase logic itself. LED's own
SnakePhase (the segment-graph one) hasn't been ported to a chase minigame
yet -- worth doing next time it's touched.
"""

from __future__ import annotations

import random
from collections import deque
from typing import Callable, Generic, TypeVar

Node = TypeVar("Node")


class Snake(Generic[Node]):
    """A body of up to `max_length` nodes that crawls a graph one step at a
    time: each step moves the head to a random neighbour (never immediately
    back the way it came, unless that's the only option), growing until
    `max_length` is reached and then holding that length, oldest node
    dropped as a new one is added.

    `weight_fn(current, candidate)` optionally weights the random choice
    instead of picking uniformly -- e.g. LED's SnakePhase (2026-08-26,
    playtesting: "moving horizontally more") weights a candidate higher
    when it's in a different digit cell than the head, so the crawl
    drifts across the display rather than looping within one digit."""

    def __init__(
        self,
        graph: dict[Node, set[Node]],
        start: Node,
        max_length: int,
        rng: random.Random,
        weight_fn: Callable[[Node, Node], float] | None = None,
    ) -> None:
        self.graph = graph
        self.max_length = max_length
        self.rng = rng
        self.weight_fn = weight_fn
        self.body: list[Node] = [start]

    def advance(self) -> None:
        head = self.body[0]
        neighbours = list(self.graph[head])
        previous = self.body[1] if len(self.body) > 1 else None
        candidates = [n for n in neighbours if n != previous] or neighbours
        if self.weight_fn is None:
            choice = self.rng.choice(candidates)
        else:
            weights = [self.weight_fn(head, c) for c in candidates]
            choice = self.rng.choices(candidates, weights=weights, k=1)[0]
        self.body.insert(0, choice)
        if len(self.body) > self.max_length:
            self.body.pop()


class ChaseSnake(Generic[Node]):
    """Like `Snake` (same growing-then-holding body, same never-immediately-
    reverse rule), but `advance()` takes a `target` node each call and
    weights its step toward closing distance on it, rather than choosing
    uniformly at random -- built for a chase minigame where two of these
    hunt each other's head.

    `distance` is caller-supplied so ChaseSnake stays agnostic about what a
    Node actually is, the same way `Snake`/`bfs_rings`/`Burst` don't know
    whether they're walking a segment graph or a dot grid: pass a function
    that scores how far a candidate node is from the target, weighted
    however suits that graph's shape (Title's SnakePhase weighs its x-axis
    heavier than its y-axis, since its grid is 256 columns by 8 rows and an
    unweighted chase would zigzag vertically as often as it closed
    horizontal ground -- see title_phases.py's `_chase_distance`).

    `chase_chance` (0..1) is how often a step is actually chosen by the
    distance weighting; the rest of the time it falls back to `Snake`'s
    plain random choice among the same candidates, so the pursuit reads as
    a hunt with some wander in it rather than a laser-guided missile beelining
    straight at its target every single step.
    """

    def __init__(
        self,
        graph: dict[Node, set[Node]],
        start: Node,
        max_length: int,
        rng: random.Random,
        distance: Callable[[Node, Node], float],
        chase_chance: float = 0.85,
    ) -> None:
        self.graph = graph
        self.max_length = max_length
        self.rng = rng
        self.distance = distance
        self.chase_chance = chase_chance
        self.body: list[Node] = [start]

    def advance(self, target: Node) -> None:
        head = self.body[0]
        neighbours = list(self.graph[head])
        previous = self.body[1] if len(self.body) > 1 else None
        candidates = [n for n in neighbours if n != previous] or neighbours
        if self.rng.random() < self.chase_chance:
            best = min(self.distance(n, target) for n in candidates)
            candidates = [n for n in candidates if self.distance(n, target) == best]
        self.body.insert(0, self.rng.choice(candidates))
        if len(self.body) > self.max_length:
            self.body.pop()


class ChasePair(Generic[Node]):
    """Two `ChaseSnake`s that hunt each other's head over the same graph
    until one catches the other (its head lands on the other's body), then
    flashes the winner a few times before reading as finished -- the
    reusable core of a snake-chase minigame Phase.

    Pulled out of Title's `SnakePhase` (2026-08-24) once LED II's own
    SnakePhase needed the identical catch/win/flash bookkeeping over its
    own, differently-shaped dot grid; the graph, starting nodes, distance
    function, and every timing constant are all caller-supplied, so this
    doesn't assume a particular grid shape or pacing -- see
    title_phases.py's SnakePhase and led_ii_phases.py's SnakePhase for two
    different grids driving the same class.

    Movement and flashing are paced by the caller, not internally: call
    `step()` at whatever rate the chase should move (typically from inside
    a `Ticker` loop, same as any other discrete-step Phase) until
    `resolved`, then `flash_tick()` at the flash rate until `finished`.
    `lit_cells()` gives the current cells to render: both bodies while
    unresolved, just the winner's body while flashing on, nothing while
    flashing off.
    """

    def __init__(
        self,
        graph: dict[Node, set[Node]],
        start_a: Node,
        start_b: Node,
        max_length: int,
        rng: random.Random,
        distance: Callable[[Node, Node], float],
        chase_chance: float,
        max_steps: int,
        flash_cycles: int,
    ) -> None:
        self.rng = rng
        self.max_steps = max_steps
        self.a = ChaseSnake(graph, start_a, max_length, rng, distance, chase_chance)
        self.b = ChaseSnake(graph, start_b, max_length, rng, distance, chase_chance)
        self.winner: ChaseSnake[Node] | None = None
        self.steps_taken = 0
        self.flash_on = True
        self._flash_toggles = 0
        self._flash_target = flash_cycles * 2  # on + off per cycle

    @property
    def resolved(self) -> bool:
        return self.winner is not None

    @property
    def finished(self) -> bool:
        return self.resolved and self._flash_toggles >= self._flash_target

    def step(self) -> None:
        """Advance both snakes one step. No-op once resolved -- check
        `resolved` before calling from a tick loop, same as `flash_tick`."""
        if self.resolved:
            return
        self.steps_taken += 1
        self.a.advance(self.b.body[0])
        self.b.advance(self.a.body[0])
        a_caught = self.a.body[0] in self.b.body
        b_caught = self.b.body[0] in self.a.body
        if a_caught and b_caught:
            self.winner = self.rng.choice([self.a, self.b])  # head-on collision: pick either
        elif a_caught:
            self.winner = self.a
        elif b_caught:
            self.winner = self.b
        elif self.steps_taken >= self.max_steps:
            # Safety net -- two snakes actively closing distance should
            # always catch well before max_steps, but don't hang forever.
            self.winner = self.rng.choice([self.a, self.b])

    def flash_tick(self) -> None:
        """Toggle the winner's blink state. No-op if not yet resolved or
        already finished -- check `resolved`/`finished` from a tick loop."""
        if not self.resolved or self.finished:
            return
        self.flash_on = not self.flash_on
        self._flash_toggles += 1

    def lit_cells(self) -> set[Node]:
        if not self.resolved:
            return set(self.a.body) | set(self.b.body)
        return set(self.winner.body) if self.flash_on else set()


def bfs_rings(graph: dict[Node, set[Node]], start: Node, max_ring: int) -> list[list[Node]]:
    """Breadth-first ring layers outward from `start`, capped at `max_ring`
    hops so a burst stays local: rings[0] is [start], rings[1] its
    neighbours, rings[2] their unvisited neighbours, and so on."""
    visited = {start: 0}
    queue = deque([start])
    rings: list[list[Node]] = [[start]]
    while queue:
        node = queue.popleft()
        dist = visited[node]
        if dist >= max_ring:
            continue
        for neighbour in graph.get(node, ()):
            if neighbour not in visited:
                visited[neighbour] = dist + 1
                queue.append(neighbour)
                while len(rings) <= dist + 1:
                    rings.append([])
                rings[dist + 1].append(neighbour)
    return rings


class Burst(Generic[Node]):
    """A radiating particle burst: bfs_rings expand outward from a start
    node, each newly-revealed node igniting at a randomized peak brightness
    (`ignite_range`) that fades linearly to 0 over `fade_duration` seconds.
    Once every ring has expanded, `spark_count` extra nodes chosen from the
    whole graph (not just the ring shape) ignite too, so the burst reads as
    a scatter of embers rather than a uniform expanding disc.

    Built for a fireworks/ripple-style Phase: call `age()` every update
    with dt, `expand_next_ring()` on each tick while `is_expanding`, then
    `add_sparks()` once; `intensities()` gives the current per-node
    brightness (0..1, absent once fully faded) for `draw()` to hand to a
    display's render_raw. `burned_out` is True once every ignited node has
    fully faded, including the sparks.
    """

    def __init__(
        self,
        graph: dict[Node, set[Node]],
        start: Node,
        max_ring: int,
        fade_duration: float,
        spark_count: int,
        rng: random.Random,
        ignite_range: tuple[float, float] = (0.7, 1.0),
    ) -> None:
        self.graph = graph
        self.rings = bfs_rings(graph, start, max_ring)
        self.fade_duration = fade_duration
        self.spark_count = spark_count
        self.rng = rng
        self.ignite_range = ignite_range
        self._ring_index = 0
        self._age: dict[Node, float] = {}
        self._peak: dict[Node, float] = {}
        self._sparked = False

    def _ignite(self, node: Node) -> None:
        self._age[node] = 0.0
        self._peak[node] = self.rng.uniform(*self.ignite_range)

    @property
    def is_expanding(self) -> bool:
        return self._ring_index < len(self.rings)

    def expand_next_ring(self) -> None:
        """Ignite the next ring. No-op once every ring has expanded --
        check `is_expanding` before calling from a tick loop."""
        if not self.is_expanding:
            return
        for node in self.rings[self._ring_index]:
            self._ignite(node)
        self._ring_index += 1

    def add_sparks(self) -> None:
        """Ignite spark_count extra random nodes from the whole graph.
        Idempotent -- safe to call every frame once expansion is done."""
        if self._sparked:
            return
        candidates = list(self.graph.keys())
        for _ in range(self.spark_count):
            self._ignite(self.rng.choice(candidates))
        self._sparked = True

    def age(self, dt: float) -> None:
        for node in self._age:
            self._age[node] += dt

    @property
    def burned_out(self) -> bool:
        return self._sparked and all(a >= self.fade_duration for a in self._age.values())

    def intensities(self) -> dict[Node, float]:
        result: dict[Node, float] = {}
        for node, age in self._age.items():
            level = self._peak[node] * (1 - age / self.fade_duration)
            if level > 0:
                result[node] = level
        return result
