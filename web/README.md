# Sonazyme Lab

The dashboard. Specified in
[docs/design/dashboard.md](../docs/design/dashboard.md); this file is the
build side.

Nothing is built yet. The app arrives with the demo track.

## What it is

A web app that reads run manifests and artefacts through the API and renders
the five screens. It holds no science: every number it shows comes from a
manifest entry and is displayed with the model and version behind it
([ADR-0004](../docs/adr/0004-provenance-on-every-number.md)).

## Constraints

- **Runs offline from a cached run.** Conference wifi is not a dependency.
  The cached run and its artefacts ship with the app.
- **Cached is labelled cached**, with the date of the run.
- **3D structures are first class.** Screens 2 and 3 are the visual argument,
  so structure rendering and the colouring of active site against changed
  region are the part to get right first.
- **Three colours with fixed meanings**: prediction, active site, changed
  region. They never swap between screens.

## Layout

```
web/
  app/        screens, in the order they are presented
  components/ the structure viewer, the variant table, the provenance tag
  lib/        the API client and the manifest types
  fixtures/   a cached run, for offline and for tests
```

## The provenance tag

One small component that takes a manifest entry and renders the model, the
version and the word predicted. It appears on every number in the app. If a
value cannot produce one, it does not get displayed.

## Local structure viewer

The variants screen discovers PDB, ENT, CIF and mmCIF files beneath the
configured structure directory and renders them locally with 3Dmol.js. It
does not call the Tamarind API. Only structure files in that directory are
available to the viewer.

Run the dashboard with `python -m sonazyme.api --web-dir web`. The default
structure directory is the local `3D models` folder configured in
`src/sonazyme/api/__main__.py`. On another machine, pass `--structures-dir
"C:\path\to\3D models"` to point at that machine's files.
