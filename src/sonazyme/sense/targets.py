"""Parse evidence-bearing target files without supplying biological defaults."""

from __future__ import annotations

import math
import re
import tomllib
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path


def _fail(path: str, message: str) -> None:
    raise ValueError(f"{path}: {message}")


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _number(value: object) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _strings(value: object) -> bool:
    return isinstance(value, list) and all(_text(item) for item in value)


def _range(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(_number(item) for item in value)
        and value[0] <= value[1]
    )


def _fields(value: object, names: set[str], path: str) -> None:
    if not isinstance(value, dict) or set(value) != names:
        _fail(path, f"expected fields {', '.join(sorted(names))}")


def _evidence(record: object, path: str, check: Callable[[object], bool]) -> None:
    if not isinstance(record, dict) or "basis" not in record:
        _fail(path, "an evidence record with basis is required")
    if set(record) - {"basis", "value", "source", "reason"}:
        _fail(path, "unknown evidence fields")
    basis = record["basis"]
    if basis not in ("literature", "guidance", "measurement", "assumption", "unknown"):
        _fail(path, "unknown evidence basis")
    for key in ("source", "reason"):
        if key in record and not _text(record[key]):
            _fail(path, f"{key} must be non-empty text")
    if basis == "unknown":
        if "value" in record or not _text(record.get("reason")):
            _fail(path, "unknown requires a reason and forbids a value")
        return
    if basis == "assumption":
        if not _text(record.get("reason")):
            _fail(path, "assumption requires a reason")
    elif not _text(record.get("source")):
        _fail(path, f"{basis} requires a source")
    if "value" not in record or not check(record["value"]):
        _fail(path, "missing or invalid value")


def validate(target: dict) -> None:
    """Check structural types and evidence markings with field-specific errors."""
    _fields(target, {"schema_version", "target", "community", "anchor", "envelope"}, "target")
    if type(target["schema_version"]) is not int or target["schema_version"] != 1:
        _fail("schema_version", "unsupported target schema version")
    metadata = target["target"]
    _fields(metadata, {"id", "name", "summary", "loop"}, "target")
    for field in ("id", "name", "summary"):
        if not _text(metadata[field]):
            _fail(f"target.{field}", "non-empty text is required")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", metadata["id"]):
        _fail("target.id", "use lowercase letters, digits and separating hyphens")
    _evidence(
        metadata["loop"],
        "target.loop",
        lambda value: (
            value
            in (
                "direct-to-chip",
                "cooling-tower",
                "heat-exchanger",
                "marine",
                "spacecraft",
                "other",
            )
        ),
    )
    _evidence(target["community"], "community", lambda value: _strings(value) and bool(value))
    anchors = target["anchor"]
    if not isinstance(anchors, list) or not anchors:
        _fail("anchor", "at least one anchor is required")
    for index, anchor in enumerate(anchors):
        path = f"anchor[{index}]"
        _fields(anchor, {"component", "kind", "bond", "enzyme_family", "share"}, path)
        for field in ("component", "bond", "enzyme_family"):
            _evidence(anchor[field], f"{path}.{field}", _text)
        _evidence(
            anchor["kind"],
            f"{path}.kind",
            lambda value: value in ("polysaccharide", "protein", "extracellular-dna"),
        )
        _evidence(
            anchor["share"], f"{path}.share", lambda value: _number(value) and 0 <= value <= 1
        )
    envelope = target["envelope"]
    _fields(envelope, {"temperature_c", "ph", "chemistry", "residence_time_s"}, "envelope")
    for field in ("temperature_c", "ph"):
        _evidence(envelope[field], f"envelope.{field}", _range)
    _evidence(envelope["chemistry"], "envelope.chemistry", _strings)
    _evidence(
        envelope["residence_time_s"],
        "envelope.residence_time_s",
        lambda value: _number(value) and value >= 0,
    )


def parse(data: bytes) -> dict:
    """Parse UTF-8 TOML, preserving unknowns and all source and assumption fields."""
    target = tomllib.loads(data.decode("utf-8"))
    validate(target)
    return deepcopy(target)


def load(path: Path) -> dict:
    """Read a target from disk using the same validation as the sense stage."""
    return parse(path.read_bytes())
