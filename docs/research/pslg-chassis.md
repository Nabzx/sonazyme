# PslG as the first research chassis

- Date: 2026-11-14
- Issues: #8, #25, #52
- Status: sourced research selection; design readiness is incomplete

No Sonazyme wet-lab result or baseline model prediction exists. The selection
is based on published matrix degradation and structure, not a claim that this
enzyme is unstable in any particular cooling loop.

## Bond and choice

[Ruijgrok et al. (2025)](https://doi.org/10.1021/jacs.4c16806), Figures 1 and 3,
identify cleavage at the Psl beta-D-glucosidic linkage labelled IV, rather than
the earlier proposed mannosidic linkage. The target now uses that explicit
figure-defined bond. This does not supply a substrate fragment for #52.

[Baker et al. (2016)](https://doi.org/10.1126/sciadv.1501632) report exogenous
Psl degradation by the PslG hydrolase. This supports choosing PslG for a
Psl-defined research target. PelA would instead address a Pel-defined target;
an alginate lyase would require an alginate target. Choosing either would
change the anchor assumption. No comparison here establishes superior loop
performance or excludes a natural enzyme needing no redesign.

## Sequence and numbering

The [5BX9 deposited FASTA](https://www.rcsb.org/fasta/entry/5BX9/display)
contains 416 residues, beginning with GSHM. The
[RCSB/SIFTS mapping](https://data.rcsb.org/rest/v1/core/polymer_entity/5BX9/1)
maps entity positions 5 to 416 to UniProt Q9I1N2 positions 31 to 442. The
registry uses that natural 412-residue segment, removing the four cloning
residues, rather than treating deposited entity numbering as construct
numbering. The original FASTA is kept under `targets/chassis/sources/`, with
its digest next to the sequence source in the registry.

[Baker et al. (2015)](https://doi.org/10.1074/jbc.M115.674929) identify the
catalytic glutamates at reference positions 165 and 276. They map to positions
135 and 246 in the tag-free construct. The loader checks both glutamate
identities, the construct digest and the arithmetic mapping. Predicted
structures will use construct numbering starting from one, not PDB author
numbering or full-length protein numbering.

## Limits before design

The current active-site definition covers the two catalytic residues, not
every residue in the substrate-binding groove. `design_ready` is therefore
false. The fold adapter permits a baseline prediction but blocks variant
folding until a complete exclusion definition has a source and review. Do not
flip this flag to bypass that work. No variant has been proposed here.

The geometry policy has no production default. #28 still needs an agreed
tolerance before a biological comparison. The stability scorer still needs
retrodiction against suitable published measurements. None is supplied by
this sequence or by the laboratory matrix-degradation observation.
