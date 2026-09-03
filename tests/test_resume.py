"""Checkpoint / resume regressions.  Plain script, no test framework:

    .venv\\Scripts\\python.exe tests\\test_resume.py

Both cases below were live bugs that only surfaced thousands of ticks after the resume
that caused them, which is exactly why they are worth pinning down here.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primordia import checkpoint as ckpt          # noqa: E402
from primordia.config import Config               # noqa: E402
from primordia.genetics import Gene               # noqa: E402
from primordia.sim import Sim                     # noqa: E402

FAILURES: list[str] = []


def check(cond: bool, label: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'}  {label}")
    if not cond:
        FAILURES.append(label)


def fresh(root: str, **over) -> Sim:
    cfg = Config.load(None, {"world": {"size": 128}, "fauna": {"max_pop": 3000},
                             "sim": {"green_up_ticks": 300, "checkpoint_seconds": 1e9,
                                     "snapshot_every": 10 ** 9, "summary_every": 10 ** 9},
                             **over})
    s = Sim(cfg, root=root, with_monitor=False)
    s.bootstrap()
    return s


def test_capacity_mismatch() -> None:
    """A saved world's capacity wins over config.

    The watchdog lowers fauna.max_pop under load and that lowered value is what lands in
    the checkpoint's config, while the arrays on disk are still the size they were
    allocated at.  Rebuilding at the config number left one derived array short, and the
    first birth past its end crashed the run thousands of ticks later.
    """
    print("capacity mismatch between saved config and saved arrays")
    root = tempfile.mkdtemp(prefix="prim_cap_")
    try:
        s = fresh(root)
        for _ in range(200):
            s.step()
        s.save()
        saved_cap = s.fauna.cap

        # simulate the watchdog having throttled the cap before the save
        meta_path = os.path.join(root, "state", "checkpoint_latest.json")
        import json
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        meta["config"]["fauna"]["max_pop"] = saved_cap - 500
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f)

        cfg = Config.load(None, {"world": {"size": 128},
                                 "fauna": {"max_pop": saved_cap - 500},
                                 "sim": {"checkpoint_seconds": 1e9,
                                         "snapshot_every": 10 ** 9,
                                         "summary_every": 10 ** 9}})
        s2 = Sim(cfg, root=root, with_monitor=False)
        s2.checkpoints_enabled = False
        s2.resume()
        fa = s2.fauna

        lens = {k: len(getattr(fa, k)) for k in fa.ARRAYS}
        for name in fa.DERIVED:
            lens[name] = len(getattr(fa, name))
        lens["genome"] = fa.schema.data.shape[0]
        check(set(lens.values()) == {fa.cap},
              f"every per-creature array is {fa.cap} long ({sorted(set(lens.values()))})")
        check(fa.cap == saved_cap, "capacity came from the checkpoint, not from config")

        for _ in range(400):
            s2.step()
        check(True, "400 ticks after resume without an index error")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_grid_size_mismatch() -> None:
    """Resuming into a differently-shaped world must fail loudly, not silently."""
    print("resume into a world of the wrong size")
    root = tempfile.mkdtemp(prefix="prim_grid_")
    try:
        s = fresh(root)
        for _ in range(120):
            s.step()
        s.save()

        cfg = Config.load(None, {"world": {"size": 192}, "fauna": {"max_pop": 3000}})
        s2 = Sim(cfg, root=root, with_monitor=False)
        s2.checkpoints_enabled = False
        try:
            s2.resume()
            check(False, "mismatched grid size was refused")
        except ValueError as e:
            check("128" in str(e) and "192" in str(e),
                  f"refused with both sizes named: {str(e)[:70]}...")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_runtime_gene_survives() -> None:
    """A gene added at runtime must come back with its effects and keep evolving."""
    print("runtime-added genes survive a resume")
    root = tempfile.mkdtemp(prefix="prim_gene_")
    try:
        s = fresh(root)
        for _ in range(200):
            s.step()
        s.intervention.apply({
            "type": "add_gene", "kingdom": "fauna", "name": "venom",
            "init": {"mean": 0.06, "std": 0.05}, "mut_std": 0.05,
            "effects": [{"stat": "attack_power", "op": "add", "per_unit": 0.8}]}, s.tick)
        s.intervention.apply({
            "type": "add_gene", "kingdom": "flora", "name": "waxleaf",
            "init": {"mean": 0.05, "std": 0.04}, "mut_std": 0.04,
            "effects": [{"stat": "water_efficiency", "op": "mul_per_unit",
                         "per_unit": -0.3}]}, s.tick)
        for _ in range(150):
            s.step()
        before = float(s.fauna.gene("venom", s.fauna.alive_idx).mean())
        s.save()

        cfg = Config.load(None, {"world": {"size": 128}, "fauna": {"max_pop": 3000}})
        s2 = Sim(cfg, root=root, with_monitor=False)
        s2.checkpoints_enabled = False
        s2.resume()
        check(s2.fauna.schema.has("venom"), "fauna gene restored")
        check(s2.flora.genome.has("waxleaf"), "flora gene restored")
        check(len(s2.fauna.effects._compiled) == 1, "fauna effect recompiled")
        check("water_efficiency" in s2.flora.stat_cache, "flora effect recompiled")
        after = float(s2.fauna.gene("venom", s2.fauna.alive_idx).mean())
        check(abs(after - before) < 1e-6, "gene values came back unchanged")
        for _ in range(150):
            s2.step()
        check(s2.fauna.pop >= 0, "world keeps running with the restored gene")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_stale_save_guard() -> None:
    """A short run must not overwrite a much longer-lived world."""
    print("stale-save guard")
    root = tempfile.mkdtemp(prefix="prim_stale_")
    try:
        s = fresh(root)
        s.tick = 500_000
        s.save()
        long_tick = ckpt.load_meta(root)["tick"]

        s2 = fresh(root)                       # a brand new, very young world
        s2.save()
        check(ckpt.load_meta(root)["tick"] == long_tick,
              "the older world is still on disk")
        check(not s2.checkpoints_enabled,
              "the young run disabled its own checkpointing instead of failing")
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    for fn in (test_capacity_mismatch, test_grid_size_mismatch,
               test_runtime_gene_survives, test_stale_save_guard):
        fn()
        print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILED: " + "; ".join(FAILURES))
        raise SystemExit(1)
    print("all resume checks passed")
