"""Genome schema registry.

Genomes are structure-of-arrays: a single (capacity, n_genes) float32 matrix per
kingdom plus a name->column map, so mutation/crossover are whole-matrix ops.  The
schema can grow at runtime (interventions add genes); new columns are allocated and
initialised from the gene's init distribution for everything currently alive.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field

import numpy as np

# ---------------------------------------------------------------- effect vocab
STATS = (
    "basal_cost", "move_cost", "bite_size", "attack_power", "armor_eff",
    "detectability", "sense_bonus", "mate_appeal", "cold_resist", "heat_resist",
    "toxin_resist", "plant_digest", "meat_digest", "fire_resist", "swim_eff",
    "scent_strength", "fertility_local",
    # flora-side stats (same vocabulary, applied by flora.step)
    "growth_mult", "seed_bonus", "water_efficiency", "toxin_bonus",
)
OPS = ("add", "mul_per_unit")
CONDITION_KEYS = (
    "is_night", "season", "biome", "moisture_gt", "moisture_lt",
    "temp_gt", "temp_lt", "in_water",
)


@dataclass
class Gene:
    name: str
    init_mean: float = 0.5
    init_std: float = 0.15
    mut_std: float = 0.05
    lo: float = 0.0
    hi: float = 1.0
    heritable: bool = True
    # runtime-added genes carry declarative effects; core genes are wired in code
    effects: list = field(default_factory=list)
    added_tick: int = 0

    def to_json(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_json(d: dict) -> "Gene":
        return Gene(**d)


def validate_effect(eff: dict) -> dict:
    """Whitelist-validate one declarative effect.  Raises ValueError on anything odd."""
    if not isinstance(eff, dict):
        raise ValueError("effect must be an object")
    stat = eff.get("stat")
    if stat not in STATS:
        raise ValueError(f"unknown stat '{stat}' (allowed: {', '.join(STATS)})")
    op = eff.get("op", "add")
    if op not in OPS:
        raise ValueError(f"unknown op '{op}'")
    try:
        per_unit = float(eff.get("per_unit", 0.0))
    except (TypeError, ValueError):
        raise ValueError("per_unit must be a number")
    when = eff.get("when") or {}
    if not isinstance(when, dict):
        raise ValueError("when must be an object")
    clean_when = {}
    for k, v in when.items():
        if k not in CONDITION_KEYS:
            raise ValueError(f"unknown condition '{k}'")
        if k in ("is_night", "in_water"):
            clean_when[k] = bool(v)
        elif k == "season":
            if str(v) not in ("spring", "summer", "autumn", "winter"):
                raise ValueError(f"bad season '{v}'")
            clean_when[k] = str(v)
        elif k == "biome":
            if str(v) not in ("ocean", "coast", "plains", "hills", "mountain"):
                raise ValueError(f"bad biome '{v}'")
            clean_when[k] = str(v)
        else:
            clean_when[k] = float(v)
    return {"stat": stat, "op": op, "per_unit": per_unit, "when": clean_when}


class GenomeSchema:
    """Ordered gene registry backed by a growable SoA matrix."""

    def __init__(self, kingdom: str, capacity: int):
        self.kingdom = kingdom
        self.capacity = int(capacity)
        self.genes: list[Gene] = []
        self.index: dict[str, int] = {}
        self.data = np.zeros((self.capacity, 0), np.float32)
        self._mut_std = np.zeros(0, np.float32)
        self._lo = np.zeros(0, np.float32)
        self._hi = np.zeros(0, np.float32)
        self._heritable = np.zeros(0, bool)

    # ------------------------------------------------------------- structure
    def add(self, gene: Gene, rng: np.random.Generator | None = None,
            alive_mask: np.ndarray | None = None) -> int:
        if gene.name in self.index:
            return self.index[gene.name]
        col = np.zeros((self.capacity, 1), np.float32)
        if rng is not None:
            vals = rng.normal(gene.init_mean, gene.init_std, self.capacity)
            col[:, 0] = np.clip(vals, gene.lo, gene.hi).astype(np.float32)
            if alive_mask is not None:
                col[~alive_mask, 0] = gene.init_mean
        else:
            col[:, 0] = gene.init_mean
        self.data = np.concatenate([self.data, col], axis=1)
        self.index[gene.name] = len(self.genes)
        self.genes.append(gene)
        self._rebuild_vectors()
        return self.index[gene.name]

    def _rebuild_vectors(self) -> None:
        self._mut_std = np.array([g.mut_std for g in self.genes], np.float32)
        self._lo = np.array([g.lo for g in self.genes], np.float32)
        self._hi = np.array([g.hi for g in self.genes], np.float32)
        self._heritable = np.array([g.heritable for g in self.genes], bool)

    @property
    def n(self) -> int:
        return len(self.genes)

    def col(self, name: str) -> np.ndarray:
        """Live view of one gene column (length = capacity)."""
        return self.data[:, self.index[name]]

    def has(self, name: str) -> bool:
        return name in self.index

    def runtime_genes(self) -> list[Gene]:
        return [g for g in self.genes if g.effects]

    def grow(self, new_capacity: int) -> None:
        if new_capacity <= self.capacity:
            return
        pad = np.zeros((new_capacity - self.capacity, self.n), np.float32)
        self.data = np.concatenate([self.data, pad], axis=0)
        self.capacity = new_capacity

    # ------------------------------------------------------------- genetics
    def init_rows(self, idx: np.ndarray, rng: np.random.Generator) -> None:
        if len(idx) == 0:
            return
        means = np.array([g.init_mean for g in self.genes], np.float32)
        stds = np.array([g.init_std for g in self.genes], np.float32)
        vals = rng.normal(means, stds, size=(len(idx), self.n)).astype(np.float32)
        self.data[idx] = np.clip(vals, self._lo, self._hi)

    def mutate_rows(self, idx: np.ndarray, rng: np.random.Generator,
                    rate: float, macro_prob: float, macro_scale: float) -> None:
        if len(idx) == 0:
            return
        n = self.n
        sigma = self._mut_std * float(rate)
        noise = rng.normal(0.0, 1.0, size=(len(idx), n)).astype(np.float32) * sigma
        # macro mutation: one random gene per selected child gets a big jump
        macro_hit = rng.random(len(idx)) < macro_prob
        if macro_hit.any():
            rows = np.nonzero(macro_hit)[0]
            cols = rng.integers(0, n, size=len(rows))
            noise[rows, cols] *= float(macro_scale)
        noise[:, ~self._heritable] = 0.0
        self.data[idx] = np.clip(self.data[idx] + noise, self._lo, self._hi)

    def inherit(self, child_idx: np.ndarray, parent_idx: np.ndarray,
                mate_idx: np.ndarray | None, rng: np.random.Generator) -> None:
        if len(child_idx) == 0:
            return
        self.data[child_idx] = self.data[parent_idx]
        if mate_idx is not None and len(mate_idx):
            mask = rng.random((len(child_idx), self.n)) < 0.5
            other = self.data[mate_idx]
            self.data[child_idx] = np.where(mask, other, self.data[child_idx])

    # ------------------------------------------------------------ checkpoint
    def schema_json(self) -> dict:
        return {"kingdom": self.kingdom, "genes": [g.to_json() for g in self.genes]}

    @staticmethod
    def from_schema_json(d: dict, capacity: int) -> "GenomeSchema":
        s = GenomeSchema(d["kingdom"], capacity)
        for gd in d["genes"]:
            s.add(Gene.from_json(gd))
        return s


# ------------------------------------------------------------------ effects
BIOME_CODE = {"ocean": 0, "coast": 1, "plains": 2, "hills": 3, "mountain": 4}


class EffectEngine:
    """Applies runtime-added genes' declarative effects to per-creature stats.

    Never executes anything from JSON: effects are (stat, op, per_unit, when) tuples
    resolved with vectorized numpy against a context dict of world samples.
    """

    def __init__(self, schema: GenomeSchema):
        self.schema = schema
        self._compiled: list[tuple[int, str, str, float, dict]] = []
        self.recompile()

    def recompile(self) -> None:
        out = []
        for gi, g in enumerate(self.schema.genes):
            for eff in g.effects:
                out.append((gi, eff["stat"], eff["op"], float(eff["per_unit"]),
                            eff.get("when") or {}))
        self._compiled = out
        self.active_stats = {e[1] for e in out}

    def any_effects(self) -> bool:
        return bool(self._compiled)

    def _mask(self, when: dict, ctx: dict, n: int) -> np.ndarray | None:
        """Returns a bool mask of length n, or None for 'always'."""
        if not when:
            return None
        m = np.ones(n, bool)
        if "is_night" in when:
            m &= (bool(ctx["is_night"]) == bool(when["is_night"]))
        if "season" in when:
            m &= (ctx["season"] == when["season"])
        if "in_water" in when:
            m &= (ctx["in_water"] == bool(when["in_water"]))
        if "biome" in when:
            m &= (ctx["biome"] == BIOME_CODE[when["biome"]])
        if "moisture_gt" in when:
            m &= ctx["moisture"] > when["moisture_gt"]
        if "moisture_lt" in when:
            m &= ctx["moisture"] < when["moisture_lt"]
        if "temp_gt" in when:
            m &= ctx["temp"] > when["temp_gt"]
        if "temp_lt" in when:
            m &= ctx["temp"] < when["temp_lt"]
        return m

    def apply(self, stats: dict[str, np.ndarray], rows: np.ndarray, ctx: dict) -> None:
        """Mutates `stats` in place.  `rows` indexes living creatures."""
        if not self._compiled:
            return
        n = len(rows)
        if n == 0:
            return
        data = self.schema.data
        for gi, stat, op, per_unit, when in self._compiled:
            if stat not in stats:
                continue
            vals = data[rows, gi]
            mask = self._mask(when, ctx, n)
            delta = vals * per_unit
            if mask is not None:
                delta = delta * mask
            if op == "add":
                stats[stat] = stats[stat] + delta
            else:  # mul_per_unit -> multiply by (1 + per_unit * gene)
                stats[stat] = stats[stat] * (1.0 + delta)


class GridGenome:
    """Per-cell genome for flora/decomposers.

    Layout is (n_genes, H, W) so each gene plane is contiguous and usable directly in
    grid math with zero copies.  Same growable-schema contract as GenomeSchema.
    """

    def __init__(self, kingdom: str, shape: tuple[int, int]):
        self.kingdom = kingdom
        self.shape = shape
        self.genes: list[Gene] = []
        self.index: dict[str, int] = {}
        self.data = np.zeros((0, *shape), np.float32)

    @property
    def n(self) -> int:
        return len(self.genes)

    def has(self, name: str) -> bool:
        return name in self.index

    def plane(self, name: str) -> np.ndarray:
        return self.data[self.index[name]]

    def runtime_genes(self) -> list[Gene]:
        return [g for g in self.genes if g.effects]

    def add(self, gene: Gene, rng: np.random.Generator | None = None) -> int:
        if gene.name in self.index:
            return self.index[gene.name]
        if rng is not None:
            p = np.clip(rng.normal(gene.init_mean, gene.init_std, self.shape),
                        gene.lo, gene.hi).astype(np.float32)
        else:
            p = np.full(self.shape, gene.init_mean, np.float32)
        self.data = np.concatenate([self.data, p[None]], axis=0)
        self.index[gene.name] = len(self.genes)
        self.genes.append(gene)
        self._rebuild()
        return self.index[gene.name]

    def _rebuild(self) -> None:
        self._mut_std = np.array([g.mut_std for g in self.genes], np.float32)[:, None]
        self._lo = np.array([g.lo for g in self.genes], np.float32)[:, None]
        self._hi = np.array([g.hi for g in self.genes], np.float32)[:, None]

    def randomize_cells(self, ys: np.ndarray, xs: np.ndarray,
                        rng: np.random.Generator) -> None:
        if len(ys) == 0:
            return
        means = np.array([g.init_mean for g in self.genes], np.float32)[:, None]
        stds = np.array([g.init_std for g in self.genes], np.float32)[:, None]
        vals = rng.normal(means, stds, size=(self.n, len(ys))).astype(np.float32)
        self.data[:, ys, xs] = np.clip(vals, self._lo, self._hi)

    def spawn_children(self, sy, sx, ty, tx, rng: np.random.Generator,
                       rate: float, macro_prob: float, macro_scale: float) -> None:
        """Copy parent cell genomes to target cells and mutate, fully vectorized."""
        k = len(ty)
        if k == 0:
            return
        vals = self.data[:, sy, sx]                       # (n, k)
        noise = rng.normal(0.0, 1.0, size=(self.n, k)).astype(np.float32)
        noise *= self._mut_std * float(rate)
        hit = rng.random(k) < macro_prob
        if hit.any():
            cols = np.nonzero(hit)[0]
            rows = rng.integers(0, self.n, size=len(cols))
            noise[rows, cols] *= float(macro_scale)
        self.data[:, ty, tx] = np.clip(vals + noise, self._lo, self._hi)

    def schema_json(self) -> dict:
        return {"kingdom": self.kingdom, "genes": [g.to_json() for g in self.genes]}
