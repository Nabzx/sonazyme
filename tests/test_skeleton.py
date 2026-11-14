import importlib

import pytest

import sonazyme
from sonazyme import STAGES, NotBuiltError

LAYERS = [*STAGES, "core", "runs", "api"]


def test_version_is_a_string():
    assert isinstance(sonazyme.__version__, str)


@pytest.mark.parametrize("name", LAYERS)
def test_every_layer_imports_and_says_what_it_is(name):
    module = importlib.import_module(f"sonazyme.{name}")
    assert module.__doc__, f"sonazyme.{name} needs a docstring saying what lives there"


@pytest.mark.parametrize("stage", list(STAGES))
def test_unbuilt_stages_name_their_milestone(stage):
    module = importlib.import_module(f"sonazyme.{stage}")
    with pytest.raises(NotBuiltError) as raised:
        module.run(object())
    assert raised.value.milestone == STAGES[stage]
    assert f"M{STAGES[stage]}" in str(raised.value)
    assert "ROADMAP.md" in str(raised.value)


def test_the_stages_are_in_pipeline_order():
    assert list(STAGES) == [
        "sense",
        "chassis",
        "design",
        "fold",
        "score",
        "rank",
        "explain",
    ]
