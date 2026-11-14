# First target: anchor and envelope research

- Date: 2026-11-14
- Issues: #5, #6, #8
- Status: recommendation; no operator sample or operating data

Nothing here is a Sonazyme experimental result. No real biofilm has been
tested. Literature evidence and assumptions are kept separate below.

## Anchor recommendation (#5)

Use a Psl-dependent matrix as the first literature-defined target, with a
Psl-degrading glycoside hydrolase as the chassis direction. This is a tractable
demonstration of the pipeline, not evidence that Psl dominates a cooling loop.
Do not call it a representative data-centre composition.

[Baker et al. (2016), Science Advances](https://doi.org/10.1126/sciadv.1501632)
report exogenous PslG and PelA hydrolase activity against Psl- and
Pel-dependent laboratory biofilms, respectively. This supports matching a
matrix polymer to its degrading enzyme. It does not establish prevalence,
enzyme transport or efficacy in industrial water.

| Candidate anchor | Reason to consider it | First-run limitation |
| --- | --- | --- |
| Psl | Published matrix degradation and structural work on PslG | Presence and dominance in the intended loop are unmeasured |
| Pel | Same study supports a matching hydrolase | Choosing it instead still needs a composition assumption |
| Alginate | Alternative matrix polymer considered in the PslG structural paper below | No evidence here that a chosen loop contains an alginate-dominated matrix |
| Extracellular DNA or protein | Possible additional matrix anchors | A source-backed chassis comparison remains research work |

An important correction to older descriptions: the
[2025 primary specificity study](https://doi.org/10.1021/jacs.4c16806)
identifies PslG as an endo-beta-glucanase. Do not infer a mannan-cleaving bond
from mannose binding alone. The target now identifies the glucosidic cleavage
at position IV in that study's Figures 1 and 3. A fragment representation
still needs to be settled before #52 lands.

## Chassis direction (#8)

[Baker et al. (2015), Journal of Biological Chemistry](https://doi.org/10.1074/jbc.M115.674929)
report PslG structure and hydrolytic activity. This makes PslG worth comparing
with alternatives for the first chassis. The follow-up
[selection and numbering note](pslg-chassis.md) records the sequence source,
construct mapping and catalytic residues now kept in the registry. A complete
binding-site exclusion and suitable stability retrodiction measurements remain
unresolved. The research selection does not imply design readiness.

This work is limited to extracellular matrix degradation. It includes no
organism engineering, clinical design or treatment recommendation.

## Envelope findings (#6)

The closed technology loop and the facility/tower side are distinct.
[ASHRAE's data-centre chapter](https://handbook.ashrae.org/handbooks/A19/SI/a19_ch20/a19_ch20_si.aspx)
describes separate liquid loops and their interface requirements. Its facility
supply classes are design categories, not measured enzyme exposure ranges.

The [OCP water-based transfer-fluid guidance](https://www.opencompute.org/documents/guidelines-for-using-water-based-transfer-fluids-in-single-phase-cold-plate-based-liquid-cooled-racks-final-pdf)
explicitly covers the closed technology loop between the CDU and equipment,
excluding the facility side. Section 1.1 gives an expected upper operating
temperature of 66 degrees C. Table 1 gives pH 8.0 to 10.5 and discusses an
inhibitor package, copper protection, optional dispersant and microbiological
control. These are recommendations for a particular fluid specification, not
operator measurements and not a universal operating envelope. The document
also identifies glycol-based fluids as an alternative specification.

| Target field | What can be sourced now | What remains unknown |
| --- | --- | --- |
| Loop identity | Technology and facility loops must be distinguished | Which partner loop the first target represents |
| Temperature | OCP specification ceiling; ASHRAE facility classes | Minimum, maximum and local film exposure for an actual loop |
| pH | OCP fluid specification range | Actual fluid, metallurgy and measured pH |
| Chemistry | OCP describes treatment categories | Product identities, concentrations and enzyme compatibility |
| Residence time | No usable value established by this research | Hydraulic residence, recirculation and film contact time |
| Community and matrix shares | Laboratory Psl/Pel cases | Site organism composition and anchor abundance |

Do not copy the ceiling into a temperature range or label a specification as
a measured envelope. Do not claim an off-the-shelf chassis denatures in this
loop before obtaining both an envelope and a relevant stability prediction.

## Next decisions

1. Use a literature-defined Psl target for the first computational run,
   explicitly marking the mapping to industrial water as an assumption.
2. Keep unknown envelope fields explicit in the target schema. Unknown
   chemistry is not an empty list meaning untreated water.
3. Obtain loop-specific values or record justified demo assumptions before
   claiming envelope-aware scoring. #53, owned with the scoring work, must
   name which fields actually influence predictions.
4. Keep #6 open for contact time and site chemistry. The #8 research selection
   is recorded in the follow-up note; full exclusion review is still required
   before any variant design. Build issues remain open until release.
