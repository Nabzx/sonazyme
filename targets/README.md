# Targets

One TOML file per target. Targets are data (ADR-0002). The v1 schema is fixed
by [ADR-0008](../docs/adr/0008-target-evidence-records.md) and checked by
`sonazyme.sense.targets.load(path)` or `parse(bytes)`.

## Available target

[psl-literature.toml](psl-literature.toml) is a research target. It names a
literature matrix anchor while marking the link to an industrial loop as an
assumption. The bond is tied to the primary paper's cleavage-position
definition. The operational envelope remains unknown. It
is usable for loading and chassis provenance integration, not an envelope-aware
scoring run. No Sonazyme wet-lab result exists.

The evidence and missing inputs are in
[the target research note](../docs/research/demo-target.md). The corrosion,
marine and spacecraft targets remain future work.

## Schema v1

The root contains exactly `schema_version = 1`, `[target]`, `[community]`,
one or more `[[anchor]]` blocks and `[envelope]`.

| Section | Required fields |
| --- | --- |
| `target` | `id`, `name`, `summary`, `loop` |
| `community` | one evidence record whose value is a non-empty list of names |
| each `anchor` | `component`, `kind`, `bond`, `enzyme_family`, `share` |
| `envelope` | `temperature_c`, `ph`, `chemistry`, `residence_time_s` |

`id`, `name` and `summary` are editorial metadata. All other fields are
evidence records. The id uses lowercase letters, digits and separating hyphens.

| Basis | Required fields | Meaning |
| --- | --- | --- |
| `literature` | `value`, `source` | Published information, with its scope retained |
| `guidance` | `value`, `source` | A specification or recommendation, not an observation |
| `measurement` | `value`, `source` | A cited measurement |
| `assumption` | `value`, `reason` | A deliberate choice with justification; source optional |
| `unknown` | `reason`, no `value` | Not established; source optional |

Known records may include a reason describing scope limits. A source is a
non-empty citation. Validation checks its presence, not the paper's contents.
A value without a marking or a cited value without a source fails loading.
Unknown keys fail too, so misspelt fields do not disappear silently.

Loop values are `direct-to-chip`, `cooling-tower`, `heat-exchanger`, `marine`,
`spacecraft` or `other`. Anchor kinds are `polysaccharide`, `protein` or
`extracellular-dna`. Component, bond and enzyme family are non-empty text.

Known temperature and pH values are ordered pairs of finite numbers. A known
residence time is a non-negative number in seconds. A known share is a fraction
between zero and one. Chemistry is a list of names. A known empty list means
no listed chemistry; an unknown chemistry has no value at all. The schema does
not infer concentrations or chemical compatibility from names.

```toml
[envelope.residence_time_s]
basis = "unknown"
reason = "No operator contact-time data."
```

The parser supplies no biological defaults. The `sense` stage writes normalised
JSON retaining every evidence record. A successful load establishes schema
validity, not readiness for design, scoring or treatment. Each downstream stage
must reject missing inputs it needs and record which envelope fields it uses.
