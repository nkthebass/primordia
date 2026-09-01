"""Grid state container, terrain generation, nutrient cycle."""
from __future__ import annotations

import numpy as np

from . import fields

# biome codes
OCEAN, COAST, PLAINS, HILLS, MOUNTAIN = 0, 1, 2, 3, 4
BIOME_NAMES = ["ocean", "coast", "plains", "hills", "mountain"]


def _value_noise(rng: np.random.Generator, size: int, freq: int) -> np.ndarray:
    """Periodic bilinear value noise at `freq` cells across the grid."""
    freq = max(2, int(freq))
    lattice = rng.random((freq, freq)).astype(np.float32)
    # tile-wrap lattice for periodicity
    lat = np.pad(lattice, ((0, 1), (0, 1)), mode="wrap")
    coords = np.linspace(0, freq, size, endpoint=False, dtype=np.float32)
    i0 = np.floor(coords).astype(np.int32)
    t = coords - i0
    # smoothstep
    t = t * t * (3.0 - 2.0 * t)
    y0 = i0[:, None]; y1 = (i0 + 1)[:, None]
    x0 = i0[None, :]; x1 = (i0 + 1)[None, :]
    ty = t[:, None]; tx = t[None, :]
    a = lat[y0, x0] * (1 - tx) + lat[y0, x1] * tx
    b = lat[y1, x0] * (1 - tx) + lat[y1, x1] * tx
    return (a * (1 - ty) + b * ty).astype(np.float32)


def fbm(rng: np.random.Generator, size: int, octaves: int, base_freq: float,
        persistence: float, lacunarity: float) -> np.ndarray:
    total = np.zeros((size, size), dtype=np.float32)
    amp, freq, norm = 1.0, float(base_freq), 0.0
    for _ in range(octaves):
        total += amp * _value_noise(rng, size, int(round(freq)))
        norm += amp
        amp *= persistence
        freq *= lacunarity
    total /= max(norm, 1e-6)
    return total


class World:
    """All per-cell grid state.  Shape (G, G), float32, row 0 = north pole."""

    def __init__(self, cfg, rng: np.random.Generator):
        self.cfg = cfg
        w = cfg.world
        self.G = int(w["size"])
        G = self.G
        self.rng = rng

        self.elevation = np.zeros((G, G), np.float32)
        self.water_depth = np.zeros((G, G), np.float32)
        self.soil_fertility = np.zeros((G, G), np.float32)
        self.moisture = np.zeros((G, G), np.float32)
        self.temperature = np.zeros((G, G), np.float32)
        self.nutrients = np.zeros((G, G), np.float32)
        self.biome = np.zeros((G, G), np.uint8)
        self.base_temp_map = np.zeros((G, G), np.float32)
        self.hotspots: list[tuple[int, int]] = []

        self.generate()

    # ---------------------------------------------------------------- terrain
    def generate(self) -> None:
        w = self.cfg.world
        G = self.G
        e = fbm(self.rng, G, int(w["noise_octaves"]), float(w["noise_base_freq"]),
                float(w["noise_persistence"]), float(w["noise_lacunarity"]))
        # continental mask: pull elevation down near the north/south edges so the
        # world reads as land masses in an ocean rather than noise everywhere.
        yy = np.linspace(-1.0, 1.0, G, dtype=np.float32)[:, None]
        edge = 1.0 - np.clip((np.abs(yy) - 0.62) / 0.38, 0.0, 1.0) ** 1.5
        big = fbm(self.rng, G, 2, 2.0, 0.5, 2.0)
        e = 0.62 * e + 0.38 * big
        e = e * (0.45 + 0.55 * edge)
        e = (e - e.min()) / max(1e-6, float(e.max() - e.min()))
        # fBm is bell-shaped, so a fixed sea level gives an unpredictable land fraction.
        # Remap so a chosen quantile lands exactly on sea_level: the world always reads
        # as continents in an ocean instead of noise with puddles.
        sea = float(w["sea_level"])
        q = float(np.quantile(e, float(w["ocean_fraction"])))
        lo = e < q
        e = np.where(lo, sea * (e / max(q, 1e-6)),
                     sea + (1.0 - sea) * (e - q) / max(1e-6, 1.0 - q))
        self.elevation = np.clip(e, 0.0, 1.0).astype(np.float32)

        self.water_depth = np.maximum(0.0, sea - self.elevation).astype(np.float32)

        self.classify()

        # fertility: noise blended with a lowland bonus, zero in deep ocean
        f = fbm(self.rng, G, 4, 5.0, 0.55, 2.0)
        low = np.clip((0.85 - self.elevation) / 0.6, 0.0, 1.0)
        fert = 0.55 * f + float(w["fertility_lowland_bonus"]) * low
        fert = np.clip(fert, 0.0, float(w["fertility_cap"])).astype(np.float32)
        fert[self.biome == OCEAN] = 0.02
        self.soil_fertility = fert

        self.moisture = np.clip(0.35 + 0.3 * fbm(self.rng, G, 3, 4.0, 0.5, 2.0),
                                0.0, 1.0).astype(np.float32)
        self.moisture[self.biome == OCEAN] = 1.0

        self._build_base_temp()
        self.temperature = self.base_temp_map.copy()

        # volcanic hotspots on high ground
        land = np.argwhere(self.elevation > float(w["hills_level"]))
        if len(land):
            pick = self.rng.choice(len(land), size=min(5, len(land)), replace=False)
            self.hotspots = [(int(land[i][0]), int(land[i][1])) for i in pick]

    def classify(self) -> None:
        w = self.cfg.world
        sea = float(w["sea_level"])
        e = self.elevation
        b = np.full(e.shape, PLAINS, np.uint8)
        b[e >= float(w["hills_level"])] = HILLS
        b[e >= float(w["mountain_level"])] = MOUNTAIN
        b[e < sea + float(w["coast_band"])] = COAST
        b[e < sea] = OCEAN
        self.biome = b

    def _build_base_temp(self) -> None:
        w = self.cfg.world
        G = self.G
        yy = np.linspace(-1.0, 1.0, G, dtype=np.float32)[:, None]
        lat = 1.0 - np.abs(yy)                       # 1 at equator, 0 at poles
        t = float(w["base_temp"]) + float(w["lat_temp_amp"]) * (lat - 0.5)
        t = np.broadcast_to(t, (G, G)).astype(np.float32)
        self.base_temp_map = (t - float(w["lapse_rate"]) * np.maximum(
            0.0, self.elevation - 0.5)).astype(np.float32)

    @property
    def is_land(self) -> np.ndarray:
        return self.biome != OCEAN

    @property
    def is_water(self) -> np.ndarray:
        return (self.biome == OCEAN) | (self.water_depth > 0.02)

    # ------------------------------------------------------------- nutrients
    def add_nutrients(self, ys: np.ndarray, xs: np.ndarray, amounts) -> None:
        if len(ys) == 0:
            return
        np.add.at(self.nutrients, (ys, xs), amounts)

    def nutrient_step(self, microbe_density: np.ndarray | None) -> None:
        w = self.cfg.world
        rate = float(w["decomp_rate"])
        if microbe_density is not None:
            eff = rate * (0.35 + 1.65 * np.clip(microbe_density, 0.0, 1.5))
        else:
            eff = rate
        moved = np.minimum(self.nutrients, self.nutrients * eff)
        # whatever will not fit under the fertility cap stays in the nutrient pool --
        # clipping it away silently drains the closed system of matter
        room = np.maximum(0.0, float(w["fertility_cap"]) - self.soil_fertility)
        moved = np.minimum(moved, room)
        self.nutrients -= moved
        self.soil_fertility += moved
        np.clip(self.nutrients, 0.0, float(w["nutrient_cap"]), out=self.nutrients)

    def erode(self) -> None:
        w = self.cfg.world
        self.elevation = fields.blur(self.elevation, float(w["erosion_rate"]))
        self.classify()
        self._build_base_temp()

    # ------------------------------------------------------------ checkpoint
    ARRAYS = ("elevation", "water_depth", "soil_fertility", "moisture",
              "temperature", "nutrients", "biome", "base_temp_map")

    def state(self) -> dict:
        d = {f"world_{k}": getattr(self, k) for k in self.ARRAYS}
        return d

    def meta(self) -> dict:
        return {"G": self.G, "hotspots": self.hotspots}

    def load(self, npz, meta: dict) -> None:
        for k in self.ARRAYS:
            setattr(self, k, npz[f"world_{k}"])
        self.G = int(meta["G"])
        self.hotspots = [tuple(h) for h in meta.get("hotspots", [])]
