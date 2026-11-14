"""Single-writer persistence for manifests and verified artefacts (ADR-0007)."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from sonazyme.core.manifest import load, validate, validate_reference


def _replace(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".write-")
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class RunStore:
    """Keep a run's target and stage artefacts under its own directory."""

    def __init__(self, directory: Path) -> None:
        """Use a caller-selected run directory, never a path derived from run id."""
        self.directory = directory.resolve()
        self.manifest_path = self.directory / "manifest.json"

    def _path(self, ref: dict) -> Path:
        validate_reference(ref)
        path = self.directory / ref["path"]
        if not path.resolve().is_relative_to(self.directory):
            raise ValueError("Artefact escapes the run directory")
        return path

    def put(self, data: bytes) -> dict:
        """Store bytes once under their SHA-256 digest and return a reference."""
        if self.manifest_path.exists() and load(self.manifest_path)["status"] == "finished":
            raise ValueError("A finished run cannot receive artefacts")
        digest = hashlib.sha256(data).hexdigest()
        ref = dict(path=f"artefacts/{digest}", sha256=digest, size_bytes=len(data))
        path = self._path(ref)
        if path.exists():
            self.read(ref)
        else:
            _replace(path, data)
        return ref

    def read(self, ref: dict) -> bytes:
        """Verify an artefact before returning it, including during offline replay."""
        data = self._path(ref).read_bytes()
        if len(data) != ref["size_bytes"] or hashlib.sha256(data).hexdigest() != ref["sha256"]:
            raise ValueError(f"Artefact content mismatch: {ref['path']}")
        return data

    def verify(self, manifest: dict) -> None:
        """Check every reference including the original target."""
        validate(manifest)
        self.read(manifest["target"])
        for entry in manifest["entries"]:
            for ref in entry["artefacts"]:
                self.read(ref)

    def save(self, manifest: dict) -> None:
        """Atomically save a valid extension, refusing history edits and truncation."""
        self.verify(manifest)
        if self.manifest_path.exists():
            old = load(self.manifest_path)
            if json.dumps(manifest, sort_keys=True) == json.dumps(old, sort_keys=True):
                return
            if old["status"] == "finished":
                raise ValueError("A finished manifest is immutable")
            for key in ("schema_version", "run_id", "target"):
                if old[key] != manifest[key]:
                    raise ValueError(f"Cannot change {key}")
            if json.dumps(manifest["entries"][: len(old["entries"])], sort_keys=True) != (
                json.dumps(old["entries"], sort_keys=True)
            ):
                raise ValueError("Cannot rewrite or truncate manifest history")
        data = (json.dumps(manifest, indent=2, allow_nan=False) + "\n").encode()
        _replace(self.manifest_path, data)

    def load(self) -> dict:
        """Load a run and verify its complete artefact chain without network calls."""
        manifest = load(self.manifest_path)
        self.verify(manifest)
        return manifest
