# 6. Which enzyme cuts what

Picking an enzyme is matching a bond to a tool. Four steps.

## 1. Name the anchor

Decide which component of the matrix you are attacking: a specific
polysaccharide, a structural protein, extracellular DNA. That component, and
the chemical bond holding it together, is what this repo calls an **anchor**.

"Degrades biofilm" is not a target. "Cuts this bond in this polymer" is.

## 2. Find the enzyme family that cuts that bond

Enzymes are grouped into families by the chemistry they do. For matrix
polymers the three that matter are:

| Anchor | Enzyme family | What it does |
| --- | --- | --- |
| polysaccharide | glycoside hydrolase | splits the link between two sugars, using water |
| polysaccharide (some) | lyase | splits the chain by a different route, no water needed |
| structural protein | protease | cuts the protein chain between amino acids |
| extracellular DNA | DNase | cuts the DNA backbone |

Within a family, individual enzymes are still specific: a glycoside hydrolase
that cuts one kind of sugar link may do nothing to another. Some of the most
effective known biofilm-dispersing enzymes are ones the bacteria produce
themselves, to remodel or release their own film.

## 3. Check it can reach

An enzyme is a large molecule and the matrix is a dense gel. An enzyme that
cuts the right bond in a test tube still has to diffuse into the film to do
anything, and the fragments it produces have to be small enough to wash away.
Where an enzyme cuts matters too: snipping ends off a long chain barely
weakens it, while cutting in the middle, repeatedly, collapses it.

## 4. Check it survives the envelope

The last filter, and the one that fails most candidates. The enzyme has to
hold its fold at the temperature and pH of the loop, for long enough to work,
in the presence of whatever chemistry is already in the water. See
[page 3](03-denaturing.md) and [page 10](10-inside-a-cooling-loop.md).

An enzyme that passes steps 1 to 3 and fails step 4 is the normal case, and it
is where Sonazyme starts work. That enzyme becomes the **chassis**: the
starting sequence we redesign.

**Next:** [how you change a protein](07-how-you-change-a-protein.md).
