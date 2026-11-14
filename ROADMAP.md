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

One real run, end to end, on one target, shown as three acts. Pre-computed
where latency would put the demo at risk, and labelled as pre-computed when it
is. Full spec in [docs/design/dashboard.md](docs/design/dashboard.md).

| Act | What it is | Depends on |
| --- | --- | --- |
| 1. The narrative | scrollable: the problem, the sealed box, the two lines, the market | nothing of ours, so nothing of ours to cite |
| 2. The simulation | in place, not scrollable: how an enzyme is designed so it does not denature in the loop, in 3D, from real predicted structures | `sense`, `chassis`, `design`, `fold`, `score`, `rank`, `explain` |
| 3. The overhead film | ten seconds: sonar pulse, detection, lab, dosing, clean, confirming pulse | nothing, it depicts the intended workflow |

Definition of done: all three acts run from one run manifest, on a laptop,
offline if the cached run is used, no screen shows a number without its model
beside it, and anything illustrative says so on screen.

## The milestones

Every milestone is a kept-open map issue with its child tickets hanging off
it. The frontier is the open children with no open blocker.

| Milestone | Goal | Map | Tag |
| --- | --- | --- | --- |
| Demo | The five screens from one real run | [#2](https://github.com/Nabzx/sonazyme/issues/2) | v0.1.0 |
| M0 | The scaffold: decisions, glossary, biology, skeleton | [#3](https://github.com/Nabzx/sonazyme/issues/3) | v0.0.1 |
| M1 | The target: schema, default target, envelope | [#4](https://github.com/Nabzx/sonazyme/issues/4) | v0.0.2 |
| M2 | The chassis: parent enzymes with sources, baseline fold | not filed | v0.0.3 |
| M3 | The loop: variants from Tamarind, folds from Boltz-2, one manifest | not filed | v0.0.4 |
| M4 | The score: stability in the envelope, integrity check, retrodiction | not filed | v0.0.5 |
| M5 | The shortlist: ranking, the trade-off front, the dashboard on real runs | not filed | v0.0.6 |
| M6 | The scientist: answers grounded in artefacts, refusals when ungrounded | not filed | v0.0.7 |
| M7 | Beyond the data centre: a second target and a second envelope | not filed | v0.0.8 |

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
