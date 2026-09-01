"""Seasons, day/night, moisture-cloud-rain loop, climate oscillation."""
from __future__ import annotations

import math

import numpy as np

from . import fields

SEASONS = ("spring", "summer", "autumn", "winter")


class Weather:
    def __init__(self, cfg, world, rng: np.random.Generator):
        self.cfg = cfg
        self.world = world
        self.rng = rng
        G = world.G
        self.cloud = np.zeros((G, G), np.float32)
        self.rain = np.zeros((G, G), np.float32)
        self.climate_osc = 0.0
        self.wind = (1.0, 0.0)
        self.season_phase = 0.0
        self.global_temp_offset = 0.0
        self.sunlight = 1.0
        self.is_night = False
        self.dust = 0.0          # meteor dust dimming, decayed by events
        self.temp_event_delta = 0.0   # cold snaps etc.
        self.rain_mult_ramp: list = []   # [(target, ticks_left, per_tick)]
        self.stack = fields.FieldStack((G, G))

    # ---------------------------------------------------------------- clock
    def year(self, tick: int) -> int:
        return int(tick // int(self.cfg.weather["ticks_per_year"]))

    def season(self, tick: int) -> str:
        tpy = int(self.cfg.weather["ticks_per_year"])
        return SEASONS[int((tick % tpy) / tpy * 4)]

    def day_frac(self, tick: int) -> float:
        return (tick % int(self.cfg.weather["ticks_per_day"])) / \
            float(self.cfg.weather["ticks_per_day"])

    # ---------------------------------------------------------------- step
    def step(self, tick: int) -> None:
        w = self.cfg.weather
        wr = self.world
        tpy = int(w["ticks_per_year"])
        self.season_phase = (tick % tpy) / tpy

        # seasonal + diurnal temperature
        seas = math.sin(2 * math.pi * (self.season_phase - 0.25))
        dayf = self.day_frac(tick)
        diurnal = math.sin(2 * math.pi * (dayf - 0.25))
        self.sunlight = max(0.0, diurnal) * (1.0 - 0.85 * self.dust)
        self.is_night = diurnal <= 0.0
        self.global_temp_offset = (float(w["season_temp_amp"]) * seas
                                   + float(w["day_temp_amp"]) * diurnal
                                   + float(w["temp_offset"]) + self.temp_event_delta)

        # hemispheric season flip: north/south get opposite seasonal swing
        G = wr.G
        hemi = np.linspace(-1.0, 1.0, G, dtype=np.float32)[:, None]
        seasonal_map = float(w["season_temp_amp"]) * seas * hemi
        wr.temperature = (wr.base_temp_map + seasonal_map
                          + float(w["day_temp_amp"]) * diurnal
                          + float(w["temp_offset"]) + self.temp_event_delta).astype(np.float32)

        # climate oscillation random walk
        if tick % int(w["climate_osc_interval"]) == 0:
            self.climate_osc = float(np.clip(
                self.climate_osc + self.rng.normal(0, float(w["climate_osc_step"])),
                -1.0, 1.0))
        self._advance_ramps()

        # wind slowly rotates over the year
        ang = 2 * math.pi * (tick / tpy) * float(w["wind_rotate_per_year"])
        spd = float(w["wind_speed"])
        self.wind = (spd * math.cos(ang), spd * 0.35 * math.sin(ang))

        # evaporation from water, scaled by warmth
        warm = np.clip(wr.temperature, 0.0, 1.5)
        evap = float(w["evaporation_rate"]) * warm * wr.is_water * (0.35 + 0.65 * self.sunlight)
        self.cloud += evap.astype(np.float32)

        # advect + diffuse cloud
        self.cloud = fields.advect(self.cloud, self.wind[0], self.wind[1])
        self.cloud = self.stack.diffuse_many([self.cloud], [float(w["cloud_diffuse"])])[0]
        self.cloud *= (1.0 - float(w["cloud_decay"]))

        # precipitation: capacity falls with cold and elevation (orographic lift)
        cap = (float(w["precip_base_capacity"])
               + float(w["precip_temp_factor"]) * np.clip(wr.temperature, 0.0, 1.2)
               - float(w["precip_elev_factor"]) * np.maximum(0.0, wr.elevation - 0.45))
        cap = np.maximum(cap, 0.03).astype(np.float32)
        excess = np.maximum(0.0, self.cloud - cap)
        rain_mult = float(w["rain_mult"]) * (1.0 + float(w["climate_rain_scale"]) * self.climate_osc)
        rain_mult = max(0.05, rain_mult)
        self.rain = (excess * float(w["precip_efficiency"]) * rain_mult).astype(np.float32)
        self.cloud -= self.rain / max(1e-3, float(w["precip_efficiency"]) * rain_mult)
        np.clip(self.cloud, 0.0, 6.0, out=self.cloud)

        # rain feeds moisture + surface water
        wr.moisture += float(w["rain_to_moisture"]) * self.rain
        wr.water_depth += float(w["rain_to_water"]) * self.rain
        wr.moisture = self.stack.diffuse_many(
            [wr.moisture], [float(w["moisture_diffuse"])])[0]
        wr.moisture *= (1.0 - float(w["moisture_decay"]) * (0.5 + np.clip(wr.temperature, 0, 1.4)))
        wr.moisture[wr.biome == 0] = 1.0
        np.clip(wr.moisture, 0.0, 1.6, out=wr.moisture)

        # surface water drains downhill-ish (decay toward zero on land)
        land = wr.biome != 0
        wr.water_depth[land] *= (1.0 - float(w["water_drain"]))
        np.clip(wr.water_depth, 0.0, 4.0, out=wr.water_depth)

        # dust decays
        if self.dust > 0:
            self.dust = max(0.0, self.dust - 1.0 / max(1.0, float(self.cfg.events["meteor_dust_duration"])))

    # ------------------------------------------------------------ intervention
    def ramp(self, param: str, value: float, ticks: int) -> None:
        cur = float(self.cfg.weather.get(param, 0.0))
        ticks = max(1, int(ticks))
        self.rain_mult_ramp.append([param, cur, float(value), ticks, ticks])

    def _advance_ramps(self) -> None:
        done = []
        for r in self.rain_mult_ramp:
            param, start, target, left, total = r
            left -= 1
            r[3] = left
            frac = 1.0 - max(0, left) / total
            self.cfg.set(f"weather.{param}", start + (target - start) * frac)
            if left <= 0:
                done.append(r)
        for r in done:
            self.rain_mult_ramp.remove(r)

    def is_drought(self) -> bool:
        return self.climate_osc < -0.45

    # ------------------------------------------------------------- checkpoint
    def state(self) -> dict:
        return {"weather_cloud": self.cloud, "weather_rain": self.rain}

    def meta(self) -> dict:
        return {"climate_osc": self.climate_osc, "dust": self.dust,
                "temp_event_delta": self.temp_event_delta,
                "ramps": self.rain_mult_ramp}

    def load(self, npz, meta: dict) -> None:
        self.cloud = npz["weather_cloud"]
        self.rain = npz["weather_rain"]
        self.climate_osc = float(meta.get("climate_osc", 0.0))
        self.dust = float(meta.get("dust", 0.0))
        self.temp_event_delta = float(meta.get("temp_event_delta", 0.0))
        self.rain_mult_ramp = [list(r) for r in meta.get("ramps", [])]
