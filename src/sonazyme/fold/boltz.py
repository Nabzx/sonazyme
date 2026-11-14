"""Execute the official Boltz CLI with explicit model and input identity."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


class LocalBoltz:
    """Use an externally provisioned Boltz Python environment and checkpoint."""

    def __init__(self, python: Path, checkpoint: Path, cache: Path, timeout_s: int = 3600):
        """Select compute resources without installing or downloading them here."""
        self.python = python.resolve()
        self.checkpoint = checkpoint.resolve()
        self.cache = cache.resolve()
        self.timeout_s = timeout_s

    def predict(self, request: dict, settings: dict, msa: bytes | None) -> tuple[bytes, bytes]:
        """Return PDB and confidence bytes only after checking model identity."""
        digest = hashlib.sha256()
        with self.checkpoint.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != settings["checkpoint_sha256"]:
            raise ValueError("Boltz checkpoint digest mismatch")
        version = subprocess.run(
            [
                str(self.python),
                "-c",
                "from importlib.metadata import version; print(version('boltz'))",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()
        if version != settings["package_version"]:
            raise ValueError("Installed Boltz version does not match request")
        with tempfile.TemporaryDirectory(prefix="sonazyme-boltz-") as directory:
            root = Path(directory)
            request = json.loads(json.dumps(request))
            if msa is not None:
                alignment = root / "protein.a3m"
                alignment.write_bytes(msa)
                request["sequences"][0]["protein"]["msa"] = str(alignment)
            input_path = root / "request.yaml"
            input_path.write_text(json.dumps(request), encoding="utf-8")
            output = root / "output"
            command = [
                str(self.python),
                "-m",
                "boltz.main",
                "predict",
                str(input_path),
                "--model",
                "boltz2",
                "--checkpoint",
                str(self.checkpoint),
                "--out_dir",
                str(output),
                "--cache",
                str(self.cache),
                "--output_format",
                "pdb",
                "--devices",
                "1",
                "--diffusion_samples",
                "1",
                "--num_workers",
                "0",
                "--override",
            ]
            for flag in ("seed", "accelerator", "recycling_steps", "sampling_steps"):
                command.extend([f"--{flag}", str(settings[flag])])
            subprocess.run(command, check=True, capture_output=True, timeout=self.timeout_s)
            prediction = output / "boltz_results_request" / "predictions" / "request"
            return (
                (prediction / "request_model_0.pdb").read_bytes(),
                (prediction / "confidence_request_model_0.json").read_bytes(),
            )
