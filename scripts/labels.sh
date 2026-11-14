#!/usr/bin/env bash
# Create or update every label in docs/agents/issue-tracker.md.
# Safe to re-run. Needs the gh CLI, authenticated.
set -euo pipefail

label() { gh label create "$1" --color "$2" --description "$3" --force >/dev/null && echo "  $1"; }

label "demo" "f9a825" "The five-screen demo track, ahead of the milestones (ADR-0006)"
for n in 0 1 2 3 4 5 6 7; do
    label "m$n" "c5def5" "Milestone $n work"
done

label "area:core"    "1d76db" "The run manifest, the envelope, the stage contract"
label "area:sense"   "0b7285" "Targets and what holds a film together"
label "area:chassis" "b60205" "Parent enzymes and their provenance"
label "area:design"  "d93f0b" "Variant generation, Tamarind Bio"
label "area:fold"    "5319e7" "Structure prediction, Boltz-2"
label "area:score"   "0e8a16" "Stability and the integrity check"
label "area:rank"    "006b75" "Ranking and the trade-off front"
label "area:explain" "8a63d2" "The scientist agent"
label "area:web"     "fbca04" "Sonazyme Lab and the API"
label "area:bio"     "65a30d" "The biology docs"
label "area:acoustic" "0b7285" "Acoustic sensing and the sonar front end"
label "area:orchestration" "7057ff" "The Claude orchestrator and Adaption fine-tuning"
label "targets"      "1f6feb" "Target files and the target schema"
label "retrodiction" "0052cc" "Retrodiction cases and reference data"
label "adr"          "bfdadc" "Needs or updates an ADR"
label "documentation" "0075ca" "Docs only"

label "wayfinder:map"       "000000" "The map issue for a milestone"
label "wayfinder:research"  "8a63d2" "An investigation ending in an ADR recommendation"
label "wayfinder:prototype" "a371f7" "A throwaway spike a human judges"
label "wayfinder:grilling"  "6e40c9" "Pressure-test a decision before it is locked"
label "wayfinder:task"      "c9b8f0" "Build work"
label "ready-for-agent"     "2ea44f" "Spec settled; an implementation agent may build it"

label "bug" "d73a4a" "Something behaves differently from the docs or an ADR"
label "p1"  "b60205" "Serious: a passing retrodiction case fails, or a number is shown with no manifest entry"
label "p2"  "d93f0b" "An ordinary defect"
label "p3"  "fef2c0" "Minor"

label "needs-repro"     "ededed" "Plausible but not yet reproduced"
label "needs-decision"  "ededed" "Blocked on a design decision"
label "needs-research"  "ededed" "Blocked on a research ticket, including a missing source"
label "regression"      "e11d21" "Worked in an earlier tagged release"
label "pending-release" "ededed" "Merged; closes when its release is tagged"

label "pitch"        "e99695" "The pitch, the script and the submission"
label "polish"       "ffd33d" "Visual craft: look, motion, lighting, detail"
label "dependencies" "0366d6" "Dependency updates"
