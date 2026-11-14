# 7. How you change a protein

A protein is a sequence of amino acids, so changing a protein means changing
one or more letters of that sequence. A single change is a **mutation**, and
in the lab it is made by editing the gene that codes for the protein and
having bacteria build the new version.

## Reading a mutation

Each amino acid has a one-letter code. A mutation is written as original
letter, position, new letter:

> `G127P` means: at position 127 the original amino acid was glycine (G), and
> it has been replaced with proline (P).

A **variant** is a chassis plus a set of such changes. `G127P + A54C + T89K`
is one variant with three mutations, and in this repo that set is called the
**mutation set**.

## What a mutation does

The twenty amino acids differ in size, in charge, in greasiness and in how
floppy they are. Swapping one for another changes the local chemistry, and
that can:

- **Help the fold.** A new salt bridge, a better-packed core, a stiffer loop.
- **Hurt the fold.** A large side group where there is no room, a charge
  buried in the greasy core, a hole left by removing something bulky.
- **Do nothing much.** Most mutations on the surface, away from anything
  important, land here.
- **Kill the activity.** A change in or near the active site, even one that
  makes the protein more stable overall.

That last case is the dangerous one, and it is why
[ADR-0005](../adr/0005-active-site-is-not-a-design-target.md) forbids design
at the active site and makes every variant pass a geometry check before it is
scored.

## Why this is a search problem

A 400 amino acid protein has 400 positions and 19 alternatives at each, so
there are about 7,600 single mutations. Pairs run into tens of millions.
Nobody can make and test those in a lab.

So the work is triage. Predict which changes are likely to help, rank them,
and hand a short list to whoever does the wet work. That is exactly what the
`design`, `score` and `rank` stages do, and the quality of the whole project
is the quality of that shortlist.

## A note on how real designs are made

Useful mutations are not usually guessed one at a time. Common strategies:

- **Consensus.** Line up hundreds of related natural proteins and, at each
  position, take the most common amino acid. Positions where evolution agrees
  tend to matter, and consensus versions are often more stable than any single
  natural one.
- **Ancestral reconstruction.** Infer the sequence of a long-extinct ancestor
  of a protein family. These often turn out to be strikingly tough, which is
  thought to reflect a hotter ancient environment.
- **Targeted rigidifying.** Find the floppiest parts of the structure and stiffen
  them deliberately, which is [page 8](08-what-makes-a-protein-stable.md).
- **Learned design.** Let a model trained on many proteins propose sequences.
  This is the part Tamarind Bio does for us.

**Next:** [what makes a protein stable](08-what-makes-a-protein-stable.md).
