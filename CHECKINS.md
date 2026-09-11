# Check-in log

Periodic engine health checks on the running world — distinct from `interventions/done/`,
which is the game-master tending the *ecology*. This log is about whether the machinery is
sound: is the simulation alive, is matter conserved, has anything gone non-finite, is the
disk holding.

Newest first. `matter` is the invariant — this world is closed, so it should not move.

| date | year | pop | H/O/C | species | matter | verdict |
|---|---:|---:|---|---:|---|---|
| 2026-09-11 | 13,814 | 514 | 236/101/177 | 5 | 1.27324e+06 | **reseeded** after total extinction; 3 new genes, ocean niche opened |
| 2026-09-11 | 13,759 | 0 | 0/0/0 | 0 | 1.27324e+06 | **TOTAL FAUNAL EXTINCTION** — matter conserved, so ecological not corruption |
| 2026-09-11 | 13,451 | 361 | — | 1 | 1.27324e+06 | **found paused 11.7 h** by the resource watchdog; resumed, ladder made reversible |
| 2026-09-11 | 13,450 | 531 | 526/5/0 | 1 | 1.27324e+06 | healthy — **arms race over, prey won**; niche shut (`armed: false`), 260y without carnivores |
| 2026-09-10 | 13,023 | 228 | 193/24/11 | 3 | 1.27325e+06 | healthy — **`spikes` swept to 0.97 then relaxed; first co-evolutionary cycle** |
| 2026-09-10 | 12,878 | 498 | 297/185/16 | 4 | 1.27326e+06 | healthy — **trophic inversion**, mean diet 0.124 → 0.421 |
| 2026-09-10 | 12,507 | 177 | 140/37/0 | 4 | 1.27326e+06 | healthy — carnivores between episodes; still armed (2.26 vs 2.14) |
| 2026-09-10 | 12,461 | 551 | 404/123/24 | 4 | 1.27326e+06 | healthy — carnivores back and armed, best 2.441 vs 2.052 |
| 2026-09-10 | 12,292 | 411 | 393/18/0 | 3 | 1.27326e+06 | healthy — carnivores at zero (*read as "tier lost" at the time; it was a trough*) |
| 2026-09-09 | 11,360 | 422 | 262/154/6 | 7 | 1.27328e+06 | healthy — carnivores crashing 46 → 6, weapon still widespread |
| 2026-09-09 | 11,264 | 452 | 340/66/46 | 5 | 1.27328e+06 | healthy — population slide reversed, predator tier holding |
| 2026-09-09 | 11,171 | 245 | 160/54/31 | 10 | 1.27328e+06 | healthy — **first evolved carnivores**, zero warnings |
| 2026-09-08 | 8,927 | 499 | — | 6 | 1.27335e+06 | healthy — recovered from the second NaN death |

## Correction — the carnivore tier was never lost

Three separate check-ins recorded the carnivore tier as lost, once with the note that
`shear_tooth` had been "purged" from 0.617 to 0.078. That reading was wrong, and the
Chronicle says so plainly once the whole record is looked at rather than the moment in
front of you.

Carnivores have been present in **5,120 of 15,077 recorded years — 34% of this world's
history** — across 47 episodes lasting five years or more. The longest ran 202 years and
peaked at 729 individuals:

| years | duration | peak |
|---|---:|---:|
| 11,697–11,898 | 202 years | 729 |
| 12,422–12,441 | 20 years | 50 |
| 12,460–12,468 | 9 years | 28 |
| 12,493–12,503 | 11 years | 21 |

This is a predator–prey limit cycle with a period of roughly 10–30 years, not a tier that
cannot establish. Every "extinction" I recorded was a trough sampled at the wrong moment.
The lesson for anything reading this file: a single check-in cannot distinguish a cycle
from a collapse, and this world's cycles are shorter than the gaps between checks.

## The arms race (year 12,508 onward)

A `spikes` gene was added from the viewer's debug dropdown at year 12,508 — +0.6 effective
armour per unit, costing 12% basal and 25% movement. Two dull outcomes looked likely: it
would be stripped out as pure cost with almost nothing hunting, or it would sweep and shut
the predator niche permanently, since defence is amplified by the kill margin and attack is
not (prey at full expression reach a bar of 2.95 against a predator ceiling near 2.75).

Neither happened.

| | year 12,508 | year 12,878 | year 13,023 |
|---|---:|---:|---:|
| `spikes` | 0.063 | **0.971** | 0.845 |
| `shear_tooth` | 0.749 | 0.892 | 0.740 |
| `carrion_gut` | 0.816 | 0.950 | 0.696 |
| mean diet | 0.124 | **0.421** | — |

`spikes` swept to near-fixation in ~370 years and `shear_tooth` climbed with it rather than
being left behind. The niche never shut: the requirement stands at 2.128 against a best
living attack power of 2.226, so predators stayed marginally ahead through the whole ascent.
Both genes are now relaxing together as the carnivores fall back from a peak of 50. That is
a co-evolutionary cycle rather than a ratchet, and it is the first this world has run.

The larger result is the **trophic inversion**: mean diet moved 0.124 → 0.421, and for a
stretch omnivores outnumbered herbivores three to one — never true before across thirteen
thousand years of herbivore monoculture. `carrion_gut` reached 0.950 on the way, which is
almost certainly the mechanism: scavenging needs no attack power, so it pays for meat
digestion first and predation follows from ground already prepared. That is the bridge
across the adaptive valley that seven hand-seeded predator waves could never cross by force.

### How it ended (year 13,091 onward)

The race resolved, and the prey won it.

Years 13,091–13,190 were the most successful predator era this world has had — carnivores
present every single year for a century, peaking at **443**. That century of heavy predation
is exactly the pressure that pays for armour. The prey armoured up, the predators starved,
and the weapon went with them:

| | year 12,878 | year 13,450 |
|---|---:|---:|
| `spikes` (prey) | 0.971 | **0.864 — fixed** |
| `shear_tooth` (predator) | 0.892 | **0.094 — purged** |
| best living attack power | 2.236 | 1.684 |
| required to kill | 2.087 | 1.976 |
| `armed` | true | **false** |

Since year 13,191 the tier has been absent for 260 years — a handful of lone individuals and
nothing more. Unlike the three earlier occasions when this log wrongly called the tier lost,
the machinery agrees this time: nothing alive can kill anything.

Armour now has nothing to defend against, but its cost (12% basal, 25% movement) is one this
world can afford, so it has not eroded. **The niche is locked from the prey side.**

Note for anyone reaching for the documented fix: `energy.trait_cost_scale` **cannot** reach
this. It scales the built-in trait costs; `spikes` carries its own per-unit costs through the
effects system, untouched by that multiplier. Retiring `spikes` would drop prey defence by
~0.52 and take the requirement to ~1.26, well under what living animals already reach — but
that is a decision about what this world is for, not about whether it is healthy.

**2026-09-11 — the watchdog paused the world and could not un-pause it.** Found the
simulation stopped for 11.7 hours, tick frozen, `paused: true`. A GPU spike to 82°C — from
something that was not the simulation, which uses numpy for its fields — drove the resource
watchdog up its throttle ladder to the last rung, `pause`.

The ladder only went down. `_ease` decremented `throttle_level` on recovery and reversed
none of the actions: `max_pop` stayed cut, `target_fps` stayed halved, `tps_cap` stayed
capped, and `sim.paused` stayed set. Every rung was a one-way door, so a transient breach
from an unrelated program stopped this world permanently and quietly — the GPU was back to
46°C and throttle 0 while the world sat frozen.

`_ease` now reverses the step that took it to each level, restoring the original values
captured on the way up. Verified by driving all four rungs down and back: cap 3000 → 2700 →
3000, fps 4.0 → 2.0 → 4.0, tps_cap cleared, paused cleared.

**2026-09-11 — total faunal extinction at year 13,736, and it was not a bug.** Matter stayed
perfectly conserved at 1,273,237 throughout. The prey won their arms race and then died of
their own armour: `spikes` fixed at 0.86 costing 12% basal and 25% movement, and once the
predators were gone that was a permanent tax for a benefit that no longer existed, stacked
on `gut_ferment`, `winter_torpor`, `highland_lung` and `carrion_gut` still being carried and
paid for. The last eight animals ran a **basal upkeep multiplier of 2.334** and held 19.05
energy against a breeding threshold of 32.98. They were young, flora was at 7,400 and
climbing, and they could never save enough to breed. The biosphere went bankrupt paying for
armour against nothing, dwindling 504 → 183 → 102 → 0 over 300 years.

**The refounding.** `spikes` retired; three conditional genes added and three stocks seeded.
The design lesson from the corpse is that *an always-on cost with a situational benefit is a
slow death sentence*, so every new gene charges its carrier mostly where it also helps them:

| gene | benefit | cost |
|---|---|---|
| `mariner` | swim; −30% move cost and −0.4 detectability **in water** | +12% basal **on land** |
| `nocturne` | −0.55 detectability, +0.5 sense **at night** | +7% basal always |
| `sunleech` | +0.45 plant digestion, −20% basal **above temp 0.55** | −0.35 cold resistance |

Seeded stock carries `toxin_tolerance` 0.95 — not optional, since the flora has evolved
toxins to a mean of 0.561 (p90 0.953) over 13,000 years while cold-start animals arrive at
0.20.

**55 years later:** 514 animals, 236/101/177 across 5 species, no warnings. Basal upkeep is
**1.433** against the dead world's 2.334. And for the first time in this world's history the
ocean is inhabited — 84% of the surface is now water, and **42% of animals are in the deep**,
with `mariner` already sorting spatially: 0.370 in deep water against 0.104 on land.

## Incidents

**2026-09-08 — the world died twice.** Went non-finite at year 8525, twice, and the second
time ran on dead for 832 years writing NaN over every checkpoint. Root cause was not
ecological: eating is vectorised, so every animal on a shared cell read the same
availability and took its own share of the whole. Crowded, a cell served N times what it
held — and since carrion carries matter that is credited to the eater, and the eater's
matter returns as carrion when it dies, the duplicate compounded around that loop. Total
matter reached 7.9e37 and overflowed float32. Fixed by rationing per-cell demand; the world
was restored from the year 8500 archive. See `WORLD-LOG.md` for the timeline branch marker.

**2026-09-08 — the disk filled to 99.9%.** The world archived a full 28 MB checkpoint every
simulated year, which at fifty ticks a second is one every forty seconds of wall clock:
123 GB across 4,632 files. Archives are now thinned on write — newest 40 years plus one per
century.

**2026-09-09 — speciation had been impossible since year 964.** `max_species` counted every
species record ever created, including the extinct, so once 200 had *ever* existed the gate
read `200 < 200` and no new species could form again. Six thousand years of the era table in
`WORLD-LOG.md` show zero speciations because of it. The world's collapse to a single species
had been read as stagnation; it was a dead cap. The gate now counts the living.

## How to refresh

```bash
.venv\Scripts\python.exe tools\worldlog.py
```

Reads `state/summary.json` and `chronicle/chronicle.md`, writes `WORLD-LOG.md`. Safe to run
against a live simulation — it never writes to the world.
