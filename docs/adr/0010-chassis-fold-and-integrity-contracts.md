# ADR-0010: Snapshot chassis records and compare predicted catalytic geometry

- Status: Accepted
- Date: 2026-11-14
- Issues: #8, #25, #27, #28

## Context

The run infrastructure can load a target. It needs a sourced parent, a
structure adapter and an integrity filter without touching the separate
Adaption or Tamarind implementations. No real model run or wet-lab result
exists here. The policy threshold for #28 has not yet been agreed.

## Decision

Keep chassis JSON under `targets/chassis/`. Require a sequence and citation,
its SHA-256, the construct's mapping to reference numbering, anchor and bond
citations, and a sourced active-site definition. Validate sequence identity
at every protected position and its reference mapping. Preserve sources in a
normalised `chassis` artefact. The chassis stage consumes one successful sense
entry and a registry artefact reference, supplied in parameters. It requires
a known matching anchor and bond. It does not fold or score internally;
those stages are separate manifest calls.

The first record uses the natural PslG segment mapped by PDB 5BX9 to UniProt
Q9I1N2, without the deposited N-terminal cloning residues. The research note
records the mapping and limits. Only experimentally identified catalytic
residues are initially defined. This is not a complete substrate-binding
exclusion map, so `design_ready` is false. Registry loading must not imply
design readiness. A complete binding-site definition needs sourced review.

The fold adapter executes the official local Boltz CLI in an explicitly
selected Python environment. It verifies the installed package version and
checkpoint digest. The producer version includes package and checkpoint
identity; request parameters record adapter version and inference settings.
It supports one protein, with an optional ligand represented by a sourced
SMILES or CCD identifier. No affinity calculation or temperature/pH input
is supplied. Use a supplied MSA artefact or explicitly opt into single-sequence
mode; never silently send sequences to a public MSA service.

The input artefact has the subject id, canonical sequence, chain `A`, protected
positions and sources. Chassis folding derives it from the chassis record.
Variant inputs require a variant record referencing that same chassis with
an explicit mutation set. Reject changes at protected positions before a call.
The first implementation accepts substitutions only. Other variant schemas
need a later contract. Compare only folds of the same chassis with identical
producer and inference settings (including ligand and alignment policy).

Each fold entry references a JSON index with input identity, raw PDB,
confidence summary and per-residue confidence. Store the request YAML too.
These are predictions, not stability, activity or unfolding simulations.
No dashboard currently exists to render them.

The integrity helper compares unchanged catalytic residues using all pairwise
distances between their named heavy atoms. Maximum absolute distance change
is invariant to global rotation and translation. Check local handedness too.
Missing/duplicate atoms, changed protected residues and incompatible model
provenance fail closed. This is a conservative catalytic-core geometry filter,
not a complete binding or activity prediction. Equivalent terminal oxygen
names can cause false rejection; do not silently loosen a threshold to pass.

The tolerance is a required caller-supplied policy with units, a rationale,
and a reference to its prior agreement on #28. There is no default production
tolerance. Tests use explicitly labelled software fixtures. Passing those is
not a retrodiction or evidence that a biological threshold is suitable.
The helper appends a `score` entry with `role: integrity` and a report. It
does not estimate stability. Adaption scoring must call `require_integrity`
on the exact fold inputs first. Do not mark scoring integration complete
until that separate adapter enforces the gate.

## Consequences

No new runtime dependency is needed in Sonazyme. Boltz and its compute/data
requirements remain externally provisioned. Its own CLI may fetch model/data
resources; the wrapper is not an offline inference guarantee. Replay of saved
artefacts remains offline. Protocol tests do not establish real model success.

## Alternatives considered

An invented hosted endpoint would be an untestable integration. Installing
GPU dependencies as part of every Sonazyme install adds cost before compute
is selected. Using experimental coordinates as the predicted chassis baseline
would mix kinds of evidence. All are rejected.
