# A ranking model proposed mutating the catalytic site

- Date: 2026-11-14
- Issues: #26, #49, refs ADR-0005
- Status: a result, from a real run

## What happened

Tamarind Bio's MutRank was run over every single point mutation in the Boltz
2.2.1 structure of NucB: 2,698 mutations, scored and ranked by predicted
favourability.

Four of its top twelve mutations change **Asn117**, a catalytic residue. The
ranking's fourth-best mutation overall is N117V.

| Rank | Mutation | Score | Conservative score |
| --- | --- | --- | --- |
| 1 | H8L | +1.55 | +1.47 |
| 2 | T135W | +1.67 | +1.43 |
| 3 | T135Y | +1.65 | +1.32 |
| **4** | **N117V** | **+1.64** | **+1.31** |
| 5 | N117M | +1.28 | +1.21 |

Asn117 is not a borderline call. The crystal structure paper names it as the
residue that chelates the catalytic magnesium, and reports that mutating the
equivalent residue abolished activity
([Baslé et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC5758888/)). An enzyme
carrying N117V would very likely be a better-behaved protein that no longer
cuts anything.

Across the whole ranking, 48 proposals fall on one of the five catalytic
residues.

## Why it happened, and why it is not a fault in the tool

MutRank does what it says: it ranks mutations by how favourable they look to a
model of protein sequence and structure. That model has no representation of
what this protein is *for*. Asparagine 117 sits in a position where a
different residue packs more comfortably, and nothing in the objective knows
that its job is to hold a magnesium ion in place.

This is the failure mode [ADR-0005](../adr/0005-active-site-is-not-a-design-target.md)
was written against, before we had any tool output at all:

> A dead but very stable variant at the top of a shortlist is the most
> damaging failure this project can have, because it looks like a success.

It is now a result rather than an argument.

## What the pipeline did with it

The import splits a ranking in two. Proposals that leave the catalytic
residues alone become a `design` entry. Proposals that do not become a
`design` entry with status `rejected`, carrying their reason and their
artefact, because what a search proposed and lost is information.

The scientist reads both, and says so when asked how the candidates compare:

> This run holds 24 designs but no stability scores, so they cannot be
> compared in the loop conditions. Worth saying: 48 proposals were set aside
> before ranking because they change a catalytic residue. A model that ranks
> mutations on how favourable they look has no way of knowing what the enzyme
> is for.

The design job that followed, HyperMPNN, was submitted with those five
residues **fixed**, so it could not make the same proposal. The exclusion is
in the request, not in a filter afterwards.

## What this does not show

- It does not show that N117V would be inactive. That is the literature's
  claim about the equivalent mutant, not something measured here.
- It does not show that the surviving 24 proposals are good. They are ranked
  on predicted favourability, which is not stability in a cooling loop, and
  the scoring stage that would judge that has not run.
- It does not show MutRank is unsuitable. It answered the question it was
  asked. The lesson is about the question.

## Why it matters beyond this run

Any pipeline that chains a design model to a ranking model inherits this
problem, and the chain is exactly what everyone is building. The protection
has to be structural: a definition of the site that comes from a source, an
exclusion applied at the request, and a record of what was rejected. Scoring
afterwards and hoping the bad ones sink is not enough, because here the bad
one floated to fourth.

## A second scorer does the same thing

- Date: 2026-11-15
- Status: a result, from a real run

ThermoMPNN was run over the same enzyme, independently of MutRank and on a
different sequence. It was given the 110-residue mature chain, folded on its
own by Boltz 2.2.1, rather than the 142-residue precursor. That is 2,090 single
point mutations, each scored once.

It reaches the same place. Of its top twelve mutations, two change a catalytic
residue, and **the second-best mutation in the whole scan is Glu94 to valine**.

| Rank | Mutation | ddG, kcal/mol | On the site |
| --- | --- | --- | --- |
| 1 | C100F | -1.09 | no |
| **2** | **E94V** | **-0.95** | **yes** |
| 3 | D38C | -0.90 | no |
| 4 | D64A | -0.85 | no |
| 5 | E94I | -0.83 | **yes** |

Glu94 is not a marginal residue either. It is the general base, the residue
that stands where the His-Me finger family keeps its catalytic histidine, and
the paper reports that the equivalent E88A abolished activity. Across the full
scan, 95 proposals fall on one of the five catalytic residues.

So two different scorers, built by different groups, run on different sequences
and reporting in different units, both put active-site destruction in their top
five. MutRank favoured Asn117; ThermoMPNN favours Glu94. This is not one tool
having a bad day. It is what a model optimising for a well-packed fold does
when nothing in its objective knows the protein has a job.

[ADR-0005](../adr/0005-active-site-is-not-a-design-target.md) was written before
any tool output existed. Two independent runs have now walked into it.

## The two runs do not share a numbering frame

Worth recording before anyone compares the two tables directly.

This repository models NucB as the **142-residue precursor**, and
`docs/result-NucB_Biofilm_DNase/` is a fold of that full sequence. The
ThermoMPNN run above used the **110-residue mature chain**, which is precursor
residues 33 to 142. Mature position *i* is precursor position *i* + 32.

Two things follow:

- Positions are not interchangeable. The mature C68F above is the precursor
  C100F in the table. Every ThermoMPNN position was mapped by adding 32 before
  import, and each mapped row was checked against the chassis sequence.
- The precursor fold carries the signal peptide, which UniProt F1BV52 gives as
  residues 1 to 22 and which is cleaved from the secreted enzyme. MutRank's
  top-ranked mutation, H8L, sits inside it. Whatever that proposal does, it
  cannot change the stability of a protein the residue is not part of. The
  precursor fold also scores lower, pTM 0.76 against 0.95 for the mature chain,
  which is what a disordered terminus does to a prediction.

Neither point affects the active-site finding, since both runs agree on the same
five catalytic residues from the same source.
