# ADR-0016: Put Sonazyme first and use literature-backed enzyme examples

- Status: Accepted
- Date: 2026-11-15
- Supersedes: the hero hierarchy and example selection in ADR-0015

## Decision

Use Sonazyme as the largest hero text. Doctor of Pipes and autonomous cleaning
of cooling pipes are smaller subheaders. Retain the existing carousel motion
and interaction, with a distinct decorative colour for each enzyme.

Replace generic examples with real enzymes studied for degrading extracellular
biofilm matrix. Keep their names, descriptions and primary-paper sources in
`web/data/enzyme-examples.json`. This is a literature display catalogue, not a
new pipeline target, shortlist or prediction. Existing stage contracts and
target definitions do not change.

The catalogue contains NucB, PslG, the isolated PelA hydrolase domain,
Dispersin B and Alg2A. They describe DNA, Psl, Pel, PNAG and alginate cleavage,
respectively. PelA refers to the experimentally studied cutting domain rather
than the full-length protein. Alg2A is a specific researched alginate lyase;
the comparative study does not support assuming that all alginate lyases
disrupt all biofilms.

Link each displayed example to its primary research paper. Do not imply that
these naturally occurring enzymes were invented by Sonazyme, that they kill
bacteria directly or that their published findings establish cooling-loop
performance. The carousel's AI-generated visual concepts remain parametric
illustrations, not measured or predicted molecular structures.

## Sources

- NucB: [Nijland et al.](https://doi.org/10.1371/journal.pone.0015668).
- PslG: [Yu et al.](https://doi.org/10.1038/cr.2015.129).
- PelA hydrolase: [Baker et al.](https://doi.org/10.1126/sciadv.1501632).
- Dispersin B: [Kerrigan et al.](https://doi.org/10.1556/ABiol.59.2008.4.5).
- Alg2A: [Characterization of different alginate lyases](https://doi.org/10.1038/s41598-020-66293-2).
