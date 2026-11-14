"""Answers composed from a run, and refusals where the run has nothing.

The scientist answers about the run in front of it (#12, #92, #93, #94). Every
answer is either grounded, carrying the citations it was built from, or a
refusal naming what is missing. There is no third kind, and nothing here
reaches for knowledge the run does not contain.

The composer is deterministic today. When a fine-tuned model takes over the
wording (#18), it replaces this layer and keeps the contract: a claim arrives
with its citation or it does not arrive.
"""

from __future__ import annotations

from sonazyme.explain.retrieval import Index

COMPOSER = {"name": "sonazyme.explain", "version": "1", "kind": "code"}


def _answer(text: str, citations: list[dict | None], *, confidence: str) -> dict:
    return {
        "grounded": True,
        "text": text,
        "confidence": confidence,
        "citations": [citation for citation in citations if citation],
    }


def _refusal(text: str, missing: list[str]) -> dict:
    return {"grounded": False, "text": text, "missing": missing, "citations": []}


def what_is_in_this_run(index: Index) -> dict:
    """Inventory. Always answerable, because absence is also an answer."""
    present = ", ".join(sorted(index.stages_present)) or "nothing yet"
    missing = ", ".join(index.missing()) or "none"
    return _answer(
        f"Run {index.run_id} is {index.status}. Stages with a successful entry: {present}. "
        f"Stages not run: {missing}.",
        [index.cite("target"), index.cite("chassis"), index.cite("structure")],
        confidence="complete",
    )


def what_do_we_know_about_the_loop(index: Index) -> dict:
    """Report what the survey supports, and how far it does not go."""
    if not index.readings:
        return _refusal(
            "This run holds no survey, so there is nothing to say about where a film is "
            "or how thick it might be.",
            ["a sense entry carrying a reading"],
        )
    reading = index.readings[0]
    sized = [
        item
        for item in reading["observation"]
        if isinstance(item["estimate"].get("film_thickness_um"), (int, float))
    ]
    undetermined = len(reading["observation"]) - len(sized)
    widest = max(
        (
            item["estimate"]["interval_um"][1] - item["estimate"]["interval_um"][0]
            for item in sized
            if item["estimate"].get("interval_um")
        ),
        default=0,
    )
    basis = reading["basis"]
    caveat = (
        "These readings are simulated by the Sonazyme forward model. No loop has been pinged."
        if basis == "simulation"
        else f"These readings have basis {basis}."
    )
    return _answer(
        f"{len(sized)} of {len(reading['observation'])} sections return a layer the model can "
        f"size, and {undetermined} return nothing it will put a number on. The widest interval "
        f"on a sized section spans {widest:.0f} um, which is the cost of a water-rich film "
        f"being acoustically close to water. {caveat}",
        [index.cite("reading")],
        confidence="simulated" if basis == "simulation" else "measured",
    )


def why_this_chassis(index: Index) -> dict:
    """Give the selection reason as recorded, with its readiness limit."""
    if not index.chassis:
        return _refusal(
            "No chassis has been selected in this run, so there is no selection to explain.",
            ["a chassis entry"],
        )
    chassis = index.chassis
    readiness = (
        "It is not marked design ready, so nothing should be designed from it yet."
        if chassis.get("design_ready") is False
        else "It is marked design ready."
    )
    return _answer(
        f"{chassis['name']} was selected for the {chassis['anchor']['component']} anchor. "
        f"{chassis['selection_reason']} {readiness}",
        [index.cite("chassis")],
        confidence="recorded",
    )


def evaluate_candidates(index: Index) -> dict:
    """Give a verdict per candidate, or refuse when there are none (#92)."""
    if not index.designs:
        missing = ["a design entry"]
        if "score" not in index.stages_present:
            missing.append("a score entry")
        return _refusal(
            "This run contains no designed variants, so there is nothing to evaluate. A verdict "
            "on a candidate that does not exist would be invention, not evaluation.",
            missing,
        )
    if not index.scores:
        return _refusal(
            f"This run holds {len(index.designs)} designs but no scores, so they cannot be "
            "ranked or compared. Which is better is exactly what has not been computed.",
            ["a score entry"],
        )
    return _answer(
        f"{len(index.designs)} designs carry scores in this run. Each verdict below cites the "
        "entry that produced its number.",
        [index.cite("design"), index.cite("score")],
        confidence="predicted",
    )


def recommend_a_treatment(index: Index) -> dict:
    """Recommend only where the run supports a recommendation (#93)."""
    missing = []
    if not index.designs:
        missing.append("a design entry")
    if not index.scores:
        missing.append("a score entry")
    if not index.ranked:
        missing.append("a rank entry")
    if missing:
        return _refusal(
            "No treatment can be recommended from this run. It has no ranked shortlist, and a "
            "recommendation without one would be a preference rather than a result. Nothing in "
            "this project is a dose, a concentration or a clearance for a real loop in any case.",
            missing,
        )
    return _answer(
        "A ranked shortlist exists. Any recommendation is a research recommendation: which "
        "candidate to make and assay first, under stated conditions. It is not a dose, not an "
        "efficacy claim and not a clearance for a real loop.",
        [index.cite("rank")],
        confidence="predicted",
    )


def next_experiment(index: Index) -> dict:
    """List what to measure next, hardest-hitting first (#94)."""
    steps: list[dict] = []
    if index.readings and index.readings[0]["basis"] == "simulation":
        steps.append(
            {
                "step": "Ping a fouled pipe section on a bench rig and compare the return with "
                "the forward model's prediction for the same layer.",
                "settles": "Whether the acoustic front end detects a soft film at all, or only "
                "a change.",
                "issue": "#68",
            }
        )
    if "score" not in index.stages_present:
        steps.append(
            {
                "step": "Retrodict a stability model against published measurements, with the "
                "tolerance fixed first.",
                "settles": "Whether any ordering this pipeline produces is informative.",
                "issue": "#9",
            }
        )
    if index.target and index.target.get("envelope"):
        unknown = [
            key
            for key, value in index.target["envelope"].items()
            if isinstance(value, dict) and value.get("basis") == "unknown"
        ]
        if unknown:
            steps.append(
                {
                    "step": f"Obtain operating data for {', '.join(sorted(unknown))} from a "
                    "partner running a real loop.",
                    "settles": "Whether the design problem is the one we have assumed.",
                    "issue": "#6",
                }
            )
    if index.chassis and index.chassis.get("design_ready") is False:
        steps.append(
            {
                "step": "Resolve the binding-site exclusion for the selected chassis so design "
                "can begin.",
                "settles": "Whether variants may be proposed from it at all.",
                "issue": "#49",
            }
        )
    if not steps:
        return _refusal(
            "Nothing in this run suggests a next measurement, which usually means the run is "
            "empty rather than complete.",
            ["any successful stage"],
        )
    answer = _answer(
        "The measurements that would change our mind most, in order.",
        [index.cite("target"), index.cite("reading"), index.cite("chassis")],
        confidence="recorded",
    )
    answer["steps"] = steps
    return answer


QUESTIONS = {
    "inventory": ("What is in this run?", what_is_in_this_run),
    "loop": ("What do we know about the loop?", what_do_we_know_about_the_loop),
    "chassis": ("Why this chassis?", why_this_chassis),
    "candidates": ("How do the candidates compare?", evaluate_candidates),
    "treatment": ("What do you recommend?", recommend_a_treatment),
    "next": ("What should we measure next?", next_experiment),
}


def compose(index: Index) -> dict:
    """Answer every question this scientist takes, grounded or refused."""
    return {
        "schema_version": 1,
        "kind": "explanation",
        "run_id": index.run_id,
        "composer": COMPOSER,
        "note": (
            "Composed from this run's manifest and artefacts. Every claim carries the entry it "
            "came from, and a question the run cannot answer is refused rather than filled in."
        ),
        "answers": [
            {"key": key, "question": question, **function(index)}
            for key, (question, function) in QUESTIONS.items()
        ],
    }
