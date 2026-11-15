"""Learn when and where to dose, inside the world model.

Tabular Q-learning, deliberately. The decision is small: which section to
treat, or none, given a coarse reading of the loop. A table learns it in about
a second on a laptop with no dependencies, and a table can be read afterwards,
which a network cannot.

The policy only sees what a sensor would report: a coarse film level at the
sections that carry a sensor, not the true state everywhere. Learning on what
the instrument can see is the point, since that is what a deployment would
have.
"""

from __future__ import annotations

import random

from sonazyme.loop.world import CEILING_C, Loop

SENSORS = (0, 2, 3, 4, 5, 6)  # sections that carry a sensor, clustered where it runs hot
LEVELS = 4  # how coarsely a sensor reports film
DOSE_COST = 1.6  # a treatment is not free
OVER_COST = 45.0  # per degree above the ceiling


def _level(value: float) -> int:
    return min(LEVELS - 1, int(value * LEVELS * 1.6))


def observe(loop: Loop) -> tuple[int, ...]:
    """Read the loop coarsely, from the sensors only.

    Raw per-sensor levels make a table too large to fill in a second, and most
    of it would never be visited. What the decision needs is how hot it is
    about to get, how bad the worst section is, and which one that is.
    """
    hot = max(
        loop.film[(loop.hot + offset) % loop.sections]
        for offset in (-1, 0, 1)
        if (loop.hot + offset) % loop.sections in SENSORS
    )
    sensed = [(loop.film[index], index) for index in SENSORS]
    worst, where = max(sensed)
    return (_level(hot), _level(worst), SENSORS.index(where))


def reward(loop: Loop, dose: int | None) -> float:
    """Cool pipes, few doses, and never over the ceiling."""
    over = max(0.0, loop.temperature() - CEILING_C)
    return -(OVER_COST * over) - (DOSE_COST if dose is not None else 0.0) - sum(loop.film)


def _actions(sections: int) -> list[int | None]:
    return [None, *range(sections)]


def train(
    *,
    episodes: int = 4200,
    hours: int = 64,
    seed: int = 7,
    alpha: float = 0.35,
    gamma: float = 0.93,
) -> dict[tuple[int, ...], list[float]]:
    """Learn a dosing policy. Returns the table, keyed by what the sensors saw."""
    rng = random.Random(seed)
    loop = Loop(seed=seed)
    actions = _actions(loop.sections)
    table: dict[tuple[int, ...], list[float]] = {}

    def row(state: tuple[int, ...]) -> list[float]:
        return table.setdefault(state, [0.0] * len(actions))

    for episode in range(episodes):
        loop.reset()
        # Exploring starts. A loop that is always clean at hour zero teaches a
        # policy nothing about a loop that is already fouled, which is the
        # state it will mostly be asked about.
        loop.film = [rng.random() ** 1.5 * 0.85 for _ in range(loop.sections)]
        state = observe(loop)
        explore = max(0.05, 1.0 - episode / (episodes * 0.7))
        for _ in range(hours):
            values = row(state)
            if rng.random() < explore:
                choice = rng.randrange(len(actions))
            else:
                best = max(values)
                choice = rng.choice([i for i, v in enumerate(values) if v == best])
            loop.step(actions[choice])
            gained = reward(loop, actions[choice])
            following = observe(loop)
            values[choice] += alpha * (gained + gamma * max(row(following)) - values[choice])
            state = following
    return table


def act(table: dict[tuple[int, ...], list[float]], loop: Loop) -> int | None:
    """Return what the learned policy would do now."""
    actions = _actions(loop.sections)
    values = table.get(observe(loop))
    if values is None:
        return None
    return actions[values.index(max(values))]
