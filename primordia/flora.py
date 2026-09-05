"""Evolving plants (one per cell) and the decomposer microbe layer."""
from __future__ import annotations

import numpy as np

from . import fields
from .genetics import Gene, GridGenome

FLORA_GENES = [
    Gene("growth_rate",   0.55, 0.18, 0.055, 0.05, 1.5),
    Gene("water_need",    0.50, 0.22, 0.055, 0.02, 1.2),
    Gene("temp_optimum",  0.55, 0.20, 0.050, 0.00, 1.2),
    Gene("temp_tolerance", 0.30, 0.10, 0.035, 0.06, 0.9),
    Gene("root_depth",    0.35, 0.18, 0.050, 0.00, 1.0),
    Gene("seed_range",    0.30, 0.15, 0.050, 0.02, 1.0),
    Gene("seed_count",    0.35, 0.15, 0.050, 0.05, 1.0),
    Gene("structure",     0.30, 0.25, 0.060, 0.00, 1.0),
    Gene("toxin",         0.12, 0.10, 0.055, 0.00, 1.0),
    Gene("fire_resist",   0.20, 0.15, 0.050, 0.00, 1.0),
    Gene("cold_dormancy", 0.35, 0.20, 0.050, 0.00, 1.0),
    Gene("lifespan",      0.45, 0.20, 0.050, 0.05, 1.0),
]
MAX_LIFE_TICKS = 5200.0
MAX_SEED_RANGE = 9.0


class Flora:
    def __init__(self, cfg, world, rng: np.random.Generator):
        self.cfg = cfg
        self.world = world
        self.rng = rng
        G = world.G
        self.G = G
        self.biomass = np.zeros((G, G), np.float32)
        self.age = np.zeros((G, G), np.float32)
        self.genome = GridGenome("flora", (G, G))
        for g in FLORA_GENES:
            self.genome.add(g, rng)
        self.burn = np.zeros((G, G), np.float32)   # active fire intensity per cell
        self.stat_cache: dict[str, np.ndarray] = {}

    # ---------------------------------------------------------------- seeding
    def seed_initial(self) -> None:
        land = self.world.is_land & (self.world.water_depth < 0.05)
        roll = self.rng.random((self.G, self.G)) < float(self.cfg.flora["seed_density"])
        ys, xs = np.nonzero(land & roll)
        self.genome.randomize_cells(ys, xs, self.rng)
        self.biomass[ys, xs] = 0.15
        self.age[ys, xs] = 0.0

    # ------------------------------------------------------------ runtime genes
    def add_runtime_gene(self, gene: Gene) -> None:
        self.genome.add(gene, self.rng)
        self.recompute_effects()

    def recompute_effects(self) -> None:
        """Precompute grid-wide multiplier planes for runtime flora genes."""
        self.stat_cache = {}
        for gi, g in enumerate(self.genome.genes):
            for eff in g.effects:
                self.stat_cache.setdefault(eff["stat"], []).append((gi, eff))

    def _stat_plane(self, stat: str, base, ctx: dict):
        entries = self.stat_cache.get(stat)
        if not entries:
            return base
        out = base
        for gi, eff in entries:
            vals = self.genome.data[gi]
            mask = self._cond_mask(eff.get("when") or {}, ctx)
            d = vals * float(eff["per_unit"])
            if mask is not None:
                d = d * mask
            if eff["op"] == "add":
                out = out + d
            else:
                out = out * (1.0 + d)
        return out

    def _cond_mask(self, when: dict, ctx: dict):
        if not when:
            return None
        from .genetics import BIOME_CODE
        m = np.ones((self.G, self.G), np.float32)
        wr = self.world
        if "is_night" in when and bool(ctx["is_night"]) != bool(when["is_night"]):
            return np.zeros((self.G, self.G), np.float32)
        if "season" in when and ctx["season"] != when["season"]:
            return np.zeros((self.G, self.G), np.float32)
        if "biome" in when:
            m = m * (wr.biome == BIOME_CODE[when["biome"]])
        if "in_water" in when:
            m = m * ((wr.water_depth > 0.05) == bool(when["in_water"]))
        if "moisture_gt" in when:
            m = m * (wr.moisture > when["moisture_gt"])
        if "moisture_lt" in when:
            m = m * (wr.moisture < when["moisture_lt"])
        if "temp_gt" in when:
            m = m * (wr.temperature > when["temp_gt"])
        if "temp_lt" in when:
            m = m * (wr.temperature < when["temp_lt"])
        return m.astype(np.float32)

    # ------------------------------------------------------------------ step
    def step(self, tick: int, sunlight: float, ctx: dict) -> dict:
        cfg = self.cfg.flora
        wr = self.world
        gm = self.genome
        alive = self.biomass > 1e-4

        growth_rate = gm.plane("growth_rate")
        water_need = gm.plane("water_need")
        t_opt = gm.plane("temp_optimum")
        t_tol = gm.plane("temp_tolerance")
        root = gm.plane("root_depth")
        structure = gm.plane("structure")
        dormancy = gm.plane("cold_dormancy")
        lifespan = gm.plane("lifespan")

        if self.stat_cache:
            growth_rate = self._stat_plane("growth_mult", growth_rate, ctx)
            water_need = self._stat_plane("water_efficiency", water_need, ctx)

        # water score: moisture vs need, buffered by roots
        eff_moist = wr.moisture + root * 0.45
        wdiff = eff_moist - water_need
        water_score = np.exp(-np.square(np.minimum(wdiff, 0.0)) * 7.0)
        water_score *= np.exp(-np.square(np.maximum(wdiff - 0.55, 0.0)) * 3.0)

        tdiff = wr.temperature - t_opt
        temp_score = np.exp(-np.square(tdiff) / (2.0 * np.square(t_tol) + 1e-4))

        # cold dormancy: below the dormancy temperature growth halts but so does death
        cold = wr.temperature < float(cfg["dormancy_temp"])
        dorm = np.where(cold, 1.0 - dormancy, 1.0).astype(np.float32)

        fert = wr.soil_fertility
        fert_avail = np.clip(fert / float(cfg["fert_half"]), 0.0, 1.0)

        gain = (float(cfg["growth_scale"]) * growth_rate * max(sunlight, 0.06)
                * fert_avail * water_score * temp_score * dorm)
        gain *= alive
        # trees grow slower but hold more biomass
        cap = float(cfg["max_biomass"]) * (0.35 + 0.9 * structure)
        gain *= np.clip(1.0 - self.biomass / np.maximum(cap, 0.2), 0.0, 1.0)
        gain[wr.water_depth > 0.35] *= 0.15
        gain = np.maximum(gain, 0.0)

        want = gain * float(cfg["fertility_cost"])
        cost = np.minimum(want, fert)
        scale = np.where(want > 1e-9, cost / np.maximum(want, 1e-9), 0.0)
        actual = (gain * scale).astype(np.float32)
        wr.soil_fertility -= cost
        self.biomass += actual

        # stress attrition when conditions are bad -- lost biomass returns to the
        # nutrient pool (the cycle must stay closed; nothing evaporates)
        stress = (0.004 + 0.02 * (1.0 - water_score * temp_score)) * alive * dorm
        lost = (self.biomass * stress).astype(np.float32)
        self.biomass -= lost
        wr.nutrients += lost * self.matter_per_biomass

        self.age += alive

        # --- death by age -------------------------------------------------
        max_age = 400.0 + lifespan * MAX_LIFE_TICKS
        dead = alive & ((self.age > max_age) | (self.biomass < 5e-3))
        n_dead = int(dead.sum())
        if n_dead:
            wr.nutrients += (self.biomass * dead * self.matter_per_biomass).astype(np.float32)
            self.biomass[dead] = 0.0
            self.age[dead] = 0.0

        # --- reproduction --------------------------------------------------
        # seeding is scattered, not continuous: run it every Nth tick with an N-scaled
        # probability for the same expected seed rain at a fraction of the cost
        sub = max(1, int(cfg.get("seed_substep", 3)))
        n_seeds = self._reproduce(tick, sub) if tick % sub == 0 else 0

        np.clip(self.biomass, 0.0, float(cfg["max_biomass"]) * 1.4, out=self.biomass)
        return {"deaths": n_dead, "seeds": n_seeds}

    def _reproduce(self, tick: int, sub: int = 1) -> int:
        cfg = self.cfg.flora
        gm = self.genome
        mature = self.biomass > float(cfg["maturity_biomass"])
        if not mature.any():
            return 0
        seed_p = float(cfg["seed_prob"]) * sub * (0.4 + 1.6 * gm.plane("seed_count"))
        if self.stat_cache.get("seed_bonus"):
            seed_p = self._stat_plane("seed_bonus", seed_p, {})
        roll = self.rng.random((self.G, self.G)) < seed_p
        sy, sx = np.nonzero(mature & roll)
        if len(sy) == 0:
            return 0
        # cap seeding work per tick so a saturated world can't stall the loop
        limit = 20000
        if len(sy) > limit:
            pick = self.rng.choice(len(sy), limit, replace=False)
            sy, sx = sy[pick], sx[pick]

        rng_plane = gm.data[gm.index["seed_range"]]
        rad = 1.0 + rng_plane[sy, sx] * MAX_SEED_RANGE
        ang = self.rng.random(len(sy)) * 2 * np.pi
        dist = 1.0 + self.rng.random(len(sy)) * rad
        ty = np.clip((sy + np.round(np.sin(ang) * dist)).astype(np.int32), 0, self.G - 1)
        tx = ((sx + np.round(np.cos(ang) * dist)).astype(np.int32)) % self.G

        wr = self.world
        ok = (wr.biome != 0) & (wr.water_depth < 0.3)
        valid = ok[ty, tx]
        # competition: land on empty, or beat the occupant by the competition edge
        occ = self.biomass[ty, tx]
        src = self.biomass[sy, sx]
        valid &= (occ < 1e-3) | (occ * float(cfg["competition_edge"]) < src)
        valid &= self.rng.random(len(sy)) < float(cfg["germination_chance"])
        if not valid.any():
            return 0
        sy, sx, ty, tx = sy[valid], sx[valid], ty[valid], tx[valid]
        # One seed per target cell.  Two seeds landing on the same occupied cell used to
        # return the displaced plant's matter twice -- np.add.at accumulates duplicates,
        # while the assignment below writes the seedling once -- so every collision minted
        # a plant's worth of matter out of nothing.
        if len(ty) > 1:
            flat = ty.astype(np.int64) * self.G + tx
            keep = np.unique(flat, return_index=True)[1]
            if len(keep) < len(ty):
                keep.sort()
                sy, sx, ty, tx = sy[keep], sx[keep], ty[keep], tx[keep]
        # returning nutrients from the displaced plant
        disp = self.biomass[ty, tx]
        wr.nutrients[ty, tx] += disp * self.matter_per_biomass

        g = self.cfg.genetics
        gm.spawn_children(sy, sx, ty, tx, self.rng,
                          float(g["mutation_rate_global"]),
                          float(g["macro_mutation_prob"]),
                          float(g["macro_mutation_scale"]))
        # A seedling's matter comes out of the soil, so the cycle stays closed -- and it
        # masses exactly what the soil could pay.  Debiting a flat 0.06 and then clipping
        # the field at zero handed a free seedling to every cell too poor to afford one.
        mpb = self.matter_per_biomass
        have = wr.soil_fertility[ty, tx]
        paid = np.minimum(have, 0.06 * mpb)
        wr.soil_fertility[ty, tx] = have - paid
        self.biomass[ty, tx] = paid / mpb
        self.age[ty, tx] = 0.0
        return int(len(ty))

    # ------------------------------------------------------------------ misc
    @property
    def matter_per_biomass(self) -> float:
        """Soil-matter locked up per unit biomass -- keeps the nutrient loop exactly closed."""
        return float(self.cfg.flora["fertility_cost"]) * float(self.cfg.flora["biomass_to_nutrient"])

    def energy_density(self) -> np.ndarray:
        c = self.cfg.flora
        s = self.genome.plane("structure")
        return (float(c["energy_density_grass"]) * (1 - s)
                + float(c["energy_density_tree"]) * s).astype(np.float32)

    def kill(self, mask: np.ndarray, to_nutrient: float = 1.0) -> int:
        n = int((mask & (self.biomass > 1e-4)).sum())
        if n:
            self.world.nutrients += (self.biomass * mask * to_nutrient
                                     * self.matter_per_biomass).astype(np.float32)
            self.biomass[mask] = 0.0
            self.age[mask] = 0.0
        return n

    # ------------------------------------------------------------- checkpoint
    def state(self) -> dict:
        return {"flora_biomass": self.biomass, "flora_age": self.age,
                "flora_genes": self.genome.data, "flora_burn": self.burn}

    def meta(self) -> dict:
        return {"schema": self.genome.schema_json()}

    def load(self, npz, meta: dict) -> None:
        from .genetics import Gene as _G
        self.genome = GridGenome("flora", (self.G, self.G))
        for gd in meta["schema"]["genes"]:
            self.genome.add(_G.from_json(gd))
        self.genome.data = npz["flora_genes"]
        self.biomass = npz["flora_biomass"]
        self.age = npz["flora_age"]
        self.burn = npz["flora_burn"]
        self.recompute_effects()


class Decomposers:
    """Microbe density field with a two-gene per-cell mini genome."""

    def __init__(self, cfg, world, rng: np.random.Generator):
        self.cfg = cfg
        self.world = world
        self.rng = rng
        G = world.G
        self.G = G
        self.density = np.zeros((G, G), np.float32)
        self.efficiency = np.clip(rng.normal(0.5, 0.15, (G, G)), 0.05, 1.0).astype(np.float32)
        self.temp_optimum = np.clip(rng.normal(0.55, 0.15, (G, G)), 0.0, 1.2).astype(np.float32)
        land = world.is_land
        self.density[land] = 0.08

    def step(self, tick: int = 0) -> None:
        c = self.cfg.decomposer
        # The microbe layer is the slowest-moving field in the world; stepping it every
        # Nth tick with N-scaled rates is the same diffusion for a fraction of the cost.
        sub = max(1, int(c.get("substep", 2)))
        if tick % sub:
            return
        wr = self.world
        food = np.clip(wr.nutrients / 0.6, 0.0, 1.0)
        tfit = np.exp(-np.square(wr.temperature - self.temp_optimum) / 0.09)
        grow = float(c["growth_rate"]) * sub * food * tfit * self.efficiency
        self.density += grow - float(c["death_rate"]) * sub * self.density
        # spread with mutation of the mini-genome: diffusion carries the trait planes
        d = min(0.24, float(c["diffuse"]) * sub)
        prev = self.density.copy()
        self.density = fields.diffuse(self.density, d)
        np.clip(self.density, 0.0, float(c["max_density"]), out=self.density)
        # trait planes follow the density flow, mutating slightly where they spread
        w = np.clip(prev / (self.density + 1e-5), 0.0, 1.0)
        eff_s = fields.diffuse(self.efficiency * prev, d) / (self.density + 1e-5)
        top_s = fields.diffuse(self.temp_optimum * prev, d) / (self.density + 1e-5)
        active = self.density > 1e-3
        ms = float(c["mut_std"])
        self.efficiency = np.where(
            active, np.clip(eff_s + self.rng.normal(0, ms, (self.G, self.G)), 0.05, 1.0),
            self.efficiency).astype(np.float32)
        self.temp_optimum = np.where(
            active, np.clip(top_s + self.rng.normal(0, ms, (self.G, self.G)), 0.0, 1.2),
            self.temp_optimum).astype(np.float32)
        wr.nutrient_step(self.density * self.efficiency
                         * (float(c["convert_rate"]) * sub / 0.055))

    def state(self) -> dict:
        return {"dec_density": self.density, "dec_eff": self.efficiency,
                "dec_topt": self.temp_optimum}

    def load(self, npz, meta: dict) -> None:
        self.density = npz["dec_density"]
        self.efficiency = npz["dec_eff"]
        self.temp_optimum = npz["dec_topt"]
