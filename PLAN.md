# PRIMORDIA — Build Plan

A fully enclosed, evolving artificial-life ecosystem: terrain, weather, disasters, evolving
plants, a continuous herbivore→omnivore→carnivore food chain with neuroevolved brains,
emergent speciation, and a **Claude-in-the-loop intervention protocol** that injects
genuinely non-algorithmic novelty on a schedule.

This document is the complete spec. It is written to be executed by a Claude session with
no other context. Follow it in the slice order of §12. Do not skip the resource-safety
staging in §10 before any long run.

---

## 1. Non-negotiables (from the owner)

1. Closed system: nothing enters/leaves except seasonal sunlight energy and scheduled
   Claude interventions. Full nutrient cycle (death → decomposition → soil fertility).
2. Terrain, weather/seasons, and natural disasters exist and disasters are BOTH
   destructive and regenerative (fires/eruptions boost fertility) — essential, not cosmetic.
3. Plants evolve. Herbivores depend on plants, omnivores on plants+prey, predators on
   prey. The food chain must be able to genuinely shift over generations.
4. Evolution is real selection over mutating genomes — no scripted outcomes.
5. The intervention loop (§8) is mandatory: the sim consumes `interventions/*.json` and
   emits `state/summary.json` so a periodically-pinged Claude can act as game-master.
6. GPU **and** CPU are resource-monitored with a staged ramp-up before full launch (§10).
   This box is also the owner's desktop: hard caps VRAM < 7 GB, CPU < 80%, RAM < 20 GB.
7. Visual: a browser dashboard the owner can glance at cold and understand (§9).
8. Everything checkpointed — a crash or reboot never loses the world.

## 2. Environment & stack

- Windows 10, RTX 3080 10 GB, Ryzen 5900X, 32 GB RAM. Python 3.11+.
- Repo root: `C:\Users\noahc\Documents\PRIMORDIA`. Create `.venv` in repo root.
- Dependencies (`requirements.txt`): `numpy`, `torch` (CUDA build if available — used ONLY
  for weather/diffusion field convolutions; must gracefully fall back to CPU conv via
  scipy/numpy if CUDA init fails), `fastapi`, `uvicorn[standard]`, `websockets`, `pillow`,
  `psutil`, `pynvml` (fallback: parse `nvidia-smi`), `orjson`.
- No pygame, no external DB, no cloud. Single process + uvicorn worker thread is fine;
  run the sim loop in a background thread, viewer via FastAPI + WebSocket.

## 3. Repo layout

```
PRIMORDIA/
  PLAN.md                  # this file
  CLAUDE.md                # project instructions
  requirements.txt
  config/default.json      # every tunable below lives here, hot-reloadable where noted
  primordia/
    __init__.py
    main.py                # arg parse, staged launch, sim thread + server
    config.py              # dataclass config, JSON load/merge
    world.py               # grid state container, terrain gen, nutrient field
    weather.py             # seasons, moisture/cloud/rain, climate oscillation
    events.py              # disasters (natural + triggered)
    flora.py               # plant genomes, growth, seeding, mutation
    fauna.py               # creature SoA, perception, actions, energy, reproduction
    brain.py               # batched tiny-MLP neuroevolution
    genetics.py            # genome schema registry (supports runtime-added genes)
    speciation.py          # clustering, species IDs, naming, phylogeny
    scent.py               # pheromone fields
    chronicle.py           # plain-English event log + jsonl
    intervention.py        # interventions/ folder watcher + effect engine
    monitor.py             # psutil + NVML watchdog, staged ramp, throttling
    stats.py               # history series, summary.json writer
    checkpoint.py          # save/load whole world (npz + json)
    server.py              # FastAPI app, WS frame streaming, inspector API
    render.py              # server-side frame composition (RGB → PNG bytes)
  viewer/index.html        # single-file dashboard (no build step, vanilla JS + canvas)
  state/                   # runtime: summary.json, checkpoints, snapshots/ (PNG timelapse)
  interventions/           # Claude drops JSON here; sim consumes & moves to interventions/done/
  chronicle/chronicle.md   # human-readable feed (+ chronicle.jsonl)
  .claude/launch.json      # {"name":"primordia","runtimeExecutable":".venv\\Scripts\\python.exe","runtimeArgs":["-m","primordia.main"],"port":8710}
```

## 4. World, terrain, nutrients (`world.py`)

- Grid `G = 384×384` (config `world.size`; staged launch may start at 192). Cell arrays
  (all `float32` numpy unless noted): `elevation`, `water_depth`, `soil_fertility`,
  `moisture`, `temperature`, `nutrients` (decay pool feeding fertility).
- Terrain gen: 4-octave value/simplex noise (implement fBm directly, no dependency),
  seeded from config `seed`. Classify: elevation < sea_level → ocean; < sea+0.03 →
  coast; then plains/hills/mountains by thresholds. Initial fertility = noise blended
  with low-elevation bonus; rivers optional (skip in v1, floods carve `water_depth`).
- Latitude temperature gradient (top cold → middle hot → bottom cold) + elevation lapse
  (−k per elevation unit) + season offset from weather.
- Nutrient cycle: corpses and dead plants add to `nutrients` at their cell; `nutrients`
  transfers into `soil_fertility` at `decomp_rate` (boosted where decomposer microbes
  are active, §6.4); fertility is consumed by plant growth. Erosion: every ~500 ticks,
  slight elevation smoothing toward neighbors (kernel blur, strength `erosion_rate`).

## 5. Weather, seasons, disasters (`weather.py`, `events.py`)

- **Calendar**: `ticks_per_year = 2000`, 4 equal seasons. Global temp offset =
  sinusoid over the year; day/night = fast sinusoid (`ticks_per_day = 50`) providing a
  sunlight multiplier for plant growth and a darkness flag for perception/camouflage.
- **Moisture loop** (torch tensors on GPU, conv2d kernels; ~microseconds at 384²):
  evaporation from ocean/water cells → `cloud` field → advected by a wind vector that
  slowly rotates over seasons → precipitation where `cloud > capacity(temp, elevation)`
  (mountains and cold precipitate more) → rain adds to `moisture`/`water_depth`;
  `moisture` diffuses and decays. Result must yield persistent wet/dry regions (verify
  visually in Slice 1).
- **Climate oscillation**: slow random walk `climate_osc ∈ [−1,1]` (step every 200
  ticks) scaling global rain; extremes = multi-season droughts / wet years.
- **Disasters** (each has natural probability per tick, scaled by conditions, AND is
  triggerable via intervention with location/intensity):

  | event | trigger bias | destructive effect | regenerative effect |
  |---|---|---|---|
  | storm | high cloud | plant damage %, creature energy drain, heavy rain | moisture surge |
  | wildfire | dry + hot + dense flora | spreads cell-to-cell through low-moisture vegetation, kills plants/slow creatures | +fertility on burned cells (ash), clears canopy |
  | flood | rain > threshold near water | drowns low-elevation cells (temp `water_depth`), kills non-swimmers | silt: +fertility on floodplain |
  | volcano | fixed hotspot cells, rare | lava kill radius, +elevation cone | large ash fertility ring |
  | cold snap | winter | temp −X for N ticks, kills low cold_tol | culls overpopulation |
  | meteor | very rare | crater (−elevation, kill radius), dust dims sun briefly | crater lake + fertility; **panspermia**: 30% chance the meteor seeds 5–20 creatures with a fully random alien genome |

  All events append to the Chronicle with coordinates and casualty counts.

## 6. Life

### 6.1 Genome registry (`genetics.py`) — must support runtime growth

Genomes are structure-of-arrays: one `float32` array per gene, length = population.
A `GenomeSchema` maps gene name → (index range, init mean/std, mutation std, bounds).
**Interventions can append new genes at runtime** (§8): appending a gene allocates a new
array initialized from its init distribution for living organisms, and registers its
effect hooks (§8.2). Checkpoints store the schema so runtime-added genes survive reload.
Mutation on reproduction: per-gene Gaussian (`sigma = gene.mut_std * mutation_rate_global`),
clipped to bounds; plus `macro_mutation_prob` (default 0.01) chance of one gene getting a
5× sigma jump. `mutation_rate_global` is intervention-tunable.

### 6.2 Flora (`flora.py`)

One plant per cell max (arrays shaped like the grid; empty = biomass 0). Genes:

`growth_rate, water_need, temp_optimum, temp_tolerance, root_depth` (drought buffer),
`seed_range, seed_count, structure` (0=grass fast/low-energy … 1=tree slow/dense/tall),
`toxin, fire_resist, cold_dormancy, lifespan`.

- Growth/tick: `biomass += growth_rate * sunlight * fert_avail * water_score * temp_score`
  where `water_score` uses moisture vs `water_need` softened by `root_depth`, and
  `temp_score = gaussian(temp − temp_optimum, temp_tolerance)`. Growth consumes fertility.
- Reproduction: mature plants scatter `seed_count` seeds within `seed_range`; a seed
  lands on an empty (or weaker-occupied, with competition roll) cell as a mutated child.
  Best-fit-for-that-cell wins → biomes emerge from selection, never painted.
- Death (age > lifespan, or killed): biomass → `nutrients`.
- Edibility: energy to herbivore = `biomass_eaten * energy_density(structure)`; eating a
  toxic plant costs `toxin − toxin_tolerance` (floored at 0) health → toxin arms race.

### 6.3 Fauna (`fauna.py`, `brain.py`)

SoA arrays, capacity preallocated to `fauna.max_pop` (default 20 000; staged launch
starts lower). Free-list for dead slots. Genes:

**Body**: `size, speed, metabolism_eff, sense_range, camouflage, armor, fangs,
toxin_tolerance, heat_tol, cold_tol, lifespan, repro_threshold, repro_invest, sexual,
social, scent_deposit, swim`.
**Diet**: `diet ∈ [0,1]` — 0 pure herbivore … 1 pure carnivore. Plant digestion
efficiency `= 1 − diet`, meat efficiency `= diet` (smoothstep both so mid-range
omnivores are viable but not dominant). Herbivore/omnivore/predator are *reporting
buckets* (`<0.33 / 0.33–0.66 / >0.66`), never behavior branches.
**Brain**: fixed topology MLP, weights are genes. Inputs (13): energy_frac, age_frac,
plant_food_here, meat_food_here (corpses), nearest-prey Δx,Δy (within sense_range,
"prey" = smaller creature or any creature if diet high), nearest-threat Δx,Δy (bigger
+ high-diet creature), kin-scent gradient x,y, foreign-scent magnitude, temp_delta
(local − comfort), is_night. Hidden 8 (tanh). Outputs (6): move_x, move_y (desired
velocity, scaled by `speed`), eat, attack, flee_gain, breed_desire. ≈ 13·8+8+8·6+6 =
166 weight genes. Forward pass = two batched matmuls over the whole population per tick.

- **Perception** via spatial binning: bucket creatures into grid cells each tick; nearest
  prey/threat looked up in a (2r+1)² neighborhood with vectorized argmin on distance.
  Camouflage subtracts from the distance at which others can detect you (doubled at night).
- **Energy economy** (all in `config.energy`, starting values — Slice 8 tunes them):
  basal drain `= 0.15 * size^0.75 / metabolism_eff` per tick; movement adds
  `0.1 * size * speed * |v|`; cold adds drain scaled by `(cold_discomfort) / size`
  (small bodies suffer). Eat plant: transfer up to `bite = 2*size` biomass. Attack: if
  `fangs + size_adv > armor + roll` → victim damaged/killed; corpse holds
  `0.6 * victim_energy + size*K` meat, decays to nutrients over 100 ticks (scavengeable —
  the decomposer/scavenger niche). Reproduce when `energy > repro_threshold_abs`:
  child gets `repro_invest` fraction of parent energy; `sexual > 0.5` requires an
  adjacent same-species mate (gene crossover 50/50 then mutate) and gives a small
  mutation-quality bonus; asexual is mutation-only. Death: age, starvation, damage,
  disaster → corpse.
- **Bootstrapping**: seed 3 hand-rolled founder populations (grazer-ish, omnivore-ish,
  predator-ish diet priors, random brains) so the food chain can ignite; after that,
  no hand-holding.

### 6.4 Decomposers (`flora.py` or own module)

A microbe density field: grows where `nutrients`/corpse mass is present, dies back
otherwise; converts nutrients → fertility at rate ∝ density; has its own two-gene
mini-genome per cell (efficiency, temp_optimum) mutated on spread. Closes the loop.

### 6.5 Scent (`scent.py`)

Per-species-cluster scent field is too big; instead one 2-channel field: `kin_scent`
tagged by species-ID hash into channel + a global `blood_scent` deposited by combat/
corpses. Creatures with `social` deposit and can follow kin gradient (brain inputs);
predators can evolve to follow blood scent. Fields diffuse+decay each tick on GPU.

### 6.6 Speciation & phylogeny (`speciation.py`)

Every 200 ticks: incremental clustering on genetic distance (weighted L2 over body genes,
brain excluded, runtime-added genes included at low weight). A cluster drifting >
`species_split_dist` from its parent centroid becomes a new species (parent link kept →
phylogeny tree); > `subspecies_dist` → subspecies. Naming: procedural Latin-ish
generator (syllable tables), subspecies get a third epithet. Each species gets a stable
hue (children = parent hue ± small shift) used everywhere in the viewer. Record per
species: founding tick, parent, population series, mean genome, extinction tick.

## 7. Tick loop (order matters)

```
1. weather.step()            # season, day/night, clouds, rain, climate osc
2. events.maybe_trigger()    # natural disasters + apply active ones (fire spread etc.)
3. flora.step()              # growth, seeding, death
4. decomposers.step(); scent.step()
5. fauna.perceive()          # spatial bins, feature vectors
6. brain.forward()           # batched MLP
7. fauna.act()               # move, eat, attack, breed
8. fauna.metabolize()        # drains, aging, deaths → corpses
9. every K ticks: intervention.poll(); speciation.update(); stats.write_summary();
   chronicle.flush(); checkpoint.autosave(); render.broadcast()
```

Performance budget: ≥ 30 ticks/sec at 10k creatures, 384² grid, pure-vectorized (zero
per-creature Python loops in the hot path — this is the #1 implementation rule).
Viewer streams at 2–4 fps regardless of tick rate; sim speed control just changes how
many ticks run between broadcasts.

## 8. Claude intervention protocol (`intervention.py`) — the non-algorithmic hand

### 8.1 Outbound: `state/summary.json` (rewritten every 500 ticks)

```json
{
  "tick": 123456, "year": 61, "season": "spring", "tps": 41.2,
  "climate": {"osc": -0.4, "global_temp_offset": 0.1, "drought": false},
  "populations": {"flora_biomass": 0, "herbivore": 0, "omnivore": 0, "carnivore": 0, "decomposer": 0},
  "species": [{"id": 17, "name": "Velox rubrum", "pop": 812, "diet_mean": 0.71,
               "trend": "growing", "notable_traits": {"speed": 0.9, "social": 0.8}}],
  "warnings": ["carnivore biomass down 60% over last year",
               "genetic variance flat for 3 years (stagnation)"],
  "recent_events": ["wildfire y58 east", "meteor y60 (panspermia)"],
  "resources": {"vram_gb": 1.2, "cpu_pct": 45, "ram_gb": 6.1}
}
```

Warnings logic: extinction risk (trophic level < threshold or −50%/year), stagnation
(variance plateau), monoculture (one species > 70% of a level), runaway (pop at cap).

### 8.2 Inbound: `interventions/*.json`, polled every 500 ticks, moved to `done/` after
applying (or `failed/` with an `.err.txt`). Types:

- `{"type":"trigger_event","event":"wildfire","x":120,"y":300,"radius":25,"intensity":0.8}`
- `{"type":"climate","param":"rain_mult|temp_offset","value":0.7,"ramp_ticks":2000}`
- `{"type":"tune","path":"energy.basal_rate","value":0.13}` — any config leaf marked hot-reloadable
- `{"type":"seed_organism","kingdom":"fauna","count":10,"x":50,"y":50,
    "genome":"random_alien" | {"diet":0.9,"size":0.7,...}}`
- `{"type":"note","text":"..."}` → Chronicle verbatim (game-master commentary)
- **`{"type":"add_gene", ...}`** — the crown jewel. Adds a brand-new heritable gene at
  runtime with effects composed from safe primitives (data, not code):

```json
{"type":"add_gene","kingdom":"fauna","name":"bioluminescence",
 "init":{"mean":0.05,"std":0.05},"mut_std":0.04,
 "effects":[
   {"stat":"mate_appeal","op":"add","per_unit":0.5,"when":{"is_night":true}},
   {"stat":"detectability","op":"add","per_unit":0.4,"when":{"is_night":true}},
   {"stat":"basal_cost","op":"mul_per_unit","per_unit":0.1}]}
```

Effect primitives the engine must support: modify any named stat used in the tick loop
(`basal_cost, move_cost, bite_size, attack_power, armor_eff, detectability, sense_bonus,
mate_appeal, cold_resist, heat_resist, toxin_resist, plant_digest, meat_digest,
fire_resist, swim_eff, scent_strength, fertility_local`), ops `add | mul_per_unit`,
conditions on `is_night, season, biome, moisture_gt/lt, temp_gt/lt, in_water`.
`mate_appeal` requires a small hook in mate selection (sexual reproducers prefer higher).
This vocabulary is rich enough that a game-master can invent genes no algorithm predicted,
while staying sandboxed (no code execution from JSON — hard rule).

### 8.3 Cadence

The running Claude session (or a scheduled task) is pinged on a fixed interval (owner
default: **every 30 min** during supervised runs). Per ping: read `summary.json`
(+ tail of chronicle), decide as game-master (break stagnation, rescue collapse, invent
a gene, or explicitly do nothing), write intervention file(s), append a `note` explaining
the reasoning. The sim must run fine unattended if no interventions arrive.

## 9. Viewer (`server.py`, `render.py`, `viewer/index.html`)

FastAPI on port **8710**. Single HTML page, no build step, dark theme, four zones:

1. **World map** (main canvas): server composes RGB per broadcast — terrain hillshade
   base, water blue-scaled by depth, flora green intensity = biomass (hue shifts by
   structure gene), creatures = 2–3 px dots in species hue (predator bucket gets a ring),
   active disasters overlaid (fire orange, storm hatch). Overlay dropdown: none / rain /
   temperature / moisture / fertility / scent / species-territory. Sent as PNG bytes over
   WS (~2–4 fps), drawn scaled to canvas; night dims the frame.
2. **Chronicle feed**: last ~40 entries, newest on top, auto-scrolling, event-type icons.
3. **History graphs** (small multiples, ~1000-point downsampled series): populations by
   trophic bucket (stacked), species count, mean diet, global temp + climate osc, flora
   biomass; disaster tick-markers on all of them.
4. **Phylogeny tree**: collapsible species tree, live pops, extinct branches greyed;
   click species → highlight its members on the map.

Controls: pause/resume, speed (1×/4×/16×/max), tick+year+season+TPS readout, resource
bar (CPU/RAM/VRAM from monitor), click-a-creature inspector (WS request → genome, species,
age, energy, last action), **debug dropdown that manually fires every disaster + spawns
test organisms + forces season** (required for smoke-testing every mechanic from the UI),
and a "write summary now" button.

## 10. Resource safety (`monitor.py`) — DO THIS BEFORE ANY LONG RUN

- Sampler thread (2 s interval): psutil CPU%/RAM + pynvml VRAM/util/temp → ring buffer,
  exposed to viewer and `summary.json`; log to `state/resources.log`.
- **Staged launch** (`python -m primordia.main --stage-test`): run 60 s at each of
  192²/5k-pop → 288²/10k → 384²/20k, print peak CPU/RAM/VRAM/TPS table, verdict per
  stage against caps (VRAM < 7 GB, CPU < 80% sustained, RAM < 20 GB, GPU temp < 80 °C).
  Refuse to full-launch a failing stage; recommend the largest passing config.
- Runtime watchdog: 3 consecutive breaches → throttle ladder: lower max_pop 10% →
  halve broadcast fps → cap TPS → pause + Chronicle alert. Never crash the box.

## 11. Checkpointing (`checkpoint.py`)

Every 5 min (and on clean shutdown / SIGINT): all grid arrays + fauna SoA + genome
schemas (incl. runtime genes + their effect defs) + species/phylogeny + chronicle offset
+ RNG states + config → `state/checkpoint_latest.npz` + sidecar JSON (write temp,
atomic rename; keep 3 rotations + one per sim-year in `state/archive/`).
`--resume` flag restores exactly. Verify determinism-adjacent sanity: resumed run doesn't
explode (bit-exact replay NOT required).

## 12. Build order — slices with acceptance criteria

Build one slice at a time; each ends runnable and visually verifiable via the viewer
(use the debug dropdown, screenshot proof). Owner's standing rule: no CLI-only stubs —
every slice's features must be visible/operable in the UI.

- **S0 scaffold**: venv, requirements, config, empty modules, FastAPI serves viewer shell,
  launch.json works. ✓ page loads on :8710.
- **S1 world+weather**: terrain gen, seasons, rain/clouds, overlays, day/night dimming.
  ✓ map shows continents/mountains; rain overlay shows wet windward regions; a year of
  seasons visibly cycles at 16×.
- **S2 flora+nutrients+decomposers**: ✓ distinct biomes emerge within ~2 sim-years from a
  uniform seeding; flora biomass graph stabilizes (no monotonic explosion/extinction);
  debug-fired wildfire burns, then regrows greener on the ash.
- **S3 herbivores**: founders graze, breed, die; corpses decay. ✓ population oscillates
  with seasons instead of flatlining or exploding for 3 sim-years unattended.
- **S4 food chain+brains+speciation**: diet axis, predation, sexual repro, clustering,
  naming, phylogeny panel. ✓ ≥2 speciation events in 5 sim-years; all three trophic
  buckets nonzero after 5 years in ≥1 of 3 seeded runs (tune until true).
- **S5 disasters+scent+social**: all six events natural + debug-triggerable; herding
  visible. ✓ meteor panspermia produces a named alien species; fire spreads believably.
- **S6 chronicle+graphs+inspector+timelapse**: ✓ Chronicle reads like a story; click any
  creature for its genome; PNG snapshot saved every 500 ticks to `state/snapshots/`.
- **S7 interventions+monitor+checkpoint**: full §8 protocol incl. `add_gene` end-to-end
  (test: add a fake "spikes" gene from a JSON file, watch it spread under predation),
  staged launch, watchdog, resume. ✓ kill process mid-run, `--resume`, world continues.
- **S8 burn-in+tuning**: run ≥3 sim-years at full scale, watch resources, tune the
  energy economy against §13 failure modes. ✓ staged-launch table + a 3-year run report.

## 13. Known failure modes & the knobs that fix them

- *Green explosion* (plants saturate): raise growth fertility cost, lower fertility cap.
- *Herbivore boom-crash to zero*: raise repro_threshold, corpse energy return, or let
  winter cull via cold drain rather than starvation cliffs.
- *Predator collapse* (most common ALife death): lower attack cost, raise corpse energy,
  or intervention-seed prey-dense refuges. Keep carnivore basal drain slightly under
  herbivore per unit size.
- *Omnivore takeover* (mid-diet dominates): sharpen the smoothstep on digestion
  efficiencies (specialists must beat generalists at their own game).
- *Stagnation*: raise `mutation_rate_global` via intervention, or add a gene / disaster.
- *Brain drift to no-ops*: ensure movement noise floor + energy pressure make "do
  nothing" lethal; verify founders actually eat before shipping S3.

Log every tuning change to the Chronicle so history is honest.
