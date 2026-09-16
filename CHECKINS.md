# Check-in log

Periodic engine health checks on the running world — distinct from `interventions/done/`,
which is the game-master tending the *ecology*. This log is about whether the machinery is
sound: is the simulation alive, is matter conserved, has anything gone non-finite, is the
disk holding.

Newest first. `matter` is the invariant — this world is closed, so it should not move.

| date | year | pop | H/O/C | species | matter | verdict |
|---|---:|---:|---|---:|---|---|
| 2026-09-16 | 15,800 | 1,043 | 1022/21/0 | 5 | 1.27319e+06 | **TIMELINE BRANCH** — restored from year 15,800 after a nine-year collapse with no identifiable cause |
| 2026-09-16 | 16,523 | 0 | 0/0/0 | 0 | 1.27319e+06 | **THIRTEENTH EXTINCTION** — 219 → 0 in nine years from a healthy population; evidence pruned before it could be read |
| 2026-09-15 | 15,470 | 436 | 422/14/0 | 6 | 1.27320e+06 | continent split in two; watcher settled the new landmass unprompted. Cooldown fix holds |
| 2026-09-14 | 13,145 | 131 | 41/85/5 | 4 | 1.27324e+06 | watcher seeded the island 6× in 630 years and kept it grazed; fixed its cooldown key and the archive pruner |
| 2026-09-14 | 12,400 | 511 | 425/85/1 | 7 | 1.27326e+06 | **TIMELINE BRANCH** — restored from year 12,400; `tools/island_watch.py` now recolonises empty islands |
| 2026-09-14 | 13,370 | 0 | 0/0/0 | 0 | 1.27325e+06 | **TWELFTH EXTINCTION** — the year-11,900 restore; 92% of all food ended up on one island with no animals |
| 2026-09-13 | 11,900 | 305 | 234/66/5 | 6 | 1.27327e+06 | **TIMELINE BRANCH** — restored from year 11,900; the year-14,500 lineage was dying of a spatial trap |
| 2026-09-13 | ~14,791 | 0 | 0/0/0 | 0 | 1.27323e+06 | **ELEVENTH EXTINCTION** — the year-14,500 restore died within 50 years of where the original timeline died |
| 2026-09-13 | 14,500 | 358 | 334/24/0 | 8 | 1.27323e+06 | **TIMELINE BRANCH** — restored the world from its own year-14,500 checkpoint after ten failed seedings |
| 2026-09-13 | 18,442 | 0 | 0/0/0 | 0 | 1.27322e+06 | **TENTH EXTINCTION** — irruption solved (350→433), still died; the breeding bar ratcheted 21.5 → 39.4 |
| 2026-09-13 | 17,421 | 0 | 0/0/0 | 0 | 1.27322e+06 | **NINTH EXTINCTION** — proven genome + evolved brains cut the irruption 28× → 4× |
| 2026-09-12 | 16,463 | 0 | 0/0/0 | 0 | 1.27322e+06 | **EIGHTH EXTINCTION** — `graze_floor` 0.12 → 0.03 moved the cliff, it did not remove it |
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

**It did not work.** I reported after thirteen years that the crash had bottomed out, and said
thirteen years was not a verdict. It was not, and the verdict went the other way — the world
died at **year 16,463**, about twenty years later:

```
16,441  pop 174  flora 733     16,455  pop 108  flora 604
16,444  pop 227  flora 798     16,457  pop  16  flora 662
16,447  pop 147  flora 608     16,460  pop  42  flora 708
16,452  pop 118  flora 572     16,463  pop   0  flora 791
```

The change moved the cliff instead of removing it. The population simply grazed down to the
*new* floor: standing crop settled at 572–798 over ~19,000 vegetated cells, which is ≈0.03 per
cell — exactly the new value. A fauna that multiplies twenty-eight-fold in a year grazes to
whatever floor exists, so **an absorbing floor at any value gives the same outcome.** The
reasoning stands as a consistency repair (24× above the death threshold was incoherent) but the
hypothesis that it would prevent extinction is falsified.

### The measurement I should have taken first

With the world empty and nothing eating it, net flora production is **tens of biomass per
year** — 76/yr at a crop of 2,000, 29/yr at 3,000, 22/yr at 4,800, 20/yr at 5,700 — and the
grazed equilibrium sat at a crop near 600, where it is lower still. That number bounds
everything else in this log, and I tuned digestion, reach, body size, seeding density and the
graze floor for an entire session without once measuring it. Eight reseedings, and the first
question — *can this world's plant growth support a fauna at all?* — went unasked.

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

## What ten failed seedings were actually measuring

Two of the three things I spent the session tuning turned out to be real, and neither was the
cause.

**The brain was real.** Every founder I made in eight attempts got a *random* brain damped to
`founder_brain_quiet` 0.35 with a fourteen-weight grazer prior over it — because with no living
donors that is what `seed_organism` does, and I never noticed that the 167 brain weights are
addressable by name (`w000`–`w165`) like any other gene. Those animals wandered more or less at
random and ate whatever they stood on, in a world whose residents had spent fourteen thousand
years learning where food is. Seeding five *real* animals out of the year-14,500 archive with
all 167 of their own weights cut the irruption from **28-fold to 4-fold** — the first change in
the whole session that moved that number.

**Arrival wealth was real.** `founder_energy_mult` 3.5 lands founders at ~77 energy against a
bar near 21, so every one breeds on arrival and so do its children. Dropping it to **1.0** cut
the irruption again, to **1.24-fold**: 350 founders became 433, not 8,349.

**And neither saved them**, which is what finally identified the actual mechanism.

### The ratchet that closes every crash

From the last seeding, as the population fell:

| | | | | | | | |
|---|---:|---:|---:|---:|---:|---:|---:|
| **breeding bar** | 21.5 | 22.3 | 24.3 | 26.7 | 29.1 | 31.5 | **39.4** |
| **% able to breed** | 11 | 17 | 5 | 13 | 10 | 16 | **0** |

The final two animals held **38.2 energy against a bar of 39.4**. They were not starving. They
were rich, and they could not breed.

During a famine an animal that breeds gives its energy away and dies; an animal that hoards
survives. So a crash selects — hard, and within tens of generations — for exactly the
individuals least able to end it. `repro_threshold` ratcheted 0.21 → 0.81, and by the time the
grass came back the only survivors were constitutionally incapable of using it. The flora was
*recovering past them* the whole way down.

That is why every crash in this world is absorbing, and it is not a problem of numbers. It is a
problem of **which** animals the famine leaves behind. A founding population built from five or
seven archetypes carries no reservoir of low-threshold breeders to ride it out. A real
population of 377 does.

### The restore (2026-09-13)

So I stopped founding a biosphere and restored one. The world runs again from its own
**year-14,500 checkpoint** — 377 animals, 8 species, `repro_threshold` mean 0.182, every array
verified finite before the restore. The dead state is preserved as
`archive/pre-restore-dead-world-y19490`, and the Chronicle keeps every entry from the rewound
years; nothing is erased.

**No laws changed with the restore.** The checkpoint carries four tuned values —
`trait_cost_scale` 0.25, `growth_scale` 0.13, `carnivore_basal_discount` 0.12, `gorge_meat`
2.5 — which include the one fix from this session that was ever verified, the carnivory subsidy
that held for three hundred years. The six I added afterwards went with the rewind and stay
gone. This population was stable in exactly this configuration for thousands of years, and
adding laws to a freshly restored living world is the mistake I made all session. The open
design questions can now be tested one at a time against a world that is alive to test them on.

### Corrections to earlier entries in this file

- **Gross primary production is not the constraint.** 180,788 biomass/year against a standing
  crop of 8,868. The flora-productivity worry raised in PR #3 was wrong.
- **Mean energy near 12 against a breeding bar near 21, with only 11–16% of animals above it,
  is this world's NORMAL state** — true of every healthy archived population from year 9,900
  onward. I read it as starvation at least four times and intervened against it each time.

## The year-14,500 population was already dead (2026-09-13)

The restore from year 14,500 died at about year **14,791**. The original timeline died from
that same checkpoint at **14,845**. Two independent runs from one state, both dead inside three
hundred years: that population was dying when I restored it, and I restored it because it
*looked* healthy by every number I was checking.

It was not food, toxins, or the `repro_threshold` ratchet:

| year | health | food energy kept | breeding bar | breeding |
|---:|---:|---:|---:|---:|
| 11,900 | 0.981 | 99% | 21.9 | 11% |
| 14,500 | 0.982 | 99% | 20.5 | 11% |
| 14,700 *(restored run)* | 0.974 | 97% | 19.7 | **5%** |

Energy was the only gate that moved. Mean energy fell to **9.4**, the lowest of any archive,
with 5,000–7,000 flora standing. The animals were surrounded by food and still under-earning.

### It was geography

Share of all harvestable food in the world lying near *some* animal:

| year | rich cells | median distance to rich cell | within 4 cells | **within 12 cells** | `sense_range` |
|---:|---:|---:|---:|---:|---:|
| 11,900 | 362 | 3.0 | 24.9% | **66.7%** | 0.339 |
| 12,900 | 648 | 2.8 | 21.5% | **60.7%** | 0.621 |
| 14,500 | 270 | 7.1 | 23.2% | **52.9%** | 0.336 |
| 14,600 | 1,288 | 5.0 | 4.7% | **11.6%** | 0.371 |
| 14,700 | 5,115 | 7.0 | 1.6% | **3.3%** | **0.193** |

The flora bloomed across the map — rich cells multiplied nineteen-fold — and the animals
never went to it. They could not perceive it. Sense radius is `1 + sense_range × MAX_SENSE`
with `MAX_SENSE` 12, so `sense_range` 0.193 is about **three cells**, and the nearest rich
cell was a median **seven** away.

Sensing costs upkeep (`cost_sense` × `trait_cost_scale`), so short sight pays while food is
underfoot — and becomes a trap the moment the local patch is grazed out. The population
contracts onto its own depleted ground (occupied cells 303 → 185), stops being able to find
the grass growing everywhere else, and starves inside sight of a bloom it cannot see.

The year-14,500 state was already on that path — only 270 rich cells, median distance 7.1,
the worst of the healthy archives — which is why every run from it died the same way. **A
checkpoint is not healthy because its population is alive; it is healthy if its population
can still reach its food.**

### The restore

The world runs again from **year 11,900**: 391 animals, 15.3% land (it has eroded to ~10%
since), two thirds of all food within twelve cells of an animal, stable for centuries, and from
before `spikes` existed. It carries only the two laws it lived under for millennia —
`trait_cost_scale` 0.25 and `growth_scale` 0.13.

**The carnivory fix was deliberately not re-applied.** That subsidy only ever proved lethal in
worlds I seeded by hand; this evolved world ran predator–prey cycles under it for nearly two
thousand years. The restored world came back with a living carnivore tier.

Everything rewound is kept: `archive/pre-restore-dead-world-y15041`,
`archive/pre-restore-dead-world-y19490`, and every Chronicle entry from both branches.

### The power cut

The shutdown on 2026-09-13 left **1,152 NUL bytes** in `chronicle.jsonl` and **841** in
`chronicle.md`, at the exact instant of the cut — pre-allocated file space that was never
written. The reader skipped them, but `grep` treated the whole file as binary. Stripped with
the sim stopped, backups kept as `*.pre-nul-strip.bak`; all 167,634 lines parse.

## The food was across the sea (2026-09-14)

The year-11,900 restore died at **year 13,370** with no intervention of any kind, and it broke
the explanation I had just committed. Health held at 0.99, the breeding bar at 19.6–21.5, diet
stayed herbivorous — and at year 13,100 `sense_range` was **0.732**, a ten-cell radius, while
90% of the food was still out of reach. Short sight was not the cause. The spatial-trap
section above is right about *what* happened and wrong about *why*.

**The check-in at year 12,636 also misread it.** It reported food-within-reach at 22.4% as "the
world's graze cycle", because that number had bounced from 27% back to 78% twice. The archives
say 12,600 was already the start of the slide.

### Islands

Erosion and cratering have split the walkable land (`water_depth < 0.2`) into three masses.
Movement blocks water deeper than 0.25 unless `swim_eff` exceeds 0.45, and no population here
has held that. So each landmass keeps its own herd, and the smallest — about 3,600 cells near
(228,293) — is marginal:

| year | the island | food on it | share of all food on **empty** land |
|---:|---|---:|---:|
| 11,900 | 115 animals | 60 | 0% |
| 12,000 | **empty** | 404 | 27% |
| 12,200 | **empty** | 2,078 | 67% |
| 12,300 | 101 animals *(recolonised)* | 88 | 0% |
| 12,400 | 77 animals | 55 | 0% |
| 12,500 | **empty** | 457 | 41% |
| 12,800 | **empty** | 3,195 | 89% |
| 13,200 | **empty** | 6,105 | **92%** |

The island's herd winks out. With nothing grazing it, its flora balloons until that one empty
island holds nine tenths of all harvestable food in the world, while ~400 animals grind the two
big landmasses down to ~300 and starve on them. It had refilled on its own once, from 12,200 to
12,300; the second gap did not close. The year-14,500 lineage almost certainly died the same
way, and its "short sight" was a consequence of crowding onto depleted ground, not the cause.

### What was done

**Restored to year 12,400** — the latest save with all three landmasses occupied (240, 67, 77
animals), no food on empty ground, every array finite. No laws changed.

**`tools/island_watch.py`**, running detached beside the simulation. Every two minutes it reads
the newest checkpoint, labels the walkable landmasses (joining across the x-wrap), and looks for
one of ≥1,000 cells with ≥100 harvestable biomass and **no animals**, while ≥40 are alive
elsewhere. It then writes an ordinary intervention: a signed note, and `seed_organism` of 40
founders at the landmass's deepest interior point with an **empty genome** — which, with living
donors, copies residents whole, body and all 167 brain weights. That is the only seeding path
that has worked in this world. Once per century per landmass at most. If everything is dead it
logs and does nothing: founding into an empty world stays a human decision.

Verified before it ran, by dry-running it against the archives: no action at 12,400; seed 40 at
(228,296) r16 at 12,500, 12,600 and 12,800; log-and-hold at 13,400. It writes data through the
intervention folder and touches the simulation in no other way.

**It must be restarted after a reboot**, like the simulation itself:

```
Start-Process -FilePath '.venv\Scripts\python.exe' -ArgumentList 'tools\island_watch.py' -WindowStyle Hidden
```

Dead state kept as `archive/pre-restore-dead-world-y13458`.

## The watcher's first 750 years, and two bugs it surfaced (2026-09-14)

**It works.** `tools/island_watch.py` seeded the ~3,600-cell island near (228,292) six times
between years 12,435 and 13,065. Its founding parties did establish — the island held **247
animals at 12,600** and 81–94 at 12,900–13,000 — and while they held it the island's share of
the world's food stayed at **6–24%**, against the 92% that killed the previous world. Every
party has eventually died out; this island cannot hold a herd for long. But the world is alive
at year 13,145, past the point where the unwatched run from 11,900 was already starving, and
the island's food is at 33% rather than running away.

**Bug: the once-a-century limit did not hold.** The watcher keyed each landmass by the 16-cell
grid square of its deepest interior point, and that point drifts as the coast erodes — (228,292),
(231,287), (233,286), (230,288) — so the key flipped between `14:17` and `14:18` and the island
was seeded at 13,020 and again at **13,065, forty-five years apart**. An earlier seeding now
counts if it lies within 40 cells or anywhere on the same landmass. Dry-run on the live
checkpoint: no action under either key inside the cooldown, seeds once it has expired, still
silent when every landmass is occupied.

**Bug: every restore silently deleted the live run's yearly archives.** `_prune_archive` kept
"the newest 40 years" by *year number*. After three rewinds the highest year numbers on disk
were 19,452–19,491 of a dead timeline, so each yearly archive the restored world wrote was the
lowest-numbered file on disk and was deleted the moment it was written. The live run was left
with nothing finer than one save per century — which is why the island's history above could
only be read at hundred-year resolution. The pruner now ranks by write time. Verified after
restart: years 13,144 and 13,145 kept, the dead timeline's yearly files draining (20 → 18),
no century archive touched.

**Still below normal:** only 6% of animals are above their breeding bar, against 11–16% in
healthy eras. The bar itself is flat at 21.0, so it is not the ratchet — but it is the number to
watch next.

## The continent broke, and the watcher settled it (2026-09-15)

Two thousand three hundred years on from the restore, and the map is not what it was. At year
12,400 there were three walkable landmasses: 19,062 / 4,833 / 3,741 cells. At year 15,470 there
are **four**:

| landmass | animals | share of the world's food |
|---:|---:|---:|
| 10,193 cells | 286 | 50% |
| 4,950 cells | 66 | 11% |
| 4,583 cells | 29 | 19% |
| 3,437 cells | 33 | 20% |

The big continent has split roughly in half. Nobody told the watcher about this: it labels the
landmasses fresh from each checkpoint, so when the new coastline appeared it simply found a
large landmass with food and no animals and settled it — at (0,178) in years 14,978 and 15,365,
and at (383,192) in year 15,136. **Every landmass is currently occupied**, which is the
condition all three dead worlds failed.

**The cooldown fix holds.** Before it, the island's drifting centre point let it be seeded twice
in forty-five years. Since the fix the spacing is exactly the intended century: 13,166 → 13,273
→ 13,374 → 13,475 → 13,575 → 13,676 → 13,777 → 13,878 → 13,981 → 14,083 → …

**And an honest reading of what the watcher is.** Twenty-six seedings of the original island,
and it has never once held a herd for longer than the cooldown. It is not restoring a
self-sustaining population there; it is running a permanent ferry service, and the island's food
share stays near 20% instead of climbing to the 92% that killed the unwatched world. That is a
treatment, not a cure, and the underlying question is still open: whether non-swimmers should be
able to cross shallow straits at all.

**Unchanged and normal:** carnivores present in 309 of the last 1,200 sampled years and
currently at a trough; breeding 9% against the 11–16% healthy band, with the bar at 22.2, below
the 23 that would mean the ratchet.

## Nine years, and no cause I can name (2026-09-16)

The year-12,400 world ran well for 4,100 years. All four landmasses stayed occupied for most
of it, the watcher settled each one as it emptied, the breeding bar stayed flat between 19.8
and 23.1, and the continent split in two without the biosphere noticing. Then:

```
16,514  219      16,518   71      16,522    1
16,515  191      16,519   31      16,523    0
16,516  148      16,520   12
16,517  117      16,521    6
```

**Nine years.** At year 16,500 that population was healthy by every measure available: energy
12.8 against a bar of 21.3, 13% breeding, health 0.989, flora 2,644 and rising, three of four
landmasses occupied and the fourth seeded eight years earlier.

The chronicle for those nine years — **restricted to this timeline**, which matters, because
year numbers repeat across rewinds and an unfiltered query silently mixes two worlds — holds no
catastrophe. Volcanoes that killed nobody, floods drowning one to five each, one volcano that
took six, and fifteen cold snaps in 130 years with five clustered in the last two decades at
−0.10 to −0.16. Every death I can name totals about **thirty animals out of two hundred and
fifty**. The rest simply stopped.

The yearly archives for that window were pruned before I could read them, and `/api/series`
only reaches back two hundred years. **The evidence is gone, and I am not going to invent a
fifth mechanism to cover it.**

### The pattern, which is now four deaths long

This world sustains a fauna for roughly two thousand years and then loses it, with a different
proximate cause each time: a carnivory subsidy; an island turning into an unreachable larder;
and now nine years of nothing in particular happening to 250 animals split four ways. Small
fragmented populations absorb ordinary bad luck until they don't.

**Restored to year 15,800** — 1,480 animals across 260/619/472 with the fourth landmass empty,
which the watcher settles within a century. Chosen over year 16,300 (441 animals, all four
occupied) for the buffer: three times the population. No laws changed.

### One repair

The watcher read `checkpoint_latest.npz` directly, holding a Windows share on it while the
simulation tried to `os.replace` that same file. It cost two saves —
`could not write the checkpoint (PermissionError: WinError 32)` at years 13,195 and 16,555.
It now copies the file and parses the copy, deleting it afterwards. Verified: `read_world`
returns the current year and leaves no temp files behind.

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
