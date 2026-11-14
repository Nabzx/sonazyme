# Can acoustics see fouling in a loop, and what would it feed

- Date: 2026-11-14
- Issues: #56, #64, #65, #68
- Status: answered enough to act on, with two limits that change our framing

## The short answer

Yes, and it is already a product. Ultrasonic biofilm monitoring is practised
commercially in industrial cooling water, and at least one vendor claims it
separates soft biological deposits from hard scale. The peer-reviewed base is
strongest for membranes rather than pipes, and biofilm-specific acoustic
property data are sparse, which is consistent with the wide intervals our
forward model produces for a soft layer.

The two limits below matter more than the yes.

## What the literature and the market support

**Ultrasonic time-domain reflectometry on membranes.** The established
peer-reviewed line. Sim and colleagues report UTDR responses correlating with
transmembrane pressure and with biofilm thickness measured offline by confocal
microscopy, using a side-stream cell and a colloidal silica enhancer reported
as not affecting bacterial viability ([Monitoring membrane biofouling via
ultrasonic time-domain reflectometry enhanced by silica
dosing](https://nanyangtechnologicaluniv.demo.elsevierpure.com/en/publications/monitoring-membrane-biofouling-via-ultrasonic-time-domain-reflect)).
Earlier reverse-osmosis work reported detection of fouling layer initiation
and growth in real time.

**Heated-target sensors in cooling water.** The closest thing to our use case
is a commercial analyser that fires ultrasonic pulses at a **heated target**
and reads the reduction in travel time as biofilm. Its own page claims
measurement accuracy "around 10 microns" against a laboratory technique, says
it distinguishes soft deposits (organic and biological) from hard deposits
(scaling), and corrects for temperature, conductivity and pressure
([OnGuard 3B analyser for
biofouling](https://www.solenis.com/en/research-and-development/innovations/onguard-3b-analyzer-for-biofouling)).
Treat these as vendor claims: they are not peer-reviewed, and the page gives
no detection limit.

**Guided waves and pipes.** Work at Penn State relates guided-wave energy loss
to viscous or semi-solid loading on a pipe or plate ([ultrasonic guided wave
and acoustic impact methods for pipe
fouling](https://pure.psu.edu/en/publications/ultrasonic-guided-wave-and-acoustic-impact-methods-for-pipe-fouli/)),
and long-range ultrasonic testing has been applied to fouling in food
pipelines ([TWI](https://www.twi-global.com/technical-knowledge/published-papers/detection-of-fouling-in-food-pipelines-using-long-range-ultrasonic-testing-september-2009)).
A Brunel thesis reviewing guided-wave fouling detection calls it promising and
non-invasive but still early
([thesis](https://bura.brunel.ac.uk/bitstream/2438/20409/1/FulltextThesis.pdf)).

**More sensitive methods exist.** A heat-exchanger fouling paper proposes coda
wave interferometry for biofilm growth, cleaning and corrosion, arguing it is
more sensitive than classic acoustic methods, and reports that a biofilm along
the propagation path changes acoustic non-linearity, with the non-linearity
ratio decreasing as deposit thickness increases
([conference
paper](https://hal.univ-lille.fr/hal-03866991/document)).

**Machine learning on cheap sensors.** Fouling during cleaning has been
classified from low-cost ultrasonic sensors on plastic and metal pipes with
high reported confidence ([Nottingham
repository](https://nottingham-repository.worktribe.com/output/4341442/monitoring-the-cleaning-of-food-fouling-in-pipes-using-ultrasonic-measurements-and-machine-learning)),
though the fouling there is food soil rather than biofilm.

## Limit one: the sensor is a coupon, not the whole pipe run

Everything that works well works on a **prepared surface**: a membrane cell, a
heated target, a side-stream coupon. Nothing in what we found supports pinging
an arbitrary run of installed pipe and getting a thickness back.

That changes our framing, and it is an improvement rather than a loss. The
honest architecture is a side-stream or coupon sensor giving a well-posed
measurement at one point, plus inference about the rest of the loop from
hydraulics and position. Our loop map already carries a per-section `sensor`
flag, so the data model survives this; what changes is the claim.

Filed as a follow-up so the ADR and the loop map wording match this.

## Limit two: biofilm against scale is claimed, not published

The commercial claim of separating soft from hard deposits is plausible on
physics: a mineral deposit has an acoustic impedance far from water, while a
water-rich film has one very close to it. That is exactly the contrast our
forward model encodes, and it is why our estimate reports a hard layer
confidently and a soft layer with a wide interval.

What we did not find is peer-reviewed acoustic property data for biofilm
specifically. So:

- The assumed constants in `sense/acoustic.py` stay marked as assumptions.
- #68 stays open, narrowed: the question is no longer "can anything see it"
  but "what separation is achievable without a heated target".
- The honest demo line is that detection of *change* is well supported and
  identification of *what the change is* is supported commercially but not
  published.

## What this feeds

A reading tells the platform **where and when**, not what to make. It picks the
section a design run is about, it says whether a treatment moved anything, and
with a heated target it reports the quantity an operator actually cares about,
heat transfer loss, rather than a thickness nobody can act on.

## Recommendation

1. Keep the simulation (ADR-0013), and keep the wide intervals, which this
   research supports rather than contradicts.
2. Reframe the sensing claim from "ping the loop" to "a coupon or side-stream
   sensor, plus inference across the loop", in the ADR, the loop map and the
   pitch.
3. If a bench rig is ever built, copy the heated-target trick. It is the one
   design choice that turns a hard inverse problem into a readable one.
4. Add heat transfer loss as the output an operator wants, alongside
   thickness.

## Sources

- [Monitoring membrane biofouling via ultrasonic time-domain reflectometry enhanced by silica dosing](https://nanyangtechnologicaluniv.demo.elsevierpure.com/en/publications/monitoring-membrane-biofouling-via-ultrasonic-time-domain-reflect)
- [OnGuard 3B analyser for biofouling, vendor page](https://www.solenis.com/en/research-and-development/innovations/onguard-3b-analyzer-for-biofouling)
- [Ultrasonic guided wave and acoustic impact methods for pipe fouling](https://pure.psu.edu/en/publications/ultrasonic-guided-wave-and-acoustic-impact-methods-for-pipe-fouli/)
- [Detection of fouling in food pipelines using long range ultrasonic testing](https://www.twi-global.com/technical-knowledge/published-papers/detection-of-fouling-in-food-pipelines-using-long-range-ultrasonic-testing-september-2009)
- [Guided-wave fouling detection thesis, Brunel](https://bura.brunel.ac.uk/bitstream/2438/20409/1/FulltextThesis.pdf)
- [Coda wave interferometry for biofilm and fouling monitoring](https://hal.univ-lille.fr/hal-03866991/document)
- [Monitoring the cleaning of food fouling in pipes using ultrasonic measurements and machine learning](https://nottingham-repository.worktribe.com/output/4341442/monitoring-the-cleaning-of-food-fouling-in-pipes-using-ultrasonic-measurements-and-machine-learning)
