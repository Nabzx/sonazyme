# Chassis registry

Records are JSON files under this directory, checked by
`sonazyme.chassis.registry.load(path)`. The first record is
[pslg-31-442.json](pslg-31-442.json); see the
[selection and numbering evidence](../../docs/research/pslg-chassis.md).

The v1 shared contract is in
[ADR-0010](../../docs/adr/0010-chassis-fold-and-integrity-contracts.md).
No sequence, active-site definition or anchor is hard-coded into a stage.

Required fields are `schema_version`, `kind: chassis`, `id`, `name`,
`selection_reason`, `design_ready`, `anchor`, `sequence` and `active_site`.
The anchor has `component`, `bond`, `source`. The sequence has `value`,
`sha256`, `source` and a `mapping` containing `reference`, `reference_start`,
`reference_end` and `source`. The source segment is contiguous. The loader
rejects inconsistent length, digest or residue mapping.

The active site has `source`, `scope` and a non-empty `residues` list. Each
residue has a construct `position`, a `reference_position`, an `amino_acid`
and explicit heavy-atom `atoms` used by the geometry check. Positions are
one-based. Sequence letters are canonical amino acids. Missing citations and
wrong protected identities fail loading.

A source's presence is checked, not the truth of its contents. `design_ready`
must stay false when the binding-site exclusion is incomplete. Validating or
selecting a chassis does not establish stability, activity or suitability for
a real loop. No Sonazyme wet-lab result exists.

## Record it in a run

From an activated repository environment:

```bash
python -m sonazyme.sense targets/psl-literature.toml --run-dir runs/chassis-check
python -m sonazyme.chassis targets/chassis/pslg-31-442.json --run-dir runs/chassis-check
```

Use this new directory because the target bond was clarified after the earlier
`runs/target-check` snapshot. Saved targets remain immutable. Repeating the
chassis command reuses its recorded success without creating another attempt.
No structure or stability prediction is made by either command.
