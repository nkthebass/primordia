"""Whole-world save/load: npz of every array + JSON sidecar of schemas and metadata."""
from __future__ import annotations

import glob
import json
import os
import shutil
import time

import numpy as np

LATEST = "checkpoint_latest"
ROTATIONS = 3
STALE_GUARD_TICKS = 5000     # slack so a normal resume-and-continue is never blocked


def _state_dir(root: str) -> str:
    d = os.path.join(root, "state")
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, "archive"), exist_ok=True)
    return d


class StaleSaveRefused(Exception):
    """Raised when a save would replace a checkpoint from a much longer-lived world."""


def save(sim, root: str, label: str | None = None, force: bool = False) -> str:
    d = _state_dir(root)
    base = os.path.join(d, LATEST)

    # A benchmark or a test run pointed at the default state/ directory will happily
    # save over a world that has been going for hundreds of sim-years.  Refuse, loudly,
    # unless the caller says it means it.
    if not force and os.path.exists(base + ".json"):
        try:
            with open(base + ".json", "r", encoding="utf-8") as f:
                existing = int(json.load(f).get("tick", 0))
        except Exception:
            existing = 0
        if existing > int(sim.tick) + STALE_GUARD_TICKS:
            raise StaleSaveRefused(
                f"refusing to overwrite state/{LATEST} at tick {existing} with a save at "
                f"tick {sim.tick}; this run is {existing - int(sim.tick)} ticks behind the "
                f"world already saved there. Point the run at its own root directory, set "
                f"sim.checkpoints_enabled = False, or save with force=True.")
    arrays: dict = {}
    for part in (sim.world, sim.weather, sim.flora, sim.decomposers, sim.fauna,
                 sim.scent, sim.events):
        arrays.update(part.state())
    meta = {
        "version": 2,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tick": int(sim.tick),
        "config": sim.cfg.as_dict(),
        "world": sim.world.meta(),
        "weather": sim.weather.meta(),
        "flora": sim.flora.meta(),
        "fauna": sim.fauna.meta(),
        "events": sim.events.meta(),
        "speciation": sim.speciation.meta(),
        "chronicle": sim.chronicle.meta(),
        "stats": sim.stats.meta(),
        "rng": _rng_state(sim.rng),
        "runtime_genes": sim.runtime_gene_defs(),
        "pending_predators": int(sim.pending_predators),
    }
    # pid-tagged temp names: two processes sharing a state/ directory must not fight
    # over the same scratch file
    tmp_npz = f"{base}.tmp{os.getpid()}.npz"   # np.savez appends .npz if it is missing
    tmp_json = f"{base}.tmp{os.getpid()}.json"
    with open(tmp_npz, "wb") as fh:
        np.savez_compressed(fh, **arrays)
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(meta, f)
    # rotate
    for i in range(ROTATIONS - 1, 0, -1):
        for ext in (".npz", ".json"):
            a, b = f"{base}.{i}{ext}", f"{base}.{i + 1}{ext}"
            if os.path.exists(a):
                os.replace(a, b)
    for ext in (".npz", ".json"):
        if os.path.exists(base + ext):
            os.replace(base + ext, f"{base}.1{ext}")
    _replace_with_retry(tmp_npz, base + ".npz")
    _replace_with_retry(tmp_json, base + ".json")
    if label:
        for ext in (".npz", ".json"):
            shutil.copyfile(base + ext, os.path.join(d, "archive", f"{label}{ext}"))
    return base + ".npz"


def _replace_with_retry(src: str, dst: str, attempts: int = 6) -> None:
    """os.replace, retried: on Windows a scanner or a second process reading the
    previous checkpoint can hold the target open for a moment."""
    for i in range(attempts):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if i == attempts - 1:
                raise
            time.sleep(0.25 * (i + 1))


def _rng_state(rng) -> dict:
    st = rng.bit_generator.state
    return json.loads(json.dumps(st, default=lambda o: o.tolist()
                                 if hasattr(o, "tolist") else str(o)))


def exists(root: str) -> bool:
    base = os.path.join(root, "state", LATEST)
    return os.path.exists(base + ".npz") and os.path.exists(base + ".json")


def load_meta(root: str) -> dict:
    base = os.path.join(root, "state", LATEST)
    with open(base + ".json", "r", encoding="utf-8") as f:
        return json.load(f)


def load(sim, root: str) -> int:
    base = os.path.join(root, "state", LATEST)
    meta = load_meta(root)
    npz = np.load(base + ".npz", allow_pickle=False)
    sim.world.load(npz, meta["world"])
    sim.weather.load(npz, meta["weather"])
    sim.flora.load(npz, meta["flora"])
    sim.decomposers.load(npz, {})
    sim.fauna.load(npz, meta["fauna"])
    sim.scent.load(npz, {})
    sim.events.load(npz, meta["events"])
    sim.speciation.load(meta["speciation"])
    sim.chronicle.load(meta["chronicle"])
    sim.stats.load(meta["stats"])
    sim.restore_runtime_genes(meta.get("runtime_genes", []))
    try:
        st = meta.get("rng")
        if st:
            st = dict(st)
            if "state" in st and isinstance(st["state"], dict):
                for k, v in st["state"].items():
                    if isinstance(v, list):
                        st["state"][k] = np.array(v, dtype=np.uint64)
            sim.rng.bit_generator.state = st
    except Exception:
        pass
    sim.pending_predators = int(meta.get("pending_predators", -1))
    sim.tick = int(meta["tick"])
    return sim.tick


def list_archives(root: str) -> list[str]:
    d = os.path.join(root, "state", "archive")
    return sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(d, "*.npz")))
