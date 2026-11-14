# Security and responsible design

## Scope of the work

Sonazyme designs enzymes that degrade the polymers holding a biofilm
together: polysaccharide, protein and extracellular DNA outside the cell.
That is the whole scope.

This repo does not host, and will not accept, work that:

- increases virulence, transmissibility, host range or environmental
  persistence of any organism
- designs toxins, or proteins intended to harm a human, animal or plant
- targets a human, animal or plant protein
- circumvents clinical antimicrobial resistance, or designs against a
  therapeutic target
- reproduces a controlled sequence of concern

A pull request or issue heading that way is closed, and the reasoning is
written on it so the boundary stays clear.

## Not a treatment

Sonazyme produces shortlists of candidate designs from models. Nothing here
has been made, assayed or dosed. No output is advice about treating a real
cooling system, and no output should be read as a safety assessment of an
enzyme in water that ends up in discharge. Anything moving towards a real
loop goes through the partner's own safety, materials compatibility and
discharge review first.

## Credentials

API keys for Tamarind Bio, Boltz-2 and Adaption Labs belong in the
environment, never in the repo, never in a run manifest, never in a dashboard
response. Run manifests record the model and version used, not the key.

## Reporting a problem

Use GitHub's private vulnerability reporting on this repo (Security tab,
"Report a vulnerability"). Please do not open a public issue for a security
problem, a leaked key, or a concern about the biology above.
