# Roadmap

Linear milestones. Every milestone ends in a tagged build that runs, even if
narrow, and in retrodiction cases that pass. A milestone is done when its
definition of done is met, not before, and it does not grow past its goal.

No dates. A milestone gets a soft estimate once the one before it has shipped
and the pace is known.

One thing runs ahead of this order: **the demo track**, the five screens of
Sonazyme Lab driven by one real run (ADR-0006). It is the first goal and it is
described before M0 below.

## Ground rules

- Every change lands through a pull request with green CI.
- An ADR is written before code for anything touching the stage contract, the
  run manifest, the target schema, which model a stage calls, the ranking
  objectives, what the scientist may say, or a new dependency.
- Each milestone opens with a Wayfinder map issue naming the decisions it
  depends on. Research and grilling tickets resolve them into ADRs before
  build tickets start.
- No scoring model reaches the shortlist without a retrodiction case.
- No number is shown anywhere without the model and version behind it.

## The demo track

One real run, end to end, on one target, shown as five screens. Pre-computed
where latency would put the demo at risk, and labelled as pre-computed when it
is.

| Screen | What it shows | Depends on |
| --- | --- | --- |
| 1. The problem | biofilm forms, biocide hits the surface, the matrix survives, the film returns | nothing, it is an animation |
| 2. The baseline | the chassis enzyme in 3D, with its predicted stability in the envelope and where it gives way | `sense`, `chassis`, `fold`, `score` |
| 3. The redesign | variants arriving with scores, best variant beside the chassis, changed region highlighted, active site shown untouched | `design`, `fold`, `score`, `rank` |
| 4. The question | a question answered from this run's artefacts, with what it cites | `explain` |
| 5. The case | status quo against the approach, scoped as a design tool, with the open questions named | nothing, it is a slide |

Definition of done: the five screens run from one run manifest, on a laptop,
offline if the cached run is used, and no screen shows a number without its
model beside it.

## The milestones

| Milestone | Goal | Tag |
| --- | --- | --- |
| Demo | The five screens from one real run | v0.1.0 |
| M0 | The scaffold: decisions, glossary, biology, skeleton | v0.0.1 |
| M1 | The target: schema, default target, envelope | v0.0.2 |
| M2 | The chassis: parent enzymes with sources, baseline fold | v0.0.3 |
| M3 | The loop: variants from Tamarind, folds from Boltz-2, one manifest | v0.0.4 |
| M4 | The score: stability in the envelope, integrity check, retrodiction | v0.0.5 |
| M5 | The shortlist: ranking, the trade-off front, the dashboard on real runs | v0.0.6 |
| M6 | The scientist: answers grounded in artefacts, refusals when ungrounded | v0.0.7 |
| M7 | Beyond the data centre: a second target and a second envelope | v0.0.8 |

### M0, the scaffold

**Goal.** Somebody new can read what this is, why each decision was made, and
what the biology underneath it means, then run the test suite.

**Done when.** Decisions ADR-0001 to ADR-0006 are accepted, the glossary
covers every term in use, `docs/biology/` explains each concept the repo
depends on, the package imports and every unbuilt stage names its milestone.

### M1, the target

**Goal.** A biofilm target is a file anyone can write and swap.

**Done when.** The target schema is settled and documented, the default
data-centre target exists with each anchor cited, the envelope is explicit
about which numbers are measured and which are assumptions, and a second
sketch target proves swapping costs one file.

### M2, the chassis

**Goal.** For each anchor in the default target, at least one parent enzyme,
with a reason and a source.

**Done when.** Chassis sequences are stored with their provenance, each is
folded once to give the baseline structure, and the baseline's predicted
stability in the envelope is recorded as the number the redesign has to beat.

### M3, the loop

**Goal.** One command turns a target into folded variants.

**Done when.** `design` produces a variant set through Tamarind Bio, `fold`
produces a structure per variant through Boltz-2, both append to one run
manifest with model versions, and a run can be replayed from the manifest
alone.

### M4, the score

**Goal.** A number per variant that is worth looking at.

**Done when.** Stability in the envelope is predicted per variant, the
active-site integrity check rejects variants that moved the catalytic
geometry, and at least one retrodiction case passes against published
measurements with a tolerance fixed beforehand.

### M5, the shortlist

**Goal.** A ranked set with its trade-offs visible, in the dashboard.

**Done when.** Ranking is multi-objective rather than a single blended score,
the front is shown rather than hidden, and Sonazyme Lab reads real run
manifests instead of fixtures.

### M6, the scientist

**Goal.** Ask why a variant is better and get an answer tied to the run.

**Done when.** The agent answers from artefacts, every claim it makes points
at the artefact behind it, and a question the run cannot answer gets a refusal
rather than a plausible paragraph. Refusal behaviour is covered by tests.

### M7, beyond the data centre

**Goal.** Show the platform is not one pipeline for one film.

**Done when.** A second target with a different anchor and a different
envelope runs end to end with no change to any stage.

## Later, not scheduled

- Pre-compensated design: predicting the fold shift under load and aiming off
  so the working shape is correct. Research direction, see ADR-0003.
- Monitoring input: loop telemetry choosing when a treatment is worth
  recommending.
- Marine and spacecraft envelopes, where discharge and resupply make the case
  stronger than cost does.
