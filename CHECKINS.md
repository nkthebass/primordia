# Check-in log

Periodic engine health checks on the running world — distinct from `interventions/done/`,
which is the game-master tending the *ecology*. This log is about whether the machinery is
sound: is the simulation alive, is matter conserved, has anything gone non-finite, is the
disk holding.

Newest first. `matter` is the invariant — this world is closed, so it should not move.

| date | year | pop | H/O/C | species | matter | verdict |
|---|---:|---:|---|---:|---|---|
| 2026-09-12 | 16,447 | 147 | 96/49/2 | 4 | 1.27322e+06 | **`graze_floor` 0.12 → 0.03** — the crash bottomed instead of going to zero. Under review |
| 2026-09-12 | 16,385 | 0 | 0/0/0 | 0 | 1.27322e+06 | **SEVENTH EXTINCTION** — 300 founders across 6 sites became **8,349 in one year**; dispersal is not the variable |
| 2026-09-12 | 15,568 | 0 | 0/0/0 | 0 | 1.27322e+06 | **SIXTH EXTINCTION** — 250 founders bred to 1,169 and crashed to zero in 38 years |
| 2026-09-12 | 15,530 | 250 | 250/0/0 | 1 | 1.27322e+06 | restored the **known-good** small-bodied state; the size question needs a human decision |
| 2026-09-12 | 15,419 | 0 | 0/0/0 | 0 | 1.27322e+06 | **FIFTH EXTINCTION** — 70 founders at size 0.62, no overshoot; size fell 0.60→0.096 in nine years |
| 2026-09-12 | 15,334 | 0 | 0/0/0 | 0 | 1.27322e+06 | **FOURTH EXTINCTION** — my own overshoot: 400 large animals into a world that carries 50–120 |
| 2026-09-12 | 15,227 | 900 | 900/0/0 | 1 | 1.27322e+06 | **third extinction diagnosed**: the Jarman-Bell term was switched off; size ratcheted to the floor. Reseeded |
| 2026-09-12 | 14,845 | 0 | 0/0/0 | 0 | 1.27322e+06 | **THIRD TOTAL EXTINCTION** — diet held at 0.12; they shrank to 0.070 and could not collect enough to breed |
| 2026-09-11 | 14,360 | 1,180 | 1180/0/0 | 4 | 1.27324e+06 | **second extinction diagnosed**: carnivory was unconditionally subsidised; discount cut, reseeded herbivore-only |
| 2026-09-11 | 14,026 | 0 | 0/0/0 | 0 | 1.27324e+06 | **SECOND TOTAL EXTINCTION** — diet had swept to 0.955 in a world with no prey and 10,264 uneaten flora |
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

## The thing that was actually killing it (year 14,026)

Two extinctions three hundred years apart, and I read the first one wrong — "the prey died of
their own armour" was a true description of the last eight animals and the wrong cause. The
archives say what really happened, and they say it about both deaths.

| | year 13,900 | year 14,000 |
|---|---:|---:|
| animals | 241 | 41 |
| **diet, mean** | **0.891** | **0.955** |
| **diet, minimum** | **0.596** | **0.857** |
| body size, mean | 0.073 | 0.096 |
| flora biomass | 6,751 | 10,264 |

There was not one plant-eater left alive in the world. Not a scarce one — the *minimum* diet
across every living animal was 0.596, then 0.857. They were standing in a meadow that was
growing faster than anything could eat it, and every one of them had evolved to be unable to
eat it. The population then lived for two more centuries on its own corpses (`corpse_energy_frac`
is 0.95, so a dead animal returns almost everything it held) while shrinking toward the size
floor, and then there was nothing left to recycle.

The cause is two subsidies to carnivory that both pay **whether or not any prey exists**:

- `energy.carnivore_basal_discount` **0.5** — basal upkeep is multiplied by `1 - 0.5 × diet`.
  A pure carnivore runs at half the metabolic cost of a pure herbivore of the same body, in
  perpetuity, for free.
- `energy.gorge_meat` **4.0** — meat intake is `bite × 1.2 × (1 + 4 × meat_digest)`, so a
  mouthful of meat is up to **six times** a mouthful of grass.

Half the upkeep and six times the intake makes herbivory a strictly dominated strategy. Diet
ratchets to 1.0, the plant-eaters convert *themselves* out of existence within about twenty
years of any seeding, and the all-carnivore world that remains eats its own dead until it
stops. Both extinctions ran that script, and so, almost certainly, did the thirteen thousand
years of trophic instability before them — including every one of the seven hand-seeded
predator waves that "failed to establish". They did not fail. They won, immediately and
completely, and that was the problem.

Both numbers were put there for good reasons. `gorge_meat` fixed a real measurement — a hunter
needed fifty ticks to strip a carcass it stood on for four — and `carnivore_basal_discount` is
PLAN §13's leaner predator. Neither was wrong on its own; stacked and unconditional, they were
a law of nature that said *stop eating plants*.

**The amendment (year 14,352).** `carnivore_basal_discount` 0.5 → **0.12**, `gorge_meat`
4.0 → **2.5**. A carcass is still a concentrated meal at 3.5× a sward, and a predator still
runs leaner — it is just no longer paid for prey it has not caught.

**The refounding, second attempt.** No carnivores seeded. The tier evolved by itself once
before, from `carrion_gut` by way of scavenging, and every hand-seeded wave has inverted the
pyramid instead. 1,180 grazers in three stocks, `diet` 0.05–0.06, `toxin_tolerance` 0.95,
body size 0.38–0.45 (the dead world ended at 0.073).

One new gene, aimed squarely at the asymmetry that `gorge_meat` created:

| gene | benefit | cost |
|---|---|---|
| `broad_crop` | mouthful ×2.1 at full expression | **attack power −0.8**, move cost +35% |

A broad cropping jaw cannot kill. It is the first gene in this world that a carnivore can
never profitably carry, which is the point — it gives the herbivore tier something the
predator tier is structurally unable to take from it.

**And a discovery from the terrain.** Twelve thousand years of cratering against volcanic
uplift has left **6.7% of the surface as land** — 9,858 cells of 147,456. But 7,907 biomass of
flora is growing in shallow water, which is **38% of all the plant life in the world**, and
nothing in this world's history has ever been able to reach it. Two of the three stocks are
swimmers (`mariner` 0.85–0.9, `tide_limb` 0.75–0.8) seeded onto the drowned shelves. Half the
larder has been sitting there uneaten since the seas rose.

**2026-09-11 — the chronicle panel was frozen for 340 years and the bug was in one missing
word.** The viewer's chronicle sat on `Year 14032 — 0 herbivores, 0 omnivores, 0 carnivores`
while the map, the graphs and the population counters an inch to its left were live at year
14,371. The file on disk was current, `/api/chronicle?n=45` returned current data to `curl`,
and the `/chronicle` page was current. The panel polls every three seconds and every one of
those polls was being answered by the browser's HTTP cache: `api()` in `viewer/index.html`
called `fetch(p, o)` with no cache directive, against a fixed GET URL, so the first response
of the session was the only one that ever arrived. `viewer/chronicle.html` had passed
`{cache:"no-store"}` by hand from the start, which is why that page was fine and this one was
not. The helper now sets it for the whole viewer. Anyone whose tab predates this needs one
hard refresh to pick up the new `index.html`.

### Did the amendment work?

The test is not whether the population survived — it is whether `diet` still ratchets when
the world fills with corpses, which is the condition that killed it twice. Over the first
twelve years the seeded grazers overshot hard, stripping 25,219 biomass of thirteen-thousand-
year-old standing crop down to 1,870 and leaving 1,200–1,900 of carrion lying on the ground:

| year | pop | flora | carrion | **diet** |
|---:|---:|---:|---:|---:|
| 14,365 | 2,597 | 3,828 | 1,932 | 0.125 |
| 14,366 | 2,458 | 2,858 | 1,541 | **0.141** |
| 14,368 | 2,594 | 1,971 | 1,424 | 0.117 |
| 14,370 | 1,898 | 1,975 | 1,183 | 0.132 |

Diet rose under peak carrion and came back down. That is a gradient with a restoring force,
where before it was a one-way door — under the old laws this exact condition took it from
0.42 to 0.955 and did not return. Flora decelerated into an equilibrium near 1,900 instead of
running away to 24,000 uneaten, which is the first grazing equilibrium this world has held.
Nine species inside twelve years, and the first carnivores appeared on their own — one and
two at a time, evolved rather than seeded, which is how the tier is supposed to arrive.

## Why nothing here has ever been big (year 14,845)

The diet fix held — across the whole 300-year decline `diet` stayed between 0.117 and 0.130
while flora climbed 1,666 → 3,748 → 17,297. Nothing converted itself into a carnivore this
time. They died of something older.

| year | n | **size** | energy | breeding bar | flora |
|---:|---:|---:|---:|---:|---:|
| 14,500 | 377 | **0.072** | 11.69 | 21.5 | 1,666 |
| 14,600 | 183 | **0.065** | 12.71 | 22.3 | 2,167 |
| 14,700 | 307 | **0.071** | 11.78 | 22.0 | 2,875 |
| 14,800 | 229 | **0.070** | 13.08 | 22.2 | 3,748 |

Seeded at 0.38–0.45, at the floor of 0.05 within 140 years. **A 0.07 animal has a 0.07
mouthful.** They sat 40% short of the breeding bar for three centuries with the larder filling
up behind them — not starving for lack of food, starving because they had evolved mouths too
small to collect it.

Size ratchets down because there is no return on body mass in this world. Basal cost scales as
`size^0.75`, so small is strictly cheaper, and the only benefit of being large is a bigger
bite — which local plant density caps. `primordia/fauna.py:522` says so in as many words:

> *Jarman-Bell: a larger gut holds forage longer and extracts more from it. Without a
> size-dependent quality term the only return on body mass is a bigger mouthful, which local
> plant density caps — so every lineage shrinks to the floor and leaves nothing big enough to
> be prey.*

`energy.digest_size_gain`, the knob that implements that term, was **0.0**. The effect was
written, documented, wired into `plant_digest` and then switched off.

This is not only the third extinction. It is the answer to a question this log has asked for
six thousand years: there has never been anything big enough to be worth hunting. Every
predator tier that flickered and died was hunting animals the size of a mouthful.

**The amendment.** `digest_size_min` 1.0 → **0.70**, `digest_size_gain` 0.0 → **1.30**. Intake
now scales as `size × (0.7 + 1.3 × size)` against a cost of `size^0.75`: from 0.05 to 0.35 that
is **10.6× the income for 4.3× the bill**, so being small stops paying. The cap on local plant
density stays as the brake on runaway gigantism, which is what makes the optimum interior and
habitat-dependent rather than a new ratchet pointing the other way.

Reseeded 900 grazers at size 0.45–0.62 with `gut_ferment` 0.90 — it was at 0.928 and nearly
fixed when they died. That lineage had solved digestion and was beaten by its own body plan.

**No swimmers this time.** Two separate stocks were handed `mariner` and `tide_limb` at
0.85–0.9 and both collapsed to 0.11 and 0.05. The water is not being refused for want of the
gene, so forcing it a third time would tell me nothing I have not already been told twice.

**2026-09-12 — the disk filled again, in the other direction.** `state/` hit the 8 GB ceiling.
Not the archives, which have been thinned since September: the *timelapse*. `Sim._snapshot`
wrote a PNG every `snapshot_every` ticks and never removed one — **43,190 files, 3.6 GB**,
larger than the checkpoint archive beside it. This is the identical unbounded-growth bug that
took the disk to 99.9% in September; it was fixed for the archives and missed for the
snapshots sitting in the same directory. `_prune_snapshots` now mirrors `_prune_archive`:
newest 600 frames at full cadence, then one per 200,000 ticks, so the timelapse still spans
the whole history at a coarser step. Caught up in place — 42,445 frames removed, 3.36 GB
reclaimed, `state/` 8.0 GB → 4.6 GB, no restart needed.

## Two more deaths, one of them mine, and the real shape of the size problem

**Year 15,334 — the fourth extinction was my error.** I reseeded 900–1,180 animals at size
0.38–0.62 three times and called each one an experiment. The world's own record says what it
carries — 241 animals at year 13,900, 585 at 14,548, 229 at 14,800, all at size ≈ 0.07. Basal
cost scales `size^0.75`, so a 0.60 animal costs 5× a 0.07 one: capacity is **50–120 large
animals**, and I put 400 into a world already holding 590 small ones. That is self-amplifying
rather than merely wasteful — a crowd that size strips biomass below `graze_floor` 0.12, and
since harvest is `max(0, biomass − floor)` the yield below the floor is *exactly zero*, so the
crash takes the residents who would have persisted. I built that.

**Year 15,419 — the fifth was the clean experiment, and it answered the question.** Seventy
founders at size 0.62 on the richest ground on the map, below the estimated capacity, into
5,754 biomass with 81% of vegetated cells harvestable. No overshoot. They bred to 410, and
then:

| year | 15,402 | 15,404 | 15,406 | 15,407 | 15,411 |
|---|---:|---:|---:|---:|---:|
| **size** | **0.601** | 0.352 | 0.173 | 0.121 | **0.096** |

Nine years. That reads as impossible for a gene with `mut_std` 0.045 until you count
generations rather than years: these animals breed on a cooldown of order 100 ticks against
2,000 ticks in a year, so nine years is **200–300 generations**, and a selection differential
of 0.003 per generation is all it takes. It is selection, it is relentless, and `reach` did
not touch it.

### Why no fix of that class can work

I had been computing income over cost — a ratio of *means*. What selects here is **variance**:

```
cap_e = max_store × (0.35 + size)        basal = 0.1 × size^0.75

size 0.07   store ×0.42   cost ×0.136   endurance 3.09
size 0.20   store ×0.55   cost ×0.299   endurance 1.84
size 0.40   store ×0.75   cost ×0.503   endurance 1.49
size 0.62   store ×0.97   cost ×0.699   endurance 1.39
size 1.00   store ×1.35   cost ×1.000   endurance 1.35
```

Endurance — how long an animal lives on a full stomach — **falls monotonically with mass**,
and it cannot be repaired by making food more rewarding, because it is not about the mean
meal. It is about the gap between meals, and this world has a day–night cycle, four seasons
and patchy grazing. Every night is a fast; a large animal fasts at five times the rate with
two and a third times the tank. Being large here is a bet that the next meal comes soon, and
the small animal wins that bet three times as often.

`digest_size_gain` and `reach_size_min` were both written to solve this and both were left
disabled by sentinels. Both are now enabled and the ratchet is unchanged — which says the
mechanism was never in the numerator.

**This needs a decision that is not mine.** Making large bodies viable means changing how
storage scales with mass — the `(0.35 + size)` term in `cap_e`, or the `size^0.75` exponent on
basal cost. That is a choice about what this world is *for*, in the same sense as the note
above about retiring `spikes`, and it is the difference between a world of tiny grazers that
runs forever and a world that can carry a food chain. **A predator tier requires it**: nothing
in fifteen thousand years has ever been big enough to be worth hunting, and that is the same
fact as this one.

**What was done instead.** Life restored in the configuration this world has actually
demonstrated it can hold: 250 founders at size 0.12 carrying what the successful lineage
carried — `gut_ferment` 0.90, `toxin_tolerance` 0.95, a low breeding threshold — into 7,900
biomass of standing crop. Not a fix, and not claimed as one; the world's own known-good state,
restored, so it is alive and stable while the question waits for an answer.

## The floor had no bottom (years 15,568 and 16,385)

Two more deaths, and between them they eliminate every explanation except one.

**Year 15,568.** 250 founders at size 0.12 — what I had called the world's known-good state —
bred to 1,169, stripped flora 6,639 → 2,640, and crashed 222 → 44 → 2 → 0 in thirty-eight
years. I had mislabelled that seeding: the 241 / 585 / 229 populations in the record were
*evolved* and spread over the whole map, not 250 animals dropped into one disc. Every seeding
this session started 10–30× over local carrying capacity — 250 in radius 14 is 0.41 animals
per cell against 0.027 for a stable 400 spread over the world's 14,800 land cells.

**Year 16,385 — and this is the one that settles it.** 300 founders across **six
well-separated sites**, 50 each at radius 30, which is 0.018 per cell, below the density the
world sustained rather than thirty times above it. One year later there were **8,349 animals**.
A 28-fold increase. Dispersal changed nothing, because each site grew to 1,400 by itself.

Seeding density is not the variable. Reproductive rate is, and no founder count avoids an
overshoot when the population multiplies twenty-eight-fold in a single year. Which leaves only
the mechanism that turns an overshoot into an extinction:

```python
avail = np.maximum(0.0, self.flora.biomass[cy0, cx0] - float(cfg_f["graze_floor"]))
```

With `graze_floor` at **0.12**, yield below the floor is not small — it is *exactly zero*. So a
grazing crash has no bottom. 8,349 animals take the mean cell from 0.30 to 0.055, **every cell
in the world reaches zero yield at the same moment**, and the entire fauna starves regardless
of body size, diet, gene loadout or starting position. All seven deaths on the seeded side ran
that script, and so, most likely, did the depletion phase of the three before them.

### The change, and why it is a change to a law rather than a repair

The floor's stated purpose is sound — flora stripped to death cannot regrow, and the food chain
follows. The *number* is wrong by more than an order of magnitude. `primordia/flora.py:167`
kills a cell only when biomass falls below **5e-3**:

```python
dead = alive & ((self.age > max_age) | (self.biomass < 5e-3))
```

So the floor protecting regrowth sat **24× higher than the threshold it was protecting**.

`graze_floor` **0.12 → 0.03** keeps a six-fold margin over the death threshold, preserves the
mechanism exactly as intended, and moves the yield cliff far below the densities a grazing
population actually visits. At the crash density of 0.055 per cell, yield goes from nothing to
0.025 — the difference between a low equilibrium and an empty world.

**This wants a second pair of eyes.** If 0.03 is too permissive the failure mode inverts:
herbivores graze cells down past 5e-3, the flora dies locally rather than recovering, and that
is worse than what we have. The first thirteen years say the crash now bottoms out — 120
founders → 1,427 → 397 → 174 → 227 → 147, holding instead of falling to zero, with flora at
608 and still yielding — but thirteen years is not a verdict.

### Also reverted: a tax I should never have levied

Setting `digest_size_min` to 0.70 to give large bodies a return cut small-animal digestive
yield by **21% at size 0.07 and 14% at 0.12** — it made the only strategy this world has ever
sustained materially poorer, and I then reseeded into it. Back to **1.0**, with
`digest_size_gain` left at 1.30, so quality is `1.0 + 1.3 × size`: at least as good as the
original at every body size, and still rewarding mass. There was never a reason to pay for the
large-body bonus out of the small-body baseline.

### Still open, and not mine to decide

- **How energy storage scales with mass.** `cap_e = max_store × (0.35 + size)` against
  `basal = 0.1 × size^0.75` makes endurance fall monotonically with body size, so large bodies
  lose every fast — and this world fasts every night and every winter. No change to food
  reward can reach it. A predator tier requires it: nothing in sixteen thousand years has been
  big enough to be worth hunting.
- **Whether the fauna should be able to breed 28-fold in a year at all.** `founder_energy_mult`
  is 3.5 and the breeding bar is ~20, so founders arrive with three and a half start-energies
  and so do their children. Every seeding is an irruption by construction.

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
