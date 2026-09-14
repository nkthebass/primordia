"""Recolonise a landmass whose herd has died out, while there are still donors to send.

Three consecutive worlds died the same way.  Erosion and cratering break the land into
separate masses that non-swimmers cannot cross (movement blocks water deeper than 0.25
unless swim_eff > 0.45).  Sooner or later the small herd on one island winks out.  With
nothing grazing it, that island's flora balloons -- in the year-11,900 restore it came to
hold 92% of all harvestable food in the world -- while every surviving animal overgrazes
the landmasses it is stuck on and starves.  Islands do refill on their own sometimes (the
~3,600-cell island at (228,293) emptied at 12,000 and was back to 101 animals by 12,300),
but a gap that lasts long enough closes the trap, and a check-in every eight hours of wall
clock is a thousand simulated years: far too slow to catch it.

This watches for exactly that and does the one thing a game-master would do: send a small
founding party to the empty island, copied whole from animals that are alive right now.
It writes an ordinary intervention file and never touches the simulation otherwise --
interventions stay data, never code.

The genome is deliberately an EMPTY object.  With living donors, seed_organism copies a
resident whole -- body, runtime genes and all 167 brain weights -- and an empty archetype
edits nothing.  That is the only seeding path that has worked in this world; composed
genomes and random brains failed ten times in a row.

If every animal is dead there are no donors and this does nothing but log: founding into an
empty world is a decision for a human or the game-master, not for a timer.

Run detached, next to the simulation:

    Start-Process -FilePath '.venv\\Scripts\\python.exe' -ArgumentList 'tools\\island_watch.py' -WindowStyle Hidden
"""
from __future__ import annotations

import io
import json
import os
import time
import urllib.request

import numpy as np
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CKPT = os.path.join(ROOT, "state", "checkpoint_latest")
IV_DIR = os.path.join(ROOT, "interventions")
STATE = os.path.join(ROOT, "state", "island_watch.json")
LOG = os.path.join(ROOT, "state", "island_watch.log")
API = "http://127.0.0.1:8710/api/summary"

POLL_S = 120              # wall-clock seconds between looks
MIN_CELLS = 1000          # landmasses smaller than this are not worth a herd
MIN_FOOD = 100.0          # harvestable biomass that makes an empty landmass worth settling
MIN_DONORS = 40           # seed_organism only copies residents when >= 20 are alive
COOLDOWN_TICKS = 200_000  # 100 simulated years before the same landmass is seeded again
MATCH_CELLS = 40          # earlier seedings this close count as the same landmass
PARTY = 40                # founders per seeding; islands here have held 35-120 animals
WALK_DEPTH = 0.2          # where spawn() and grazers treat ground as walkable


def log(msg: str) -> None:
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state() -> dict:
    try:
        return json.load(io.open(STATE, encoding="utf-8"))
    except Exception:
        return {"seeded": {}}


def save_state(s: dict) -> None:
    tmp = STATE + ".tmp"
    io.open(tmp, "w", encoding="utf-8").write(json.dumps(s, indent=1))
    os.replace(tmp, STATE)


def landmasses(water_depth: np.ndarray) -> np.ndarray:
    """Label walkable ground, joining masses that continue across the x-wrap seam."""
    walk = water_depth < WALK_DEPTH
    G = walk.shape[1]
    lab, _ = ndimage.label(np.concatenate([walk, walk], axis=1))
    L = lab[:, :G].copy()
    for r in range(walk.shape[0]):
        a, b = lab[r, G - 1], lab[r, G]
        if a and b and a != b:
            L[L == b] = a
    return L


def read_world():
    """The newest checkpoint, retried: the sim replaces it every few seconds."""
    for _ in range(5):
        try:
            meta = json.load(io.open(CKPT + ".json", encoding="utf-8"))
            with np.load(CKPT + ".npz") as z:
                alive = z["fauna_alive"].astype(bool)
                return meta, {
                    "x": z["fauna_x"][alive].copy(),
                    "y": z["fauna_y"][alive].copy(),
                    "water_depth": z["world_water_depth"].copy(),
                    "biomass": z["flora_biomass"].copy(),
                }
        except Exception:
            time.sleep(3)
    return None, None


def pending_interventions() -> bool:
    try:
        return any(n.endswith(".json") for n in os.listdir(IV_DIR))
    except OSError:
        return True


def check_once(state: dict) -> None:
    try:
        summary = json.load(urllib.request.urlopen(API, timeout=10))
    except Exception:
        return                                   # sim down; the check-in handles that
    if summary.get("paused"):
        return
    meta, w = read_world()
    if meta is None:
        return
    tick = int(meta["tick"])
    n = len(w["x"])
    if n == 0:
        if not state.get("logged_extinct"):
            log(f"tick {tick}: no living fauna -- no donors, leaving this to a human")
            state["logged_extinct"] = True
            save_state(state)
        return
    state["logged_extinct"] = False
    if n < MIN_DONORS or pending_interventions():
        return

    G = w["biomass"].shape[0]
    floor = float(meta.get("tuned", {}).get("fauna.graze_floor", 0.12))
    avail = np.maximum(0.0, w["biomass"] - floor)
    L = landmasses(w["water_depth"])
    sizes = np.bincount(L.ravel())
    ax = np.clip(w["x"].astype(np.int64), 0, G - 1)
    ay = np.clip(w["y"].astype(np.int64), 0, G - 1)
    occupied = np.bincount(L[ay, ax].ravel(), minlength=len(sizes))

    for c in range(1, len(sizes)):
        if sizes[c] < MIN_CELLS or occupied[c] > 0:
            continue
        mask = L == c
        food = float(avail[mask].sum())
        if food < MIN_FOOD:
            continue
        inside = ndimage.distance_transform_edt(mask)
        iy, ix = np.unravel_index(int(np.argmax(inside)), inside.shape)
        depth = float(inside.max())
        # The interior point drifts as the coast erodes, so an exact grid-square key let the
        # same island be seeded twice in 45 years (keys 14:17 and 14:18).  Treat any earlier
        # seeding within MATCH_CELLS of here -- or anywhere on this landmass -- as the same place.
        key = f"{ix // 16}:{iy // 16}"
        last = -10**12
        for k, t in state["seeded"].items():
            try:
                kx, ky = (int(v) for v in k.split(":"))
            except ValueError:
                continue
            px, py = kx * 16 + 8, ky * 16 + 8
            dx = min(abs(px - ix), G - abs(px - ix))           # x wraps
            same = (dx * dx + (py - iy) ** 2 <= MATCH_CELLS ** 2
                    or L[min(max(py, 0), G - 1), px % G] == c)
            if same:
                last = max(last, int(t))
        if tick - last < COOLDOWN_TICKS:
            continue
        radius = float(max(4.0, min(20.0, depth * 0.6)))   # keep founders on dry land
        year = tick // 2000
        others = int((occupied[1:] > 0).sum())
        note = (f"Year {year}. A landmass of {int(sizes[c])} cells centred near ({ix},{iy}) has "
                f"no animals on it and {food:.0f} harvestable biomass going ungrazed, while "
                f"{n} animals are alive on {others} other landmass(es) they cannot leave. That "
                f"is how three worlds died: an island herd winks out, the island becomes the "
                f"world's larder, and everyone else starves on overgrazed ground across water "
                f"too deep to walk. Sending {PARTY} founders copied whole from living animals, "
                f"brains included. -- tools/island_watch.py")
        items = [
            {"type": "note", "text": note},
            {"type": "seed_organism", "kingdom": "fauna", "count": PARTY,
             "x": int(ix), "y": int(iy), "radius": radius, "genome": {}},
        ]
        name = os.path.join(IV_DIR, time.strftime("%Y%m%d-%H%M%S") + "_island_watch.json")
        io.open(name, "w", encoding="utf-8", newline="\n").write(json.dumps(items))
        state["seeded"][key] = tick
        save_state(state)
        log(f"tick {tick} (year {year}): seeded {PARTY} at ({ix},{iy}) r{radius:.0f} -- "
            f"{int(sizes[c])} cells, food {food:.0f}, {n} alive elsewhere")
        return                                   # one landmass per look


def main() -> None:
    log("island_watch started")
    state = load_state()
    while True:
        try:
            check_once(state)
        except Exception as e:                   # never die on a bad read
            log(f"error: {e!r}")
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()
