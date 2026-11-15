# Partner model data hand-off

- Prepared: 2026-11-15
- Refs: #34
- Scope: model outputs for continuing the simulation, not a completed demo run

The original MutRank and HyperMPNN CSVs are included here, copied byte for
byte from the local provider exports. Nothing in this package has been tested
in a Sonazyme wet lab. These are predictions, not measurements of activity or
stability in cooling water.

## Files

| File | Contents |
| --- | --- |
| `mutrank_results.csv` | Full MutRank ranking: 2,698 single substitutions over the NucB parent |
| `mutrank_per_residue.csv` | Original per-residue output: 142 rows |
| `hypermpnn_sequences.csv` | All eight complete designed sequences and the model's original metrics |
| `hypermpnn_sequences.fasta` | The same sequences as FASTA; ids match the imported variant records |
| `run-snapshot.json` | Verified saved run, including the target, chassis, imported outputs, acoustic simulations and explanations |
| `provenance.json` | SHA-256, sizes, row counts, producer labels and original source notes |

The parent is [nucb-precursor.json](../../targets/chassis/nucb-precursor.json).
The structure files and confidence outputs are already committed under
[`docs/result-NucB_Biofilm_DNase/`](../result-NucB_Biofilm_DNase/).
The website's existing trace is [`web/data/enzyme.json`](../../web/data/enzyme.json).

Use the full CSVs when continuing modelling. The saved run contains only the
selected MutRank proposals and the rejection subset, not the full ranking.
The sequence CSV and FASTA retain complete HyperMPNN sequences, whereas the
current imported variant records store their mutation sets and metrics.

The full ranking includes proposals at protected catalytic positions. They
are raw tool output, not approved designs. The HyperMPNN outputs have been
checked against the recorded parent and preserve the five declared catalytic
residues. The chassis still has `design_ready: false` because its complete
binding-site exclusion is unresolved. No geometric integrity pass, trusted
stability score or ranked shortlist is claimed by this hand-off.

## Restore the saved run on another device

From the repository root, after installing the package:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m sonazyme.api restore --snapshot docs/partner-handoff/run-snapshot.json --run-dir runs/partner-handoff
```

Restore requires a new directory and verifies every referenced artefact. It
does not call a model or overwrite an existing run. The manifest remains
`running`, as exported: scoring and ranking have not run. This package does
not satisfy the complete real-run fixture in #34.

For the read-only API:

```bash
python -m sonazyme.api --runs-dir runs
```

The restored manifest is available at
`http://127.0.0.1:8000/api/runs/partner-handoff/manifest`.
No service credentials or original job settings archive is included.
