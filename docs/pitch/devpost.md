# Sonazyme

A doctor for data centre pipes: we find the blockage with sound, then design an
enzyme to dissolve it.

## Inspiration

AI data centres are cooled with water. Bacteria live in that water, stick to the
inside of the pipes, and build a slimy layer around themselves called a biofilm.
That layer acts like a blanket on the metal. Heat stops moving, pumps work
harder, and the chips throttle.

Today operators pour biocide into the loop. It kills the bacteria on the surface
but leaves the glue they built, so the film grows straight back. Enzymes can
dissolve that glue properly, but normal enzymes fall apart in warm water within
minutes.

So the problem is not "find an enzyme". It is "find an enzyme that survives the
pipe". That is a design problem, and design problems are what AI is good at.

## What it does

Sonazyme has three parts.

**It listens.** You cannot cut open a live cooling pipe, so we use sound. A
pulse through the pipe wall comes back changed by whatever is stuck on the
inside. We built a physics model of that: how much of the pulse bounces at the
boundary depends on the two materials either side,

$$R = \frac{Z_2 - Z_1}{Z_2 + Z_1}$$

where $Z$ is the acoustic impedance. Biofilm is mostly water, so $Z_2$ is very
close to $Z_1$ and the echo barely changes. That is the hard part of the
problem, and our model shows it honestly: a hard mineral deposit is easy to
spot, a soft film comes back with a wide error bar.

**It designs.** We take an enzyme that cuts the right bond, predict its 3D shape
with Boltz-2, then use Tamarind Bio to redesign it for heat, keeping the cutting
site frozen so it still works. Every design is folded again and checked.

**It decides.** We built a small model of the whole cooling loop and used
reinforcement learning to work out when and where to dose, so pipes stay clean
without the chips ever running hot.

## How we built it

- **Boltz-2** predicts the 3D structure of the enzyme and every redesign.
- **Tamarind Bio** runs the design and scoring models: HyperMPNN for heat-stable
  redesigns, MutRank and ThermoMPNN for ranking every single mutation.
- **Adaption** fine-tunes a model on enzyme data so it can score candidates for
  survival in cooling-loop conditions.
- **Synthesia** turns each run into a short video briefing.
- The site is plain JavaScript and three.js, no framework, so everything runs
  offline from a laptop.

Everything flows through one run record. Each step writes what it did, which
model produced it and which file it wrote, so every number on our site can be
traced back to the thing that produced it.

## Challenges we ran into

**The design model tried to break the enzyme.** We asked a ranking model for the
best mutations and its fourth best choice changed a catalytic residue, the exact
part that does the cutting. The paper on this enzyme says that mutation kills it.
A stable but dead enzyme at the top of a list is the worst possible failure,
because it looks like a success. We now exclude the active site in the request
itself, not afterwards, and 48 proposals got rejected on that rule.

**Sound struggles to see biofilm.** We wanted to claim detection and the physics
would not let us. So we kept the wide error bars on screen instead of hiding
them.

**The first policy we trained was useless.** It learned on clean pipes and then
met dirty ones. Starting every training run from a random amount of fouling
fixed it.

## What we learned

The biology was the easy part to read about and the hard part to be honest
about. Most of our work ended up being about provenance: labelling what is a
prediction, what is from a paper, and what is just a drawing. That discipline
caught the broken enzyme above, so it paid for itself.

## What's next

Anywhere water meets metal has this problem: ships, water networks, and
spacecraft life support, where you cannot send anyone to scrub a pipe. The
platform does not change. Only the target file does.
