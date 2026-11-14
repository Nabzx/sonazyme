# 8. What makes a protein stable

Stability is the difference between the folded state and the unfolded state.
A protein is stable when folded is comfortably better than unfolded, and the
surprise of protein chemistry is how small that difference usually is: the
folded state wins by about as much energy as a handful of hydrogen bonds. That
is why a modest amount of heat can tip the balance.

There are two ways to tip it back.

## Make folded more comfortable

- **Pack the core properly.** Greasy side groups buried in the middle are the
  main force holding a protein together, and gaps between them are wasted
  opportunity. Filling a cavity with a slightly larger side group helps.
- **Add salt bridges.** Put a positive side group next to a negative one,
  especially on the surface, where networks of them are a common feature of
  enzymes from hot-spring organisms.
- **Add a disulfide bridge.** Two cysteines close in space can form a real
  covalent bond, pinning two parts of the chain together. Strong, but only
  placeable where the geometry already suits it, and it needs the right
  chemical conditions to form and stay formed.
- **Fix the helix ends.** Helices have a slight electrical polarity, and
  putting the right charge at each end is a small, cheap gain.

## Make unfolded less comfortable

This is the less obvious half and it is often the more effective one.

An unfolded chain is free to flop into an enormous number of arrangements, and
that freedom is worth a lot of energy. Take some of it away and unfolding
becomes less attractive, without touching the folded state at all.

- **Proline.** Proline's side group loops back and joins the chain, so a
  proline cannot bend as freely as other amino acids. Putting one at a
  flexible loop removes options from the unfolded chain. This is why proline
  substitutions appear in almost every thermostabilisation study.
- **Glycine removal.** Glycine is the opposite: no real side group, so it is
  unusually floppy. Replacing a glycine that is not doing a structural job
  stiffens the chain in the same way.

## The trade-off

A stiffer protein is often a slower one, because the active site needs some
movement to close around its substrate (the induced fit from
[page 1](01-what-an-enzyme-is.md)). Enzymes from hot-spring organisms are
frequently sluggish at room temperature for exactly this reason: they are
tuned to be flexible at the temperature they evolved in.

So "most stable variant" is not the same as "best variant". This is why
Sonazyme ranks on several objectives rather than one blended score, and why
the dashboard shows the trade-off rather than a single number
([ROADMAP.md](../../ROADMAP.md), M5).

## Two routes, and the one we took

**Rigidify**: everything above. Keep the job, toughen the fold, check the
active site is untouched. Standard protein engineering, with public
measurements to check predictions against.

**Pre-compensate**: predict how the fold shifts when hot, and design a
sequence that arrives at the right shape once it is at temperature, the way an
engineer pre-bends a part that will relax after welding. Much more striking,
and much harder: the structure models available to us predict one static
structure and do not take temperature as an input, so there is nothing to aim
with, and no cheap way to check the aim.

Sonazyme rigidifies, and says so. The reasoning is
[ADR-0003](../adr/0003-rigidify-not-pre-compensate.md).

**Next:** [how AI predicts structure](09-how-ai-predicts-structure.md).
