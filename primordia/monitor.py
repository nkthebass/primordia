"""Resource watchdog: psutil + NVML sampling, staged ramp verdicts, throttle ladder.

This box is the owner's daily desktop.  The rule is: never make it unusable.
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque

import psutil

_nvml = None
_nvml_handle = None


def _init_nvml():
    global _nvml, _nvml_handle
    if _nvml is not None:
        return _nvml
    try:
        import pynvml
        pynvml.nvmlInit()
        _nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        _nvml = pynvml
    except Exception:
        _nvml = False
    return _nvml


def gpu_sample() -> dict:
    nv = _init_nvml()
    if not nv:
        return {"vram_gb": 0.0, "gpu_util": 0.0, "gpu_temp_c": 0.0, "gpu": "n/a"}
    try:
        mem = nv.nvmlDeviceGetMemoryInfo(_nvml_handle)
        util = nv.nvmlDeviceGetUtilizationRates(_nvml_handle)
        temp = nv.nvmlDeviceGetTemperature(_nvml_handle, nv.NVML_TEMPERATURE_GPU)
        name = nv.nvmlDeviceGetName(_nvml_handle)
        if isinstance(name, bytes):
            name = name.decode()
        return {"vram_gb": mem.used / 1e9, "gpu_util": float(util.gpu),
                "gpu_temp_c": float(temp), "gpu": name}
    except Exception:
        return {"vram_gb": 0.0, "gpu_util": 0.0, "gpu_temp_c": 0.0, "gpu": "n/a"}


class Monitor:
    THROTTLE_STEPS = ("lower_max_pop", "halve_broadcast", "cap_tps", "pause")

    def __init__(self, cfg, root: str, sim=None):
        self.cfg = cfg
        self.sim = sim
        self.root = root
        self.proc = psutil.Process(os.getpid())
        self.ring: deque = deque(maxlen=900)
        self.breaches = 0
        self.throttle_level = 0
        self.peak = {"cpu_pct": 0.0, "ram_gb": 0.0, "vram_gb": 0.0, "gpu_temp_c": 0.0}
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.logfile = os.path.join(root, "state", "resources.log")
        os.makedirs(os.path.dirname(self.logfile), exist_ok=True)
        self.proc.cpu_percent(None)
        psutil.cpu_percent(None)

    # ------------------------------------------------------------------ thread
    def start(self) -> None:
        if self._thread:
            return
        self._thread = threading.Thread(target=self._loop, name="monitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        interval = float(self.cfg.monitor["sample_interval"])
        while not self._stop.wait(interval):
            try:
                self.sample()
            except Exception:
                pass

    # ------------------------------------------------------------------ sample
    def sample(self) -> dict:
        cpu_sys = psutil.cpu_percent(None)
        vm = psutil.virtual_memory()
        try:
            ram_gb = self.proc.memory_info().rss / 1e9
        except Exception:
            ram_gb = 0.0
        g = gpu_sample()
        s = {"t": time.time(), "cpu_pct": float(cpu_sys),
             "ram_gb": round(ram_gb, 3),
             "ram_sys_pct": float(vm.percent), **g}
        self.ring.append(s)
        for k in self.peak:
            self.peak[k] = max(self.peak[k], float(s.get(k, 0.0)))
        self._check(s)
        try:
            with open(self.logfile, "a", encoding="utf-8") as f:
                f.write(f"{s['t']:.0f} cpu={s['cpu_pct']:.0f} ram={s['ram_gb']:.2f} "
                        f"vram={s['vram_gb']:.2f} gputemp={s['gpu_temp_c']:.0f} "
                        f"gpuutil={s['gpu_util']:.0f} throttle={self.throttle_level}\n")
        except Exception:
            pass
        return s

    def breached(self, s: dict) -> list[str]:
        m = self.cfg.monitor
        out = []
        if s["cpu_pct"] > float(m["cpu_cap_pct"]):
            out.append(f"CPU {s['cpu_pct']:.0f}% > {m['cpu_cap_pct']}%")
        if s["ram_gb"] > float(m["ram_cap_gb"]):
            out.append(f"RAM {s['ram_gb']:.1f}GB > {m['ram_cap_gb']}GB")
        if s["vram_gb"] > float(m["vram_cap_gb"]):
            out.append(f"VRAM {s['vram_gb']:.1f}GB > {m['vram_cap_gb']}GB")
        if s["gpu_temp_c"] > float(m["gpu_temp_cap_c"]):
            out.append(f"GPU {s['gpu_temp_c']:.0f}C > {m['gpu_temp_cap_c']}C")
        return out

    def _check(self, s: dict) -> None:
        b = self.breached(s)
        if b:
            self.breaches += 1
        else:
            self.breaches = max(0, self.breaches - 1)
        if self.breaches >= int(self.cfg.monitor["breach_limit"]) and self.sim:
            self.breaches = 0
            self._throttle(b)
        elif self.breaches == 0 and self.throttle_level > 0 and self.sim:
            # recovered: back off the ladder one step
            self.throttle_level -= 1
            self.sim.log_event("resource", "Resources back under caps; easing throttle "
                                           f"to level {self.throttle_level}.")

    def _throttle(self, reasons: list[str]) -> None:
        sim = self.sim
        lvl = self.throttle_level
        why = ", ".join(reasons)
        if lvl == 0:
            newcap = int(sim.fauna.cap * 0.9)
            self.cfg.set("fauna.max_pop", newcap)
            sim.log_event("resource", f"Resource caps breached ({why}); "
                                      f"lowering max population to {newcap}.")
        elif lvl == 1:
            self.cfg.set("sim.target_fps", max(0.5, float(self.cfg.sim["target_fps"]) / 2))
            sim.log_event("resource", f"Still over caps ({why}); halving viewer frame rate.")
        elif lvl == 2:
            sim.tps_cap = max(4.0, sim.tps_cap * 0.5 if sim.tps_cap else 15.0)
            sim.log_event("resource", f"Still over caps ({why}); capping simulation to "
                                      f"{sim.tps_cap:.0f} ticks/s.")
        else:
            self.cfg.set("sim.paused", True)
            sim.log_event("resource", f"ALERT: resource caps still breached ({why}). "
                                      f"Simulation paused to protect the desktop.")
        self.throttle_level = min(3, lvl + 1)

    # ------------------------------------------------------------------ report
    def snapshot(self) -> dict:
        if not self.ring:
            return self.sample()
        s = dict(self.ring[-1])
        s["throttle_level"] = self.throttle_level
        s["peak"] = dict(self.peak)
        s.pop("t", None)
        return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()}

    def window(self, seconds: float = 60.0) -> dict:
        now = time.time()
        rows = [r for r in self.ring if now - r["t"] <= seconds] or list(self.ring)[-1:]
        if not rows:
            return {}
        def mx(k): return max(float(r.get(k, 0.0)) for r in rows)
        def av(k): return sum(float(r.get(k, 0.0)) for r in rows) / len(rows)
        return {"cpu_max": mx("cpu_pct"), "cpu_avg": av("cpu_pct"),
                "ram_max": mx("ram_gb"), "vram_max": mx("vram_gb"),
                "gpu_temp_max": mx("gpu_temp_c"), "gpu_util_avg": av("gpu_util"),
                "samples": len(rows)}

    def warnings(self) -> list[str]:
        if not self.ring:
            return []
        w = self.breached(self.ring[-1])
        if self.throttle_level:
            w.append(f"throttle level {self.throttle_level} active")
        return w

    def reset_peak(self) -> None:
        self.peak = {k: 0.0 for k in self.peak}
