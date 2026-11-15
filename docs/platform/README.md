# Platform integrations

One note per external service: what we use it for, what we trust it for, what
we do not, and what the run manifest records about it.

| Service | Stage | Note |
| --- | --- | --- |
| Tamarind Bio | `design` | [tamarind.md](tamarind.md) |
| Boltz-2 | `fold` | [boltz2.md](boltz2.md) |
| Adaption Labs | `explain` | [adaption.md](adaption.md) |

Rules that apply to all of them.

- **Keys live in the environment.** Never in the repo, never in a manifest,
  never in a response the dashboard can see.
- **Versions are recorded.** Every call writes the model and version into the
  manifest ([ADR-0004](../adr/0004-provenance-on-every-number.md)).
- **Failures are recorded, not swallowed.** A call that fails or times out
  appears in the manifest as a failed entry. A stage never substitutes a
  plausible number for a missing one.
- **Replay before re-call.** A run that has a cached artefact for an identical
  input reuses it, so the demo works offline and the bill stays small.
