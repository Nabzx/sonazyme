"""Loop maps and readings: where a measurement was taken, and on what basis.

A loop is the circuit being treated, divided into sections. A reading is what
an instrument, or the forward model standing in for one, reported about one
section at one time. The basis of a reading is part of the record: a simulated
reading says so here, in the manifest, and on the screen (ADR-0013).
"""

from __future__ import annotations

import math
import tomllib
from copy import deepcopy

MATERIALS = ("copper", "aluminium", "stainless-steel", "carbon-steel", "polymer")
BASES = ("simulation", "instrument", "literature")


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _fail(where: str, message: str) -> None:
    raise ValueError(f"{where}: {message}")


def validate_loop(record: dict) -> dict:
    """Check a loop map: identified sections, each with material and geometry."""
    if record.get("schema_version") != 1 or record.get("kind") != "loop":
        raise ValueError("Unsupported loop record")
    if not all(_text(record.get(key)) for key in ("id", "name", "basis_note")):
        raise ValueError("A loop needs an id, a name and a note on where it came from")
    sections = record.get("section")
    if not isinstance(sections, list) or not sections:
        raise ValueError("A loop needs at least one section")
    seen = set()
    for index, section in enumerate(sections):
        where = f"section[{index}]"
        if not _text(section.get("id")) or section["id"] in seen:
            _fail(where, "a unique section id is required")
        seen.add(section["id"])
        if section.get("material") not in MATERIALS:
            _fail(where, f"material must be one of {', '.join(MATERIALS)}")
        for key in ("bore_mm", "wall_mm", "length_m"):
            if not _number(section.get(key)) or section[key] <= 0:
                _fail(where, f"{key} must be a positive number")
        if not _text(section.get("role")):
            _fail(where, "a role is required, for example cold plate or return header")
        if section.get("sensor") not in (True, False):
            _fail(where, "say explicitly whether a sensor sits on this section")
    return deepcopy(record)


def parse_loop(data: bytes) -> dict:
    """Read a loop map from TOML, refusing anything the schema does not cover."""
    try:
        record = tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Loop file is not readable TOML: {error}") from None
    return validate_loop(record)


def validate_reading(record: dict) -> dict:
    """Check a reading: one section, one basis, features, and an estimate with an interval."""
    if record.get("schema_version") != 1 or record.get("kind") != "reading":
        raise ValueError("Unsupported reading record")
    if record.get("basis") not in BASES:
        raise ValueError(f"A reading basis must be one of {', '.join(BASES)}")
    if not _text(record.get("basis_reason")):
        raise ValueError("A reading must say why it has that basis")
    if not _text(record.get("loop_id")) or not _text(record.get("instrument")):
        raise ValueError("A reading names its loop and the instrument or model behind it")
    observations = record.get("observation")
    if not isinstance(observations, list) or not observations:
        raise ValueError("A reading needs at least one observation")
    for index, observation in enumerate(observations):
        where = f"observation[{index}]"
        if not _text(observation.get("section_id")):
            _fail(where, "every observation names its section")
        features = observation.get("features")
        if not isinstance(features, dict) or not features:
            _fail(where, "signal features are required")
        for name, value in features.items():
            if not _text(name) or not _number(value):
                _fail(where, f"feature {name} must be a finite number")
        estimate = observation.get("estimate")
        if not isinstance(estimate, dict):
            _fail(where, "an estimate is required, even when it is uninformative")
        thickness = estimate.get("film_thickness_um")
        if thickness is not None:
            interval = estimate.get("interval_um")
            if not _number(thickness) or thickness < 0:
                _fail(where, "a thickness estimate must be a non-negative number")
            if (
                not isinstance(interval, list)
                or len(interval) != 2
                or not all(_number(bound) for bound in interval)
                or not interval[0] <= thickness <= interval[1]
            ):
                _fail(where, "a thickness estimate requires an interval containing it")
        elif not _text(estimate.get("reason")):
            _fail(where, "an estimate with no value must say why")
        if estimate.get("layer") not in ("soft", "hard", "undetermined"):
            _fail(where, "a layer is soft, hard or undetermined, never guessed")
    return deepcopy(record)
