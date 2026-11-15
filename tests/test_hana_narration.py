"""Keep the recorded speech separate from source notes and check caption timing."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "hana_recorder", ROOT / "tools/synthesia/record_hana.py"
)
recorder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recorder)


def test_only_spoken_script_is_read_not_the_claim_ledger():
    paragraphs = recorder.narration(ROOT / "docs/pitch/hana-script.md")
    speech = " ".join(paragraphs)
    assert "AI scientist" in speech
    assert speech.startswith("Hi, I'm an AI scientist.")
    assert len(speech.split()) <= 135
    assert "wet-lab" not in speech
    assert "http" not in speech
    assert "Claim ledger" not in speech
    assert "SYNTHESIA_API_KEY" not in speech


def test_missing_spoken_boundary_fails_instead_of_reading_the_document(tmp_path):
    script = tmp_path / "unreviewed.md"
    script.write_text("Private notes are not a spoken script")
    with pytest.raises(ValueError, match="sections"):
        recorder.narration(script)


def test_captions_stay_inside_observed_speech_intervals():
    result = recorder.captions(
        [
            {
                "start": 2,
                "end": 8,
                "text": (
                    "These words belong to an authored explanation with captions "
                    "that follow recorded speech intervals."
                ),
            }
        ]
    )
    assert result.startswith("WEBVTT\n")
    assert "00:00:02.000 -->" in result
    assert "--> 00:00:08.000" in result
    lines = [line for line in result.splitlines() if line and "-->" not in line]
    assert "recorded speech intervals." in " ".join(lines)
    assert recorder.vtt_time(3599.9999) == "01:00:00.000"


def test_pronunciation_does_not_change_displayed_script():
    text = "NucB is a DNase. MutRank and Hyper M P N N propose changes."
    spoken = recorder.spoken_text(text)
    assert "Nuke Bee" in spoken
    assert "NucB" in text
    assert "Hyper, M, P, N, N" in spoken
