# Hana: the scientist beside the simulation

- Presenter: Hana, an AI presenter playing Sonazyme's scientist
- Avatar: `3190429b-1eda-4151-bf24-96162e405840`
- Cartesia voice: `1ac31ebd-9113-405b-9d80-4a4bbbeea91c`
- Delivery: warm, assured, curious and energetic. Short pauses. No shouting.
- Format: one prerecorded explanation beside the simulation
- Production record: `web/media/scientist.json` after recording

## Spoken script

Hi, I'm an AI scientist. This simulation shows how we design enzymes to target biofilm.

Biofilm is a layer of bacteria held together by a sticky mesh. Some of that mesh is DNA outside the cells.

Watch the enzyme fold. It is a chain of amino acids, and its shape creates an active site: tiny molecular scissors. Our starting enzyme, NucB, cuts DNA.

Boltz predicted its shape. Through Tamarind Bio, MutRank explored changes and Hyper M P N N generated new sequences while we kept known cutting positions unchanged.

Finally, the heat animation illustrates how an enzyme can lose its shape. Our goal is to redesign the surrounding chain so the scissors keep their shape in a cooling loop.

## Delivery notes

Target length: 45 to 60 seconds. Follow the simulation from folding, to cutting
DNA in the matrix, to sequence design and the illustrative heat animation.

Keep the website's existing experimental-status notice beside the video.
The spoken explanation does not repeat that notice. Describe computational
designs and predictions without implying physical production or measured activity.

Say NucB as “nuke bee”, Boltz as “bolts”, MutRank as “mute rank”, and
HyperMPNN as “hyper em pee en en”. Use pronunciation spellings only for speech.

The designs preserve five known catalytic positions. Do not imply that this
establishes full active-site integrity or improved stability. The heat sequence
is an illustration, not a measured temperature or molecular-dynamics result.

## Claim ledger

| Claim | Source |
| --- | --- |
| Matrix contains polysaccharide, protein and extracellular DNA | `docs/biology/04-what-a-biofilm-is.md`, `docs/biology/05-what-the-matrix-is-made-of.md` |
| Enzymes fold from amino-acid chains; the fold supports the active site | `docs/biology/01-what-an-enzyme-is.md`, `docs/biology/02-why-shape-is-everything.md` |
| Temperature and chemistry can affect function | `docs/biology/03-denaturing.md`; no particular loop envelope is claimed |
| NucB is the DNase chassis for the extracellular-DNA target | `targets/chassis/nucb-precursor.json`, `targets/edna-literature.toml` |
| Starting structure was predicted | `docs/result-NucB_Biofilm_DNase/`, Boltz 2.2.1 |
| MutRank explored sequence changes | [Provider export](https://github.com/Nabzx/sonazyme/blob/854bf4e5afcfe5760da3420ffe698d2aa2244086/docs/partner-handoff/mutrank_results.csv), MutRank producer label `tamarind-2026-11-14` |
| HyperMPNN generated sequences preserving known catalytic positions | [Provider sequences](https://github.com/Nabzx/sonazyme/blob/854bf4e5afcfe5760da3420ffe698d2aa2244086/docs/partner-handoff/hypermpnn_sequences.csv), [provenance](https://github.com/Nabzx/sonazyme/blob/854bf4e5afcfe5760da3420ffe698d2aa2244086/docs/partner-handoff/provenance.json), HyperMPNN producer label `tamarind-2026-11-14` |
| No Sonazyme wet-lab result or loop efficacy established | `SECURITY.md`, saved partial run |
