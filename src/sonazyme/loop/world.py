"""A fast world model of a cooling loop, and what a treatment does to it.

The loop is a ring of sections. Film grows on each one at its own rate, faster
where the water is warm and slow. Film insulates, so the water leaves the rack
hotter, and the chip temperature follows. A dose of enzyme clears film at the
section it is applied to, and a little downstream of it.

Everything here is a model. No cooling loop has been measured, and the
constants are chosen to make the dynamics behave sensibly rather than to match
a site. The point of the model is to let a policy learn when and where to
treat without touching anything real.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

SECTIONS = 8
CEILING_C = 78.0  # the chip temperature a policy must stay under
BASE_C = 62.0  # chip temperature on a clean loop


@dataclass
class Loop:
    """One loop, rolled forward in hours."""

    seed: int = 7
    sections: int = SECTIONS
    film: list[float] = field(default_factory=list)
    growth: list[float] = field(default_factory=list)
    hot: int = 0  # the section nearest the chips, where temperature is read
    hours: int = 0
    random: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        """Start from a clean loop with its own growth rates."""
        self.random = random.Random(self.seed)
        self.hot = self.sections // 2
        self.reset()

    def reset(self) -> None:
        """Clean the loop and redraw the growth rates."""
        self.hours = 0
        self.film = [self.random.uniform(0.0, 0.04) for _ in range(self.sections)]
        # Warm, slow sections foul faster. The hot section is the worst.
        self.growth = [
            0.010 + 0.016 * math.exp(-(((i - self.hot) / 2.2) ** 2)) + self.random.uniform(0, 0.004)
            for i in range(self.sections)
        ]

    def temperature(self) -> float:
        """Chip temperature, driven by the film on the hot section and its neighbours."""
        window = [self.film[(self.hot + offset) % self.sections] for offset in (-1, 0, 1)]
        insulation = 0.55 * window[1] + 0.225 * (window[0] + window[2])
        return BASE_C + 34.0 * insulation

    def step(self, dose: int | None) -> dict:
        """Advance one hour, optionally dosing one section. Returns what happened."""
        if dose is not None:
            if not 0 <= dose < self.sections:
                raise ValueError("A dose names a section of this loop")
            # The enzyme clears film where it is applied, and is carried
            # downstream, weaker as it goes.
            for offset, clearing in ((0, 0.72), (1, 0.34), (2, 0.12)):
                index = (dose + offset) % self.sections
                self.film[index] = max(0.0, self.film[index] * (1 - clearing))
        for index in range(self.sections):
            # Film grows faster once it has a foothold, and saturates.
            level = self.film[index]
            self.film[index] = min(1.0, level + self.growth[index] * (0.35 + level) * (1 - level))
        self.hours += 1
        return {
            "hours": self.hours,
            "temperature_c": self.temperature(),
            "film": list(self.film),
            "dosed": dose,
        }
