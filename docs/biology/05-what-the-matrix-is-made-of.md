# 5. What the matrix is made of

The material a biofilm secretes around itself is called the **matrix**. In the
literature you will see it called EPS, extracellular polymeric substances,
meaning polymers outside the cell. This repo says matrix (see
[CONTEXT.md](../../CONTEXT.md)).

By weight it is mostly water. The structure comes from three families of long
molecules, plus some smaller components.

## Polysaccharides

A **polysaccharide** is a chain of sugar units linked together, the way a
protein is a chain of amino acids. Starch and cellulose are polysaccharides,
and so are the main structural polymers of most biofilms.

Different bacteria make different ones, and a single species often makes
several, each with a slightly different job. Some form a mesh that gives the
film its bulk, some stick the film to the surface, some stick cells to each
other. Which one dominates depends on the organism, and on the conditions it
is growing in.

The links between sugars in these chains are the bonds a **glycoside
hydrolase** cuts. That makes polysaccharides the most common target for
enzymatic biofilm removal, and the first place Sonazyme looks.

## Proteins

The matrix contains proteins that are not enzymes but structural: adhesins
that bind cells to surfaces and to each other, and in many species fibres
with an **amyloid** structure, which is a very regular stacked arrangement
that is notably tough. Amyloid fibres act like reinforcing bar in concrete:
the polysaccharide is the bulk, the fibres carry tension.

Protein in the matrix is cut by a **protease**.

## Extracellular DNA

When cells die and burst, their DNA ends up in the matrix, and in many species
this is not accidental: some cells release DNA deliberately. It is long,
charged and sticky, and it contributes real mechanical strength, particularly
early in a film's life.

Extracellular DNA is cut by a **DNase**.

## Why one enzyme is rarely enough

A matrix built from a mesh of sugar chains, reinforced with protein fibres and
threaded with DNA, is a composite material. Removing one component weakens it
without dissolving it, in the same way pulling the steel out of reinforced
concrete leaves you with concrete.

This has two consequences for Sonazyme. A real treatment is likely to be a
combination rather than a single enzyme, and the pipeline therefore designs
per **anchor**: one named component, and the bond it offers. A target file
lists several anchors and the shortlist can cover more than one.

## What we do not know

Which anchors actually dominate in a given data-centre cooling loop is not
something this repo can assert. It depends on the organisms present, the water
chemistry, the materials and the treatment history. This is exactly why
[ADR-0002](../adr/0002-targets-are-data.md) makes the target a file with each
value sourced or marked as an assumption, rather than a fact baked into the
code.

**Next:** [which enzyme cuts what](06-which-enzyme-cuts-what.md).
