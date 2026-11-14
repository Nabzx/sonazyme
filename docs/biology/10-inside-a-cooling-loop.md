# 10. Inside a cooling loop

The biology only makes sense next to the plumbing. This page is the
environment our enzyme has to work in, and what we do and do not know about
it.

## Where the water goes

A dense AI data centre moves heat from chips to the outside world in stages.

- **Direct-to-chip.** A cold plate sits on the processor and a coolant runs
  through it, millimetres from the hottest surface in the building. Narrow
  channels, so this is where fouling is least forgiving.
- **Rear-door and immersion variants.** Different geometry, same idea: liquid
  takes the heat away from the rack.
- **The facility loop.** A heat exchanger passes the heat from the equipment
  loop into a second circuit.
- **Rejection.** A cooling tower, a dry cooler or a chiller dumps the heat.
  Towers are open to the air, which means dust, sunlight and microorganisms
  arriving continuously.

The two loops are deliberately different. The equipment loop is closed, clean
and chemically controlled. The tower side is open, dirtier and much more
biologically active.

## What the water is like

- **Warm, not hot.** Heat is collected at one end and rejected at the other,
  so water in a running loop sits in the range that suits many bacteria
  perfectly: too hot for a typical enzyme to be comfortable, not hot enough to
  sterilise anything.
- **Alkaline.** Treated loop water is usually held slightly alkaline, because
  acidic water attacks metal. That is away from where many useful enzymes work
  best.
- **Already treated.** The water contains corrosion inhibitors, scale
  inhibitors, dispersants and biocide. Any enzyme we propose has to tolerate
  that chemistry, and must not damage the inhibitors doing the protecting.
- **Flowing.** Enzyme dosed into a loop is carried along, so the question is
  not only whether it works but whether it works during the time it spends in
  contact with the film.
- **Mixed materials.** Copper, aluminium, stainless steel, brazed joints,
  polymer tubing and seals. Compatibility with all of them is a partner's
  requirement, not an afterthought.

## What we are assuming

Sonazyme does not have measurements from a real data-centre loop. The default
target's envelope, in `targets/`, is an assumption, and it is marked as one,
value by value. Every number in it is a parameter to be replaced by a
measurement when a partner gives us one, not a finding of this project.

That is the point of making targets data rather than code
([ADR-0002](../adr/0002-targets-are-data.md)). If the real loop turns out to
run cooler, or at a different pH, or with a different organism dominating, the
answer is a new target file and another run.

## Why the hard cases are elsewhere

The same pipeline, pointed at a ship's hull or a spacecraft water system,
meets a stronger version of the same problem. Marine biofouling is severe, and
the chemicals used against it end up in the sea. On a spacecraft, water is
recycled, resupply is impossible and maintenance is extremely expensive.

Data centres come first because they are accessible, the loops are
instrumented and the economics are easy to explain. The harder environments
are where a biological answer beats a chemical one most clearly.

**Next:** [from biology to the code](11-from-biology-to-the-code.md).
