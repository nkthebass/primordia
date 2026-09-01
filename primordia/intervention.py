"""The Claude-in-the-loop intervention protocol.

Inbound: `interventions/*.json` -> applied -> moved to `interventions/done/`
(or `failed/` with a `.err.txt`).  Interventions are DATA.  Nothing in a JSON file is
ever executed as code -- every effect is composed from a fixed whitelist of primitives
validated in `genetics.validate_effect`.
"""
from __future__ import annotations

import json
import os
import shutil
import time
import traceback

import numpy as np

from .genetics import Gene, validate_effect

TYPES = ("trigger_event", "climate", "tune", "seed_organism", "note", "add_gene",
         "checkpoint", "set_speed")


class Intervention:
    def __init__(self, cfg, sim, root: str):
        self.cfg = cfg
        self.sim = sim
        self.root = root
        self.dir = os.path.join(root, "interventions")
        self.done = os.path.join(self.dir, "done")
        self.failed = os.path.join(self.dir, "failed")
        for d in (self.dir, self.done, self.failed):
            os.makedirs(d, exist_ok=True)
        self.applied_count = 0
        self.failed_count = 0
        self.last_tick = -1
        self.log: list[dict] = []

    # ------------------------------------------------------------------- poll
    def poll(self, tick: int) -> list[dict]:
        results = []
        try:
            names = sorted(n for n in os.listdir(self.dir) if n.lower().endswith(".json"))
        except FileNotFoundError:
            return results
        for name in names:
            path = os.path.join(self.dir, name)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            except Exception as e:
                self._fail(path, name, f"could not parse JSON: {e}")
                results.append({"file": name, "ok": False, "error": str(e)})
                continue
            items = payload if isinstance(payload, list) else [payload]
            errors = []
            applied = []
            for item in items:
                try:
                    msg = self.apply(item, tick)
                    applied.append(msg)
                except Exception as e:
                    errors.append(f"{item.get('type', '?')}: {e}")
            if errors:
                self._fail(path, name, "\n".join(errors) + "\n\n" +
                           ("applied first: " + "; ".join(applied) if applied else ""))
                results.append({"file": name, "ok": False, "error": "; ".join(errors)})
            else:
                self._ok(path, name)
                results.append({"file": name, "ok": True, "applied": applied})
        self.last_tick = tick
        return results

    def _ok(self, path: str, name: str) -> None:
        self.applied_count += 1
        stamp = time.strftime("%Y%m%d-%H%M%S")
        shutil.move(path, os.path.join(self.done, f"{stamp}_{name}"))

    def _fail(self, path: str, name: str, err: str) -> None:
        self.failed_count += 1
        stamp = time.strftime("%Y%m%d-%H%M%S")
        dest = os.path.join(self.failed, f"{stamp}_{name}")
        shutil.move(path, dest)
        with open(dest + ".err.txt", "w", encoding="utf-8") as f:
            f.write(err + "\n")
        self.sim.log_event("intervention", f"Intervention '{name}' REJECTED: {err[:220]}")

    # ------------------------------------------------------------------ apply
    def apply(self, item: dict, tick: int) -> str:
        if not isinstance(item, dict):
            raise ValueError("each intervention must be a JSON object")
        t = item.get("type")
        if t not in TYPES:
            raise ValueError(f"unknown type '{t}' (allowed: {', '.join(TYPES)})")
        fn = getattr(self, f"_do_{t}")
        msg = fn(item, tick)
        self.log.append({"tick": tick, "type": t, "msg": msg})
        if len(self.log) > 200:
            self.log.pop(0)
        return msg

    # -------- individual handlers ---------------------------------------
    def _do_trigger_event(self, item: dict, tick: int) -> str:
        from .events import EVENT_TYPES
        ev = item.get("event")
        if ev not in EVENT_TYPES:
            raise ValueError(f"unknown event '{ev}' (allowed: {', '.join(EVENT_TYPES)})")
        G = self.sim.world.G
        x = int(item.get("x", self.sim.rng.integers(0, G)))
        y = int(item.get("y", self.sim.rng.integers(0, G)))
        radius = item.get("radius")
        intensity = float(np.clip(item.get("intensity", 0.7), 0.05, 1.0))
        self.sim.events.trigger(ev, x, y, None if radius is None else float(radius),
                                intensity, tick)
        self.sim.stats.mark(tick, ev)
        msg = f"triggered {ev} at ({x},{y}) intensity {intensity:.2f}"
        self.sim.log_event("intervention", f"By decree: {msg}.")
        return msg

    def _do_climate(self, item: dict, tick: int) -> str:
        param = item.get("param")
        if param not in ("rain_mult", "temp_offset"):
            raise ValueError("climate param must be 'rain_mult' or 'temp_offset'")
        value = float(item["value"])
        if param == "rain_mult":
            value = float(np.clip(value, 0.05, 4.0))
        else:
            value = float(np.clip(value, -0.6, 0.6))
        ramp = int(item.get("ramp_ticks", 0))
        if ramp > 0:
            self.sim.weather.ramp(param, value, ramp)
            msg = f"climate {param} ramping to {value} over {ramp} ticks"
        else:
            self.cfg.set(f"weather.{param}", value)
            msg = f"climate {param} set to {value}"
        self.sim.log_event("intervention", f"The climate shifts: {msg}.")
        return msg

    def _do_tune(self, item: dict, tick: int) -> str:
        path = str(item["path"])
        value = item["value"]
        if not isinstance(value, (int, float, bool)):
            raise ValueError("tune value must be a number or boolean")
        before = self.cfg.get(path)
        if before is None:
            raise ValueError(f"config leaf '{path}' does not exist")
        self.cfg.set(path, value, enforce_hot=True)
        if path.startswith("fauna.max_pop"):
            self.sim.fauna.schema.grow(int(value))
        msg = f"tuned {path}: {before} -> {value}"
        self.sim.log_event("tuning", f"Law of nature amended: {msg}.")
        return msg

    def _do_seed_organism(self, item: dict, tick: int) -> str:
        kingdom = item.get("kingdom", "fauna")
        count = int(np.clip(item.get("count", 10), 1, 2000))
        G = self.sim.world.G
        x = float(item.get("x", self.sim.rng.integers(0, G)))
        y = float(item.get("y", self.sim.rng.integers(0, G)))
        radius = float(item.get("radius", 12.0))
        genome = item.get("genome", "random_alien")
        if kingdom == "fauna":
            if genome == "random_alien":
                idx = self.sim.fauna.spawn(count, cx=x, cy=y, radius=radius,
                                           alien=True, tick=tick)
            elif isinstance(genome, dict):
                bad = [k for k in genome if k not in self.sim.fauna.schema.index]
                if bad:
                    raise ValueError(f"unknown fauna genes: {', '.join(bad[:6])}")
                idx = self.sim.fauna.spawn(count, cx=x, cy=y, radius=radius,
                                           archetype=genome, tick=tick)
            else:
                raise ValueError("genome must be 'random_alien' or an object of gene values")
            msg = f"seeded {len(idx)} fauna at ({int(x)},{int(y)})"
        elif kingdom == "flora":
            fl = self.sim.flora
            ang = self.sim.rng.random(count) * 2 * np.pi
            r = self.sim.rng.random(count) ** 0.5 * radius
            ty = np.clip((y + np.sin(ang) * r).astype(np.int32), 0, G - 1)
            tx = ((x + np.cos(ang) * r).astype(np.int32)) % G
            ok = self.sim.world.is_land[ty, tx]
            ty, tx = ty[ok], tx[ok]
            if isinstance(genome, dict):
                bad = [k for k in genome if not fl.genome.has(k)]
                if bad:
                    raise ValueError(f"unknown flora genes: {', '.join(bad[:6])}")
                fl.genome.randomize_cells(ty, tx, self.sim.rng)
                for k, v in genome.items():
                    fl.genome.data[fl.genome.index[k], ty, tx] = float(v)
            else:
                fl.genome.randomize_cells(ty, tx, self.sim.rng)
            fl.biomass[ty, tx] = np.maximum(fl.biomass[ty, tx], 0.2)
            fl.age[ty, tx] = 0.0
            msg = f"seeded {len(ty)} flora at ({int(x)},{int(y)})"
        else:
            raise ValueError("kingdom must be 'fauna' or 'flora'")
        self.sim.log_event("intervention", f"Life arrives from nowhere: {msg}.")
        return msg

    def _do_note(self, item: dict, tick: int) -> str:
        text = str(item.get("text", "")).strip()
        if not text:
            raise ValueError("note requires non-empty 'text'")
        self.sim.log_event("note", text[:4000])
        return f"note recorded ({len(text)} chars)"

    def _do_checkpoint(self, item: dict, tick: int) -> str:
        self.sim.request_checkpoint(str(item.get("label") or "") or None)
        return "checkpoint requested"

    def _do_set_speed(self, item: dict, tick: int) -> str:
        v = int(np.clip(item.get("value", 4), 0, 4096))
        self.cfg.set("sim.speed", v)
        return f"sim speed set to {v}"

    # -------- the crown jewel -------------------------------------------
    def _do_add_gene(self, item: dict, tick: int) -> str:
        kingdom = item.get("kingdom", "fauna")
        if kingdom not in ("fauna", "flora"):
            raise ValueError("kingdom must be 'fauna' or 'flora'")
        name = str(item.get("name", "")).strip()
        if not name or not name.replace("_", "").isalnum():
            raise ValueError("gene 'name' must be a non-empty alphanumeric/underscore string")
        if name.startswith("w0") or name.startswith("w1"):
            raise ValueError("gene names starting with 'w0'/'w1' are reserved for brains")
        init = item.get("init") or {}
        mean = float(np.clip(init.get("mean", 0.05), -4.0, 4.0))
        std = float(np.clip(init.get("std", 0.05), 0.0, 2.0))
        mut = float(np.clip(item.get("mut_std", 0.04), 0.0, 1.0))
        lo = float(item.get("lo", 0.0))
        hi = float(item.get("hi", 1.0))
        if hi <= lo:
            raise ValueError("'hi' must be greater than 'lo'")
        effects = item.get("effects") or []
        if not isinstance(effects, list) or not effects:
            raise ValueError("add_gene requires a non-empty 'effects' list")
        if len(effects) > 8:
            raise ValueError("at most 8 effects per gene")
        clean = [validate_effect(e) for e in effects]

        target = self.sim.fauna if kingdom == "fauna" else self.sim.flora
        if kingdom == "fauna":
            if self.sim.fauna.schema.has(name):
                raise ValueError(f"fauna already has a gene named '{name}'")
        elif self.sim.flora.genome.has(name):
            raise ValueError(f"flora already has a gene named '{name}'")

        gene = Gene(name, mean, std, mut, lo, hi, True, clean, int(tick))
        target.add_runtime_gene(gene)
        self.sim.speciation._rebuild_cols()
        desc = "; ".join(
            f"{e['stat']} {e['op']} {e['per_unit']:+g}"
            + (f" when {e['when']}" if e["when"] else "") for e in clean)
        self.sim.log_event(
            "gene",
            f"A new heritable trait appears in the {kingdom}: **{name}** "
            f"(init {mean:.2f}±{std:.2f}, mutation {mut:.2f}) — {desc}.",
            {"gene": name, "kingdom": kingdom, "effects": clean})
        return f"added {kingdom} gene '{name}' with {len(clean)} effect(s)"

    # ------------------------------------------------------------------ misc
    def write_example(self) -> str:
        """Drops a commented example into interventions/ (not consumed: .txt)."""
        p = os.path.join(self.dir, "EXAMPLES.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(EXAMPLES)
        return p


EXAMPLES = """PRIMORDIA intervention files
============================
Drop a .json file (one object, or a list of objects) into this folder.  The sim polls
every `sim.intervention_every` ticks, applies it, and moves it to done/ (or failed/
with a .err.txt explaining why).  Nothing here is executed as code.

{"type":"trigger_event","event":"wildfire","x":120,"y":300,"radius":25,"intensity":0.8}
  events: storm | wildfire | flood | volcano | cold_snap | meteor

{"type":"climate","param":"rain_mult","value":0.7,"ramp_ticks":2000}
  param: rain_mult (0.05-4.0) | temp_offset (-0.6-0.6)

{"type":"tune","path":"energy.basal_rate","value":0.13}
  any hot-reloadable config leaf (weather./events./flora./decomposer./fauna./energy./
  genetics./speciation./scent./sim./monitor.)

{"type":"seed_organism","kingdom":"fauna","count":10,"x":50,"y":50,
 "genome":"random_alien"}
{"type":"seed_organism","kingdom":"fauna","count":30,"x":50,"y":50,
 "genome":{"diet":0.9,"size":0.7,"speed":0.8}}

{"type":"note","text":"Carnivores were collapsing so I seeded a prey refuge."}

{"type":"add_gene","kingdom":"fauna","name":"bioluminescence",
 "init":{"mean":0.05,"std":0.05},"mut_std":0.04,
 "effects":[
   {"stat":"mate_appeal","op":"add","per_unit":0.5,"when":{"is_night":true}},
   {"stat":"detectability","op":"add","per_unit":0.4,"when":{"is_night":true}},
   {"stat":"basal_cost","op":"mul_per_unit","per_unit":0.1}]}

  stats: basal_cost move_cost bite_size attack_power armor_eff detectability
         sense_bonus mate_appeal cold_resist heat_resist toxin_resist plant_digest
         meat_digest fire_resist swim_eff scent_strength fertility_local
         growth_mult seed_bonus water_efficiency toxin_bonus   (last four: flora)
  ops:   add | mul_per_unit
  when:  is_night(bool) season(spring|summer|autumn|winter)
         biome(ocean|coast|plains|hills|mountain) in_water(bool)
         moisture_gt/lt(num) temp_gt/lt(num)

{"type":"checkpoint","label":"before-the-great-drought"}
{"type":"set_speed","value":16}
"""
