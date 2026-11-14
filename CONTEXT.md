# Sonazyme

Enzymes designed to break down biofilm inside data-centre cooling loops, and
redesigned to keep their fold in the conditions of a running loop.

This file is the glossary. When an issue, a commit, an ADR, a test or a
dashboard label names one of these concepts, use the term as defined here. Do
not drift to the synonyms under _Avoid_. New terms are added lazily, as
decisions settle, not upfront.

A plain-language version of the biology behind these terms is in
[`docs/biology/`](docs/biology).

## The problem

**Biofilm**:
A layer of microorganisms attached to a surface and held there by material
they secrete. The thing Sonazyme attacks.
_Avoid_: slime (outside the biology docs), fouling, scale, sludge

**Matrix**:
The secreted material that holds a biofilm together and to the wall:
polysaccharide, protein and extracellular DNA. The target of an enzyme.
_Avoid_: EPS (in code and issues; fine in the biology docs where it is
defined), glue, goo

**Anchor**:
One named component of the matrix that an enzyme could cut, with the bond it
offers. A target definition lists its anchors.
_Avoid_: substrate (ambiguous), component, epitope

**Envelope**:
The conditions an enzyme has to work in: temperature range, pH range, the
treatment chemistry present, and the residence time. Attached to a target,
never assumed globally.
_Avoid_: operating conditions, environment, regime

**Loop**:
The water circuit being treated: direct-to-chip, rear-door, cooling tower.
_Avoid_: system, circuit, pipe (in code)

## The design

**Target**:
A file naming an organism or community, its anchors, and its envelope. Data,
not code (ADR-0002).
_Avoid_: scenario, profile, case

**Chassis**:
A natural parent enzyme chosen because it cuts one of the target's anchors.
The starting sequence for design.
_Avoid_: wild type (in prose; fine in a figure), baseline, scaffold, template

**Variant**:
A chassis with a defined set of mutations. The unit that gets folded, scored
and ranked.
_Avoid_: candidate (except in the dashboard copy), mutant, design

**Mutation set**:
The specific changes a variant carries, written in the usual one-letter form,
for example `G127P`.
_Avoid_: edits, changes, diff

**Active site**:
The part of the enzyme that does the cutting. Sonazyme changes the rest of the
chain and checks this part is unchanged.
_Avoid_: catalytic pocket (in code), binding site

**Integrity check**:
The test that a variant's active site geometry still matches the chassis
within tolerance. A variant that fails it is rejected whatever its stability.
_Avoid_: sanity check, validation (that word means something else here)

**Stability estimate**:
A predicted number saying how well a variant holds its fold in the envelope,
with the model and version that produced it.
_Avoid_: thermostability score (too specific), robustness, fitness

**Shortlist**:
The ranked set a run ends in, with the trade-off each entry makes visible.
The product of a run.
_Avoid_: results, winners, top hits

## The machinery

**Stage**:
One step of the pipeline: `sense`, `chassis`, `design`, `fold`, `score`,
`rank`, `explain`. The unit of replacement. A stage reads the run manifest and
appends to it.
_Avoid_: step, module, phase, node

**Run**:
One pass of the pipeline over one target, identified and reproducible.
_Avoid_: job, experiment, session

**Run manifest**:
The single record of a run: every input, model, version, score and artefact
path, in order. What the dashboard and the agent read.
_Avoid_: log, results file, metadata

**Artefact**:
A file a stage produced: a structure, a score table, a prediction. Referenced
by the manifest, never pasted into it.
_Avoid_: output, asset, blob

**Scientist**:
The agent in the `explain` stage. It answers questions about a run using that
run's artefacts and says when it cannot.
_Avoid_: copilot, assistant, chatbot, AI

**Retrodiction case**:
A published measurement, the model's prediction of it, and a tolerance fixed
before the run. How Sonazyme checks a scoring model is worth trusting.
_Avoid_: benchmark, test (that word means unit test here), evaluation

## Words we do not use

**Cleans**, **sterilises**, **eliminates**, **eradicates**: Sonazyme designs
candidates. Nothing in this repo has removed a biofilm from anything.

**Proven**, **validated** (of a design), **ready**: a retrodiction case
passing says a model is worth trusting, not that a variant works.

**Saves X%**: no saving figure appears anywhere until a measurement exists
behind it.
