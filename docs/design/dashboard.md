# Sonazyme Lab

The demo. Three acts, in order: a scrollable narrative, a simulation that runs
in place, and a ten second overhead film of the whole workflow.

The rule underneath all of it: every number on screen comes from a run
manifest entry, with the model that produced it shown next to it, labelled as
a prediction ([ADR-0004](../adr/0004-provenance-on-every-number.md)). A screen
reading a cached run says so, with the date of the run
([ADR-0006](../adr/0006-demo-track.md)). Anything illustrative is marked
illustrative, in the UI, not in a footnote.

## The two lines

> We use sonar to detect biofilm build-up in cooling pipes, then release
> enzymes designed to break it down.

That is the whole product in two lines, and the same wording is used in the
README, in Act 1, and in the submission. Nothing in the demo should need more
than those two lines plus what is on screen to be understood.

## Act 1, the narrative (scrollable)

Simple, high-impact language. Short sentences, one idea per section, no
jargon that is not shown as a picture at the same time.

1. **The problem.** A pipe wall, cells arriving and sticking, the matrix
   building up, a biocide dose arriving, the cells at the surface dying, the
   matrix staying, the film returning over the following days. The line it has
   to land: killing the cells does not remove what holds the film to the wall.
2. **The sealed box.** Nobody can see inside a running loop, so chemistry is
   dosed on a schedule rather than on evidence.
3. **The solution.** The two lines above.
4. **The market.** What is spent on cooling and water treatment, and how much
   capacity is being built. Industry figures, cited on screen, describing
   current practice rather than our effect on it.

No numbers of ours appear in Act 1, so there is nothing of ours to cite.

## Act 2, the simulation (in place, not scrollable)

The centrepiece, and the answer to the question the track actually asks: where
is the machine learning?

It runs in place in a fixed frame, self-running with controls, showing how an
enzyme is designed so that it does not denature in the conditions of a loop:

1. **The chassis.** The natural enzyme, rendered from its real predicted
   structure, with the active site coloured.
2. **The envelope.** The loop conditions, from the target file, each value
   marked sourced or assumed.
3. **Why it fails.** The chassis stability estimate in that envelope, shown
   against where the envelope sits. Any depiction of the fold giving way is
   **illustrative**, driven by the stability estimate, and labelled as such.
   The structure models take no temperature input, so nothing here is a
   simulation of real unfolding ([ADR-0003](../adr/0003-rigidify-not-pre-compensate.md)).
4. **The design step.** Variants proposed through Tamarind Bio, arriving with
   their mutation sets, scored by the fine-tuned scorer, rejects visibly
   discarded with their reason.
5. **The winner.** The best variant beside the chassis, same orientation,
   changed region in one colour, active site visibly untouched in another.
6. **The verdict.** The scientist agent's written reading of why this one,
   citing the entries it used.

Every structure in Act 2 is a real Boltz-2 prediction from the run, rendered
from its coordinates. Nothing is a stylised stand-in for a protein.

## Act 3, the overhead film (ten seconds)

One continuous overhead shot of the whole workflow, fast, looping, with no
narration needed. Five beats:

1. A sonar pulse travels along a cooling pipe.
2. The pulse returns changed, and a patch of biofilm lights up where it is
   building.
3. Beside the pipe, a small lab module: the enzyme is designed and made.
4. The enzyme is dosed into the loop.
5. The patch clears, and a second pulse confirms it.

This is the platform in one shot: monitor, design, treat, monitor again. It
plays at the top of the page and again at the end. It is a depiction of the
intended workflow, not a readout, and it says so.

## Visual language

- Dark, instrument-panel feel. `assets/hero.svg` sets the palette.
- Three colours with fixed meanings across every act: prediction, active site,
  changed region. They never swap.
- Every tile carries its model and version in small type. No exceptions, no
  hover to reveal.
- An assumed value is marked assumed wherever it appears, and an illustrative
  animation is marked illustrative.

## Build notes

The app reads the API, which serves run manifests and artefacts and computes
nothing ([ARCHITECTURE.md](../architecture/ARCHITECTURE.md)). Act 2 connects
to the backend for structures and scores, live where latency allows and from
the cached run otherwise. The whole thing must run from a cached run with no
network, because conference wifi is not a dependency anyone should accept.
