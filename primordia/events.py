"""Natural disasters -- destructive AND regenerative.  All also triggerable by hand."""
from __future__ import annotations

import numpy as np

from . import fields

EVENT_TYPES = ("storm", "wildfire", "flood", "volcano", "cold_snap", "meteor")


class Event:
    __slots__ = ("kind", "x", "y", "radius", "intensity", "ticks_left", "data", "born")

    def __init__(self, kind, x, y, radius, intensity, ticks_left, born, data=None):
        self.kind = kind
        self.x = int(x); self.y = int(y)
        self.radius = float(radius)
        self.intensity = float(intensity)
        self.ticks_left = int(ticks_left)
        self.born = int(born)
        self.data = data or {}

    def to_json(self) -> dict:
        return {"kind": self.kind, "x": self.x, "y": self.y, "radius": self.radius,
                "intensity": self.intensity, "ticks_left": self.ticks_left,
                "born": self.born, "data": self.data}

    @staticmethod
    def from_json(d: dict) -> "Event":
        return Event(d["kind"], d["x"], d["y"], d["radius"], d["intensity"],
                     d["ticks_left"], d.get("born", 0), d.get("data"))


class Events:
    def __init__(self, cfg, world, weather, flora, fauna, rng, chronicle):
        self.cfg = cfg
        self.world = world
        self.weather = weather
        self.flora = flora
        self.fauna = fauna
        self.rng = rng
        self.chronicle = chronicle
        self.active: list[Event] = []
        self.fire = np.zeros((world.G, world.G), np.float32)
        self.flood = np.zeros((world.G, world.G), np.float32)
        self.recent: list[dict] = []
        self._yy, self._xx = np.mgrid[0:world.G, 0:world.G]

    # ------------------------------------------------------------------ utils
    def enrich(self) -> float:
        """How much of a disaster's fertility gift the ground can still accept.

        Ash, ejecta and silt make disasters regenerative, which PLAN section 1.2 requires.
        Nothing bounded the total, though, and 2,400 of them over two thousand years drove
        the world's matter eighteen-fold above where it started until 98% of it sat inert
        in saturated soil.  Saturated ground takes no more, so the gift scales to the room
        that is left -- and since the matter now comes out of the lithosphere rather than
        out of nothing, a disaster redistributes rather than creates.
        """
        cap = float(self.cfg.world["nutrient_cap"])
        sat = float(self.world.nutrients.mean()) / max(cap, 1e-6)
        return float(np.clip(1.0 - sat / float(self.cfg.events["enrich_saturation"]),
                             0.0, 1.0))

    def gift(self, mask, amount: float) -> float:
        """A disaster's fertility gift, drawn from rock and never from thin air."""
        return self.world.draw(self.world.soil_fertility, mask,
                               amount * self.enrich(),
                               float(self.cfg.world["fertility_cap"]))

    def disc(self, cy: int, cx: int, r: float) -> np.ndarray:
        G = self.world.G
        dy = self._yy - cy
        dx = (self._xx - cx + G // 2) % G - G // 2
        return (dy * dy + dx * dx) <= r * r

    def creatures_in(self, cy: int, cx: int, r: float):
        f = self.fauna
        if f.pop == 0:
            return np.zeros(0, np.int64)
        rows = f.alive_idx
        G = self.world.G
        dy = f.y[rows] - cy
        dx = (f.x[rows] - cx + G / 2) % G - G / 2
        return rows[(dy * dy + dx * dx) <= r * r]

    def _log(self, tick: int, kind: str, text: str, extra: dict | None = None) -> None:
        self.recent.append({"tick": tick, "kind": kind, "text": text})
        if len(self.recent) > 60:
            self.recent.pop(0)
        if self.chronicle:
            self.chronicle.event(tick, kind, text, extra or {})

    # ---------------------------------------------------------------- triggers
    def maybe_trigger(self, tick: int) -> None:
        if not self.cfg.events["enabled"]:
            self.apply_active(tick)
            return
        c = self.cfg.events
        r = self.rng
        wr, wx = self.world, self.weather
        if len(self.active) < int(c["max_active"]):
            # storms follow heavy cloud
            cloudy = float(wx.cloud.mean())
            if r.random() < float(c["storm_prob"]) * (0.4 + 2.0 * min(cloudy, 1.5)):
                cy, cx = self._weighted_cell(wx.cloud)
                self.trigger("storm", cx, cy, float(c["storm_radius"]),
                             0.4 + 0.6 * r.random(), tick)
            # wildfire wants dry, hot, vegetated ground
            dry = (wr.moisture < float(c["fire_spread_moisture_max"])) & \
                  (self.flora.biomass > float(c["fire_min_biomass"])) & (wr.temperature > 0.45)
            frac = float(dry.mean())
            if frac > 0.001 and r.random() < float(c["wildfire_prob"]) * (0.3 + 6.0 * frac):
                cy, cx = self._weighted_cell(dry.astype(np.float32) * self.flora.biomass)
                self.trigger("wildfire", cx, cy, 3.0, 0.5 + 0.5 * r.random(), tick)
            # floods near water after heavy rain
            rainy = float(wx.rain.mean())
            if rainy > 0.0008 and r.random() < float(c["flood_prob"]) * (1.0 + 400 * rainy):
                cy, cx = self._weighted_cell(wx.rain * (wr.water_depth > 0.01))
                self.trigger("flood", cx, cy, 22 + 30 * r.random(), 0.5 + 0.5 * r.random(), tick)
            if wr.hotspots and r.random() < float(c["volcano_prob"]):
                hy, hx = wr.hotspots[int(r.integers(0, len(wr.hotspots)))]
                self.trigger("volcano", hx, hy, float(c["volcano_ash_radius"]),
                             0.6 + 0.4 * r.random(), tick)
            if wx.season(tick) == "winter" and r.random() < float(c["coldsnap_prob"]):
                self.trigger("cold_snap", 0, 0, 0, 0.5 + 0.5 * r.random(), tick)
            if r.random() < float(c["meteor_prob"]):
                self.trigger("meteor", int(r.integers(0, wr.G)), int(r.integers(0, wr.G)),
                             float(c["meteor_crater_radius"]), 0.5 + 0.5 * r.random(), tick)
        self.apply_active(tick)

    def _weighted_cell(self, weight: np.ndarray) -> tuple[int, int]:
        w = np.maximum(weight, 0.0).ravel()
        s = w.sum()
        if s <= 1e-9:
            i = int(self.rng.integers(0, w.size))
        else:
            i = int(self.rng.choice(w.size, p=w / s))
        return i // self.world.G, i % self.world.G

    def trigger(self, kind: str, x, y, radius=None, intensity=0.7, tick=0) -> Event | None:
        c = self.cfg.events
        G = self.world.G
        x = int(x) % G
        y = int(np.clip(y, 0, G - 1))
        if kind == "storm":
            e = Event(kind, x, y, radius or c["storm_radius"], intensity,
                      int(c["storm_duration"]), tick)
            self._log(tick, kind, f"A storm gathers over ({x},{y}).")
        elif kind == "wildfire":
            e = Event(kind, x, y, radius or 3.0, intensity, int(c["fire_duration"]), tick)
            seed = self.disc(y, x, max(2.0, float(radius or 3.0)))
            self.fire[seed & (self.flora.biomass > 0.02)] = intensity
            self._log(tick, kind, f"Fire breaks out at ({x},{y}).")
        elif kind == "flood":
            e = Event(kind, x, y, radius or 25.0, intensity, 120, tick)
            self._apply_flood(e, tick)
        elif kind == "volcano":
            e = Event(kind, x, y, radius or c["volcano_ash_radius"], intensity, 200, tick)
            self._apply_volcano(e, tick)
        elif kind == "cold_snap":
            e = Event(kind, x, y, 0, intensity, int(c["coldsnap_duration"]), tick)
            self.weather.temp_event_delta += float(c["coldsnap_delta"]) * intensity
            e.data["applied"] = float(c["coldsnap_delta"]) * intensity
            self._log(tick, kind, f"A cold snap grips the world "
                                  f"({float(c['coldsnap_delta']) * intensity:+.2f} temp).")
        elif kind == "meteor":
            e = Event(kind, x, y, radius or c["meteor_crater_radius"], intensity, 60, tick)
            self._apply_meteor(e, tick)
        else:
            return None
        self.active.append(e)
        return e

    # ---------------------------------------------------------------- effects
    def apply_active(self, tick: int) -> None:
        wr, wx, fl, fa = self.world, self.weather, self.flora, self.fauna
        c = self.cfg.events
        done = []
        for e in self.active:
            e.ticks_left -= 1
            if e.kind == "storm":
                m = self.disc(e.y, e.x, e.radius)
                wx.cloud[m] += 0.06 * e.intensity
                wr.moisture[m] += 0.02 * e.intensity
                # Stripped foliage falls to the ground it grew on.  Scaling biomass down
                # and saying nothing about the difference quietly deleted matter, and
                # storms are the most frequent event in the world by a wide margin.
                torn = fl.biomass[m] * (0.004 * e.intensity)
                fl.biomass[m] -= torn
                wr.nutrients[m] += torn * fl.matter_per_biomass
                hit = self.creatures_in(e.y, e.x, e.radius)
                if len(hit):
                    fa.energy[hit] -= 0.05 * e.intensity
            elif e.kind == "wildfire":
                self._spread_fire(e, tick)
                if not (self.fire > 0.01).any():
                    e.ticks_left = 0
            elif e.kind == "flood":
                m = self.disc(e.y, e.x, e.radius) & (wr.elevation < float(wr.cfg.world["sea_level"]) + 0.09)
                self.flood[m] = e.intensity
                if e.ticks_left <= 1:
                    self.gift(m, float(c["flood_silt_fertility"]) * e.intensity)
                    self.flood[m] = 0.0
            elif e.kind == "cold_snap" and e.ticks_left <= 0:
                wx.temp_event_delta -= float(e.data.get("applied", 0.0))
            if e.ticks_left <= 0:
                done.append(e)
        for e in done:
            self.active.remove(e)

    def _spread_fire(self, e: Event, tick: int) -> None:
        c = self.cfg.events
        wr, fl, fa = self.world, self.flora, self.fauna
        burning = self.fire > 0.02
        if not burning.any():
            return
        fuel = (fl.biomass > float(c["fire_min_biomass"])) & \
               (wr.moisture < float(c["fire_spread_moisture_max"])) & (wr.water_depth < 0.1)
        # neighbours of burning cells catch, resisted by the plant's fire_resist gene
        spread_p = fields.blur(self.fire, 0.85) * float(c["fire_spread_chance"])
        resist = fl.genome.plane("fire_resist")
        catch = fuel & ~burning & (self.rng.random(self.fire.shape) < spread_p * (1.0 - 0.85 * resist))
        self.fire[catch] = e.intensity * 0.9

        # burn: consume biomass, deposit ash as fertility, kill slow creatures
        burnt = self.fire > 0.02
        loss = fl.biomass * burnt * (0.22 * (1.0 - 0.7 * resist))
        fl.biomass -= loss
        # Fire is regenerative because it unlocks matter *instantly* as plant-available
        # ash instead of slowly through decomposition -- not because it invents matter.
        matter = loss * fl.matter_per_biomass
        ash = matter * float(c["fire_ash_fertility"])
        room = np.maximum(0.0, float(wr.cfg.world["fertility_cap"]) - wr.soil_fertility)
        ash_fit = np.minimum(ash, room)
        wr.soil_fertility += ash_fit
        wr.nutrients += (matter - ash_fit)
        wr.moisture[burnt] *= 0.94
        self.fire[burnt] -= float(c["fire_burnout"])
        self.fire[fl.biomass <= 0.01] = 0.0
        np.clip(self.fire, 0.0, 1.5, out=self.fire)

        if fa.pop:
            rows = fa.alive_idx
            cy = np.clip(fa.y[rows].astype(np.int32), 0, wr.G - 1)
            cx = np.clip(fa.x[rows].astype(np.int32), 0, wr.G - 1)
            inflame = self.fire[cy, cx] > 0.05
            if inflame.any():
                speed = fa.gene("speed", rows)
                heat = self.fire[cy, cx]
                doomed = inflame & (self.rng.random(len(rows))
                                    < float(c["fire_kill_rate"]) * heat * (1.0 - speed))
                fa.energy[rows[inflame]] -= 0.6 * heat[inflame]
                if doomed.any():
                    n = int(doomed.sum())
                    fa.die(rows[doomed])
                    e.data["casualties"] = e.data.get("casualties", 0) + n

    def _apply_flood(self, e: Event, tick: int) -> None:
        wr, fa = self.world, self.fauna
        m = self.disc(e.y, e.x, e.radius) & (wr.elevation < float(wr.cfg.world["sea_level"]) + 0.09)
        wr.water_depth[m] += 0.5 * e.intensity
        self.flood[m] = e.intensity
        hit = self.creatures_in(e.y, e.x, e.radius)
        n = 0
        if len(hit):
            swim = fa.gene("swim", hit)
            low = wr.elevation[np.clip(fa.y[hit].astype(np.int32), 0, wr.G - 1),
                               np.clip(fa.x[hit].astype(np.int32), 0, wr.G - 1)] < \
                float(wr.cfg.world["sea_level"]) + 0.09
            drown = low & (swim < 0.45) & (self.rng.random(len(hit)) < 0.5 * e.intensity)
            n = int(drown.sum())
            if n:
                fa.die(hit[drown])
        e.data["casualties"] = n
        self._log(tick, "flood", f"Floodwaters swamp ({e.x},{e.y}); {n} drowned. "
                                 f"Silt will enrich the plain.")

    def _apply_volcano(self, e: Event, tick: int) -> None:
        c = self.cfg.events
        wr, fl, fa = self.world, self.flora, self.fauna
        kill_r = float(c["volcano_kill_radius"]) * (0.6 + 0.8 * e.intensity)
        lava = self.disc(e.y, e.x, kill_r)
        ash = self.disc(e.y, e.x, e.radius)
        dead_plants = fl.kill(lava)
        hit = self.creatures_in(e.y, e.x, kill_r)
        n = len(hit)
        if n:
            fa.die(hit)
        # build a cone
        G = wr.G
        dy = self._yy - e.y
        dx = (self._xx - e.x + G // 2) % G - G // 2
        d = np.sqrt(dy * dy + dx * dx)
        cone = np.maximum(0.0, 1.0 - d / max(kill_r, 1.0)) * 0.18 * e.intensity
        wr.elevation = np.clip(wr.elevation + cone, 0.0, 1.0).astype(np.float32)
        wr.classify(); wr._build_base_temp()
        self.gift(ash, 0.45 * e.intensity)
        e.data["casualties"] = n
        self._log(tick, "volcano",
                  f"A volcano erupts at ({e.x},{e.y}): {n} creatures and {dead_plants} "
                  f"plants destroyed, a wide ash ring left fertile.")

    def _apply_meteor(self, e: Event, tick: int) -> None:
        c = self.cfg.events
        wr, fl, fa = self.world, self.flora, self.fauna
        r = e.radius * (0.6 + 0.8 * e.intensity)
        crater = self.disc(e.y, e.x, r)
        ring = self.disc(e.y, e.x, r * 2.6)
        fl.kill(crater)
        hit = self.creatures_in(e.y, e.x, r * 1.3)
        n = len(hit)
        if n:
            fa.die(hit)
        G = wr.G
        dy = self._yy - e.y
        dx = (self._xx - e.x + G // 2) % G - G // 2
        d = np.sqrt(dy * dy + dx * dx)
        bowl = np.maximum(0.0, 1.0 - d / max(r, 1.0)) * 0.22 * e.intensity
        wr.elevation = np.clip(wr.elevation - bowl, 0.0, 1.0).astype(np.float32)
        wr.classify(); wr._build_base_temp()
        wr.water_depth[crater] += 0.4
        self.gift(ring, 0.3 * e.intensity)
        self.weather.dust = min(1.0, self.weather.dust + 0.8 * e.intensity)
        msg = (f"A meteor strikes ({e.x},{e.y}). {n} killed; a crater lake forms and "
               f"dust dims the sun.")
        alien = 0
        if self.rng.random() < float(c["panspermia_chance"]):
            alien = int(self.rng.integers(5, 21))
            idx = fa.spawn(alien, cx=e.x, cy=e.y, radius=r * 1.5, alien=True, tick=tick)
            alien = len(idx)
            e.data["panspermia"] = alien
            msg += f" Something came with it: {alien} organisms of unknown origin stir in the ash."
        e.data["casualties"] = n
        self._log(tick, "meteor", msg, {"panspermia": alien})

    # ------------------------------------------------------------- checkpoint
    def state(self) -> dict:
        return {"events_fire": self.fire, "events_flood": self.flood}

    def meta(self) -> dict:
        return {"active": [e.to_json() for e in self.active], "recent": self.recent}

    def load(self, npz, meta: dict) -> None:
        self.fire = npz["events_fire"]
        self.flood = npz["events_flood"]
        self.active = [Event.from_json(d) for d in meta.get("active", [])]
        self.recent = meta.get("recent", [])
