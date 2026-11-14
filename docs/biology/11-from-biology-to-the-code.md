# 11. From biology to the code

Each idea from the previous pages lives somewhere specific in this repo. This
page is the map.

| Biology | Repo term | Where it lives |
| --- | --- | --- |
| the film in the pipe | biofilm | `targets/`, the thing being attacked |
| the material holding it together | matrix | a target's anchor list |
| one component plus the bond it offers | anchor | a target file |
| temperature, pH, chemistry, contact time | envelope | a target file |
| the natural enzyme we start from | chassis | `src/sonazyme/chassis/` |
| a chassis plus mutations | variant | produced by `src/sonazyme/design/` |
| `G127P` and friends | mutation set | a field on a variant |
| the pocket that does the cutting | active site | defined per chassis, checked in `score` |
| predicted shape | structure | produced by `src/sonazyme/fold/`, via Boltz-2 |
| will it hold its fold in the envelope | stability estimate | produced by `src/sonazyme/score/` |
| did the pocket survive the redesign | integrity check | `src/sonazyme/score/` |
| stability against activity against confidence | shortlist | `src/sonazyme/rank/` |
| a published measurement to check a model | retrodiction case | `validation/cases/` |

## The stages, in biological terms

1. **`sense`.** What is the film made of, and what conditions is it living in?
   Pages [4](04-what-a-biofilm-is.md), [5](05-what-the-matrix-is-made-of.md),
   [10](10-inside-a-cooling-loop.md).
2. **`chassis`.** Which natural enzyme cuts that bond? Page
   [6](06-which-enzyme-cuts-what.md).
3. **`design`.** Which changes to that enzyme might toughen it? Pages
   [7](07-how-you-change-a-protein.md),
   [8](08-what-makes-a-protein-stable.md).
4. **`fold`.** What shape does each changed version take? Page
   [9](09-how-ai-predicts-structure.md).
5. **`score`.** Will it hold that shape in the loop, and is the pocket intact?
   Pages [3](03-denaturing.md), [8](08-what-makes-a-protein-stable.md).
6. **`rank`.** Which ones are worth making, given the trade-offs? Page
   [8](08-what-makes-a-protein-stable.md).
7. **`explain`.** Why this one, in words, from this run's own output.

## The sentence this all adds up to

Find what glues the film to the pipe, pick the enzyme that cuts that glue,
redesign it so the heat and the pH of a working loop do not unfold it, check
the cutting pocket survived the redesign, and hand over a short, honest list
of the ones worth making.

Nothing in that sentence has been tested in a wet lab, and the repo says so
wherever a result appears.
