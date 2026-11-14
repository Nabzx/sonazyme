"""Load source-bearing chassis records without fetching mutable remote data."""

from __future__ import annotations

import json
from pathlib import Path

from sonazyme.core.records import validate_chassis


def parse(data: bytes) -> dict:
    """Validate a JSON chassis record, including its residue numbering map."""
    record = json.loads(data)
    validate_chassis(record)
    return record


def load(path: Path) -> dict:
    """Load a registry record from a caller-selected file under targets."""
    return parse(path.read_bytes())
