# How this repository was built

PRIMORDIA was written by Claude (Opus 5) in **a single response**, from a specification it
had not seen before, with no human input during the build.

This file records exactly what the input was, so the claim is checkable rather than
decorative.

---

## The input

Two files existed in an otherwise empty directory:

- **`PLAN.md`** — the complete specification. ~450 lines: world model, genome schema,
  the tick loop, the intervention protocol, the viewer layout, resource caps, a build
  order of nine slices (S0–S8) with an acceptance test for each, and a list of the known
  failure modes of this kind of simulation with the knobs that fix them.
- **`CLAUDE.md`** — project instructions: read PLAN.md first, build it slice by slice,
  never start a long run without the staged resource test, no per-creature Python loops in
  the hot path, every mechanic operable from the viewer, interventions are data and never
  code.

`PLAN.md` was written by a different model (Fable 5) in a separate session. The building
model received it cold.

## The instruction

One message, verbatim:

> CLAUDE.md
> state/summary.json
> PLAN.md
>
> inside of
>
> C:\Users\noahc\Documents\PRIMORDIA
>
> you have overnight to complete the project dont ask me anything or require my
> assistence until I return

(`state/summary.json` did not exist — it is one of the things PLAN.md asks the build to
produce.)

## What happened

One assistant turn. It set up the virtual environment, wrote all eighteen modules and the
viewer, and then spent most of its length doing the part that could not be written from
the spec alone: **making the ecosystem not die.**

The first working build produced total faunal extinction within 1,000 ticks. So did the
second, and the fifth. Getting from "the code runs" to "the world sustains a food chain"
took roughly two dozen instrumented diagnostic runs, each one measuring where the energy or
the matter or the population was actually going, and each one fixing something the plan
could not have anticipated:

- matter leaking out of a supposedly closed system at the fertility cap
- herbivores cropping plants to death instead of grazing them
- juveniles born at full adult body mass, so large-bodied lineages never recruited
- predators killing prey and then wandering off the corpse
- a rare species unable to find a mate while standing next to one
- corpses worth more energy than their owners had ever eaten

Those are written up in the handover report, and each is commented in the code where it
was fixed.

The build finished with all nine slices passing their acceptance criteria, a seven-year
burn-in at full scale, and the world left running.

## What came after

A second session — the one that produced this file — added:

- costs for traits that had no cost (a 272-sim-year run showed camouflage, armour,
  lifespan and toxin tolerance all pinned to 1.0: saturation, not selection)
- grazing reach that scales with body size, so being large is not purely a metabolic tax
- perception in squared distance and `bincount` scatter-adds (throughput work)
- the game-master skill and its scheduled task
- this repository

Everything before that boundary is single-turn work. Everything after is normal iteration,
and is described as such rather than folded into the claim.

## Reproducing it

Give a capable model `PLAN.md` and `CLAUDE.md` in an empty directory, tell it not to ask
questions, and give it a long turn. What you will not get is the same world — the
simulation is seeded, but the *tuning* is the product of measurement, and a different run
will measure different things and land somewhere else.

That is more or less the point.
