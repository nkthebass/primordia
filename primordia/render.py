"""Server-side frame composition: world state -> RGB -> PNG bytes."""
from __future__ import annotations

import io

import numpy as np
from PIL import Image

OVERLAYS = ("none", "rain", "temperature", "moisture", "fertility", "nutrients",
            "scent", "species", "elevation", "decomposer")


def hsv_to_rgb(h, s, v):
    """Vectorized HSV->RGB.  h,s,v are arrays in [0,1].  Returns (..., 3) float."""
    h = np.mod(h, 1.0) * 6.0
    i = np.floor(h).astype(np.int32)
    f = h - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    i = i % 6
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [v, q, p, p, t, v])
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [t, v, v, q, p, p])
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1)


def _ramp(x, stops):
    """Piecewise-linear colour ramp.  stops = [(pos, (r,g,b)), ...] in 0..1."""
    x = np.clip(x, 0.0, 1.0)
    out = np.zeros(x.shape + (3,), np.float32)
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        m = (x >= p0) & (x <= p1)
        if not m.any():
            continue
        t = ((x[m] - p0) / max(1e-6, p1 - p0))[:, None]
        out[m] = np.array(c0, np.float32) * (1 - t) + np.array(c1, np.float32) * t
    return out


TEMP_RAMP = [(0.0, (0.20, 0.35, 0.85)), (0.35, (0.25, 0.75, 0.85)),
             (0.5, (0.35, 0.85, 0.4)), (0.7, (0.95, 0.8, 0.25)),
             (1.0, (0.9, 0.2, 0.15))]
WET_RAMP = [(0.0, (0.55, 0.42, 0.24)), (0.4, (0.45, 0.55, 0.35)),
            (1.0, (0.15, 0.55, 0.95))]
FERT_RAMP = [(0.0, (0.25, 0.18, 0.12)), (0.5, (0.55, 0.42, 0.15)),
             (1.0, (0.35, 0.95, 0.35))]


class Renderer:
    def __init__(self, sim):
        self.sim = sim
        G = sim.world.G
        self.G = G
        self._hill_cache = None
        self._hill_tick = -10**9

    # ------------------------------------------------------------------ base
    def hillshade(self) -> np.ndarray:
        wr = self.sim.world
        if self._hill_cache is not None and self.sim.tick - self._hill_tick < 500:
            return self._hill_cache
        e = wr.elevation
        gx = np.roll(e, -1, axis=1) - np.roll(e, 1, axis=1)
        gy = np.empty_like(e)
        gy[1:-1] = e[2:] - e[:-2]; gy[0] = 0; gy[-1] = 0
        shade = np.clip(0.72 + 2.4 * (gx * 0.7 + gy * 0.7), 0.35, 1.35)
        self._hill_cache = shade.astype(np.float32)
        self._hill_tick = self.sim.tick
        return self._hill_cache

    def terrain_rgb(self) -> np.ndarray:
        wr = self.sim.world
        e = wr.elevation
        sea = float(self.sim.cfg.world["sea_level"])
        rgb = np.zeros((self.G, self.G, 3), np.float32)
        land = wr.biome != 0
        # land base: elevation-graded rock/soil
        t = np.clip((e - sea) / max(1e-3, 1.0 - sea), 0, 1)
        base = _ramp(t, [(0.0, (0.52, 0.47, 0.33)), (0.35, (0.40, 0.42, 0.28)),
                         (0.7, (0.44, 0.40, 0.36)), (1.0, (0.90, 0.92, 0.96))])
        rgb[land] = base[land]
        # ocean: depth-scaled blue
        d = np.clip((sea - e) / max(1e-3, sea), 0, 1)
        ocean = _ramp(d, [(0.0, (0.16, 0.36, 0.55)), (1.0, (0.03, 0.08, 0.24))])
        rgb[~land] = ocean[~land]
        rgb *= self.hillshade()[..., None]
        return rgb

    # ------------------------------------------------------------------ frame
    def compose(self, overlay: str = "none", highlight_species: int = -1,
                scale: int = 1) -> np.ndarray:
        s = self.sim
        wr, fl, fa, wx, ev = s.world, s.flora, s.fauna, s.weather, s.events
        rgb = self.terrain_rgb()

        # --- flora: green intensity by biomass, hue shifted by structure gene
        bm = np.clip(fl.biomass / 1.6, 0.0, 1.0)
        struct = fl.genome.plane("structure")
        veg_h = 0.33 - 0.10 * struct          # grass yellow-green -> tree deep green
        veg_s = 0.55 + 0.35 * struct
        veg_v = 0.28 + 0.55 * bm
        veg = hsv_to_rgb(veg_h, veg_s, veg_v)
        a = (bm ** 0.7)[..., None]
        rgb = rgb * (1 - a) + veg * a

        # --- surface water on land
        wet = np.clip(wr.water_depth * 1.4, 0, 1) * (wr.biome != 0)
        rgb = rgb * (1 - wet[..., None] * 0.75) + \
            np.array([0.12, 0.35, 0.62], np.float32) * (wet[..., None] * 0.75)

        # --- overlays --------------------------------------------------------
        if overlay == "rain":
            v = np.clip(wx.rain * 60.0, 0, 1) * 0.85 + np.clip(wx.cloud / 2.2, 0, 1) * 0.35
            rgb = self._blend(rgb, _ramp(np.clip(v, 0, 1),
                                         [(0.0, (0.1, 0.1, 0.15)), (0.4, (0.3, 0.5, 0.9)),
                                          (1.0, (0.85, 0.95, 1.0))]), np.clip(v, 0, 1) * 0.85)
        elif overlay == "temperature":
            v = np.clip(wr.temperature / 1.1, 0, 1)
            rgb = self._blend(rgb, _ramp(v, TEMP_RAMP), 0.72)
        elif overlay == "moisture":
            v = np.clip(wr.moisture / 1.2, 0, 1)
            rgb = self._blend(rgb, _ramp(v, WET_RAMP), 0.72)
        elif overlay == "fertility":
            v = np.clip(wr.soil_fertility / max(1e-3, float(self.sim.cfg.world["fertility_cap"])), 0, 1)
            rgb = self._blend(rgb, _ramp(v, FERT_RAMP), 0.72)
        elif overlay == "nutrients":
            v = np.clip(wr.nutrients / 1.2, 0, 1)
            rgb = self._blend(rgb, _ramp(v, [(0.0, (0.1, 0.1, 0.1)), (1.0, (0.85, 0.55, 0.85))]), 0.75)
        elif overlay == "decomposer":
            v = np.clip(s.decomposers.density, 0, 1)
            rgb = self._blend(rgb, _ramp(v, [(0.0, (0.1, 0.1, 0.1)), (1.0, (0.95, 0.85, 0.45))]), 0.7)
        elif overlay == "elevation":
            v = np.clip(wr.elevation, 0, 1)
            rgb = self._blend(rgb, _ramp(v, [(0.0, (0.05, 0.05, 0.2)), (0.42, (0.2, 0.5, 0.7)),
                                             (0.5, (0.3, 0.6, 0.25)), (0.8, (0.6, 0.5, 0.3)),
                                             (1.0, (1, 1, 1))]), 0.85)
        elif overlay == "scent":
            sc = s.scent.field
            v = np.stack([np.clip(sc[0] / 3.0, 0, 1), np.clip(sc[1] / 3.0, 0, 1),
                          np.clip(sc[2] / 3.0, 0, 1)], -1)
            rgb = self._blend(rgb, v.astype(np.float32), np.clip(v.max(-1), 0, 1) * 0.9)
        elif overlay == "species":
            terr = self._species_territory()
            rgb = self._blend(rgb, terr[0], terr[1] * 0.8)

        # --- disasters --------------------------------------------------------
        if ev.fire.max() > 0.01:
            f = np.clip(ev.fire, 0, 1)
            fire_col = _ramp(f, [(0.0, (0.5, 0.1, 0.0)), (0.5, (1.0, 0.45, 0.05)),
                                 (1.0, (1.0, 0.95, 0.6))])
            rgb = self._blend(rgb, fire_col, np.clip(f * 1.6, 0, 1))
        if ev.flood.max() > 0.01:
            fl_a = np.clip(ev.flood, 0, 1) * 0.6
            rgb = self._blend(rgb, np.array([0.25, 0.45, 0.8], np.float32), fl_a)
        for e in ev.active:
            if e.kind == "storm":
                m = ev.disc(e.y, e.x, e.radius)
                hatch = ((self._yy_xx_sum() + s.tick) % 7 == 0) & m
                rgb[hatch] = rgb[hatch] * 0.45 + np.array([0.55, 0.6, 0.75], np.float32) * 0.55

        # --- creatures ---------------------------------------------------------
        if fa.pop:
            rows = fa.alive_idx
            cy = np.clip(fa.y[rows].astype(np.int32), 0, self.G - 1)
            cx = np.clip(fa.x[rows].astype(np.int32), 0, self.G - 1)
            hues = s.speciation.hues()
            sid = np.clip(fa.species[rows], 0, len(hues) - 1)
            h = hues[sid]
            diet = fa.gene("diet", rows)
            sizes = fa.gene("size", rows)
            val = np.clip(0.72 + 0.5 * sizes, 0, 1.0)
            sat = np.clip(0.55 + 0.45 * diet, 0, 1)
            col = hsv_to_rgb(h, sat, val)
            if highlight_species >= 0:
                dim = sid != highlight_species
                col[dim] *= 0.28
            layer = np.zeros_like(rgb)
            alpha = np.zeros((self.G, self.G), np.float32)
            np.maximum.at(alpha, (cy, cx), 1.0)
            layer[cy, cx] = col
            # predators get a ring: paint the 4-neighbourhood faintly
            carn = diet > 0.66
            if carn.any():
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ry = np.clip(cy[carn] + dy, 0, self.G - 1)
                    rx = (cx[carn] + dx) % self.G
                    ring_a = alpha[ry, rx]
                    layer[ry, rx] = np.where((ring_a < 0.5)[:, None],
                                             col[carn] * 0.85, layer[ry, rx])
                    np.maximum.at(alpha, (ry, rx), 0.55)
            rgb = rgb * (1 - alpha[..., None]) + layer * alpha[..., None]

        # --- night dimming ------------------------------------------------------
        if overlay == "none":
            dim = 0.40 + 0.60 * min(1.0, wx.sunlight * 1.35 + 0.12)
            rgb = rgb * dim
            if wx.dust > 0.02:
                rgb = rgb * (1 - 0.35 * wx.dust) + \
                    np.array([0.22, 0.18, 0.15], np.float32) * (0.35 * wx.dust)

        out = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
        if scale > 1:
            out = np.repeat(np.repeat(out, scale, 0), scale, 1)
        return out

    def _yy_xx_sum(self):
        if not hasattr(self, "_yxs"):
            yy, xx = np.mgrid[0:self.G, 0:self.G]
            self._yxs = (yy + xx).astype(np.int32)
        return self._yxs

    @staticmethod
    def _blend(base, over, alpha):
        a = alpha if np.ndim(alpha) == 0 else np.asarray(alpha)[..., None]
        return base * (1 - a) + over * a

    def _species_territory(self):
        s = self.sim
        fa = s.fauna
        acc_h = np.zeros((self.G, self.G), np.float32)
        acc_n = np.zeros((self.G, self.G), np.float32)
        if fa.pop:
            rows = fa.alive_idx
            cy = np.clip(fa.y[rows].astype(np.int32), 0, self.G - 1)
            cx = np.clip(fa.x[rows].astype(np.int32), 0, self.G - 1)
            hues = s.speciation.hues()
            h = hues[np.clip(fa.species[rows], 0, len(hues) - 1)]
            np.add.at(acc_h, (cy, cx), h)
            np.add.at(acc_n, (cy, cx), 1.0)
        from . import fields
        acc_h = fields.diffuse(acc_h, 0.22, 6)
        acc_n = fields.diffuse(acc_n, 0.22, 6)
        hue = np.where(acc_n > 1e-4, acc_h / np.maximum(acc_n, 1e-4), 0.0)
        alpha = np.clip(acc_n * 6.0, 0, 1)
        return hsv_to_rgb(hue, np.full_like(hue, 0.75), np.full_like(hue, 0.9)), alpha

    # ------------------------------------------------------------------ output
    def png(self, overlay: str = "none", highlight_species: int = -1,
            scale: int = 1) -> bytes:
        arr = self.compose(overlay, highlight_species, scale)
        buf = io.BytesIO()
        Image.fromarray(arr, "RGB").save(buf, format="PNG", compress_level=1)
        return buf.getvalue()

    def snapshot(self, path: str, overlay: str = "none") -> None:
        arr = self.compose(overlay)
        Image.fromarray(arr, "RGB").save(path, format="PNG")
