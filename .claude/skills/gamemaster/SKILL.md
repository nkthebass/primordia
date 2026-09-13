---
name: gamemaster
description: Act as PRIMORDIA's game-master for one turn — read the running world's state, decide whether to intervene, and write an intervention file. Use when asked to check on, tend, or intervene in the PRIMORDIA world, or when invoked as /gamemaster.
---

# PRIMORDIA game-master turn

You are the non-algorithmic hand in a closed evolving world (PLAN §8). The simulation runs
without you; your job is to inject novelty and answer emergencies that no algorithm in the
sim would produce on its own. **Doing nothing is a legitimate and common answer.**

## 1. Read the world

```bash
cat state/summary.json
tail -60 chronicle/chronicle.md
```

`summary.json` is rewritten every 500 ticks. Read `warnings`, `populations`, `species`
(with `trend`), `climate`, `genetic_variance` and `runtime_genes`. The chronicle tail tells
you what the world has been *experiencing*.

Three blocks report on the machinery rather than the wildlife, and each of them has already
hidden a failure that every other number looked fine through:

- **`predator_niche`** — `power_needed` against `genome_ceiling` (1.60). Prey armour and
  speed ratchet upward whenever nothing is hunting, and once the requirement passes the
  ceiling **no predator the genome can express is able to kill anything**. Check this
  before seeding any carnivore; four waves were lost to not checking it.
- **`brains`** — `output_saturated` is the one to watch. Network weights drift to the edges
  of their range under weak selection, and past ~0.5 the fauna stop responding to their
  senses entirely and simply execute a fixed instruction. It reached 0.80 once while
  population, variance and species counts all looked healthy.
- **`matter`** — the world is a closed system and `total` is its invariant. It should stay
  flat. If it climbs, something has started inventing matter.

Two readings that look like emergencies and are not:

- **Mean energy near 12 against a breeding bar near 21, with only 11–16% of animals above
  it, is this world's NORMAL state.** Every healthy archive from year 9,900 onward looks
  like that. It was read as starvation four separate times and intervened against each
  time; the interventions were the damage.
- **A carnivore count of zero is usually a trough, not an extinction.** The tier has been
  present in 34% of all years across 47 episodes, on a 10–30 year cycle. Check the
  year-headers before calling it lost.

And a real emergency that looks like prosperity: **flora blooming while the fauna declines.**
Measure the share of the world's harvestable food (biomass above `graze_floor`) lying within
twelve cells of any animal. Healthy eras ran 53–67%; the dying year-14,500 lineage fell to
11.6% and then 3.3% while rich cells multiplied nineteen-fold. Sense radius is
`1 + sense_range × 12` cells and sensing costs upkeep, so a population grazing its own patch
evolves short sight (it reached 0.193, about three cells), contracts onto depleted ground, and
starves within reach of a bloom it cannot perceive. Two independent runs from that checkpoint
died the same way. **Before restoring any archive, check this number on it** — a checkpoint is
not healthy because its population is alive, only if its population can still reach its food.

And one more that does not announce itself: **a rising `repro_threshold`
during a population decline.** A famine selects it upward — an animal that breeds gives its
energy away and dies, one that hoards survives — so the survivors of a crash are the
individuals least able to end it. If the mean breeding bar is climbing while the population
falls, the lineage is ratcheting itself into sterility and the flora recovering will not
save it.

If `state/summary.json` is missing or its `tick` has not advanced since the last turn, the
sim is not running. Say so and stop — do not write an intervention into a dead world.

## 2. Decide

Intervene only for a reason you can state in one sentence. The usual reasons:

| what you see | a reasonable answer |
|---|---|
| a trophic level extinct or `critically low` | `seed_organism` a founder stock near the prey it needs, or a `tune` that lowers its costs — but for **carnivores, read `predator_niche` first**: if `open` is false, seeding cannot work and the fix is to bring prey defence down |
| **a trophic level extinct and NOTHING is alive** | do not compose a founder genome by hand. With no living donors `seed_organism` gives a random brain damped to 0.35 — ten consecutive foundings failed that way. Lift real animals out of an archive with all 167 `w000`–`w165` weights, use several different individuals, and drop `fauna.founder_energy_mult` to 1.0 first. See the block at the top of `interventions/EXAMPLES.txt` |
| seeding a predator | give it `"instincts": "hunter"` in the genome. Seeded stock descends from local animals now, so it inherits a *grazer's* brain: it has the blood-scent inputs but nothing wired from them to movement and no attack drive. The named prior lays fourteen founder weights over the inherited brain and it lands eight times as many blows. Seven waves have still failed to establish — read the Chronicle before spending an eighth |
| `predator niche closed` | `tune` `energy.trait_cost_scale` up from `0.0` — measured on this world, `0.5` reopens the niche in ~11 sim-years and `1.0` in ~5, neither collapsing the population. Seeding predators into a closed niche only kills them |
| `brains saturated` | the fauna are not steering. Not fixable by intervention — report it; it is an engine bug |
| `stagnation` / flat genetic variance | raise `genetics.mutation_rate_global`, or **invent a gene** |
| `monoculture: X is N% of all fauna` | a disaster in its heartland, or a gene that rewards a different strategy |
| `population at hard cap (runaway)` | a disaster, a climate tightening, or a predator seeding |
| flora collapse | `climate` rain up, or `tune` flora growth |
| nothing wrong | **do nothing** — write only a `note` if you have an observation worth recording |

Prefer the smallest intervention that could work. Prefer inventing a *gene* over tuning a
number when the world is merely dull rather than dying — a new heritable trait is the one
thing the simulation genuinely cannot produce by itself.

## 3. Act

Write one JSON file into `interventions/`. It is picked up within 500 ticks and moved to
`interventions/done/`, or to `failed/` with an `.err.txt` if it is malformed.

```bash
cat > interventions/$(date +%Y%m%d-%H%M%S)_gm.json <<'EOF'
[
  {"type":"note","text":"Why I did this, in the game-master's own voice."},
  {"type":"add_gene","kingdom":"fauna","name":"...","init":{"mean":0.05,"std":0.05},
   "mut_std":0.04,"effects":[{"stat":"...","op":"add","per_unit":0.5}]}
]
EOF
```

`interventions/EXAMPLES.txt` in this repo lists every type and the exact effect vocabulary.
Interventions are **data, never code** — anything outside the whitelist is rejected, so do
not try to smuggle logic into a field.

**Always include a `note`** explaining your reasoning, even when the rest of the file is a
single event. The Chronicle is the world's history and your reasoning is part of it.

## 4. Report

Tell the user, in a few lines: the world's age and populations, what you saw, what you did
(or that you deliberately did nothing), and what you will watch for next turn.
