"""Creature population: SoA state, perception, brain-driven action, energy, reproduction.

Hard rule from the plan: no per-creature Python loops anywhere in here.  Everything is
whole-array numpy over the living population.
"""
from __future__ import annotations

import numpy as np

from . import brain as brainmod
from .brain import Brain, N_IN, N_OUT
from .genetics import Gene, GenomeSchema, EffectEngine

BODY_GENES = [
    Gene("size",            0.35, 0.14, 0.045, 0.05, 1.0),
    Gene("speed",           0.45, 0.16, 0.050, 0.02, 1.0),
    Gene("metabolism_eff",  0.50, 0.14, 0.045, 0.15, 1.0),
    Gene("sense_range",     0.40, 0.16, 0.050, 0.03, 1.0),
    Gene("camouflage",      0.20, 0.14, 0.050, 0.00, 1.0),
    Gene("armor",           0.15, 0.12, 0.050, 0.00, 1.0),
    Gene("fangs",           0.15, 0.14, 0.055, 0.00, 1.0),
    Gene("toxin_tolerance", 0.20, 0.14, 0.050, 0.00, 1.0),
    Gene("heat_tol",        0.50, 0.16, 0.045, 0.00, 1.0),
    Gene("cold_tol",        0.50, 0.16, 0.045, 0.00, 1.0),
    Gene("lifespan",        0.50, 0.16, 0.045, 0.08, 1.0),
    Gene("repro_threshold", 0.50, 0.16, 0.050, 0.10, 1.0),
    Gene("repro_invest",    0.40, 0.14, 0.045, 0.12, 0.75),
    Gene("sexual",          0.35, 0.28, 0.060, 0.00, 1.0),
    Gene("social",          0.35, 0.22, 0.055, 0.00, 1.0),
    Gene("scent_deposit",   0.30, 0.20, 0.055, 0.00, 1.0),
    Gene("swim",            0.15, 0.15, 0.055, 0.00, 1.0),
    Gene("diet",            0.30, 0.22, 0.055, 0.00, 1.0),
]
BODY_NAMES = [g.name for g in BODY_GENES]

MAX_LIFE = 2600.0        # ticks at lifespan gene == 1
MAX_SENSE = 12.0         # cells at sense_range == 1
MAX_SPEED = 0.85         # cells/tick at speed == 1
BIN = 6                  # spatial bin size in cells
NEIGH = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
# Predation is decided by attack power against armour, with a clear margin so that
# near-parity does not turn a guild into a meat grinder that consumes itself, and a loose
# mass ceiling so nothing hunts something several times its own size.
PREY_POWER_MARGIN = 1.25
THREAT_POWER_MARGIN = 1.25
MAX_PREY_SIZE_MULT = 2.5
# what fraction of nominal attack power a founder's wiring actually delivers through
# the attack output; the hit check multiplies power by it, so arming must divide by it
FOUNDER_ATTACK_DRIVE = 0.9

ACT_IDLE, ACT_MOVE, ACT_EAT, ACT_ATTACK, ACT_BREED, ACT_FLEE = 0, 1, 2, 3, 4, 5
ACTION_NAMES = ("idle", "move", "eat", "attack", "breed", "flee")

# --- founder brain wiring helpers -------------------------------------------------
# Genome layout (brain.py): W1 (13x8) | b1 (8) | W2 (8x6) | b2 (6).
_W2_OFF = brainmod.N_W1 + brainmod.N_B1
_B2_OFF = _W2_OFF + brainmod.N_W2


def _w1(inp: int, hid: int) -> str:
    return f"w{inp * brainmod.N_HID + hid:03d}"


def _w2(hid: int, out: int) -> str:
    return f"w{_W2_OFF + hid * brainmod.N_OUT + out:03d}"


def _b1(hid: int) -> str:
    return f"w{brainmod.N_W1 + hid:03d}"


def _b2(out: int) -> str:
    return f"w{_B2_OFF + out:03d}"


IN_PREY_DX, IN_PREY_DY, IN_THREAT_DX, IN_THREAT_DY = 4, 5, 6, 7
OUT_MOVE_X, OUT_MOVE_Y, OUT_EAT, OUT_ATTACK, OUT_FLEE, OUT_BREED = 0, 1, 2, 3, 4, 5
BIAS_EAT, BIAS_ATTACK, BIAS_BREED = _b2(OUT_EAT), _b2(OUT_ATTACK), _b2(OUT_BREED)

# A random 13-8-6 MLP never chases anything, so a founder predator starves next to a
# herd it cannot steer toward.  These four circuits (chase prey / run from threats) are
# the whole of the hand-holding: every weight is an ordinary mutable gene afterwards.
IN_ENERGY = 0
CHASE = {_w1(IN_PREY_DX, 0): 2.2, _w2(0, OUT_MOVE_X): 1.8,
         _w1(IN_PREY_DY, 1): 2.2, _w2(1, OUT_MOVE_Y): 1.8}
FLEE = {_w1(IN_THREAT_DX, 2): 2.2, _w2(2, OUT_MOVE_X): -1.8, _w2(2, OUT_FLEE): 1.2,
        _w1(IN_THREAT_DY, 3): 2.2, _w2(3, OUT_MOVE_Y): -1.8}
# hidden unit 4 = "am I short of a full belly".  Centred so a predator hunts at any
# energy below roughly its breeding threshold and stops once it is full -- centred on
# *starving* instead, it declines to hunt until it is already too weak to.
HUNGER_GATE = {_w1(IN_ENERGY, 4): -2.5, _b1(4): 3.0}

# The burst channel (OUT_FLEE) is a plain speed multiplier for whoever raises it, but
# only the grazers were ever wired to raise it: FLEE runs threat-detector -> burst, and
# the hunter archetype had no circuit driving that output at all.  So prey sprinted at
# 1.35x while the animal chasing them jogged, and after two thousand years of selection
# on prey speed no chase could close: measured over 24,796 pursuits the hunters steered
# at their targets (alignment +0.41) and held station at 3.95 cells, real speed 1.076
# against fleeing prey at 1.144.  They starved in sight of food.  Pursuit spends the
# same currency flight does; hidden unit 4 already says "hungry", so it drives the
# sprint.  Ordinary mutable genes afterwards, like every other founder prior.
PURSUE = {_w2(4, OUT_FLEE): 1.5}
IN_SCENT_DX, IN_SCENT_DY = 8, 9
# follow the scent gradient (kin for grazers, blood for carnivores -- same two inputs,
# blended by the diet gene in scent.sample_gradient)
TRACK = {_w1(IN_SCENT_DX, 5): 2.0, _w2(5, OUT_MOVE_X): 1.2,
         _w1(IN_SCENT_DY, 6): 2.0, _w2(6, OUT_MOVE_Y): 1.2}

# founder archetypes.  Body priors plus a *minimal* behavioural prior: a random MLP
# eats only by accident and the whole biosphere starves before selection can act, so
# founders are born wanting to eat and breed.  Everything after that is evolved.
# (name, share of `fauna.founders_per_type`, genes) -- an inverted pyramid of equal
# numbers means the predators eat the entire cradle in fifty ticks.
FOUNDERS = [
    ("grazer",   6.0, {"diet": 0.10, "size": 0.30, "speed": 0.40, "fangs": 0.05,
                  "sense_range": 0.35, BIAS_EAT: 1.4, BIAS_BREED: 0.6, **FLEE}),
    ("omnivore", 1.5, {"diet": 0.45, "size": 0.42, "speed": 0.50, "fangs": 0.28,
                  "sense_range": 0.45, BIAS_EAT: 1.3,
                  BIAS_BREED: 0.6, **CHASE, **FLEE, **TRACK, **HUNGER_GATE,
                  _w2(4, OUT_ATTACK): 1.4, BIAS_ATTACK: -0.2}),
    ("hunter",   2.20, {"diet": 0.85, "size": 0.46, "speed": 0.85, "fangs": 0.62,
                  "sense_range": 0.78, "speed": 0.85, BIAS_EAT: 1.2,
                  BIAS_BREED: 0.6, **CHASE, **TRACK, **HUNGER_GATE, **PURSUE,
                  _w2(4, OUT_ATTACK): 2.0, BIAS_ATTACK: 0.1}),
]


BINCOUNT_RATIO = 6      # use bincount once the scatter covers ~1/6 of the grid


def scatter_add(grid, cy, cx, vals) -> None:
    """grid[cy, cx] += vals, accumulating duplicates.

    np.add.at is the obvious way and is roughly an order of magnitude slower than a
    bincount over flattened indices; this runs several times per tick over the whole
    population.
    """
    n = len(cy)
    if n == 0:
        return
    if n * BINCOUNT_RATIO < grid.size:
        # bincount always costs O(grid.size); with few scatterers that is worse than
        # ufunc.at, which costs O(n).  Pick per call, not once.
        np.add.at(grid, (cy, cx), vals)
        return
    g = grid.shape[1]
    flat = np.bincount((cy.astype(np.int64) * g + cx), weights=vals,
                       minlength=grid.size)
    grid += flat.reshape(grid.shape).astype(grid.dtype, copy=False)


def scatter_sub(grid, cy, cx, vals) -> None:
    scatter_add(grid, cy, cx, -np.asarray(vals, np.float32))


def reflect_y(v, G: int):
    """Bounce a y coordinate off the poles instead of pinning it to them.

    Clamping makes the top and bottom rows absorbing: drifting in costs nothing and
    leaving requires directed movement, so over enough ticks the boundary swallows the
    population.  It did -- 14,326 of 19,986 creatures ended up inside the last two rows
    of a 384-row world, which read from every summary as a thriving pelagic ecotype and
    was in fact a queue against a wall.
    """
    top = np.float32(G - 1.001)
    v = np.abs(v)                       # reflect across y = 0
    v = np.where(v > top, 2.0 * top - v, v)
    return np.clip(v, 0.0, top).astype(np.float32)


def wrap_x(v, G: int):
    """Wrap an x coordinate into [0, G).  float32 `v % G` can round up to exactly G,
    which then indexes out of bounds -- clamp below the top edge as well."""
    return np.minimum(np.mod(v, G), np.float32(G - 1e-3)).astype(np.float32)


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


class Fauna:
    def __init__(self, cfg, world, flora, scent, rng: np.random.Generator):
        self.cfg = cfg
        self.world = world
        self.flora = flora
        self.scent = scent
        self.rng = rng
        G = world.G
        self.G = G
        cap = int(cfg.fauna["max_pop"])
        self.cap = cap

        self.schema = GenomeSchema("fauna", cap)
        for g in BODY_GENES:
            self.schema.add(g)
        for g in brainmod.brain_genes(float(cfg.genetics.get("brain_decay", 0.015))):
            self.schema.add(g)
        self.brain = Brain(self.schema)
        self.effects = EffectEngine(self.schema)
        # gene column indices, cached (hot path)
        self.gi = {n: self.schema.index[n] for n in BODY_NAMES}

        self.alive = np.zeros(cap, bool)
        self.x = np.zeros(cap, np.float32)
        self.y = np.zeros(cap, np.float32)
        self.energy = np.zeros(cap, np.float32)
        # body condition: surplus food banked as tissue.  It is what a predator
        # actually harvests from a carcass and what a starving animal lives off.
        self.tissue = np.zeros(cap, np.float32)
        self.health = np.zeros(cap, np.float32)
        self.age = np.zeros(cap, np.float32)
        self.matter = np.zeros(cap, np.float32)
        self.species = np.zeros(cap, np.int32)
        self.last_action = np.zeros(cap, np.int8)
        self.birth_tick = np.zeros(cap, np.int32)
        self.parent = np.full(cap, -1, np.int32)
        self.uid = np.zeros(cap, np.int64)
        self.last_birth = np.full(cap, -10**8, np.int32)
        self._next_uid = 1

        # corpse / meat pools (per cell)
        self.meat = np.zeros((G, G), np.float32)
        self.meat_matter = np.zeros((G, G), np.float32)

        # effective (ontogenetic) body size, refreshed every tick by build_stats
        self.size_eff = np.zeros(cap, np.float32)
        self.last_hunter_arming: dict = {}
        self.alive_idx = np.zeros(0, np.int64)
        self.nb = max(1, -(-G // BIN))   # ceil: a grid not divisible by BIN still needs the last bin
        self.last_inputs = np.zeros((0, N_IN), np.float32)
        self.last_outputs = np.zeros((0, N_OUT), np.float32)

    # ------------------------------------------------------------------ setup
    @property
    def pop(self) -> int:
        return int(self.alive_idx.size)

    def gene(self, name: str, rows=None) -> np.ndarray:
        col = self.schema.data[:, self.schema.index[name]]
        return col if rows is None else col[rows]

    def _free_slots(self, n: int) -> np.ndarray:
        if n <= 0:
            return np.zeros(0, np.int64)
        free = np.nonzero(~self.alive)[0]
        return free[:n]

    def spawn(self, n: int, cx: float | None = None, cy: float | None = None,
              radius: float = 12.0, archetype: dict | None = None,
              alien: bool = False, tick: int = 0,
              energy_mult: float = 1.0, brain_quiet: float = 1.0) -> np.ndarray:
        """Vectorized spawn.  Returns the indices created."""
        idx = self._free_slots(n)
        if len(idx) == 0:
            return idx
        n = len(idx)
        self.schema.init_rows(idx, self.rng)
        if alien:
            # a fully random alien genome: uniform over every gene's whole range
            lo = np.array([g.lo for g in self.schema.genes], np.float32)
            hi = np.array([g.hi for g in self.schema.genes], np.float32)
            self.schema.data[idx] = (lo + self.rng.random((n, self.schema.n)).astype(np.float32) * (hi - lo))
        if brain_quiet != 1.0:
            # A founder prior is six weights out of 166.  The other 160 are drawn at
            # std 0.7, and their summed contribution to any one pre-activation swamps
            # the instinct: seeded hunters chased with alignment 0.4 and pushed their
            # attack output to 0.65 when the wiring intends 0.97 -- and since a blow
            # lands only if attack_power * attack_output clears armour plus the evasion
            # roll, that shortfall put every kill mathematically out of reach.  Damping
            # the untaught weights lets the instinct read through; mutation restores the
            # diversity within a few dozen generations.
            self.schema.data[idx, self.brain.start:self.brain.end] *= float(brain_quiet)
        if archetype:
            for k, v in archetype.items():
                if k in self.schema.index:
                    g = self.schema.genes[self.schema.index[k]]
                    jitter = self.rng.normal(0, 0.06 * (g.hi - g.lo), n).astype(np.float32)
                    self.schema.data[idx, self.schema.index[k]] = np.clip(
                        float(v) + jitter, g.lo, g.hi)

        # placement: on land, near (cx, cy) if given
        land = np.argwhere(self.world.is_land & (self.world.water_depth < 0.2))
        if len(land) == 0:
            land = np.argwhere(np.ones((self.G, self.G), bool))
        if cx is None:
            pick = self.rng.choice(len(land), n, replace=True)
            py, px = land[pick, 0].astype(np.float32), land[pick, 1].astype(np.float32)
        else:
            ang = self.rng.random(n) * 2 * np.pi
            r = self.rng.random(n) ** 0.5 * radius
            py = reflect_y(cy + np.sin(ang) * r, self.G)
            px = wrap_x(cx + np.cos(ang) * r, self.G)
        self.y[idx] = py
        self.x[idx] = px
        self.alive[idx] = True
        # Founders arrive as established adults, not as newborns.  Seeded with one
        # start_energy a predator wave has about 250 ticks of fuel and starves before it
        # can find its first kill -- 221 of 255 died inside that window.
        self.energy[idx] = float(self.cfg.energy["start_energy"]) * float(energy_mult)
        self.tissue[idx] = (float(self.cfg.energy["tissue_store"])
                            * self.schema.data[idx, self.schema.index["size"]]
                            * float(self.cfg.energy["founder_condition"]))
        self.health[idx] = 1.0
        self.age[idx] = 0.0
        self.matter[idx] = 0.0
        self.species[idx] = 0
        self.birth_tick[idx] = tick
        self.parent[idx] = -1
        self.uid[idx] = np.arange(self._next_uid, self._next_uid + n)
        self.size_eff[idx] = self.schema.data[idx, self.schema.index["size"]]
        self.last_birth[idx] = tick
        self._next_uid += n
        self._refresh()
        return idx

    def _cradle(self) -> tuple[float, float]:
        """The greenest ground available -- where a founder stock has a chance."""
        good = (self.world.is_land & (self.world.water_depth < 0.15)
                & (self.flora.biomass > 0.15))
        if good.sum() < 50:
            good = self.world.is_land & (self.world.water_depth < 0.15)
        land = np.argwhere(good)
        if not len(land):
            return self.G / 2, self.G / 2
        c = land[self.rng.integers(0, len(land))]
        return float(c[0]), float(c[1])

    def prey_hotspot(self) -> tuple[float, float]:
        """Centre of the densest concentration of small-bodied creatures."""
        if self.pop == 0:
            return self._cradle()
        rows = self.alive_idx
        small = rows[self.size_eff[rows] < 0.5]
        if len(small) < 8:
            small = rows
        cy = np.clip(self.y[small].astype(np.int32), 0, self.G - 1) // BIN
        cx = np.clip(self.x[small].astype(np.int32), 0, self.G - 1) // BIN
        counts = np.zeros((self.nb, self.nb), np.int32)
        np.add.at(counts, (cy, cx), 1)
        from . import fields
        dens = fields.blur(counts.astype(np.float32), 0.6)
        j = int(np.argmax(dens))
        return float((j // self.nb) * BIN + BIN / 2), float((j % self.nb) * BIN + BIN / 2)

    def _arm_hunter(self, arch: dict) -> dict:
        """Scale a founder predator's weaponry to the prey it is being dropped among.

        The archetype is fixed at attack power 0.90.  That ignites a fresh world, and it
        is useless in one that has been running: after two thousand years of unopposed
        escalation the grazers here carry effective armour 1.04, and the engine wants a
        clear margin over that before anything registers as prey at all.  A wave seeded
        at the default found a target on 9.5% of its ticks, then 0%, and starved in a
        world containing five thousand animals it could not see as food.
        """
        rows = self.alive_idx
        if len(rows) < 50:
            return arch
        d = self.schema.data
        gi = self.gi
        # size_eff is derived during perceive and is still zero on a freshly resumed
        # world, which quietly dropped the 0.35*size term out of the armour estimate.
        size = self.size_eff[rows]
        if not size.any():
            size = d[rows, gi["size"]] * float(self.cfg.fauna["juvenile_size"])
        armour = d[rows, gi["armor"]] + 0.35 * size
        small = size < np.median(size) * 1.2          # what a predator would go after
        sel = small if small.any() else np.ones(len(rows), bool)
        target = float(np.percentile(armour[sel], 60))
        # A blow lands when attack_power * attack_output > armour + roll, where the roll
        # runs uniform over 0..0.45 plus 0.35*prey speed.  Arming against armour alone
        # ignored both terms: it reported "sufficient" at power 1.32 when the real bar
        # averaged 1.36 and the attack output only ever delivers a fraction of nominal
        # power.  Measured over four seedings that arithmetic produced exactly zero
        # kills while the hunters landed hits and starved.
        evasion = 0.225 + float(self.cfg.energy["evasion"]) * float(d[rows, gi["speed"]][sel].mean())
        need = (target + evasion) * PREY_POWER_MARGIN / FOUNDER_ATTACK_DRIVE

        arch = dict(arch)
        base_size = float(arch.get("size", 0.46))
        # power = fangs + 0.6 * size; spend on fangs first, then on frame
        fangs = min(1.0, max(float(arch.get("fangs", 0.62)), need - 0.6 * base_size))
        if fangs + 0.6 * base_size < need:
            base_size = min(1.0, (need - fangs) / 0.6)
        arch["fangs"] = fangs
        arch["size"] = base_size
        power = fangs + 0.6 * base_size
        self.last_hunter_arming = {
            "prey_armour_p60": round(target, 3), "evasion": round(evasion, 3),
            "power_needed": round(need, 3), "genome_ceiling": 1.6,
            "fangs": round(fangs, 3), "size": round(base_size, 3),
            "power": round(power, 3), "sufficient": bool(power >= need * 0.98)}
        return arch

    def seed_founders(self, tick: int = 0, only: set[str] | None = None,
                      at: tuple[float, float] | None = None,
                      count: int | None = None) -> int:
        """Drop founder populations.

        `only` restricts which archetypes are seeded; `count` overrides the per-type
        stock with an absolute number (used to size the predator wave against the prey
        base that actually exists rather than a constant).
        """
        per = int(self.cfg.fauna["founders_per_type"] * (self.G / 192.0) ** 2)
        base_y, base_x = at if at is not None else self._cradle()
        n = 0
        for name, share, arch in FOUNDERS:
            if only is not None and name not in only:
                continue
            if name == "hunter":
                arch = self._arm_hunter(arch)
            off = self.G * 0.05
            cy = float(np.clip(base_y + self.rng.normal(0, off), 0, self.G - 1))
            cx = float((base_x + self.rng.normal(0, off)) % self.G)
            want = int(count) if count is not None else int(per * share)
            # a predator wave crowded into one hotspot competes with itself for the same
            # few prey, so spread it wider than the herbivore cradle
            spread = 0.45 if name == "hunter" else 0.30
            n += len(self.spawn(max(4, want), cx=cx, cy=cy,
                                radius=self.G * spread, tick=tick, archetype=arch,
                                energy_mult=float(self.cfg.fauna["founder_energy_mult"]),
                                brain_quiet=float(self.cfg.fauna["founder_brain_quiet"])))
        return n

    def _refresh(self) -> None:
        self.alive_idx = np.nonzero(self.alive)[0]

    # ------------------------------------------------------------ derived stats
    def build_stats(self, rows: np.ndarray, ctx: dict) -> dict:
        """Baseline stat dict, then runtime-gene effects layered on top."""
        d = self.schema.data
        gi = self.gi
        diet = d[rows, gi["diet"]]
        # Ontogeny: a newborn is a fraction of its adult size and grows into it.  Born
        # at full adult mass, a big-bodied juvenile carries an adult's metabolic bill
        # with none of an adult's competence, and large predators never recruit.
        mat = max(1.0, float(self.cfg.fauna["min_repro_age"]))
        grow = (float(self.cfg.fauna["juvenile_size"])
                + (1.0 - float(self.cfg.fauna["juvenile_size"]))
                * np.clip(self.age[rows] / mat, 0.0, 1.0))
        size = (d[rows, gi["size"]] * grow).astype(np.float32)
        self.size_eff[rows] = size
        # Every trait is paid for.  Run 272 sim-years without this and camouflage, armour,
        # lifespan, toxin tolerance and metabolic efficiency all pin to 1.0 within a few
        # dozen generations -- a free lunch is not a selection pressure, it is a ratchet.
        e = self.cfg.energy
        # One knob for the whole trade-off.  At 0 every trait is free and selection pins
        # them all to 1.0; at 1 they are fully costed and settle at interior optima, but
        # predators -- who cannot economise on sense range -- pay the most and the top of
        # the food chain gets fragile.  See README, "Traits cost something".
        tcs = float(e["trait_cost_scale"])
        upkeep = (1.0 + tcs * (
                  float(e["cost_camouflage"]) * d[rows, gi["camouflage"]]
                  + float(e["cost_toxin_tol"]) * d[rows, gi["toxin_tolerance"]]
                  + float(e["cost_sense"]) * d[rows, gi["sense_range"]]
                  + float(e["cost_armor"]) * d[rows, gi["armor"]]
                  + float(e["cost_fangs"]) * d[rows, gi["fangs"]]
                  + float(e["cost_lifespan"]) * d[rows, gi["lifespan"]])).astype(np.float32)
        stats = {
            "size": size,
            "basal_cost": upkeep,
            "move_cost": (1.0 + tcs * float(e["move_cost_armor"])
                          * d[rows, gi["armor"]]).astype(np.float32),
            "bite_size": float(self.cfg.fauna["bite_scale"]) * size,
            "attack_power": d[rows, gi["fangs"]] + 0.6 * size,
            "armor_eff": d[rows, gi["armor"]] + 0.35 * size,
            "detectability": 1.0 - d[rows, gi["camouflage"]],
            "sense_bonus": np.zeros(len(rows), np.float32),
            "mate_appeal": np.zeros(len(rows), np.float32),
            "cold_resist": d[rows, gi["cold_tol"]],
            "heat_resist": d[rows, gi["heat_tol"]],
            "toxin_resist": d[rows, gi["toxin_tolerance"]],
            # PLAN 13: specialists must beat generalists at their own game.  These
            # smoothsteps are deliberately steeper than complementary -- a mid-diet
            # omnivore gets about 0.28 on each side rather than 0.5, so the diet axis has
            # two peaks and a carnivore lineage is not slowly pulled back down it.
            # Jarman-Bell: a larger gut holds forage longer and extracts more from it.
            # Without a size-dependent *quality* term the only return on body mass is a
            # bigger mouthful, which local plant density caps -- so every lineage shrinks
            # to the floor and leaves nothing big enough to be prey.
            "plant_digest": (smoothstep(1.15 - diet * 1.45)
                             * (float(e["digest_size_min"])
                                + float(e["digest_size_gain"]) * size)),
            "meat_digest": smoothstep(diet * 1.45 - 0.30),
            "fire_resist": np.zeros(len(rows), np.float32),
            "swim_eff": d[rows, gi["swim"]],
            "scent_strength": d[rows, gi["scent_deposit"]],
            "fertility_local": np.zeros(len(rows), np.float32),
        }
        if self.effects.any_effects():
            self.effects.apply(stats, rows, ctx)
        return stats

    # ------------------------------------------------------------- perception
    def _bins(self, rows: np.ndarray):
        cy = np.clip(self.y[rows].astype(np.int32), 0, self.G - 1)
        cx = np.clip(self.x[rows].astype(np.int32), 0, self.G - 1)
        return cy, cx, cy // BIN, cx // BIN

    def perceive(self, rows: np.ndarray, ctx: dict, stats: dict):
        """Builds the (n, 13) input matrix.  Also returns the target index arrays."""
        n = len(rows)
        G, nb = self.G, self.nb
        d = self.schema.data
        gi = self.gi
        cy, cx, by, bx = self._bins(rows)
        size = np.asarray(stats["size"], np.float32)
        diet = d[rows, gi["diet"]]
        # What decides whether you can take something is not mass alone but mass plus
        # weaponry.  Tying predation to raw size means that when herbivores evolve large
        # bodies no predator can be big enough to eat them and the tier goes extinct.
        # What makes something huntable is whether you could beat it, not what it weighs.
        # A hard size ratio forces a body-mass treadmill: prey evolve larger, predators
        # must out-grow them, the gene ceiling arrives, and the tier dies.  Power against
        # armour makes fangs and armour the arms race -- which is what those genes are
        # for -- and lets a small well-armed hunter take a large soft grazer.
        power = np.asarray(stats["attack_power"], np.float32)
        armour = np.asarray(stats["armor_eff"], np.float32)
        power_full = np.zeros(self.cap, np.float32)
        power_full[rows] = power
        armour_full = np.zeros(self.cap, np.float32)
        armour_full[rows] = armour
        sense = 1.0 + d[rows, gi["sense_range"]] * MAX_SENSE + stats["sense_bonus"] * 4.0

        # --- bin representatives: the softest target and the hardest hitter ----
        big_idx = np.full((nb, nb), -1, np.int64)
        small_idx = np.full((nb, nb), -1, np.int64)
        o_pow = np.argsort(power, kind="stable")
        big_idx[by[o_pow], bx[o_pow]] = rows[o_pow]          # last write = most dangerous
        o_arm = np.argsort(-armour, kind="stable")
        small_idx[by[o_arm], bx[o_arm]] = rows[o_arm]        # last write = least armoured

        # visibility: camouflage shrinks the range at which you are seen (2x at night)
        detect = np.clip(stats["detectability"], 0.05, 2.0)
        if ctx["is_night"]:
            detect = detect * 0.5
        det_full = np.zeros(self.cap, np.float32)
        det_full[rows] = detect
        size_full = np.zeros(self.cap, np.float32)
        size_full[rows] = size
        diet_full = np.zeros(self.cap, np.float32)
        diet_full[rows] = diet
        xf, yf = self.x, self.y

        # Work in squared distance throughout; the only place a real distance is needed
        # is the final relative-bearing vector, so 18 whole-population sqrt calls per
        # tick collapse into two.
        best_prey_d = np.full(n, 1e18, np.float32)
        best_prey = np.full(n, -1, np.int64)
        best_threat_d = np.full(n, 1e18, np.float32)
        best_threat = np.full(n, -1, np.int64)
        sense_sq = (sense * sense).astype(np.float32)

        # 3x3 bins at BIN=6 already reaches MAX_SENSE cells.  A 5x5 window costs 2.5x
        # the work for range nothing can actually perceive; materialising all offsets
        # as one (n, 50) gather is slower still -- it leaves cache.
        for dy, dx in NEIGH:
            nby = np.clip(by + dy, 0, nb - 1)
            nbx = (bx + dx) % nb
            for cand_grid, is_prey in ((small_idx, True), (big_idx, False)):
                cand = cand_grid[nby, nbx]
                ok = (cand >= 0) & (cand != rows)
                if not ok.any():
                    continue
                c = np.where(ok, cand, 0)
                ddx = xf[c] - self.x[rows]
                ddx = (ddx + G / 2) % G - G / 2
                ddy = yf[c] - self.y[rows]
                dist = ddx * ddx + ddy * ddy + 1e-8            # squared
                det = np.clip(det_full[c], 0.05, 2.0)
                visible = ok & (dist < sense_sq * det * det)
                if is_prey:
                    # Kin recognition.  With ontogeny the smallest creature in any bin is
                    # usually somebody's juvenile, so without this a founding predator
                    # stock eats its own recruitment and cannot establish.
                    pm = (visible
                          & (power > armour_full[c] * PREY_POWER_MARGIN)
                          & (size_full[c] < size * MAX_PREY_SIZE_MULT)
                          & (diet > 0.18)
                          & (self.species[c] != self.species[rows]))
                    upd = pm & (dist < best_prey_d)
                    best_prey_d = np.where(upd, dist, best_prey_d)
                    best_prey = np.where(upd, c, best_prey)
                else:
                    tm = (visible
                          & (power_full[c] > armour * THREAT_POWER_MARGIN)
                          & (diet_full[c] > 0.35))
                    upd = tm & (dist < best_threat_d)
                    best_threat_d = np.where(upd, dist, best_threat_d)
                    best_threat = np.where(upd, c, best_threat)

        return self._finish_perceive(
            rows, ctx, stats, n, G, d, gi, cy, cx, diet,
            best_prey, best_prey_d, best_threat, best_threat_d)

    def _finish_perceive(self, rows, ctx, stats, n, G, d, gi, cy, cx, diet,
                         best_prey, best_prey_d, best_threat, best_threat_d):
        """Turn the chosen targets into the brain's input vector."""
        def rel(target, tdist):
            has = target >= 0
            t = np.where(has, target, 0)
            ddx = (self.x[t] - self.x[rows] + G / 2) % G - G / 2
            ddy = self.y[t] - self.y[rows]
            inv = 1.0 / np.maximum(tdist, 1.0)
            return (np.where(has, ddx * inv, 0.0).astype(np.float32),
                    np.where(has, ddy * inv, 0.0).astype(np.float32))

        best_prey_d = np.sqrt(best_prey_d, dtype=np.float32)
        best_threat_d = np.sqrt(best_threat_d, dtype=np.float32)
        prey_dx, prey_dy = rel(best_prey, best_prey_d)
        thr_dx, thr_dy = rel(best_threat, best_threat_d)

        # --- environment samples ---------------------------------------------
        plant = np.clip(self.flora.biomass[cy, cx] / 1.5, 0.0, 1.5).astype(np.float32)
        meat = np.clip(self.meat[cy, cx] / 8.0, 0.0, 1.5).astype(np.float32)
        ch = self.scent.channel_for(self.species[rows])
        kgx, kgy = self.scent.sample_gradient(ch, cy, cx, blood_weight=diet)
        foreign = np.clip(self.scent.foreign(ch, cy, cx) / 4.0, 0.0, 2.0)
        comfort = 0.35 + 0.5 * (d[rows, gi["heat_tol"]] * 0.5
                                + (1.0 - d[rows, gi["cold_tol"]]) * 0.5)
        temp_delta = np.clip(self.world.temperature[cy, cx] - comfort, -1.5, 1.5)
        emax = np.maximum(float(self.cfg.energy["repro_threshold_abs"]), 1.0)
        life = 200.0 + d[rows, gi["lifespan"]] * MAX_LIFE

        inp = np.empty((n, N_IN), np.float32)
        inp[:, 0] = np.clip(self.energy[rows] / emax, 0.0, 2.0)
        inp[:, 1] = np.clip(self.age[rows] / life, 0.0, 1.5)
        inp[:, 2] = plant
        inp[:, 3] = meat
        inp[:, 4] = prey_dx
        inp[:, 5] = prey_dy
        inp[:, 6] = thr_dx
        inp[:, 7] = thr_dy
        inp[:, 8] = np.clip(kgx, -2, 2)
        inp[:, 9] = np.clip(kgy, -2, 2)
        inp[:, 10] = foreign
        inp[:, 11] = temp_delta
        inp[:, 12] = 1.0 if ctx["is_night"] else 0.0
        return inp, cy, cx, best_prey, best_prey_d, best_threat, best_threat_d

    # ------------------------------------------------------------------- act
    def act(self, rows, out, cy, cx, prey, prey_d, ctx, stats, tick) -> dict:
        cfg_f = self.cfg.fauna
        cfg_e = self.cfg.energy
        d = self.schema.data
        gi = self.gi
        n = len(rows)
        G = self.G
        ev = {"eaten_plant": 0.0, "eaten_meat": 0.0, "kills": 0, "births": 0,
              "attacks": 0}

        size = stats["size"]
        speed_g = d[rows, gi["speed"]]
        action = np.full(n, ACT_IDLE, np.int8)

        # --- movement ---------------------------------------------------------
        mv = out[:, :2]
        flee = np.clip(out[:, 4], 0.0, 1.0)
        noise = self.rng.normal(0, float(cfg_f["move_noise"]), (n, 2)).astype(np.float32)
        # an economical metabolism is not also a powerful one
        power = (float(cfg_e["speed_eff_penalty"])
                 - (float(cfg_e["speed_eff_penalty"]) - 1.0)
                 * d[rows, gi["metabolism_eff"]]).astype(np.float32)
        # Sprint musculature.  Prey speed is under ferocious selection and shares the same
        # gene ceiling as a hunter's, so once the herds are as fast as the predators no
        # chase ever closes and the top of the food chain quietly starves. A meat-eater
        # trades endurance for burst; this is the fast-twitch half of that trade.
        sprint = 1.0 + float(cfg_e["sprint_diet"]) * d[rows, gi["diet"]]
        vel = ((mv + noise) * (speed_g * MAX_SPEED * power * sprint)[:, None]
               * (1.0 + 0.35 * flee)[:, None])
        vmag = np.sqrt(vel[:, 0] ** 2 + vel[:, 1] ** 2)
        newx = wrap_x(self.x[rows] + vel[:, 0], G)
        raw_y = self.y[rows] + vel[:, 1]
        newy = reflect_y(raw_y, G)
        # a creature that bounced is heading the other way now
        vel[:, 1] = np.where(raw_y != newy, -vel[:, 1], vel[:, 1])
        ny_i = np.clip(newy.astype(np.int32), 0, G - 1)
        nx_i = np.clip(newx.astype(np.int32), 0, G - 1)
        deep = self.world.water_depth[ny_i, nx_i] > 0.25
        can_swim = stats["swim_eff"] > 0.45
        blocked = deep & ~can_swim
        self.x[rows] = np.where(blocked, self.x[rows], newx)
        self.y[rows] = np.where(blocked, self.y[rows], newy)
        vmag = np.where(blocked, 0.0, vmag)
        action = np.where(vmag > 0.05, ACT_MOVE, action).astype(np.int8)

        cy = np.clip(self.y[rows].astype(np.int32), 0, G - 1)
        cx = np.clip(self.x[rows].astype(np.int32), 0, G - 1)

        # --- eating -----------------------------------------------------------
        want_eat = out[:, 2] > 0.0
        bite = stats["bite_size"] * np.clip(out[:, 2], 0, 1)
        # plants
        # metabolic efficiency trades against reserve capacity: a lean, economical body
        # is not also a larder
        cap_e = (float(cfg_e["max_store"]) * (0.35 + size)
                 * (float(cfg_e["store_eff_penalty"])
                    - (float(cfg_e["store_eff_penalty"]) - 1.0) * d[rows, gi["metabolism_eff"]]))
        cap_t = float(cfg_e["tissue_store"]) * size
        room = (np.maximum(0.0, cap_e - self.energy[rows])
                + np.maximum(0.0, cap_t - self.tissue[rows]))
        # A grazer crops a plant; it cannot eat the crown out of it.  Without this floor
        # herbivores strip every cell to death and the whole food chain follows.
        avail = np.maximum(0.0, self.flora.biomass[cy, cx] - float(cfg_f["graze_floor"]))
        # A large grazer reaches beyond the cell it stands on.  Per-tick intake capped at
        # one cell's biomass is what drives every lineage to the size floor: basal cost
        # rises with mass but the meal does not, so nothing stays big enough to be prey
        # and the predator tier has nobody to eat.
        graze = float(cfg_f["graze_fraction"])
        reach = np.clip((size - float(cfg_f["reach_size_min"]))
                        / float(cfg_f["reach_size_span"]), 0.0, 1.0).astype(np.float32)
        # four gathers and four scatters per tick for nothing when reach is disabled
        use_reach = bool(reach.any())
        if use_reach:
            ny = [np.clip(cy - 1, 0, G - 1), np.clip(cy + 1, 0, G - 1), cy, cy]
            nx = [cx, cx, (cx - 1) % G, (cx + 1) % G]
            near = [np.maximum(0.0, self.flora.biomass[a, b] - float(cfg_f["graze_floor"]))
                    for a, b in zip(ny, nx)]
            avail_all = avail + sum(near) * reach
        else:
            avail_all = avail
        take = np.minimum(bite, avail_all * graze) * want_eat * (stats["plant_digest"] > 0.02)
        take = np.maximum(take, 0.0)
        edens0 = self.flora.energy_density()[cy, cx]
        per_unit = np.maximum(edens0 * float(cfg_e["plant_energy_scale"])
                              * stats["plant_digest"], 1e-6)
        take = np.minimum(take, room / per_unit)      # do not harvest what you cannot store
        if take.any():
            if use_reach:
                share = take / np.maximum(avail_all, 1e-6)
                scatter_sub(self.flora.biomass, cy, cx, avail * share)
                for (a, b), nb in zip(zip(ny, nx), near):
                    scatter_sub(self.flora.biomass, a, b, nb * reach * share)
            else:
                scatter_sub(self.flora.biomass, cy, cx, take)
            np.clip(self.flora.biomass, 0.0, None, out=self.flora.biomass)
            gainE = take * per_unit
            # toxin arms race: mostly a digestive tax on the energy you extract, with a
            # small cumulative health cost -- lethal-per-bite poison wipes the herbivores
            # out before tolerance can evolve.
            tox = self.flora.genome.plane("toxin")[cy, cx]
            excess = np.maximum(0.0, tox - stats["toxin_resist"]) * (take > 1e-4)
            gainE = gainE * np.clip(1.0 - excess * float(cfg_e["toxin_energy_penalty"]), 0.0, 1.0)
            np.add.at(self.energy, rows, gainE)
            np.subtract.at(self.health, rows, excess * float(cfg_e["toxin_damage_scale"]))
            self.matter[rows] += take * self.flora.matter_per_biomass
            ev["eaten_plant"] = float(take.sum())
            action = np.where(take > 1e-3, ACT_EAT, action).astype(np.int8)
        # carrion
        mavail = self.meat[cy, cx]
        room = (np.maximum(0.0, cap_e - self.energy[rows])
                + np.maximum(0.0, cap_t - self.tissue[rows]))
        # meat is stored as energy, so digestion is a loss factor, never a multiplier
        m_per_unit = np.maximum(
            min(1.0, float(cfg_e["meat_energy_scale"])) * stats["meat_digest"], 1e-6)
        mtake = np.minimum(bite * 1.2, mavail * 0.5) * want_eat * (stats["meat_digest"] > 0.02)
        mtake = np.maximum(np.minimum(mtake, room / m_per_unit), 0.0)
        if mtake.any():
            frac = np.where(mavail > 1e-6, mtake / np.maximum(mavail, 1e-6), 0.0)
            mmatter = self.meat_matter[cy, cx] * frac
            scatter_sub(self.meat, cy, cx, mtake)
            scatter_sub(self.meat_matter, cy, cx, mmatter)
            np.clip(self.meat, 0.0, None, out=self.meat)
            np.clip(self.meat_matter, 0.0, None, out=self.meat_matter)
            np.add.at(self.energy, rows, mtake * m_per_unit)
            self.matter[rows] += mmatter
            ev["eaten_meat"] = float(mtake.sum())
            action = np.where(mtake > 1e-3, ACT_EAT, action).astype(np.int8)

        # energy above what the body can hold is laid down as tissue
        over = np.maximum(0.0, self.energy[rows] - cap_e)
        if over.any():
            self.energy[rows] -= over
            self.tissue[rows] = np.minimum(self.tissue[rows] + over, cap_t)

        # --- attack -----------------------------------------------------------
        want_att = (out[:, 3] > 0.15) & (prey >= 0) & (prey_d < float(cfg_f["attack_range"]))
        if want_att.any():
            a = np.nonzero(want_att)[0]
            att_rows = rows[a]
            vic = prey[a]
            self.energy[att_rows] -= float(cfg_e["attack_cost"]) * (1.0 + size[a])
            power = stats["attack_power"][a] * np.clip(out[a, 3], 0, 1)
            vsize = self.size_eff[vic]
            varmor = d[vic, gi["armor"]] + 0.35 * vsize
            vspeed = d[vic, gi["speed"]]
            roll = (self.rng.random(len(a)).astype(np.float32) * 0.45
                    + float(cfg_e["evasion"]) * vspeed)
            hit = power > (varmor + roll)
            dmg = np.where(hit, float(cfg_e["hit_base"]) + power * float(cfg_e["hit_scale"]),
                           0.0).astype(np.float32)
            np.subtract.at(self.health, vic, dmg)
            self.scent.deposit_blood(
                np.clip(self.y[vic].astype(np.int32), 0, G - 1),
                np.clip(self.x[vic].astype(np.int32), 0, G - 1),
                float(self.cfg.scent["blood_deposit"]) * dmg)
            # A landed blow closes the distance.  Without this the attacker stays a cell
            # or two off, the victim dies, the chase signal vanishes with it, and the
            # predator wanders away from the kill it just made -- which is why the world
            # filled up with uneaten carrion while the carnivores starved.
            if hit.any():
                lunge = a[hit]
                self.x[rows[lunge]] = self.x[vic[hit]]
                self.y[rows[lunge]] = self.y[vic[hit]]
            action[a] = np.where(hit, ACT_ATTACK, action[a]).astype(np.int8)
            ev["attacks"] = int(hit.sum())

        # --- breeding ---------------------------------------------------------
        births = self._reproduce(rows, out, stats, ctx, tick)
        ev["births"] = births
        if births:
            action = np.where(out[:, 5] > 0.2, ACT_BREED, action).astype(np.int8)

        # --- scent deposition --------------------------------------------------
        dep = stats["scent_strength"] * float(self.cfg.scent["deposit_scale"])
        social = d[rows, gi["social"]]
        dep = dep * (0.25 + social)
        ch = self.scent.channel_for(self.species[rows])
        self.scent.deposit(ch, cy, cx, dep)

        self.last_action[rows] = action
        self._move_cost = vmag * size * float(cfg_e["move_cost"]) * stats["move_cost"]
        return ev

    def _reproduce(self, rows, out, stats, ctx, tick) -> int:
        cfg_e = self.cfg.energy
        cfg_f = self.cfg.fauna
        d = self.schema.data
        gi = self.gi
        thr = float(cfg_e["repro_threshold_abs"]) * (0.5 + d[rows, gi["repro_threshold"]])
        # gestation: an animal cannot spawn a child every twenty ticks.  Without a
        # cooldown the herbivores blow past carrying capacity in one season, strip the
        # world, and take the whole food chain down with them.
        cool = (float(cfg_f["repro_cooldown"]) * (0.5 + d[rows, gi["size"]])
                * (float(cfg_f["cooldown_lifespan"])
                   + (1.0 - float(cfg_f["cooldown_lifespan"])) * 2.0
                   * d[rows, gi["lifespan"]]))
        # (cooldown uses the adult gene: a big animal always gestates slowly)
        ready = ((self.energy[rows] > thr)
                 & (out[:, 5] > 0.0)
                 & (self.age[rows] > float(cfg_f["min_repro_age"]))
                 & (tick - self.last_birth[rows] > cool)
                 & (self.health[rows] > 0.45))
        if not ready.any():
            return 0
        pr = np.nonzero(ready)[0]
        parents = rows[pr]
        # cap births per tick to whatever capacity allows
        free = np.nonzero(~self.alive)[0]
        if len(free) == 0:
            return 0
        if len(parents) > len(free):
            pick = self.rng.choice(len(parents), len(free), replace=False)
            pr, parents = pr[pick], parents[pick]
        kids = free[:len(parents)]

        # sexual reproduction needs a nearby partner; find one via the bin grid
        sexual = d[parents, gi["sexual"]] > 0.5
        mates = np.full(len(parents), -1, np.int64)
        if sexual.any():
            mates = self._find_mates(parents, sexual, stats, rows)
            # sexual parents without a mate this tick simply don't breed
            keep = (~sexual) | (mates >= 0)
            if not keep.all():
                pr, parents, kids, mates = pr[keep], parents[keep], kids[keep], mates[keep]
                sexual = sexual[keep]
            if len(parents) == 0:
                return 0

        g = self.cfg.genetics
        has_mate = mates >= 0
        self.schema.inherit(kids, parents, None, self.rng)
        if has_mate.any():
            km = kids[has_mate]
            mask = self.rng.random((len(km), self.schema.n)) < 0.5
            self.schema.data[km] = np.where(mask, self.schema.data[mates[has_mate]],
                                            self.schema.data[km])
        rate = float(g["mutation_rate_global"])
        # sexual lineages get a small mutation-quality bonus (tighter, less lethal drift)
        self.schema.mutate_rows(kids[has_mate], self.rng, rate * float(g["crossover_bonus"]),
                                float(g["macro_mutation_prob"]), float(g["macro_mutation_scale"]))
        self.schema.mutate_rows(kids[~has_mate], self.rng, rate,
                                float(g["macro_mutation_prob"]), float(g["macro_mutation_scale"]))

        invest = d[parents, gi["repro_invest"]]
        give = self.energy[parents] * invest
        give = np.maximum(give, float(cfg_f["child_energy_min"]))
        give = np.minimum(give, self.energy[parents] * 0.8)
        self.energy[parents] -= give
        mgive = self.matter[parents] * invest
        self.matter[parents] -= mgive

        self.alive[kids] = True
        self.size_eff[kids] = (self.schema.data[kids, gi["size"]]
                               * float(cfg_f["juvenile_size"]))
        # Part of what the parent invests becomes body, not fuel.  This is what makes a
        # carcass worth eating even when its owner died with an empty stomach -- and it
        # is paid for out of the parent's energy, so nothing is created.
        struct = give * float(cfg_e["struct_birth_frac"])
        self.energy[kids] = give - struct
        self.tissue[kids] = struct
        self.matter[kids] = mgive
        self.health[kids] = 1.0
        self.age[kids] = 0.0
        jit = self.rng.normal(0, 1.2, (len(kids), 2)).astype(np.float32)
        self.x[kids] = wrap_x(self.x[parents] + jit[:, 0], self.G)
        self.y[kids] = reflect_y(self.y[parents] + jit[:, 1], self.G)
        self.species[kids] = self.species[parents]
        self.birth_tick[kids] = tick
        self.parent[kids] = parents.astype(np.int32)
        self.uid[kids] = np.arange(self._next_uid, self._next_uid + len(kids))
        self._next_uid += len(kids)
        self.last_birth[kids] = tick
        self.last_birth[parents] = tick
        if has_mate.any():
            self.last_birth[mates[has_mate]] = tick
        self.last_action[kids] = ACT_IDLE
        return int(len(kids))

    def _find_mates(self, parents, sexual, stats, rows) -> np.ndarray:
        """Nearest same-species adult, preferring high mate_appeal.

        The candidate grid is built **per species**.  One representative per bin drawn
        from the whole population is worse than useless for a rare lineage: every bin a
        scarce predator looks in is occupied by some abundant herbivore, so it never
        finds a mate and the lineage cannot breed at all -- even standing next to a
        conspecific.
        """
        G, nb = self.G, self.nb
        mates = np.full(len(parents), -1, np.int64)
        s_idx = np.nonzero(sexual)[0]
        if len(s_idx) == 0:
            return mates

        mature = float(self.cfg.fauna["min_repro_age"])
        adults = rows[self.age[rows] > mature]
        if len(adults) == 0:
            return mates
        appeal = np.zeros(self.cap, np.float32)
        appeal[rows] = stats["mate_appeal"] + self.rng.random(len(rows)).astype(np.float32) * 0.25

        p_all = parents[s_idx]
        rng_all = (float(self.cfg.fauna["mate_range"])
                   * (1.0 + self.schema.data[p_all, self.gi["sense_range"]] * 4.0))
        adult_sp = self.species[adults]

        for sp in np.unique(self.species[p_all]):
            sel = np.nonzero(self.species[p_all] == sp)[0]
            cand = adults[adult_sp == sp]
            if len(cand) < 2 or len(sel) == 0:
                continue
            aby = np.clip(self.y[cand].astype(np.int32), 0, G - 1) // BIN
            abx = np.clip(self.x[cand].astype(np.int32), 0, G - 1) // BIN
            order = np.argsort(appeal[cand], kind="stable")
            grid = np.full((nb, nb), -1, np.int64)
            grid[aby[order], abx[order]] = cand[order]   # last write = most appealing

            p = p_all[sel]
            pby = np.clip(self.y[p].astype(np.int32), 0, G - 1) // BIN
            pbx = np.clip(self.x[p].astype(np.int32), 0, G - 1) // BIN
            best = np.full(len(p), -1, np.int64)
            bestd = np.full(len(p), 1e9, np.float32)
            reach = rng_all[sel]
            for dy, dx in NEIGH:
                c = grid[np.clip(pby + dy, 0, nb - 1), (pbx + dx) % nb]
                ok = (c >= 0) & (c != p)
                cc = np.where(ok, c, 0)
                ddx = (self.x[cc] - self.x[p] + G / 2) % G - G / 2
                ddy = self.y[cc] - self.y[p]
                dist = np.sqrt(ddx * ddx + ddy * ddy)
                upd = ok & (dist < reach) & (dist < bestd)
                bestd = np.where(upd, dist, bestd)
                best = np.where(upd, cc, best)
            mates[s_idx[sel]] = best
        return mates

    # ------------------------------------------------------------- metabolism
    def metabolize(self, rows, ctx, stats, tick) -> dict:
        cfg_e = self.cfg.energy
        d = self.schema.data
        gi = self.gi
        G = self.G
        size = stats["size"]
        diet = d[rows, gi["diet"]]
        meta = d[rows, gi["metabolism_eff"]]

        basal = (float(cfg_e["basal_rate"]) * np.power(np.maximum(size, 0.02),
                                                       float(cfg_e["size_exp"]))
                 / np.maximum(float(cfg_e["meta_floor"])
                              + (1.0 - float(cfg_e["meta_floor"])) * meta, 0.1))
        # predators run slightly leaner per unit mass (plan §13)
        basal *= (1.0 - float(cfg_e["carnivore_basal_discount"]) * diet)
        basal *= stats["basal_cost"]

        cy = np.clip(self.y[rows].astype(np.int32), 0, G - 1)
        cx = np.clip(self.x[rows].astype(np.int32), 0, G - 1)
        G = self.G
        temp = self.world.temperature[cy, cx]
        cold_gap = np.maximum(0.0, (0.42 - stats["cold_resist"] * 0.42) - temp)
        heat_gap = np.maximum(0.0, temp - (0.62 + stats["heat_resist"] * 0.45))
        thermal = (float(cfg_e["cold_cost"]) * cold_gap / (0.35 + size)
                   + float(cfg_e["heat_cost"]) * heat_gap)

        # Interference competition.  Nothing in the world charged for crowding, so a
        # single cell could hold twenty-one animals as cheaply as one -- and once the
        # brains degenerated into a constant heading and drove everybody into the same
        # corner, that corner became the best address in the world instead of the worst.
        counts = np.bincount((cy.astype(np.int64) * G + cx),
                             minlength=self.G * self.G).reshape(self.G, self.G)
        crowd = counts[cy, cx].astype(np.float32)
        crowding = (float(cfg_e["crowd_cost"])
                    * np.maximum(0.0, crowd - float(cfg_e["crowd_free"])))

        drain = basal + thermal + crowding + getattr(self, "_move_cost", 0.0)
        self.energy[rows] -= drain

        # A lean animal lives off its own condition before it starves -- but only down
        # to a structural floor.  Nothing metabolises itself away to nothing.
        deficit = np.maximum(0.0, -self.energy[rows])
        if deficit.any():
            floor = (float(cfg_e["tissue_store"]) * size
                     * float(cfg_e["tissue_floor"]))
            burnable = np.maximum(0.0, self.tissue[rows] - floor)
            pull = np.minimum(burnable, deficit)
            self.energy[rows] += pull
            self.tissue[rows] -= pull

        # metabolic waste: a living animal continuously returns matter to the ground it
        # stands on.  Without this, every creature is a permanent matter sink and the
        # soil slowly empties.
        ex = self.matter[rows] * float(cfg_e["excrete_rate"])
        self.matter[rows] -= ex
        scatter_add(self.world.nutrients, cy, cx, ex)
        self.age[rows] += 1.0
        self.health[rows] = np.minimum(1.0, self.health[rows] + float(cfg_e["heal_rate"]))

        life = 200.0 + d[rows, gi["lifespan"]] * MAX_LIFE
        starved = self.energy[rows] <= 0.0
        aged = self.age[rows] > life
        wounded = self.health[rows] <= 0.0
        dead_mask = starved | aged | wounded
        n_dead = int(dead_mask.sum())
        causes = {"starved": int(starved.sum()), "aged": int((aged & ~starved).sum()),
                  "killed": int((wounded & ~starved & ~aged).sum())}
        if n_dead:
            self.die(rows[dead_mask])
        return {"deaths": n_dead, **causes}

    def die(self, victims: np.ndarray) -> None:
        if len(victims) == 0:
            return
        G = self.G
        d = self.schema.data
        size = self.size_eff[victims]
        cy = np.clip(self.y[victims].astype(np.int32), 0, G - 1)
        cx = np.clip(self.x[victims].astype(np.int32), 0, G - 1)
        # A corpse is worth a fraction of the energy its owner was actually carrying --
        # nothing more.  The old body-mass term handed out energy the animal had never
        # eaten, so predators cannibalising each other ran a perpetual motion machine and
        # the top of the food chain exploded to the population cap on free calories.
        meat = float(self.cfg.fauna["corpse_energy_frac"]) * (
            np.maximum(self.energy[victims], 0.0) + np.maximum(self.tissue[victims], 0.0))
        scatter_add(self.meat, cy, cx, meat)
        scatter_add(self.meat_matter, cy, cx, np.maximum(self.matter[victims], 0.0))
        self.scent.deposit_blood(cy, cx,
                                 float(self.cfg.scent["blood_deposit"]) * (0.5 + size))
        self.alive[victims] = False
        self.energy[victims] = 0.0
        self.tissue[victims] = 0.0
        self.matter[victims] = 0.0
        self.health[victims] = 0.0
        self._refresh()

    def decay_corpses(self) -> None:
        k = 1.0 / max(1.0, float(self.cfg.fauna["corpse_decay_ticks"]))
        gone_m = self.meat_matter * k
        self.world.nutrients += gone_m
        self.meat_matter -= gone_m
        self.meat *= (1.0 - k)
        self.meat[self.meat < 1e-4] = 0.0
        # Carrion keeps smelling for as long as it lasts.  Without this the world is
        # full of meat nothing can find, meat-eating never pays, and the diet axis
        # collapses to pure herbivory.
        # Saturating, not linear.  An unbounded deposit lets one cell out-signal the
        # whole world: a freezing pole accumulated 2488 units of carrion in a single row,
        # its blood plume drowned every other gradient, and scavengers walked into it,
        # died of cold and fed it -- 80%% of the biosphere ended up queued in a freezer
        # eating each other. A nose cannot tell two thousand carcasses from twenty.
        cap = float(self.cfg.scent["carrion_scent_cap"])
        self.scent.field[2] += (np.minimum(self.meat, cap)
                                * float(self.cfg.scent["carrion_scent"]))

    # ---------------------------------------------------------------- reporting
    def trophic_counts(self) -> tuple[int, int, int]:
        if self.pop == 0:
            return 0, 0, 0
        diet = self.gene("diet", self.alive_idx)
        return (int((diet < 0.33).sum()), int(((diet >= 0.33) & (diet <= 0.66)).sum()),
                int((diet > 0.66).sum()))

    def inspect(self, idx: int) -> dict:
        if idx < 0 or idx >= self.cap or not self.alive[idx]:
            return {}
        genes = {g.name: round(float(self.schema.data[idx, i]), 4)
                 for i, g in enumerate(self.schema.genes) if not g.name.startswith("w0")
                 and not g.name.startswith("w1")}
        return {
            "index": int(idx), "uid": int(self.uid[idx]),
            "species": int(self.species[idx]),
            "x": round(float(self.x[idx]), 2), "y": round(float(self.y[idx]), 2),
            "energy": round(float(self.energy[idx]), 2),
            "body_condition": round(float(self.tissue[idx]), 2),
            "health": round(float(self.health[idx]), 3),
            "age": int(self.age[idx]),
            "birth_tick": int(self.birth_tick[idx]),
            "last_action": ACTION_NAMES[int(self.last_action[idx])],
            "genome": genes,
        }

    def nearest_to(self, x: float, y: float, radius: float = 8.0) -> int:
        if self.pop == 0:
            return -1
        rows = self.alive_idx
        ddx = (self.x[rows] - x + self.G / 2) % self.G - self.G / 2
        ddy = self.y[rows] - y
        dist = ddx * ddx + ddy * ddy
        j = int(np.argmin(dist))
        return int(rows[j]) if dist[j] <= radius * radius else -1

    # ------------------------------------------------------------ runtime genes
    def add_runtime_gene(self, gene: Gene) -> None:
        self.schema.add(gene, self.rng, alive_mask=self.alive)
        self.effects.recompile()
        self.brain = Brain(self.schema)   # brain slice offsets are unchanged (appended)

    # ------------------------------------------------------------- checkpoint
    ARRAYS = ("alive", "x", "y", "energy", "tissue", "health", "age", "matter",
              "species", "last_action", "birth_tick", "parent", "uid", "last_birth")

    def state(self) -> dict:
        d = {f"fauna_{k}": getattr(self, k) for k in self.ARRAYS}
        d["fauna_genes"] = self.schema.data
        d["fauna_meat"] = self.meat
        d["fauna_meat_matter"] = self.meat_matter
        return d

    def meta(self) -> dict:
        return {"schema": self.schema.schema_json(), "next_uid": self._next_uid,
                "cap": self.cap}

    # per-creature scratch that is derived every tick and so is never checkpointed --
    # but it still has to be resized when a restored world has a different capacity
    DERIVED = ("size_eff",)

    def load(self, npz, meta: dict) -> None:
        # The checkpoint is authoritative about capacity.  config's max_pop can differ --
        # the watchdog lowers it under load and that lowered value gets saved -- and a
        # single array left at the config size crashes thousands of ticks later, when a
        # birth first lands past its end.
        self.cap = int(npz["fauna_alive"].shape[0])
        self.schema = GenomeSchema.from_schema_json(meta["schema"], self.cap)
        # Weight decay is a rule of the world, not saved population state.  A checkpoint
        # written before the rule existed carries genes with decay 0, and rebuilding the
        # schema from it silently reinstates the unbounded random walk on every resume.
        brain_decay = float(self.cfg.genetics.get("brain_decay", 0.015))
        for g in self.schema.genes:
            if g.name.startswith("w") and g.name[1:].isdigit():
                g.decay = brain_decay
        self.schema._rebuild_vectors()
        self.schema.data = npz["fauna_genes"]
        self.schema.capacity = int(self.schema.data.shape[0])
        for name in self.DERIVED:
            setattr(self, name, np.zeros(self.cap, np.float32))
        self.brain = Brain(self.schema)
        self.effects = EffectEngine(self.schema)
        self.gi = {n: self.schema.index[n] for n in BODY_NAMES}
        for k in self.ARRAYS:
            setattr(self, k, npz[f"fauna_{k}"])
        self.meat = npz["fauna_meat"]
        self.meat_matter = npz["fauna_meat_matter"]
        self._next_uid = int(meta["next_uid"])
        bad = [k for k in self.ARRAYS if len(getattr(self, k)) != self.cap]
        if bad or self.schema.data.shape[0] != self.cap:
            raise ValueError(f"checkpoint is inconsistent: capacity {self.cap} but "
                             f"{bad or 'the genome matrix'} disagree")
        self._refresh()
