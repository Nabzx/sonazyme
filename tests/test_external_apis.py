import json
from types import SimpleNamespace

import pytest

from sonazyme.api import tamarind
from sonazyme.core.manifest import create
from sonazyme.design.tamarind import submit_design_job
from sonazyme.explain.adaption import AdaptionExplainer, build_evidence
from sonazyme.explain.retrieval import Index
from sonazyme.runs.store import RunStore


class FakeResponse:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def getcode(self):
        return self.status

    def read(self):
        return self.body


class FakeDesignClient:
    def __init__(self, validation=None):
        self.validated = None
        self.submitted = None
        self.validation = validation or {"valid": True, "normalized": None}

    def list_tools(self):
        return [
            {
                "name": "live-design-tool",
                "settings": [
                    {"name": "sequence", "required": True},
                    {"name": "count", "default": 4},
                ],
            }
        ]

    def validate_job(self, tool, settings, *, job_name):
        self.validated = (tool, settings, job_name)
        result = dict(self.validation)
        if result.get("normalized") is None:
            result["normalized"] = settings
        return result

    def submit_job(self, job_name, tool, settings):
        self.submitted = (job_name, tool, settings)
        return "submitted"


class FakeAdaptionClient:
    def __init__(self, output):
        self.output = output
        self.request = None
        self.responses = self

    def create(self, **request):
        self.request = request
        return SimpleNamespace(output_text=json.dumps(self.output))


def _evidence():
    return {
        "run_id": "run-1",
        "candidate_codes": ["C2V", "D3Y"],
        "candidates": [
            {
                "code": "C2V",
                "mutations": ["C2V"],
                "metrics": [],
                "citation": "fold-1",
                "integrity_status": "not_checked",
                "integrity_citation": None,
            },
            {
                "code": "D3Y",
                "mutations": ["D3Y"],
                "metrics": [],
                "citation": "fold-2",
                "integrity_status": "passed",
                "integrity_citation": "integrity-2",
            },
        ],
        "measured_comparators": [{"entry_id": "measurement-1", "metrics": []}],
        "training_data": {"status": "unavailable", "records": []},
        "rank_entry_ids": [],
        "citation_entry_ids": ["fold-1", "fold-2", "integrity-2", "measurement-1"],
    }


def _writeup():
    return {
        "schema_version": 1,
        "kind": "stability-writeup",
        "summary": "The run contains two candidates; the selected candidate is listed below.",
        "summary_citations": ["fold-1"],
        "selected_candidate": {
            "code": "C2V",
            "rationale": "Its supplied fold evidence supports this preliminary choice.",
            "citations": ["fold-1"],
        },
        "measured_comparisons": [
            {"text": "A measured comparator is available.", "citations": ["measurement-1"]}
        ],
        "limitations": ["This is not a wet-lab result."],
    }


def test_tamarind_client_requires_the_environment_key(monkeypatch):
    monkeypatch.delenv("TAMARIND_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="TAMARIND_API_KEY"):
        tamarind.TamarindClient()


def test_design_submission_uses_live_schema_and_preflight():
    client = FakeDesignClient()

    result = submit_design_job("run-1", "live-design-tool", {"sequence": "ABC"}, client=client)

    assert result == "submitted"
    assert client.validated == (
        "live-design-tool",
        {"sequence": "ABC", "count": 4},
        "run-1",
    )
    assert client.submitted == (
        "run-1",
        "live-design-tool",
        {"sequence": "ABC", "count": 4},
    )


def test_design_submission_refuses_unknown_tool_settings():
    client = FakeDesignClient()

    with pytest.raises(ValueError, match="Unknown settings"):
        submit_design_job(
            "run-1", "live-design-tool", {"sequence": "ABC", "guess": 1}, client=client
        )

    assert client.submitted is None


def test_design_submission_refuses_missing_required_settings():
    client = FakeDesignClient()

    with pytest.raises(ValueError, match="Missing required settings"):
        submit_design_job("run-1", "live-design-tool", {}, client=client)

    assert client.validated is None
    assert client.submitted is None


def test_design_submission_does_not_submit_failed_preflight():
    client = FakeDesignClient({"valid": False, "error": "settings do not match"})

    with pytest.raises(ValueError, match="settings do not match"):
        submit_design_job("run-1", "live-design-tool", {"sequence": "ABC"}, client=client)

    assert client.validated is not None
    assert client.submitted is None


def test_tamarind_requests_use_header_key_and_result_download_omits_it(monkeypatch):
    monkeypatch.setenv("TAMARIND_API_KEY", "test-secret")
    requests = []

    def fake_urlopen(request, timeout):
        assert timeout == 30
        requests.append(request)
        if request.full_url.endswith("/tools"):
            return FakeResponse(b"[]")
        return FakeResponse(b"archive", status=200)

    monkeypatch.setattr(tamarind, "urlopen", fake_urlopen)
    client = tamarind.TamarindClient()

    assert client.list_tools() == []
    assert requests[0].get_header("X-api-key") == "test-secret"
    assert client.download_result("https://download.example/archive") == b"archive"
    assert requests[1].get_header("X-api-key") is None


def test_tamarind_result_url_handles_preparing_response(monkeypatch):
    monkeypatch.setenv("TAMARIND_API_KEY", "test-secret")

    def fake_urlopen(request, timeout):
        assert request.full_url.endswith("/result")
        assert timeout == 30
        return FakeResponse(b'{"status":"preparing"}', status=202)

    monkeypatch.setattr(
        tamarind,
        "urlopen",
        fake_urlopen,
    )

    assert tamarind.TamarindClient().result_url("run-1") is None


def test_tamarind_result_url_parses_json_encoded_url(monkeypatch):
    monkeypatch.setenv("TAMARIND_API_KEY", "test-secret")
    download_url = "https://download.example/archive"

    def fake_urlopen(request, timeout):
        assert request.full_url.endswith("/result")
        assert timeout == 30
        return FakeResponse(json.dumps(download_url).encode())

    monkeypatch.setattr(
        tamarind,
        "urlopen",
        fake_urlopen,
    )

    assert tamarind.TamarindClient().result_url("run-1") == download_url


def test_adaption_uses_environment_key_and_validates_citations(monkeypatch):
    monkeypatch.setenv("ADAPTION_API_KEY", "test-secret")
    client = FakeAdaptionClient(_writeup())

    result = AdaptionExplainer("stack:scientist", client=client).writeup(_evidence())

    assert result["kind"] == "stability-writeup"
    assert result["selected_candidate"]["code"] == "C2V"
    assert client.request["model"] == "stack:scientist"
    assert json.loads(client.request["input"])["candidate_codes"] == ["C2V", "D3Y"]

    invalid = _writeup()
    invalid["selected_candidate"]["citations"] = ["not-in-run"]
    client.output = invalid
    with pytest.raises(ValueError, match="not supplied"):
        AdaptionExplainer("stack:scientist", client=client).writeup(_evidence())

    invalid = _writeup()
    invalid["selected_candidate"]["code"] = "not-in-run"
    client.output = invalid
    with pytest.raises(ValueError, match="not supplied"):
        AdaptionExplainer("stack:scientist", client=client).writeup(_evidence())

    invalid = _writeup()
    invalid["summary"] = "This result was trained on the same mutation dataset."
    client.output = invalid
    with pytest.raises(ValueError, match="absent training data"):
        AdaptionExplainer("stack:scientist", client=client).writeup(_evidence())

    invalid = _writeup()
    invalid["measured_comparisons"][0]["text"] = (
        "A substitution was measured at +2.1 degrees under comparable conditions."
    )
    client.output = invalid
    with pytest.raises(ValueError, match="numeric claims"):
        AdaptionExplainer("stack:scientist", client=client).writeup(_evidence())


def test_adaption_requires_environment_key(monkeypatch):
    monkeypatch.delenv("ADAPTION_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="ADAPTION_API_KEY"):
        AdaptionExplainer("stack:scientist", client=FakeAdaptionClient(_writeup()))


def test_adaption_evidence_uses_recorded_fold_codes_and_measurements():
    records = {
        "baseline": {
            "sequence": "ACD",
            "points": [{"position": 31}, {"position": 32}, {"position": 33}],
        },
        "variant": {
            "sequence": "AVD",
            "points": [{"position": 31}, {"position": 32}, {"position": 33}],
        },
    }

    class Store:
        def read(self, ref):
            return json.dumps(records[ref["id"]]).encode()

    manifest = {
        "run_id": "run-1",
        "entries": [
            {
                "id": "wild-type",
                "stage": "fold",
                "status": "succeeded",
                "inputs": [],
                "parameters": {"changed": []},
                "artefacts": [{"id": "baseline"}],
                "metrics": [],
            },
            {
                "id": "variant-1",
                "stage": "fold",
                "status": "succeeded",
                "inputs": [],
                "parameters": {"changed": [32]},
                "artefacts": [{"id": "variant"}],
                "metrics": [],
            },
            {
                "id": "variant-rejected",
                "stage": "fold",
                "status": "succeeded",
                "inputs": [],
                "parameters": {"changed": [32]},
                "artefacts": [{"id": "variant"}],
                "metrics": [],
            },
            {
                "id": "integrity-rejected",
                "stage": "score",
                "status": "rejected",
                "parameters": {"role": "integrity"},
                "inputs": ["chassis-1", "wild-type", "variant-rejected"],
                "artefacts": [],
                "metrics": [],
            },
            {
                "id": "measurement-1",
                "stage": "score",
                "status": "succeeded",
                "inputs": [],
                "parameters": {},
                "artefacts": [],
                "metrics": [
                    {
                        "name": "stability",
                        "value": 1.0,
                        "unit": "kcal/mol",
                        "basis": "measurement",
                        "source": "paper",
                    }
                ],
            },
        ],
    }

    evidence = build_evidence(Store(), manifest)

    assert evidence["candidate_codes"] == ["C32V"]
    assert evidence["measured_comparators"][0]["entry_id"] == "measurement-1"
    assert evidence["training_data"] == {"status": "unavailable", "records": []}
    assert evidence["citation_entry_ids"] == ["measurement-1", "variant-1"]


def test_adaption_receives_all_folded_candidates_without_truncation():
    sequence = "ACDEFGHIKLMNP"
    records = {
        "baseline": {
            "sequence": sequence,
            "points": [
                {"position": position} for position in range(1, len(sequence) + 1)
            ],
        }
    }
    entries = [
        {
            "id": "wild-type",
            "stage": "fold",
            "status": "succeeded",
            "inputs": [],
            "parameters": {"changed": []},
            "artefacts": [{"id": "baseline"}],
            "metrics": [],
        }
    ]
    for position in range(1, 12):
        variant_sequence = list(sequence)
        variant_sequence[position - 1] = "A" if sequence[position - 1] != "A" else "C"
        variant_id = f"variant-{position}"
        records[variant_id] = {
            "sequence": "".join(variant_sequence),
            "points": records["baseline"]["points"],
        }
        entries.append(
            {
                "id": variant_id,
                "stage": "fold",
                "status": "succeeded",
                "inputs": [],
                "parameters": {"changed": [position]},
                "artefacts": [{"id": variant_id}],
                "metrics": [],
            }
        )

    class Store:
        def read(self, ref):
            return json.dumps(records[ref["id"]]).encode()

    evidence = build_evidence(Store(), {"run_id": "many-folds", "entries": entries})

    assert len(evidence["candidates"]) == 11
    assert evidence["candidate_codes"][-1] == "M11A"


def test_adaption_pairs_fold_artifacts_with_their_own_chassis_baselines():
    producer = {"name": "Boltz-2", "version": "2.2.1", "kind": "model"}
    settings = {"msa": {"mode": "single"}, "seed": 1}
    records = {
        "baseline-1": {
            "kind": "fold",
            "chassis_id": "chassis-1",
            "producer": producer,
            "settings": settings,
            "role": "baseline",
            "subject_id": "chassis-1",
            "sequence": "ACD",
        },
        "variant-1": {
            "kind": "fold",
            "chassis_id": "chassis-1",
            "producer": producer,
            "settings": settings,
            "role": "variant",
            "subject_id": "chassis-1-v1",
            "sequence": "AVD",
        },
        "baseline-2": {
            "kind": "fold",
            "chassis_id": "chassis-2",
            "producer": producer,
            "settings": settings,
            "role": "baseline",
            "subject_id": "chassis-2",
            "sequence": "GHM",
        },
        "variant-2": {
            "kind": "fold",
            "chassis_id": "chassis-2",
            "producer": producer,
            "settings": settings,
            "role": "variant",
            "subject_id": "chassis-2-v1",
            "sequence": "GAM",
        },
    }

    class Store:
        def read(self, ref):
            return json.dumps(records[ref["id"]]).encode()

    entries = [
        {
            "id": entry_id,
            "stage": "fold",
            "status": "succeeded",
            "inputs": [],
            "parameters": {},
            "artefacts": [{"id": ref}],
            "metrics": [],
        }
        for entry_id, ref in (
            ("baseline-1", "baseline-1"),
            ("variant-1", "variant-1"),
            ("baseline-2", "baseline-2"),
            ("variant-2", "variant-2"),
        )
    ]

    evidence = build_evidence(Store(), {"run_id": "two-chassis", "entries": entries})

    assert evidence["candidate_codes"] == ["chassis-1-v1:C2V", "chassis-2-v1:H2A"]


def test_explain_stage_records_adaption_writeup_and_model_provenance(tmp_path, monkeypatch):
    import sonazyme.explain as explain

    class FakeExplainer:
        def __init__(self, model):
            assert model == "stack:scientist"

        def writeup(self, evidence):
            assert evidence["candidate_codes"] == ["C2V", "D3Y"]
            return _writeup()

    def fake_build(store, manifest):
        assert isinstance(store, RunStore)
        assert manifest["run_id"] == "run-1"
        return Index("run-1", "running")

    def fake_build_evidence(store, manifest):
        assert isinstance(store, RunStore)
        assert manifest["run_id"] == "run-1"
        return _evidence()

    monkeypatch.setattr(explain, "build", fake_build)
    monkeypatch.setattr(explain, "build_evidence", fake_build_evidence)
    monkeypatch.setattr(explain, "AdaptionExplainer", FakeExplainer)
    store = RunStore(tmp_path / "run")
    manifest = create("run-1", store.put(b"target"))

    result = explain.run(
        manifest,
        store=store,
        parameters={"adaption_model": "stack:scientist"},
    )

    entry = result["entries"][-1]
    record = json.loads(store.read(entry["artefacts"][0]))
    assert entry["producer"] == {
        "name": "adaption.responses",
        "version": "stack:scientist",
        "kind": "model",
    }
    assert record["stability_writeup"]["kind"] == "stability-writeup"
    assert record["stability_writeup"]["selected_candidate"]["code"] == "C2V"
    assert record["stability_writeup"]["training_data_comparison"]["status"] == "unavailable"
    assert record["stability_writeup"]["citation_entry_ids"] == [
        "fold-1",
        "fold-2",
        "integrity-2",
        "measurement-1",
    ]
