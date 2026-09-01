# PRIMORDIA

A closed, evolving artificial-life ecosystem: terrain and weather, evolving plants, a
continuous herbivore→omnivore→carnivore food chain with neuroevolved brains, emergent
speciation with a live phylogeny — and a Claude-in-the-loop intervention protocol that
can inject genuinely non-algorithmic novelty into a running world.

Built to the specification in [PLAN.md](PLAN.md) — in a single response, from a spec the
model had not seen, with no human input during the build. See [PROMPT.md](PROMPT.md) for
exactly what the input was and where that claim stops being true.

---

## Run it

```bash
.venv\Scripts\python.exe -m primordia.main --stage-test
```

Always run the staged resource test first. It runs 192²/288²/384² for 60 s each,
prints a peak CPU/RAM/VRAM/TPS table and refuses to recommend a configuration that
breaches the caps (VRAM < 7 GB, CPU < 80 %, RAM < 20 GB, GPU < 80 °C). This machine is
the owner's daily desktop; the watchdog exists so a long run never makes it unusable.

Then launch the world:

```bash
.venv\Scripts\python.exe -m primordia.main --size 384 --max-pop 20000
```

Open **http://127.0.0.1:8710**. To continue an existing world instead of generating a
new one, add `--resume`.

Useful flags: `--seed N`, `--headless --ticks N`, `--report path.json`, `--fresh`,
`--no-monitor`, `--config extra.json`.

---

## The viewer (port 8710)

- **World map** — server-composed PNG streamed over a WebSocket at 2–4 fps. Terrain
  hillshade, depth-scaled water, flora green (hue shifts grass→tree with the `structure`
  gene), creatures as dots in their species hue with a ring on predators, live fire and
  storm overlays, and night dimming. Ten overlays: rain, temperature, moisture,
  fertility, nutrients, scent, species territory, elevation, decomposer density.
- **Chronicle** — the world's story, newest first, colour-coded by event type.
- **History graphs** — trophic levels (stacked), flora biomass, living species, mean
  diet, temperature and climate oscillation, with disaster tick-markers on all of them.
- **Phylogeny** — the full species tree, extinct branches struck through; click a
  species to highlight only its members on the map.
- **Inspector** — click anywhere: the nearest creature's full genome, species, age,
  energy and last action, plus that cell's soil, weather, carrion and plant genome.
- **Debug panel** — fire any of the six disasters at a chosen point and intensity, spawn
  alien / herbivore / predator stock, force the season, add a runtime gene, tune any
  hot-reloadable config leaf, poll `interventions/`, checkpoint, or wipe all fauna to
  watch the world recover. Every mechanic in the simulation is operable from here.

---

## The intervention protocol

The running world talks to a game-master Claude session through three paths:

| path | direction | contents |
|---|---|---|
| `state/summary.json` | outbound | rewritten every 500 ticks: populations, species with traits and trends, climate, warnings, recent events, runtime genes, resources |
| `interventions/*.json` | inbound | polled every 500 ticks, applied, then moved to `interventions/done/` (or `failed/` with a `.err.txt` saying exactly why) |
| `chronicle/chronicle.md` | outbound | append-only human-readable history (`chronicle.jsonl` alongside it) |

`interventions/EXAMPLES.txt` documents every type with a working example. In brief:

```json
{"type":"trigger_event","event":"wildfire","x":120,"y":300,"radius":25,"intensity":0.8}
{"type":"climate","param":"rain_mult","value":0.7,"ramp_ticks":2000}
{"type":"tune","path":"energy.basal_rate","value":0.13}
{"type":"seed_organism","kingdom":"fauna","count":10,"x":50,"y":50,"genome":"random_alien"}
{"type":"note","text":"why I did this"}
{"type":"add_gene", ...}
```

### `add_gene` — new heritable traits at runtime

Interventions are **data, never code**. `add_gene` composes an effect from a fixed
whitelist of stats, two operators and a set of conditions; anything outside the
vocabulary is rejected with an explanatory error rather than executed.

```json
{"type":"add_gene","kingdom":"fauna","name":"bioluminescence",
 "init":{"mean":0.05,"std":0.05},"mut_std":0.04,
 "effects":[
   {"stat":"mate_appeal","op":"add","per_unit":0.5,"when":{"is_night":true}},
   {"stat":"detectability","op":"add","per_unit":0.4,"when":{"is_night":true}},
   {"stat":"basal_cost","op":"mul_per_unit","per_unit":0.1}]}
```

The new gene gets a real column in the genome matrix, is initialised from its
distribution for everything currently alive, mutates and is inherited like any other
gene, counts (at low weight) toward genetic distance for speciation, and survives
checkpoint/resume. `stat` ∈ `basal_cost move_cost bite_size attack_power armor_eff
detectability sense_bonus mate_appeal cold_resist heat_resist toxin_resist plant_digest
meat_digest fire_resist swim_eff scent_strength fertility_local` (plus `growth_mult
seed_bonus water_efficiency toxin_bonus` for flora); `op` ∈ `add | mul_per_unit`;
`when` ∈ `is_night season biome in_water moisture_gt/lt temp_gt/lt`.

---

## Claude as game-master

PLAN §8.3 puts a Claude session in the loop on a fixed cadence. Two ways to run it:

- **Manually** — `/gamemaster` in a session opened on this repo. The skill lives at
  `.claude/skills/gamemaster/SKILL.md`: read the world, decide, write at most one
  intervention file, report.
- **On a schedule** — a local scheduled task (`primordia-gamemaster`, every 30 minutes)
  runs the same brief unattended while the app is open. Manage or disable it from the
  "Scheduled" section in the sidebar.

The brief is deliberately conservative: it intervenes only for a reason it can state in
one sentence, prefers the smallest thing that could work, prefers inventing a gene over
tuning a number when the world is merely dull, refuses to write into a world whose tick
has not advanced, and treats doing nothing as the normal answer. Every intervention it
writes carries a `note` explaining itself, so the Chronicle records the reasoning
alongside the consequences.

---

## How the world works

**Energy only ever flows downhill.** A carcass is worth a fraction of the energy and body
condition its owner was actually carrying — never more. Animals bank surplus food as
*tissue*, a newborn's investment is partly structure rather than fuel, and starvation burns
condition down to a structural floor. That tissue is what a predator harvests, and every
calorie of it was paid for upstream by something that ate.

**Matter is conserved.** Soil fertility → plant biomass → animal tissue → corpse →
nutrients → soil fertility, with a fixed total. Growing a gram of plant costs exactly
the soil matter a gram of plant returns when it dies; animals excrete continuously;
fire releases a plant's own matter as ash rather than inventing any. Energy is the only
thing that enters, and it enters as sunlight.

**Predation is decided by weapons, not weight.** Whether something counts as prey is
attack power against armour, with a clear margin — not a body-mass ratio. A mass ratio
forces a treadmill: prey evolve larger, predators have to out-grow them, the gene ceiling
arrives, and the tier dies. Power against armour makes fangs and armour the arms race,
which is what those genes are for, and lets a small well-armed hunter take a large soft
grazer. Meat-eaters also sprint: prey speed is under ferocious selection and shares the
same gene ceiling, so without a diet-scaled burst no chase ever closes.

**Nothing is scripted.** Biomes are not painted — plants carry twelve genes and the
best-fitted seedling wins each cell, so forest, scrub and desert fall out of selection.
Trophic roles are not behaviour branches — one continuous `diet` gene sets plant and
meat digestion efficiency on two deliberately steep curves, so specialists beat
generalists at their own game (PLAN §13) and herbivore/omnivore/carnivore are only
reporting buckets. Species are not declared — they are clusters in genome space
that drift apart, get a procedural Latin binomial and a stable hue, and are recorded
with their parent so the phylogeny is a real record of descent.

**Brains are genes.** Each creature carries its own 13→8→6 MLP as 166 weight genes.
One forward pass covers the whole population as two batched matmuls. There are no
per-creature Python loops anywhere in the hot path.

**Scale matters for the top of the chain.** All three trophic levels survive five sim-years
in 3 of 3 seeds at the recommended 384² configuration. At the 192² staging size the predator
tier does not make it to year 5 — the absolute prey numbers are too small for it to ride out
a crash. Run small worlds for speed, not for ecology.

**Bootstrapping vs. evolution.** The three founder stocks are hand-rolled — body priors
plus four small brain circuits (eat, chase prey, flee threats, follow the scent
gradient) and a hunger gate on attacking. A random MLP never eats and the whole
biosphere starves before selection can act. After the founders, every one of those
weights is an ordinary mutable gene and nothing is held in place. Predators are seeded
once the prey base can carry them — a prey *density*, with a tick floor so the wave cannot
fire on the founder stock itself — and not onto bare rock. Founders arrive provisioned:
seeded with a single `start_energy` a predator wave has about 250 ticks of fuel and 221 of
255 starve inside that window, before any of them find a first kill. And they arrive in
**three waves** at fresh hotspots rather than one: a single wave is a single gamble that
overshoots its local prey and crashes, and whether the survivors recover is a coin-flip.
Three smaller waves are three independent chances, which took the acceptance result from
3 of 6 seeds to 5 of 6.

---

## The realism pack (off by default)

Left free, selection pins every beneficial gene to its ceiling. A 272-sim-year run
finished with camouflage 0.95, armour 0.92, lifespan 0.93 and metabolic efficiency 0.94,
while body size collapsed to the floor at 0.08 — saturation rather than selection, and no
body left large enough to be anybody's prey.

The mechanics that fix that are implemented and measured, but they destabilise the top of
the food chain, so they ship **off**. Each is a config value in `config/default.json`:

| knob | off | on | what it does |
|---|---|---|---|
| `energy.trait_cost_scale` | `0.0` | `0.5` | camouflage, toxin tolerance, sense range, armour, fangs and lifespan cost upkeep; armour also costs movement |
| `energy.digest_size_min` / `digest_size_gain` | `1.0` / `0.0` | `0.75` / `0.42` | Jarman–Bell: a larger gut extracts more from the same forage |
| `fauna.reach_size_min` / `reach_size_span` | `99` / `1.0` | `0.12` / `0.55` | large grazers crop the neighbouring cells, not only the one they stand on |
| `energy.fangs_reach` | `0.0` | `0.85` | weapons offset body mass when deciding what counts as prey |
| `energy.speed_eff_penalty` | `1.0` | `1.55` | metabolic efficiency trades against power output |
| `energy.store_eff_penalty` | `1.0` | `1.40` | metabolic efficiency trades against reserve capacity |
| `energy.meta_floor` | `0.0` | `0.40` | diminishing returns on metabolic efficiency |
| `fauna.cooldown_lifespan` | `1.0` | `0.30` | long life trades against breeding rate |

Turned on together, camouflage settles around 0.27–0.34 and armour 0.29–0.50 instead of
pinning, and body size holds near 0.5 instead of collapsing.

They stay off by default, and re-measuring them against the current predation model says
why. Over the same six seeds the pack passes S4 in **2 of 6** against the default's 5 of 6,
and total fauna lands at 407–1,025 against 2,384–5,689. The original diagnosis — that they
fed a body-size treadmill predators could not win — is obsolete, since predation no longer
turns on body mass. What remains is simpler: when every trait costs upkeep, the same
primary production supports far fewer animals, and small populations are demographically
fragile. The genes behave better and the ecosystem is thinner. That is a real trade, not a
bug, and it is yours to make. `config/realism.json` turns the whole set on in one go:

```bash
.venv\Scripts\python.exe -m primordia.main --config config/realism.json
```

## Acceptance

S4 asks for ≥2 speciation events in five sim-years and all three trophic buckets nonzero,
in at least one of three seeded runs. Measured over six seeds at 384²:

| | result |
|---|---|
| full criterion met | **5 of 6 seeds** |
| carnivores present at year 5 | 5 of 6 |
| omnivores present at year 5 | **6 of 6** (39–61 individuals) |
| speciation events | 15–19 in every seed |

The one failing seed loses its carnivores and keeps everything else.

---

## Layout

```
config/default.json     every tunable; hot-reloadable sections marked in config.py
primordia/
  main.py      arg parsing, staged launch, sim thread + uvicorn
  sim.py       owns every subsystem; the tick loop (PLAN §7)
  world.py     grid state, terrain generation, nutrient cycle
  weather.py   seasons, day/night, cloud→rain loop, climate oscillation
  events.py    the six disasters, destructive and regenerative
  flora.py     evolving plants + the decomposer microbe layer
  fauna.py     creature SoA, perception, action, energy, reproduction
  brain.py     batched tiny-MLP neuroevolution
  genetics.py  growable genome schemas + the sandboxed effect engine
  speciation.py clustering, naming, phylogeny
  scent.py     kin and blood pheromone fields
  intervention.py  the interventions/ watcher and effect applier
  monitor.py   psutil + NVML watchdog, staged ramp, throttle ladder
  stats.py     history series, warnings, summary.json
  checkpoint.py  whole-world save/load
  server.py    FastAPI + WebSocket + inspector/debug API
  render.py    world state → RGB → PNG
  fields.py    grid ops; CUDA via torch, graceful CPU fallback
viewer/index.html   the whole dashboard, no build step
state/       summary.json, checkpoints, archive/, snapshots/, resources.log
interventions/      drop JSON here; done/ and failed/ alongside
chronicle/   chronicle.md + chronicle.jsonl
```

## Performance

Measured at 384²: ~36 ticks/s early in a run, ~37 at 4k creatures, and **25.3 ticks/s
held at 10.2k** — 84% of the plan's ≥30-at-10k budget. Perception is no longer the hot path
(squared-distance comparison and bins sized so a 3×3 neighbourhood already covers maximum
sense range took it from 42% of the tick to 20%); what remains is spread evenly across
perception, action, the microbe layer, flora growth and weather, with no single target
left. Closing the last 16% is not a numba job: a JIT'd parallel perception scan, verified to
produce identical targets across 13,932 selections, measured **21.0 tps against numpy's
27.0** and was removed rather than shipped. The scan is ~139k tiny iterations per tick, so
parallel dispatch costs more than it saves while numpy's gathers are already
memory-bandwidth-bound. What is left would be a restructure, not an optimisation.

Scatter-adds pick `bincount` or `ufunc.at` per call by population-to-grid ratio, since
bincount always costs O(grid) and loses badly when few creatures scatter onto a large one.
The microbe layer and plant seeding are substepped, verified to leave the flora equilibrium
unchanged (cover 0.634 vs 0.635, biomass within 7%). One consequence worth knowing: because
the scatter algorithm varies with population, floating-point summation order does too, so a
seed no longer reproduces a fixed world run to run.

torch/CUDA is detected and kept as the fallback contract, but at these grid sizes the
host<->device copy dominates a 3x3 stencil and numpy is 9-16x faster. The sim benchmarks
both once at startup and picks the winner, reporting the choice in the viewer's header.

## Safety

`monitor.py` samples CPU/RAM/VRAM/GPU-temp every 2 s. VRAM is measured **per process**,
not per card — on a machine that is also a daily desktop, another application's memory
would otherwise pin the simulation at the bottom of the throttle ladder forever. The
viewer shows both, ours and the card total. Three consecutive breaches walk a
throttle ladder — drop max population 10 %, halve the viewer frame rate, cap the tick
rate, finally pause with a Chronicle alert — and it steps back down as soon as the box
recovers. The world checkpoints every 5 minutes, on every sim-year, and on clean
shutdown, keeping three rotations plus a per-year archive; `--resume` restores
everything including runtime-added genes.
