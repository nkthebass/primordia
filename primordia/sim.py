"""The world: owns every subsystem and runs the tick loop (PLAN §7)."""
from __future__ import annotations

import os
import threading
import time

import numpy as np

from . import checkpoint as ckpt
from . import fields
from .chronicle import Chronicle
from .config import Config
from .events import Events
from .fauna import Fauna
from .flora import Flora, Decomposers
from .genetics import Gene
from .intervention import Intervention
from .monitor import Monitor
from .render import Renderer
from .scent import Scent
from .speciation import Speciation
from .stats import Stats
from .weather import Weather
from .world import World

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Sim:
    def __init__(self, cfg: Config, root: str = ROOT, with_monitor: bool = True):
        self.cfg = cfg
        self.root = root
        self.tick = 0
        self.tps = 0.0
        self.tps_cap = 0.0            # 0 = uncapped
        self.running = True
        self.lock = threading.RLock()
        self._ckpt_request: str | None = None
        self._ckpt_last = time.time()
        self._ckpt_fails = 0
        self.checkpoints_enabled = True
        self._tick_times: list[float] = []
        self.frame_seq = 0

        fields.init_backend(cfg.get("device", "auto"))
        self.rng = np.random.default_rng(int(cfg["seed"]))

        self.world = World(cfg, self.rng)
        self.field_path = fields.choose_field_path((self.world.G, self.world.G))
        self.weather = Weather(cfg, self.world, self.rng)
        self.chronicle = Chronicle(root, self.weather)
        self.flora = Flora(cfg, self.world, self.rng)
        self.decomposers = Decomposers(cfg, self.world, self.rng)
        self.scent = Scent(cfg, self.world)
        self.fauna = Fauna(cfg, self.world, self.flora, self.scent, self.rng)
        self.events = Events(cfg, self.world, self.weather, self.flora, self.fauna,
                             self.rng, self.chronicle)
        self.speciation = Speciation(cfg, self.fauna, self.rng, self.chronicle)
        self.monitor = Monitor(cfg, root, self) if with_monitor else None
        self.stats = Stats(cfg, self)
        self.intervention = Intervention(cfg, self, root)
        self.render = Renderer(self)

        self.frame_listeners: list = []
        self.pending_predators = -1
        self.predator_waves_total = 1
        self.predator_waves = 0
        self.next_predator_tick = 0
        self.seeded = False
        self.last_summary: dict = {}
        self.paused_reason = ""

    # ------------------------------------------------------------------ setup
    def bootstrap(self, green_up: int | None = None) -> None:
        """Seed the initial biosphere.  Only called for a fresh world.

        Flora and weather run alone for `green_up` ticks first: dropping herbivores onto
        bare rock starves the whole food chain before selection gets a chance (PLAN 13).
        """
        self.flora.seed_initial()
        self.decomposers.density[self.world.is_land] = 0.1
        n = int(self.cfg.sim.get("green_up_ticks", 1400) if green_up is None else green_up)
        for t in range(n):
            self.weather.step(t)
            ctx = {"is_night": self.weather.is_night, "season": self.weather.season(t)}
            self.flora.step(t, self.weather.sunlight, ctx)
            self.decomposers.step()
        # Herbivores and omnivores first.  Predators dropped onto a bare world eat the
        # entire founding stock in one season and then starve; they are seeded once the
        # prey base has established itself (PLAN 6.3 bootstrapping).
        self.fauna.seed_founders(self.tick, only={"grazer", "omnivore"})
        # deadline, not a schedule: predators arrive as soon as the prey base can carry
        # them, or at this tick at the latest
        self.pending_predators = int(self.cfg.sim.get("predator_delay_ticks", 4000))
        self.predator_waves_total = max(1, int(self.cfg.sim.get("predator_waves", 3)))
        self.predator_waves = self.predator_waves_total
        self.next_predator_tick = int(self.cfg.sim.get("predator_min_tick", 900))
        self.seeded = True
        self.log_event("world",
                       f"A world of {self.world.G}x{self.world.G} cells condenses out of "
                       f"noise. {int((self.world.biome != 0).mean() * 100)}% is dry land. "
                       f"{int((self.flora.biomass > 1e-3).sum())} plants take root and "
                       f"{self.fauna.pop} creatures draw their first breath.")
        self.intervention.write_example()
        self.chronicle.flush()

    def log_event(self, kind: str, text: str, extra: dict | None = None) -> None:
        self.chronicle.event(self.tick, kind, text, extra)

    # ------------------------------------------------------------------- tick
    def step(self) -> None:
        t0 = time.perf_counter()
        tick = self.tick
        cfg = self.cfg
        wx, wr, fl, fa = self.weather, self.world, self.flora, self.fauna

        # 1 weather
        wx.step(tick)
        ctx = {"is_night": wx.is_night, "season": wx.season(tick)}

        # 2 disasters
        self.events.maybe_trigger(tick)

        # 3 flora
        fl.step(tick, wx.sunlight, ctx)

        # 4 decomposers + scent
        self.decomposers.step(tick)
        self.scent.step()
        fa.decay_corpses()

        # 5-8 fauna
        rows = fa.alive_idx
        if len(rows):
            stats = fa.build_stats(rows, self._world_ctx(rows, ctx))
            inp, cy, cx, prey, prey_d, threat, threat_d = fa.perceive(rows, ctx, stats)
            out = fa.brain.forward(rows, inp)
            fa.last_inputs, fa.last_outputs = inp, out
            fa.act(rows, out, cy, cx, prey, prey_d, ctx, stats, tick)
            fa.metabolize(rows, ctx, stats, tick)
            fa._refresh()

        # 9 housekeeping
        self.tick = tick + 1
        self._housekeeping(self.tick)

        dt = time.perf_counter() - t0
        self._tick_times.append(dt)
        if len(self._tick_times) > 60:
            self._tick_times.pop(0)
        avg = sum(self._tick_times) / len(self._tick_times)
        self.tps = 1.0 / avg if avg > 0 else 0.0

    def _world_ctx(self, rows, ctx) -> dict:
        wr = self.world
        cy = np.clip(self.fauna.y[rows].astype(np.int32), 0, wr.G - 1)
        cx = np.clip(self.fauna.x[rows].astype(np.int32), 0, wr.G - 1)
        return {"is_night": ctx["is_night"], "season": ctx["season"],
                "biome": wr.biome[cy, cx], "moisture": wr.moisture[cy, cx],
                "temp": wr.temperature[cy, cx],
                "in_water": wr.water_depth[cy, cx] > 0.05}

    def _housekeeping(self, tick: int) -> None:
        cfg = self.cfg
        if self.predator_waves > 0 and tick >= self.next_predator_tick:
            h, o, _ = self.fauna.trophic_counts()
            # A density, not a count: 600 prey is a crowd on a 192 grid and a rumour on a
            # 384 one.  The tick floor stops the first wave firing on the founder stock
            # itself, before the herbivores have had a single generation to establish.
            need = float(cfg.sim.get("predator_seed_prey_density", 0.0115)) * (self.world.G ** 2)
            if (h + o) >= need or tick >= self.pending_predators:
                # One big wave is a single gamble: it overshoots the local prey, crashes,
                # and either the survivors recover or the tier is gone for good.  Several
                # smaller waves at fresh hotspots are several independent chances.
                total = int(np.clip(float(cfg.sim.get("predator_seed_frac", 0.12)) * (h + o),
                                    30, 1500))
                per = max(10, total // max(1, self.predator_waves_total))
                n = self.fauna.seed_founders(tick, only={"hunter"},
                                             at=self.fauna.prey_hotspot(), count=per)
                self.predator_waves -= 1
                self.next_predator_tick = tick + int(cfg.sim.get("predator_wave_gap", 900))
                if self.predator_waves == 0:
                    self.pending_predators = -1
                wave = self.predator_waves_total - self.predator_waves
                self.log_event(
                    "world",
                    f"Something learns to hunt (wave {wave} of "
                    f"{self.predator_waves_total}): {n} predators appear among herds "
                    f"{h + o} strong.")
        every = int(cfg.sim["housekeeping_every"])
        if tick % int(cfg.world["erosion_interval"]) == 0:
            self.world.erode()
        if tick % int(cfg.speciation["interval"]) == 0:
            news = self.speciation.update(tick)
            for n in news:
                self.stats.mark(tick, "speciation")
        if tick % every == 0:
            self.stats.sample(tick)
            self.chronicle.flush()
            self._season_notes(tick)
        if tick % int(cfg.sim["intervention_every"]) == 0:
            self.intervention.poll(tick)
        if tick % int(cfg.sim["summary_every"]) == 0:
            self.write_summary()
        if tick % int(cfg.sim["snapshot_every"]) == 0:
            self._snapshot(tick)
        if (self._ckpt_request is not None
                or time.time() - self._ckpt_last > float(cfg.sim["checkpoint_seconds"])):
            label = self._ckpt_request
            self._ckpt_request = None
            self.save(label)

    def _season_notes(self, tick: int) -> None:
        tpy = int(self.cfg.weather["ticks_per_year"])
        if tick % tpy == 0 and tick > 0:
            y = self.weather.year(tick)
            h, o, c = self.fauna.trophic_counts()
            self.log_event("season",
                           f"Year {y} begins. Flora {self.flora.biomass.sum():.0f}; "
                           f"{h} herbivores, {o} omnivores, {c} carnivores across "
                           f"{len(self.speciation.living())} living species.")
            self.save(f"year_{y:04d}")

    # ------------------------------------------------------------------ output
    def write_summary(self) -> dict:
        path = os.path.join(self.root, "state", "summary.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with self.lock:
            self.last_summary = self.stats.write_summary(self.tick, path)
        return self.last_summary

    def _snapshot(self, tick: int) -> None:
        d = os.path.join(self.root, "state", "snapshots")
        os.makedirs(d, exist_ok=True)
        try:
            self.render.snapshot(os.path.join(d, f"t{tick:09d}.png"))
        except Exception:
            pass

    # ------------------------------------------------------------- checkpoint
    def request_checkpoint(self, label: str | None = None) -> None:
        self._ckpt_request = label or ""

    def save(self, label: str | None = None) -> str:
        """Never raises: a world that dies because one checkpoint could not be written
        is worse than a world with one missing checkpoint."""
        if not self.checkpoints_enabled:
            return ""
        try:
            with self.lock:
                self.chronicle.flush()
                p = ckpt.save(self, self.root, label or None)
                self._ckpt_last = time.time()
            self._ckpt_fails = 0
            return p
        except ckpt.StaleSaveRefused as e:
            # not a failure: this run is deliberately not allowed to clobber a longer one
            self.checkpoints_enabled = False
            self._ckpt_last = time.time()
            self.log_event("checkpoint",
                           f"Checkpointing disabled for this run: {e}")
            return ""
        except Exception as e:
            self._ckpt_fails += 1
            self._ckpt_last = time.time()
            self.log_event("checkpoint",
                           f"WARNING: could not write the checkpoint "
                           f"({e.__class__.__name__}: {str(e)[:160]}). The world keeps "
                           f"running; {self._ckpt_fails} consecutive failure(s).")
            return ""

    def resume(self) -> int:
        with self.lock:
            t = ckpt.load(self, self.root)
            self.seeded = True
            self.render = Renderer(self)
            self.events.fauna = self.fauna
            self.events.flora = self.flora
            self.speciation.fauna = self.fauna
            self.speciation._rebuild_cols()
            self.fauna.flora = self.flora
            self.fauna.scent = self.scent
        self.log_event("checkpoint", f"World resumed from checkpoint at tick {t}.")
        return t

    # ---------------------------------------------------------- runtime genes
    def runtime_gene_list(self):
        out = []
        for g in self.fauna.schema.runtime_genes():
            out.append(("fauna", g))
        for g in self.flora.genome.runtime_genes():
            out.append(("flora", g))
        return out

    def runtime_gene_defs(self) -> list[dict]:
        return [{"kingdom": k, **g.to_json()} for k, g in self.runtime_gene_list()]

    def restore_runtime_genes(self, defs: list[dict]) -> None:
        # schemas are restored wholesale by checkpoint.load; just recompile the engines
        self.fauna.effects.recompile()
        self.flora.recompute_effects()

    # ------------------------------------------------------------------ loop
    def run_forever(self) -> None:
        cfg = self.cfg
        last_broadcast = 0.0
        while self.running:
            if cfg.sim["paused"]:
                time.sleep(0.05)
                self._maybe_broadcast(force=True)
                continue
            speed = max(1, int(cfg.sim["speed"]))
            t0 = time.perf_counter()
            with self.lock:
                for _ in range(speed):
                    self.step()
                    if cfg.sim["paused"]:
                        break
            if self.tps_cap > 0:
                want = speed / self.tps_cap
                slack = want - (time.perf_counter() - t0)
                if slack > 0:
                    time.sleep(slack)
            else:
                time.sleep(0)      # yield to the server thread
            self._maybe_broadcast()

    def _maybe_broadcast(self, force: bool = False) -> None:
        fps = float(self.cfg.sim["target_fps"])
        if fps <= 0:
            return
        now = time.time()
        if not force and now - getattr(self, "_last_frame", 0.0) < 1.0 / fps:
            return
        self._last_frame = now
        self.frame_seq += 1
        for cb in list(self.frame_listeners):
            try:
                cb(self.frame_seq)
            except Exception:
                pass

    def shutdown(self) -> None:
        self.running = False
        try:
            self.log_event("checkpoint", "Clean shutdown; world saved.")
            self.save()
        except Exception:
            pass
        if self.monitor:
            self.monitor.stop()
