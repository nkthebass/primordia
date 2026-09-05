"""History series, warning detection, state/summary.json writer."""
from __future__ import annotations

import json
import os
import time
from collections import deque

import numpy as np

SERIES = ("tick", "herbivore", "omnivore", "carnivore", "flora_biomass",
          "species_count", "diet_mean", "temp", "climate_osc", "decomposer",
          "fertility", "nutrients", "tps", "pop", "gen_variance", "meat")


class Stats:
    def __init__(self, cfg, sim):
        self.cfg = cfg
        self.sim = sim
        n = int(cfg.sim["history_max"])
        self.h = {k: deque(maxlen=n) for k in SERIES}
        self.markers: deque = deque(maxlen=400)   # disaster tick markers
        self.year_snapshots: dict[int, dict] = {}
        self.warnings: list[str] = []
        self.last_summary_tick = -1

    # ---------------------------------------------------------------- sampling
    def sample(self, tick: int) -> None:
        s = self.sim
        fa, fl, wr, wx = s.fauna, s.flora, s.world, s.weather
        herb, omni, carn = fa.trophic_counts()
        rows = fa.alive_idx
        diet_mean = float(fa.gene("diet", rows).mean()) if len(rows) else 0.0
        var = self._genetic_variance(rows)
        vals = {
            "tick": tick, "herbivore": herb, "omnivore": omni, "carnivore": carn,
            "flora_biomass": float(fl.biomass.sum()),
            "species_count": len(s.speciation.living()),
            "diet_mean": diet_mean,
            "temp": float(wr.temperature.mean()),
            "climate_osc": float(wx.climate_osc),
            "decomposer": float(s.decomposers.density.sum()),
            "fertility": float(wr.soil_fertility.mean()),
            "nutrients": float(wr.nutrients.mean()),
            "tps": float(s.tps),
            "pop": int(fa.pop),
            "gen_variance": var,
            "meat": float(fa.meat.sum()),
        }
        for k, v in vals.items():
            self.h[k].append(v)

    def _genetic_variance(self, rows) -> float:
        fa = self.sim.fauna
        if len(rows) < 8:
            return 0.0
        cols = self.sim.speciation.cols
        v = fa.schema.data[np.ix_(rows[::max(1, len(rows) // 2000)], cols)]
        return float(v.var(axis=0).mean())

    def mark(self, tick: int, kind: str) -> None:
        self.markers.append({"tick": int(tick), "kind": kind})

    # ---------------------------------------------------------------- warnings
    def compute_warnings(self, tick: int) -> list[str]:
        w: list[str] = []
        s = self.sim
        tpy = int(self.cfg.weather["ticks_per_year"])
        h = self.h
        n = len(h["tick"])
        if n < 4:
            return w
        step = max(1, tpy // int(self.cfg.sim["housekeeping_every"]))
        prev_i = max(0, n - 1 - step)
        cur = {k: h[k][-1] for k in ("herbivore", "omnivore", "carnivore",
                                     "flora_biomass", "gen_variance", "pop")}
        old = {k: h[k][prev_i] for k in cur}

        for level in ("herbivore", "omnivore", "carnivore"):
            c, o = cur[level], old[level]
            if c == 0 and o > 0:
                w.append(f"{level}s are extinct")
            elif o > 30 and c < 0.5 * o:
                w.append(f"{level} biomass down {100 * (1 - c / max(o, 1)):.0f}% over last year")
            elif 0 < c < 25:
                w.append(f"{level} population critically low ({c})")

        if cur["flora_biomass"] < 0.35 * max(old["flora_biomass"], 1e-6):
            w.append("flora biomass down >65% over last year")

        # stagnation: variance plateau over 3 years
        need = 3 * step
        if n > need:
            recent = [h["gen_variance"][i] for i in range(n - need, n)]
            if recent and max(recent) > 0:
                spread = (max(recent) - min(recent)) / max(recent)
                if spread < 0.06:
                    w.append("genetic variance flat for 3 years (stagnation)")

        living = s.speciation.living()
        total = max(1, s.fauna.pop)
        for sp in living[:3]:
            if sp.pop / total > 0.7:
                w.append(f"monoculture: {sp.name} is {100 * sp.pop / total:.0f}% of all fauna")
        if s.fauna.pop >= 0.97 * s.fauna.cap:
            w.append("population at hard cap (runaway)")
        pn = self._predator_niche()
        if pn and not pn["open"]:
            w.append(f"predator niche closed: prey defence {pn['prey_defence']:.2f} "
                     f"needs attack power {pn['power_needed']:.2f}, genome ceiling is "
                     f"1.60 - seeding predators here cannot work until prey armour or "
                     f"speed comes down")
        b = self._brain_health()
        if b.get("output_saturated", 0) > 0.5:
            w.append(f"brains saturated: {b['output_saturated']*100:.0f}% of outputs "
                     f"pinned, weight sd {b['weight_sd']:.2f} — the fauna are not "
                     f"responding to their senses")
        if s.fauna.pop == 0:
            w.append("TOTAL FAUNAL EXTINCTION")
        if s.monitor:
            w += s.monitor.warnings()
        self.warnings = w
        return w

    # ---------------------------------------------------------------- summary
    def summary(self, tick: int) -> dict:
        s = self.sim
        fa, fl, wr, wx = s.fauna, s.flora, s.world, s.weather
        herb, omni, carn = fa.trophic_counts()
        species = []
        for sp in s.speciation.living()[:24]:
            trend = self._trend(sp)
            species.append({
                "id": sp.id, "name": sp.name, "rank": sp.rank, "pop": sp.pop,
                "parent": sp.parent, "founded_tick": sp.founded,
                "diet_mean": round(sp.diet_mean, 3), "trend": trend,
                "notable_traits": {k: v for k, v in sorted(
                    sp.traits.items(), key=lambda kv: -abs(kv[1] - 0.4))[:4]},
            })
        res = s.monitor.snapshot() if s.monitor else {}
        recent = [f"{e['kind']} {e['stamp']}" for e in list(s.chronicle.recent)[-8:]
                  if e["kind"] in ("wildfire", "flood", "volcano", "meteor", "storm",
                                   "cold_snap", "speciation", "extinction", "gene")]
        return {
            "tick": int(tick), "year": wx.year(tick), "season": wx.season(tick),
            "tps": round(float(s.tps), 2),
            "real_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "climate": {"osc": round(float(wx.climate_osc), 3),
                        "global_temp_offset": round(float(wx.global_temp_offset), 3),
                        "mean_temp": round(float(wr.temperature.mean()), 3),
                        "drought": bool(wx.is_drought()),
                        "rain_mult": round(float(self.cfg.weather["rain_mult"]), 3)},
            "populations": {
                "flora_biomass": round(float(fl.biomass.sum()), 1),
                "flora_cover": round(float((fl.biomass > 1e-3).mean()), 4),
                "herbivore": herb, "omnivore": omni, "carnivore": carn,
                "total_fauna": int(fa.pop),
                "decomposer": round(float(s.decomposers.density.sum()), 1),
                "carrion": round(float(fa.meat.sum()), 1),
            },
            "soil": {"fertility_mean": round(float(wr.soil_fertility.mean()), 4),
                     "nutrients_mean": round(float(wr.nutrients.mean()), 4)},
            "species": species,
            "species_total_ever": len(s.speciation.species),
            "genetic_variance": round(self._genetic_variance(fa.alive_idx), 5),
            "brains": self._brain_health(),
            "predator_niche": self._predator_niche(),
            "warnings": self.compute_warnings(tick),
            "recent_events": recent,
            "active_events": [e.to_json() for e in s.events.active][:10],
            "runtime_genes": [
                {"kingdom": k, "name": g.name, "added_tick": g.added_tick,
                 "effects": g.effects, **self._gene_report(k, g.name)}
                for k, g in s.runtime_gene_list()],
            "interventions": {"applied": s.intervention.applied_count,
                              "failed": s.intervention.failed_count,
                              "last_tick": s.intervention.last_tick},
            "resources": res,
            "config_hot": {"mutation_rate_global": self.cfg.genetics["mutation_rate_global"],
                           "energy.basal_rate": self.cfg.energy["basal_rate"]},
        }

    def _predator_niche(self) -> dict:
        """Can the genome still express an animal able to kill what is grazing here?

        A blow lands when attack_power * attack_output exceeds the victim's armour plus
        an evasion roll, and attack_power tops out at fangs 1.0 + 0.6 * size 1.0 = 1.60.
        Herbivore armour and speed are under continuous selection; predators are not
        always present to push back.  Two thousand years of that ratchet took the bar to
        1.89 here, and every predator seeding after that point was arithmetically dead on
        arrival -- the hunters chased, closed, landed blows, and could not convert them.
        """
        fa = self.sim.fauna
        rows = fa.alive_idx
        if len(rows) < 50:
            return {}
        d = fa.schema.data
        gi = fa.gi
        size = fa.size_eff[rows]
        if not size.any():
            size = d[rows, gi["size"]] * float(fa.cfg.fauna["juvenile_size"])
        armour = d[rows, gi["armor"]] + 0.35 * size
        small = size < np.median(size) * 1.2
        sel = small if small.any() else np.ones(len(rows), bool)
        bar = float(np.percentile(armour[sel], 60))
        evasion = 0.225 + float(fa.cfg.energy["evasion"]) * float(d[rows, gi["speed"]][sel].mean())
        need = (bar + evasion) * 1.25 / 0.9
        return {"prey_defence": round(bar + evasion, 3),
                "power_needed": round(need, 3),
                "genome_ceiling": 1.6,
                "open": bool(need <= 1.6)}

    def _brain_health(self) -> dict:
        """Is the network still a controller, or has it become a constant?

        Weights under weak selection random-walk to the edges of their range, and once the
        spread is large every pre-activation saturates tanh: outputs pin to +-1 whatever
        the senses report, and the fauna stop steering.  `output_saturated` is the honest
        alarm -- it reached 0.80 here while every other statistic in this file looked
        healthy, and nothing in the report would have shown it.
        """
        fa = self.sim.fauna
        rows = fa.alive_idx
        if len(rows) < 20:
            return {}
        gn = [g.name for g in fa.schema.genes]
        bcols = [i for i, n in enumerate(gn) if n.startswith("w") and n[1:].isdigit()]
        if not bcols:
            return {}
        bw = fa.schema.data[np.ix_(rows, bcols)]
        out = {"weight_sd": round(float(bw.std()), 3),
               "weight_at_bound": round(float((np.abs(bw) > 3.99).mean()), 4)}
        # last_outputs is the most recent tick's forward pass.  Requiring it to match the
        # current row count exactly means one birth or death between the tick and the
        # write silently drops the metric -- which it did, reporting 0.000 saturation
        # while the brains were 80%% pinned.
        o = fa.last_outputs
        if len(o):
            out["output_saturated"] = round(float((np.abs(o) > 0.95).mean()), 4)
            # spread of one steering channel across animals seeing different things:
            # near zero means everybody is doing the same thing regardless of input
            out["steering_spread"] = round(float(o[:, 1].std()), 3)
        return out

    def _gene_report(self, kingdom: str, name: str) -> dict:
        """Distribution of one runtime gene, not just its mean.

        A scalar mean cannot tell a gene that swept from a gene that is drifting: winter
        torpor read 0.47 either way.  What separates them is the spread against the
        between-group difference -- torpor's trophic means were 0.500/0.460/0.424 with an
        sd of 0.298, so its selection differential was a fifth of its noise and the mean
        was reporting drift as success.  `split` below is that ratio, made explicit.
        """
        s = self.sim
        if kingdom == "fauna":
            rows = s.fauna.alive_idx
            if len(rows) == 0 or not s.fauna.schema.has(name):
                return {"mean": 0.0, "n": 0}
            v = s.fauna.gene(name, rows)
            out = self._dist(v)

            diet = s.fauna.gene("diet", rows)
            trophic = {}
            for lo, hi, lab in ((0.0, 0.33, "herbivore"), (0.33, 0.66, "omnivore"),
                                (0.66, 1.01, "carnivore")):
                m = (diet >= lo) & (diet < hi)
                # same floor as the biome groups: a bucket holding two carnivores
                # produces a mean that swamps the split ratio with noise
                if m.sum() >= 20:
                    trophic[lab] = round(float(v[m].mean()), 4)
            out["by_trophic"] = trophic

            # ...and by habitat, because a gene conditioned on biome or water cannot show
            # up in a trophic breakdown at all
            from .world import BIOME_NAMES
            G = s.world.G
            cy = np.clip(s.fauna.y[rows].astype(np.int32), 0, G - 1)
            cx = np.clip(s.fauna.x[rows].astype(np.int32), 0, G - 1)
            b = s.world.biome[cy, cx]
            habitat, share = {}, {}
            for code, lab in enumerate(BIOME_NAMES):
                m = b == code
                if m.sum() >= 20:
                    habitat[lab] = round(float(v[m].mean()), 4)
                    share[lab] = round(float(m.mean()), 4)
            out["by_biome"] = habitat
            out["pop_share_by_biome"] = share

            # `split` is the between-group spread measured in standard deviations.  Below
            # about 0.5 a gene is drifting, whatever its mean says: winter torpor read a
            # respectable 0.47 while splitting the fauna by 0.25 sd, which is noise.
            for key, groups in (("split_trophic", trophic), ("split_biome", habitat)):
                if len(groups) > 1 and out["sd"] > 1e-9:
                    out[key] = round((max(groups.values()) - min(groups.values()))
                                     / out["sd"], 3)
            out["split"] = max((out.get("split_trophic", 0.0),
                                out.get("split_biome", 0.0)))
            return out
        if not s.flora.genome.has(name):
            return {"mean": 0.0, "n": 0}
        m = s.flora.biomass > 1e-3
        if not m.any():
            return {"mean": 0.0, "n": 0}
        return self._dist(s.flora.genome.plane(name)[m])

    @staticmethod
    def _dist(v) -> dict:
        q = np.percentile(v, [5, 25, 50, 75, 95])
        return {"mean": round(float(v.mean()), 4), "sd": round(float(v.std()), 4),
                "n": int(v.size),
                "p5": round(float(q[0]), 4), "p25": round(float(q[1]), 4),
                "p50": round(float(q[2]), 4), "p75": round(float(q[3]), 4),
                "p95": round(float(q[4]), 4),
                "frac_above_half": round(float((v > 0.5).mean()), 4)}

    def _trend(self, sp) -> str:
        ser = [p for _, p in sp.pop_series[-14:]]
        if len(ser) < 4:
            return "new"
        a = sum(ser[:len(ser) // 2]) / max(1, len(ser) // 2)
        b = sum(ser[len(ser) // 2:]) / max(1, len(ser) - len(ser) // 2)
        if b > a * 1.18:
            return "growing"
        if b < a * 0.82:
            return "declining"
        return "stable"

    def write_summary(self, tick: int, path: str) -> dict:
        d = self.summary(tick)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
        os.replace(tmp, path)
        self.last_summary_tick = tick
        return d

    # ---------------------------------------------------------------- viewer
    def series(self, max_points: int = 1000) -> dict:
        n = len(self.h["tick"])
        if n == 0:
            return {k: [] for k in SERIES} | {"markers": []}
        step = max(1, n // max_points)
        out = {k: list(self.h[k])[::step] for k in SERIES}
        out["markers"] = list(self.markers)
        return out

    def meta(self) -> dict:
        return {"h": {k: list(v) for k, v in self.h.items()},
                "markers": list(self.markers)}

    def load(self, meta: dict) -> None:
        n = int(self.cfg.sim["history_max"])
        for k, v in meta.get("h", {}).items():
            if k in self.h:
                self.h[k] = deque(v, maxlen=n)
        self.markers = deque(meta.get("markers", []), maxlen=400)
