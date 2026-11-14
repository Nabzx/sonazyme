"""Read and export verified run snapshots without running scientific code."""

from __future__ import annotations

import base64
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from sonazyme.core.manifest import validate
from sonazyme.runs.store import RunStore

MAX_EXPORT_BYTES = 32 * 1024 * 1024


def references(manifest: dict) -> dict[str, dict]:
    """Collect only directly referenced artefacts, including the original target."""
    refs = [manifest["target"], *(r for e in manifest["entries"] for r in e["artefacts"])]
    return {ref["sha256"]: ref for ref in refs}


def modified_at(path: Path) -> str:
    """Describe filesystem metadata, never infer a model execution date."""
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()


def export_snapshot(directory: Path) -> dict:
    """Package the original manifest and exact referenced bytes for offline reading."""
    store = RunStore(directory)
    manifest = store.load()
    refs = references(manifest)
    if sum(ref["size_bytes"] for ref in refs.values()) > MAX_EXPORT_BYTES:
        raise ValueError("Snapshot exceeds the local export size limit")
    return {
        "schema_version": 1,
        "kind": "sonazyme-snapshot",
        "manifest": manifest,
        "metadata": {
            "file_modified_at": modified_at(store.manifest_path),
            "exported_at": datetime.now(UTC).isoformat(),
            "notice": "Saved artefacts only. Snapshot metadata is not a model run date.",
        },
        "artefacts": {
            digest: base64.b64encode(store.read(ref)).decode("ascii")
            for digest, ref in refs.items()
        },
    }


def restore_snapshot(snapshot: dict, directory: Path) -> None:
    """Verify an exported snapshot and publish it into a new run directory only."""
    if not isinstance(snapshot, dict) or set(snapshot) != {
        "schema_version",
        "kind",
        "manifest",
        "metadata",
        "artefacts",
    }:
        raise ValueError("Invalid snapshot fields")
    if (
        type(snapshot["schema_version"]) is not int
        or snapshot["schema_version"] != 1
        or snapshot["kind"] != "sonazyme-snapshot"
    ):
        raise ValueError("Unsupported snapshot format")
    manifest = snapshot["manifest"]
    validate(manifest)
    refs = references(manifest)
    encoded = snapshot["artefacts"]
    if not isinstance(encoded, dict) or set(encoded) != set(refs):
        raise ValueError("Snapshot must contain exactly its referenced artefacts")
    if sum(ref["size_bytes"] for ref in refs.values()) > MAX_EXPORT_BYTES:
        raise ValueError("Snapshot exceeds the local restore size limit")
    decoded = {}
    for digest, ref in refs.items():
        value = encoded[digest]
        if not isinstance(value, str) or len(value) > ((ref["size_bytes"] + 2) // 3) * 4:
            raise ValueError("Invalid base64 artefact length")
        decoded[digest] = base64.b64decode(value, validate=True)
        if len(decoded[digest]) != ref["size_bytes"]:
            raise ValueError("Snapshot artefact size mismatch")
    directory = directory.absolute()
    if directory.exists() or directory.is_symlink():
        raise FileExistsError("Restore requires a new run directory")
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=directory.parent, prefix=".restore-") as temporary:
        store = RunStore(Path(temporary) / "run")
        for digest, data in decoded.items():
            if store.put(data) != refs[digest]:
                raise ValueError("Snapshot artefact digest mismatch")
        store.save(manifest)
        # Verify the complete chain, including duplicate references, before publication.
        store.load()
        if directory.exists() or directory.is_symlink():
            raise FileExistsError("Restore destination already exists")
        os.rename(store.directory, directory)


def read_snapshot(path: Path) -> dict:
    """Bound a local export file before parsing its JSON."""
    if path.stat().st_size > MAX_EXPORT_BYTES * 2:
        raise ValueError("Snapshot file exceeds the local input size limit")
    return json.loads(path.read_text(encoding="utf-8"))
