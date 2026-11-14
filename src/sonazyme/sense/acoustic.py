"""What a layer on the pipe wall does to a pulse, and what can be read back.

Forward first, deliberately. The model says what signal a stated layer would
produce; the inverse then works on that signal. Doing it in this order makes
the size of the effect visible before anything claims to detect it, and for a
biofilm that effect is small: the film is mostly water, so its acoustic
contrast with the water above it is slight (ADR-0013).

Every constant here is an assumption of textbook order, not a sourced value,
and each carries that marking into the record. Sourcing them is #64, and
whether the separation below survives in a real loop is #68.
"""

from __future__ import annotations

import math
import random

VERSION = "1"

# Acoustic impedance, in MRayl, and longitudinal speed, in m/s.
# basis: assumption. These are textbook orders of magnitude, pending #64.
MEDIA = {
    "water": {"impedance_mrayl": 1.48, "speed_ms": 1480.0},
    "biofilm": {"impedance_mrayl": 1.52, "speed_ms": 1510.0},
    "scale": {"impedance_mrayl": 16.0, "speed_ms": 6000.0},
}
WALL_IMPEDANCE_MRAYL = {
    "copper": 41.6,
    "aluminium": 17.3,
    "stainless-steel": 45.4,
    "carbon-steel": 46.0,
    "polymer": 3.2,
}
# Noise on the recovered features, as a fraction of the feature, assumed.
NOISE = 0.04
# Below this thickness the round trip through the layer is shorter than the
# pulse can resolve, on the assumed centre frequency.
RESOLUTION_UM = 25.0

ASSUMPTIONS = [
    {
        "name": "media impedance and speed",
        "basis": "assumption",
        "reason": (
            "Textbook orders of magnitude for water, a water-rich film and mineral "
            "scale, pending sourcing in #64."
        ),
    },
    {
        "name": "feature noise",
        "basis": "assumption",
        "reason": (
            f"A flat {NOISE:.0%} of each feature, standing in for instrument and "
            "coupling variation."
        ),
    },
    {
        "name": "resolution floor",
        "basis": "assumption",
        "reason": (
            f"Layers under {RESOLUTION_UM:.0f} um are not separated from the wall echo "
            "at the assumed centre frequency."
        ),
    },
]


def reflection(first: float, second: float) -> float:
    """Pressure reflection coefficient at a boundary between two impedances."""
    return (second - first) / (second + first)


def forward(
    *,
    material: str,
    layer: str,
    thickness_um: float,
    seed: int | None = None,
) -> dict:
    """Return the features a stated layer on a stated wall would produce.

    The caller supplies the truth; this returns what an instrument would see.
    Nothing here is an observation of anything.
    """
    if material not in WALL_IMPEDANCE_MRAYL:
        raise ValueError(f"Unknown wall material: {material}")
    if layer not in ("none", "biofilm", "scale"):
        raise ValueError(f"Unknown layer: {layer}")
    if not math.isfinite(thickness_um) or thickness_um < 0:
        raise ValueError("Thickness must be a non-negative number")

    wall = WALL_IMPEDANCE_MRAYL[material]
    water = MEDIA["water"]
    present = layer != "none" and thickness_um > 0
    inner = MEDIA[layer] if present else water

    # What the wall sees behind it: the layer if there is one, else water.
    amplitude = abs(reflection(wall, inner["impedance_mrayl"]))
    # Round trip through the layer, in microseconds.
    travel_us = (2 * thickness_um * 1e-6) / inner["speed_ms"] * 1e6 if present else 0.0
    # A soft film scatters little; mineral scale attenuates far more.
    attenuation_db = (0.02 if layer == "biofilm" else 0.35) * thickness_um / 100 if present else 0.0

    noise = random.Random(seed).gauss if seed is not None else random.gauss
    jitter = lambda value: value * (1 + noise(0, NOISE))  # noqa: E731
    return {
        "echo_amplitude": round(max(0.0, jitter(amplitude)), 6),
        "round_trip_us": round(max(0.0, jitter(travel_us)) if present else 0.0, 6),
        "attenuation_db": round(max(0.0, jitter(attenuation_db)), 6),
    }


def estimate(features: dict, *, material: str) -> dict:
    """Recover what can honestly be recovered from those features.

    Returns a layer classification and, where the signal supports one, a
    thickness with an interval. Where it does not, the estimate says so rather
    than returning a number nobody should use.
    """
    if material not in WALL_IMPEDANCE_MRAYL:
        raise ValueError(f"Unknown wall material: {material}")
    for key in ("echo_amplitude", "round_trip_us", "attenuation_db"):
        value = features.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Feature {key} must be a non-negative finite number")

    wall = WALL_IMPEDANCE_MRAYL[material]
    water_amplitude = abs(reflection(wall, MEDIA["water"]["impedance_mrayl"]))
    scale_amplitude = abs(reflection(wall, MEDIA["scale"]["impedance_mrayl"]))

    # A hard deposit changes the boundary a great deal; a water-rich film
    # barely changes it at all, which is the whole difficulty.
    separation = abs(water_amplitude - scale_amplitude)
    towards_hard = abs(features["echo_amplitude"] - scale_amplitude) < separation * 0.25
    layer = "hard" if towards_hard else "undetermined"

    travel = features["round_trip_us"]
    if travel <= 0:
        return {
            "layer": layer if towards_hard else "undetermined",
            "film_thickness_um": None,
            "reason": (
                "No resolvable return from inside the wall echo. A layer thinner than the "
                f"assumed {RESOLUTION_UM:.0f} um floor would look the same as a clean wall."
            ),
            "assumptions": ASSUMPTIONS,
        }

    speed = MEDIA["scale" if towards_hard else "biofilm"]["speed_ms"]
    thickness = travel * 1e-6 * speed / 2 * 1e6
    # The interval carries the feature noise and, for a soft layer, the fact
    # that the speed itself is an assumption rather than a measurement.
    spread = NOISE + (0.0 if towards_hard else 0.12)
    low, high = thickness * (1 - spread * 2), thickness * (1 + spread * 2)
    if thickness < RESOLUTION_UM:
        return {
            "layer": "undetermined",
            "film_thickness_um": None,
            "reason": (
                f"Implied thickness is under the assumed {RESOLUTION_UM:.0f} um resolution "
                "floor, so it is not separated from the wall echo."
            ),
            "assumptions": ASSUMPTIONS,
        }
    if not towards_hard:
        layer = "soft"
    return {
        "layer": layer,
        "film_thickness_um": round(thickness, 1),
        "interval_um": [round(max(0.0, low), 1), round(high, 1)],
        "reason": (
            "Thickness from the round trip through the layer, at an assumed speed of sound. "
            "A soft layer and water differ little acoustically, so the interval is wide."
        ),
        "assumptions": ASSUMPTIONS,
    }


def survey(loop: dict, truth: dict, *, seed: int | None = None) -> list[dict]:
    """Run the forward model and the estimate over every section of a loop.

    `truth` maps a section id to {"layer": ..., "thickness_um": ...}. It is the
    simulation's input, never an observation, and it is recorded alongside the
    result so nobody can mistake one for the other.
    """
    observations = []
    for index, section in enumerate(loop["section"]):
        state = truth.get(section["id"], {"layer": "none", "thickness_um": 0.0})
        features = forward(
            material=section["material"],
            layer=state.get("layer", "none"),
            thickness_um=float(state.get("thickness_um", 0.0)),
            seed=None if seed is None else seed + index,
        )
        observations.append(
            {
                "section_id": section["id"],
                "features": features,
                "estimate": estimate(features, material=section["material"]),
                "simulated_truth": {
                    "layer": state.get("layer", "none"),
                    "thickness_um": float(state.get("thickness_um", 0.0)),
                    "note": (
                        "The simulation's input, kept so the estimate can be checked against it."
                    ),
                },
            }
        )
    return observations
