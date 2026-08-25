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
random, so two of them can hunt each other. Not yet ported to LED/LED II's
own SnakePhases -- see PLAN.md's "Future framework polish".
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
    dropped as a new one is added."""

    def __init__(self, graph: dict[Node, set[Node]], start: Node, max_length: int, rng: random.Random) -> None:
        self.graph = graph
        self.max_length = max_length
        self.rng = rng
        self.body: list[Node] = [start]

    def advance(self) -> None:
        head = self.body[0]
        neighbours = list(self.graph[head])
        previous = self.body[1] if len(self.body) > 1 else None
        candidates = [n for n in neighbours if n != previous] or neighbours
        self.body.insert(0, self.rng.choice(candidates))
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
