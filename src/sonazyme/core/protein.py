"""Canonical protein sequences and strict single-model PDB coordinate reading."""

from __future__ import annotations

import math

AMINO_ACIDS = dict(
    zip(
        ("ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL").split(),
        "ARNDCQEGHILKMFPSTWYV",
        strict=True,
    )
)


def validate_sequence(sequence: str) -> None:
    """Require an explicit canonical sequence, with no gaps or ambiguous residues."""
    if not isinstance(sequence, str) or not sequence or set(sequence) - set(AMINO_ACIDS.values()):
        raise ValueError("A non-empty canonical amino-acid sequence is required")


def read_pdb(data: bytes, sequence: str, chain: str = "A") -> dict:
    """Read a complete protein chain with unique atoms and predicted confidence."""
    validate_sequence(sequence)
    atoms = {}
    confidence = {}
    models = 0
    residues = {}
    for line in data.decode("ascii").splitlines():
        if line.startswith("MODEL "):
            models += 1
            if models > 1:
                raise ValueError("Multiple PDB models are not supported")
        if not line.startswith("ATOM  ") or line[21:22] != chain:
            continue
        if len(line) < 66 or line[16] != " " or line[26] != " ":
            raise ValueError("Alternate locations or insertion codes are not supported")
        position = int(line[22:26])
        residue = AMINO_ACIDS.get(line[17:20])
        if not 1 <= position <= len(sequence) or sequence[position - 1] != residue:
            raise ValueError("PDB residue does not match the recorded input sequence")
        atom = line[12:16].strip()
        key = (position, atom)
        if not atom or key in atoms:
            raise ValueError("Duplicate or empty PDB atom")
        xyz = tuple(float(line[start : start + 8]) for start in (30, 38, 46))
        plddt = float(line[60:66]) / 100
        if not all(math.isfinite(v) for v in (*xyz, plddt)) or not 0 <= plddt <= 1:
            raise ValueError("Invalid PDB coordinates or predicted confidence")
        atoms[key] = xyz
        if position in confidence and confidence[position] != plddt:
            raise ValueError("Inconsistent per-residue predicted confidence")
        confidence[position] = plddt
        residues[position] = residue
    if set(residues) != set(range(1, len(sequence) + 1)):
        raise ValueError("PDB protein chain is incomplete")
    if any((position, "CA") not in atoms for position in residues):
        raise ValueError("PDB protein residue is missing its alpha carbon")
    return {"atoms": atoms, "confidence": confidence}
