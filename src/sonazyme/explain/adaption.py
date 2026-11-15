"""Run-grounded narrative generation through an Adaption inference stack."""

from __future__ import annotations

import json
import os
import re
from typing import Protocol

from sonazyme.core.folding import comparison_settings


class EvidenceStore(Protocol):
    """The artefact read operation required by evidence extraction."""

    def read(self, ref: dict) -> bytes:
        """Read a verified artefact."""
        ...

INSTRUCTIONS = """\
Write a structured report using only the supplied run evidence. Select exactly
one of the supplied folded candidates as a preliminary model choice. This is
not a validated ranking or experimental result. Do not calculate or invent
scores, measurements, citations, training examples, or experimental claims.
Only candidates with a rejected integrity verdict are excluded; never present
an unchecked candidate as having passed that check.
Training records were not supplied. Do not mention or claim access to training
data or FireProtDB. Only compare a prediction with a supplied measurement when
their metric name and unit match. The run has no structured assay-condition
fields, so do not claim comparable experimental conditions. If there is no
comparable measurement, say so plainly. Do not include numeric values in
generated prose; the application displays recorded values separately.
Return only JSON with this shape:
{
  "schema_version": 1,
  "kind": "stability-writeup",
  "summary": "string",
  "summary_citations": ["entry id"],
  "selected_candidate": {
    "code": "candidate code",
    "rationale": "string",
    "citations": ["entry id"]
  },
  "measured_comparisons": [
    {"text": "string", "citations": ["entry id"]}
  ],
  "limitations": ["string"]
}
The selected candidate must be exactly one supplied code and cite its own fold
entry. Every comparison must cite supplied measured evidence. Do not treat
predicted values as measurements or as a validated result.
"""


class AdaptionExplainer:
    """Generate a structured write-up from explicit run evidence."""

    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        client: object | None = None,
    ) -> None:
        """Create an explainer using the Adaption key from the environment."""
        key = api_key if api_key is not None else os.environ.get("ADAPTION_API_KEY")
        if not key or not key.strip():
            raise RuntimeError("Set ADAPTION_API_KEY in the server environment.")
        if not model or not model.strip():
            raise ValueError("An Adaption inference model or stack id is required.")
        self.model = model.strip()
        if client is None:
            try:
                from adaption import Adaption
            except ImportError as error:
                raise RuntimeError(
                    "Install the Adaption SDK with "
                    '`pip install ".[api]"` to use model explanations.'
                ) from error
            client = Adaption(api_key=key.strip())
        self._client = client

    def writeup(self, evidence: dict) -> dict:
        """Return validated JSON whose citations refer only to supplied evidence."""
        _validate_evidence(evidence)
        response = self._client.responses.create(
            model=self.model,
            instructions=INSTRUCTIONS,
            input=json.dumps(evidence, allow_nan=False),
            temperature=0,
            max_output_tokens=2500,
        )
        output = getattr(response, "output_text", None)
        if not isinstance(output, str) or not output.strip():
            raise ValueError("Adaption returned no structured explanation.")
        try:
            record = json.loads(output)
        except json.JSONDecodeError as error:
            raise ValueError("Adaption did not return valid structured JSON.") from error
        return _validate_writeup(record, evidence)


def build_evidence(store: EvidenceStore, manifest: dict) -> dict:
    """Extract folded candidates and measured records from a run."""
    entries = manifest["entries"]
    successful_folds = [
        entry
        for entry in entries
        if entry["stage"] == "fold" and entry["status"] == "succeeded"
    ]
    fold_data = []
    baselines = {}
    for entry in successful_folds:
        record = _read_first_artefact(store, entry)
        if record.get("kind") == "fold":
            sequence = record.get("sequence")
            if not isinstance(sequence, str):
                raise ValueError(f"Fold entry {entry['id']} has no recorded sequence.")
            residues = {position: aa for position, aa in enumerate(sequence, start=1)}
            settings = record.get("settings")
            if not isinstance(settings, dict):
                raise ValueError(f"Fold entry {entry['id']} has no recorded settings.")
            group = (
                "fold",
                record.get("chassis_id"),
                json.dumps(record.get("producer"), sort_keys=True),
                json.dumps(comparison_settings(settings), sort_keys=True),
            )
            role = record.get("role")
            if role not in {"baseline", "variant"}:
                raise ValueError(f"Fold entry {entry['id']} has an unsupported fold role.")
            subject_id = record.get("subject_id")
        else:
            residues = _residues_by_position(record)
            explicit_changed = record.get(
                "changed", entry["parameters"].get("changed", [])
            )
            if not isinstance(explicit_changed, list) or any(
                type(position) is not int for position in explicit_changed
            ):
                raise ValueError(f"Fold entry {entry['id']} has invalid changed positions.")
            role = "variant" if explicit_changed else "baseline"
            group = (
                "imported",
                json.dumps(record.get("producer", entry.get("producer")), sort_keys=True),
                json.dumps(record.get("source_note"), sort_keys=True),
            )
            subject_id = record.get("subject_id") or record.get("id")
        item = {
            "entry": entry,
            "record": record,
            "residues": residues,
            "group": group,
            "role": role,
            "subject_id": subject_id,
        }
        fold_data.append(item)
        if role == "baseline":
            baselines.setdefault(group, []).append(item)

    candidates = []
    citations = []
    integrity_by_fold = {}
    for entry in entries:
        if (
            entry["stage"] == "score"
            and entry["parameters"].get("role") == "integrity"
            and len(entry["inputs"]) == 3
        ):
            integrity_by_fold[entry["inputs"][-1]] = entry
    for item in fold_data:
        entry = item["entry"]
        if item["role"] != "variant":
            continue
        matching_baselines = baselines.get(item["group"], [])
        if len(matching_baselines) != 1:
            raise ValueError(
                f"Fold entry {entry['id']} needs one matching baseline fold; "
                f"found {len(matching_baselines)}."
            )
        baseline_residues = matching_baselines[0]["residues"]
        variant_residues = item["residues"]
        if baseline_residues.keys() != variant_residues.keys():
            raise ValueError(f"Fold entry {entry['id']} does not match its baseline positions.")
        changed = [
            position
            for position in baseline_residues
            if baseline_residues[position] != variant_residues[position]
        ]
        explicit_changed = item["record"].get(
            "changed", entry["parameters"].get("changed")
        )
        if explicit_changed is not None and (
            not isinstance(explicit_changed, list)
            or any(type(position) is not int for position in explicit_changed)
            or sorted(explicit_changed) != sorted(changed)
        ):
            raise ValueError(f"Fold entry {entry['id']} changed positions disagree with sequence.")
        if not changed:
            raise ValueError(f"Fold entry {entry['id']} has no changed sequence residues.")
        integrity = integrity_by_fold.get(entry["id"])
        if integrity and integrity["status"] == "rejected":
            continue
        mutations = [
            f"{baseline_residues[position]}{position}{variant_residues[position]}"
            for position in changed
        ]
        code = ",".join(mutations)
        if item["subject_id"]:
            code = f"{item['subject_id']}:{code}"
        candidates.append(
            {
                "code": code,
                "subject_id": item["subject_id"],
                "chassis_id": item["record"].get("chassis_id"),
                "mutations": mutations,
                "metrics": entry["metrics"],
                "citation": entry["id"],
                "integrity_status": (
                    "passed"
                    if integrity and integrity["status"] == "succeeded"
                    else "check_failed"
                    if integrity and integrity["status"] == "failed"
                    else "not_checked"
                ),
                "integrity_citation": integrity["id"] if integrity else None,
            }
        )
        citations.append(entry["id"])
        if integrity:
            citations.append(integrity["id"])
    measured = []
    for entry in entries:
        measurements = [
            metric for metric in entry["metrics"] if metric["basis"] == "measurement"
        ]
        if measurements:
            measured.append({"entry_id": entry["id"], "metrics": measurements})
            citations.append(entry["id"])
    return {
        "run_id": manifest["run_id"],
        "candidate_codes": [candidate["code"] for candidate in candidates],
        "candidates": candidates,
        "measured_comparators": measured,
        "training_data": {
            "status": "unavailable",
            "records": [],
        },
        "rank_entry_ids": [
            entry["id"]
            for entry in entries
            if entry["stage"] == "rank" and entry["status"] == "succeeded"
        ],
        "citation_entry_ids": sorted(set(citations)),
    }


def _read_first_artefact(store: EvidenceStore, entry: dict) -> dict:
    if not entry["artefacts"]:
        raise ValueError(f"Fold entry {entry['id']} has no structure artefact.")
    record = json.loads(store.read(entry["artefacts"][0]))
    if not isinstance(record, dict):
        raise ValueError(f"Fold entry {entry['id']} structure artefact is not an object.")
    return record


def _residues_by_position(record: dict) -> dict[int, str]:
    sequence = record.get("sequence")
    points = record.get("points")
    if (
        not isinstance(sequence, str)
        or not isinstance(points, list)
        or len(points) != len(sequence)
    ):
        raise ValueError("A folded structure needs matching sequence and residue positions.")
    residues = {}
    for amino_acid, point in zip(sequence, points, strict=True):
        position = point.get("position") if isinstance(point, dict) else None
        if type(position) is not int or position in residues:
            raise ValueError("A folded structure has invalid or duplicate residue positions.")
        residues[position] = amino_acid
    return residues


def _validate_evidence(evidence: dict) -> None:
    if not isinstance(evidence, dict):
        raise ValueError("Adaption evidence must be an object.")
    candidates = evidence.get("candidates")
    citation_ids = evidence.get("citation_entry_ids")
    if not isinstance(candidates, list) or not isinstance(citation_ids, list):
        raise ValueError("Adaption evidence requires candidates and citation entry ids.")
    if not candidates:
        raise ValueError("Adaption selection requires at least one folded candidate.")
    if any(
        not isinstance(candidate, dict)
        or not isinstance(candidate.get("code"), str)
        or not candidate["code"]
        or not isinstance(candidate.get("citation"), str)
        or candidate.get("integrity_status")
        not in {"passed", "check_failed", "not_checked"}
        or (
            candidate.get("integrity_citation") is not None
            and not isinstance(candidate.get("integrity_citation"), str)
        )
        for candidate in candidates
    ):
        raise ValueError("Every Adaption candidate requires a code and citation.")
    if any(not isinstance(citation, str) for citation in citation_ids):
        raise ValueError("Adaption citation entry ids must be strings.")
    codes = [candidate["code"] for candidate in candidates]
    if len(set(codes)) != len(codes):
        raise ValueError("Adaption candidate codes must be unique.")
    if evidence.get("candidate_codes") != codes:
        raise ValueError("Adaption candidate codes do not match the candidate evidence.")
    if not set(candidate["citation"] for candidate in candidates).issubset(citation_ids):
        raise ValueError("Candidate citations must be included in the evidence citation list.")
    if any(
        candidate["integrity_citation"] is not None
        and candidate["integrity_citation"] not in citation_ids
        for candidate in candidates
    ):
        raise ValueError("Integrity checks must cite a supplied run entry.")
    if any(
        candidate["integrity_status"] == "passed"
        and not candidate["integrity_citation"]
        for candidate in candidates
    ):
        raise ValueError("Passing integrity checks require a run-entry citation.")
    if evidence.get("training_data") != {"status": "unavailable", "records": []}:
        raise ValueError("Adaption training data must be explicitly supplied before comparison.")


def _validate_writeup(record: object, evidence: dict) -> dict:
    if not isinstance(record, dict) or set(record) != {
        "schema_version",
        "kind",
        "summary",
        "summary_citations",
        "selected_candidate",
        "measured_comparisons",
        "limitations",
    }:
        raise ValueError("Adaption returned an unsupported stability write-up shape.")
    if (
        type(record["schema_version"]) is not int
        or record["schema_version"] != 1
        or record["kind"] != "stability-writeup"
    ):
        raise ValueError("Adaption returned an unsupported stability write-up version.")
    if not isinstance(record["summary"], str) or not record["summary"].strip():
        raise ValueError("Adaption write-up requires a summary.")
    citation_ids = set(evidence["citation_entry_ids"])
    _validate_citations(record["summary_citations"], citation_ids)
    candidate_citations = {
        candidate["code"]: candidate["citation"] for candidate in evidence["candidates"]
    }
    selected = record["selected_candidate"]
    if not isinstance(selected, dict) or set(selected) != {"code", "rationale", "citations"}:
        raise ValueError("Adaption must return exactly one selected candidate.")
    selected_code = selected["code"]
    if not isinstance(selected_code, str) or selected_code not in candidate_citations:
        raise ValueError("Adaption selected a candidate that was not supplied.")
    if not isinstance(selected["rationale"], str) or not selected["rationale"].strip():
        raise ValueError("Adaption selection requires a rationale.")
    _validate_citations(selected["citations"], citation_ids)
    if candidate_citations[selected_code] not in selected["citations"]:
        raise ValueError("Adaption selection must cite the selected candidate's fold entry.")
    if not isinstance(record["limitations"], list) or any(
        not isinstance(item, str) for item in record["limitations"]
    ):
        raise ValueError("Adaption write-up limitations must be strings.")
    comparisons = record["measured_comparisons"]
    if not isinstance(comparisons, list):
        raise ValueError("Adaption measured comparisons must be a list.")
    measured_ids = {
        item["entry_id"] for item in evidence["measured_comparators"]
    }
    for comparison in comparisons:
        if not isinstance(comparison, dict) or set(comparison) != {"text", "citations"}:
            raise ValueError("Adaption returned an invalid measured comparison.")
        if not isinstance(comparison["text"], str) or not comparison["text"].strip():
            raise ValueError("Adaption measured comparisons require text.")
        _validate_citations(comparison["citations"], measured_ids)
    generated_text = [
        record["summary"],
        selected["rationale"],
        *record["limitations"],
        *(comparison["text"] for comparison in comparisons),
    ]
    if any(
        re.search(r"\b(?:training|trained|train|FireProtDB)\b", text, re.IGNORECASE)
        for text in generated_text
    ):
        raise ValueError("Adaption must not claim access to absent training data.")
    if any(any(character.isdigit() for character in text) for text in generated_text):
        raise ValueError("Adaption must not add numeric claims to generated prose.")
    return record


def _validate_citations(citations: object, allowed: set[str]) -> None:
    if (
        not isinstance(citations, list)
        or not citations
        or any(not isinstance(citation, str) or citation not in allowed for citation in citations)
    ):
        raise ValueError("Adaption cited evidence that was not supplied.")
