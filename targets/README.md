# Targets

One file per biofilm target. A target is data, not code
([ADR-0002](../docs/adr/0002-targets-are-data.md)): adding one is adding a
file, and no stage changes.

There are none yet. The schema settles and the first target lands in M1, and
nothing is written here before its values have sources, because a target file
full of plausible numbers is worse than an empty folder.

## What a target file holds

```toml
[target]
id          = "..."     # stable identifier, used in run manifests
name        = "..."     # human name
loop        = "..."     # direct-to-chip | cooling-tower | heat-exchanger | other
summary     = "..."     # two sentences, plain

[community]
organisms   = [...]     # organism or community, each with a source
basis       = "..."     # how we know: sample, literature, assumption

[[anchor]]              # one block per component we could cut
component   = "..."     # the polymer
kind        = "..."     # polysaccharide | protein | extracellular-dna
bond        = "..."     # the link an enzyme would cut
enzyme_family = "..."   # glycoside hydrolase | lyase | protease | dnase
share       = "..."     # how much of the matrix, if known
source      = "..."     # citation, or "assumption"

[envelope]
temperature_c = [..,..] # range
ph            = [..,..]
chemistry     = [...]   # what is already in the water
residence     = "..."   # contact time available to a dosed enzyme
source        = "..."   # per value where they differ
```

## Rules

- **Every value carries a source or is marked `assumption`.** Both are fine.
  A value with neither is a defect.
- **An assumption stays visible downstream.** `sense` carries the marking
  into the run manifest, and the dashboard shows it on screen.
- **No target asserts what we have not been told.** If an operator has not
  given us composition data, the target says so.

## Planned

| Target | Status |
| --- | --- |
| data-centre direct-to-chip loop, default | M1, blocked on sources |
| sulfate-reducing community, corrosion case | M1 |
| marine hull | M7 |
| spacecraft water loop | M7 |
