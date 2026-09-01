"""FastAPI app: serves the viewer, streams PNG frames over WebSocket, exposes the
inspector / debug / control API."""
from __future__ import annotations

import asyncio
import json
import os
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response

from .events import EVENT_TYPES
from .render import OVERLAYS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VIEWER = os.path.join(ROOT, "viewer", "index.html")


def create_app(sim) -> FastAPI:
    app = FastAPI(title="PRIMORDIA", docs_url=None, redoc_url=None)
    app.state.sim = sim

    # ------------------------------------------------------------------ page
    @app.get("/", response_class=HTMLResponse)
    async def index():
        if not os.path.exists(VIEWER):
            return HTMLResponse("<h1>PRIMORDIA</h1><p>viewer/index.html missing</p>")
        return FileResponse(VIEWER)

    @app.get("/api/meta")
    async def meta():
        return {
            "G": sim.world.G, "overlays": list(OVERLAYS), "events": list(EVENT_TYPES),
            "seed": sim.cfg["seed"], "backend": _backend(),
            "max_pop": sim.fauna.cap,
            "body_genes": [g.name for g in sim.fauna.schema.genes
                           if not g.name.startswith("w")],
            "config": sim.cfg.as_dict(),
        }

    @app.get("/api/state")
    async def state():
        return _state(sim)

    @app.get("/api/series")
    async def series(points: int = 900):
        return sim.stats.series(points)

    @app.get("/api/chronicle")
    async def chronicle(n: int = 40):
        return sim.chronicle.tail(n)

    @app.get("/api/species")
    async def species():
        return sim.speciation.tree()

    @app.get("/api/summary")
    async def summary():
        return sim.last_summary or sim.stats.summary(sim.tick)

    @app.post("/api/summary/write")
    async def write_summary():
        return sim.write_summary()

    @app.get("/api/frame.png")
    async def frame(overlay: str = "none", species: int = -1, scale: int = 1):
        png = sim.render.png(overlay if overlay in OVERLAYS else "none", species,
                             max(1, min(3, scale)))
        return Response(png, media_type="image/png",
                        headers={"Cache-Control": "no-store"})

    @app.get("/api/inspect")
    async def inspect(x: float, y: float, radius: float = 8.0):
        with sim.lock:
            idx = sim.fauna.nearest_to(x, y, radius)
            if idx < 0:
                return _cell_info(sim, x, y)
            d = sim.fauna.inspect(idx)
        sp = sim.speciation.species.get(d.get("species", -1))
        if sp:
            d["species_name"] = sp.name
            d["species_rank"] = sp.rank
            d["species_hue"] = sp.hue
        d["cell"] = _cell_info(sim, x, y)
        return d

    # ---------------------------------------------------------------- control
    @app.post("/api/control")
    async def control(body: dict):
        cmd = body.get("cmd")
        with sim.lock:
            if cmd == "pause":
                sim.cfg.set("sim.paused", True)
            elif cmd == "resume":
                sim.cfg.set("sim.paused", False)
            elif cmd == "speed":
                sim.cfg.set("sim.speed", max(1, min(4096, int(body.get("value", 4)))))
            elif cmd == "fps":
                sim.cfg.set("sim.target_fps", max(0.5, min(20.0, float(body.get("value", 4)))))
            elif cmd == "checkpoint":
                sim.request_checkpoint(body.get("label"))
            elif cmd == "tune":
                sim.cfg.set(str(body["path"]), body["value"], enforce_hot=True)
                sim.log_event("tuning", f"Viewer tuned {body['path']} to {body['value']}.")
            else:
                return JSONResponse({"ok": False, "error": f"unknown cmd '{cmd}'"}, 400)
        return {"ok": True, "state": _state(sim)}

    # ------------------------------------------------------------------ debug
    @app.post("/api/debug")
    async def debug(body: dict):
        """Everything the plan requires to smoke-test a mechanic from the UI."""
        action = body.get("action")
        try:
            with sim.lock:
                if action == "event":
                    kind = body.get("event")
                    if kind not in EVENT_TYPES:
                        raise ValueError(f"unknown event '{kind}'")
                    G = sim.world.G
                    x = int(body.get("x", sim.rng.integers(0, G)))
                    y = int(body.get("y", sim.rng.integers(0, G)))
                    r = body.get("radius")
                    e = sim.events.trigger(kind, x, y, None if r in (None, "") else float(r),
                                           float(body.get("intensity", 0.8)), sim.tick)
                    sim.stats.mark(sim.tick, kind)
                    msg = f"{kind} at ({x},{y})" if e else f"{kind} failed"
                elif action == "spawn":
                    n = int(body.get("count", 20))
                    G = sim.world.G
                    x = float(body.get("x", sim.rng.integers(0, G)))
                    y = float(body.get("y", sim.rng.integers(0, G)))
                    kingdom = body.get("kingdom", "fauna")
                    if kingdom == "flora":
                        payload = {"type": "seed_organism", "kingdom": "flora",
                                   "count": n, "x": x, "y": y,
                                   "radius": float(body.get("radius", 14))}
                        msg = sim.intervention.apply(payload, sim.tick)
                    else:
                        arch = body.get("genome")
                        alien = body.get("alien", False) or arch in (None, "", "random_alien")
                        idx = sim.fauna.spawn(n, cx=x, cy=y,
                                              radius=float(body.get("radius", 14)),
                                              archetype=None if alien else arch,
                                              alien=bool(alien), tick=sim.tick)
                        msg = f"spawned {len(idx)} {'alien ' if alien else ''}creatures"
                        sim.log_event("intervention", f"Debug spawn: {msg} at ({int(x)},{int(y)}).")
                elif action == "season":
                    season = body.get("season", "summer")
                    order = ("spring", "summer", "autumn", "winter")
                    if season not in order:
                        raise ValueError("bad season")
                    tpy = int(sim.cfg.weather["ticks_per_year"])
                    year = sim.tick // tpy
                    sim.tick = year * tpy + order.index(season) * (tpy // 4)
                    msg = f"forced season to {season} (tick {sim.tick})"
                    sim.log_event("season", f"Debug: time jumped to {season}.")
                elif action == "intervention":
                    msg = sim.intervention.apply(body.get("payload") or {}, sim.tick)
                elif action == "poll_interventions":
                    res = sim.intervention.poll(sim.tick)
                    msg = f"polled: {len(res)} file(s)"
                elif action == "kill_all_fauna":
                    n = sim.fauna.pop
                    sim.fauna.die(sim.fauna.alive_idx.copy())
                    msg = f"killed {n} creatures"
                elif action == "example_interventions":
                    msg = f"wrote {sim.intervention.write_example()}"
                else:
                    raise ValueError(f"unknown debug action '{action}'")
            return {"ok": True, "msg": msg, "state": _state(sim)}
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, 400)

    @app.get("/api/interventions")
    async def interventions():
        d = sim.intervention
        def ls(p):
            try:
                return sorted(os.listdir(p))[-25:]
            except FileNotFoundError:
                return []
        return {"pending": [f for f in ls(d.dir) if f.endswith(".json")],
                "done": ls(d.done), "failed": ls(d.failed),
                "applied": d.applied_count, "failed_count": d.failed_count,
                "log": d.log[-25:]}

    @app.get("/api/resources")
    async def resources():
        if not sim.monitor:
            return {}
        return {"now": sim.monitor.snapshot(), "window": sim.monitor.window(120)}

    # -------------------------------------------------------------- websocket
    @app.websocket("/ws")
    async def ws(sock: WebSocket):
        await sock.accept()
        opts = {"overlay": "none", "species": -1, "scale": 1}
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue(maxsize=2)

        def on_frame(seq: int):
            try:
                loop.call_soon_threadsafe(queue.put_nowait, seq)
            except (asyncio.QueueFull, RuntimeError):
                pass

        sim.frame_listeners.append(on_frame)

        async def reader():
            try:
                while True:
                    msg = await sock.receive_text()
                    try:
                        d = json.loads(msg)
                    except Exception:
                        continue
                    if "overlay" in d and d["overlay"] in OVERLAYS:
                        opts["overlay"] = d["overlay"]
                    if "species" in d:
                        opts["species"] = int(d["species"])
                    if "scale" in d:
                        opts["scale"] = max(1, min(3, int(d["scale"])))
            except (WebSocketDisconnect, RuntimeError):
                pass

        rtask = asyncio.create_task(reader())
        try:
            while True:
                try:
                    await asyncio.wait_for(queue.get(), timeout=2.0)
                except asyncio.TimeoutError:
                    pass
                png = await loop.run_in_executor(
                    None, lambda: sim.render.png(opts["overlay"], opts["species"],
                                                 opts["scale"]))
                await sock.send_bytes(png)
                await sock.send_text(json.dumps({"t": "state", **_state(sim)}))
        except (WebSocketDisconnect, RuntimeError, ConnectionResetError):
            pass
        finally:
            rtask.cancel()
            try:
                sim.frame_listeners.remove(on_frame)
            except ValueError:
                pass

    return app


# ---------------------------------------------------------------------- helpers
def _backend() -> str:
    from . import fields
    note = fields.field_note()
    return f"{fields.backend()} · fields:{fields.choose_field_path((0, 0))}" + (f" ({note})" if note else "")


def _state(sim) -> dict:
    h, o, c = sim.fauna.trophic_counts()
    wx = sim.weather
    res = sim.monitor.snapshot() if sim.monitor else {}
    return {
        "tick": sim.tick, "year": wx.year(sim.tick), "season": wx.season(sim.tick),
        "day_frac": round(wx.day_frac(sim.tick), 3), "is_night": bool(wx.is_night),
        "sunlight": round(float(wx.sunlight), 3),
        "tps": round(float(sim.tps), 1), "paused": bool(sim.cfg.sim["paused"]),
        "speed": int(sim.cfg.sim["speed"]), "fps": float(sim.cfg.sim["target_fps"]),
        "pop": sim.fauna.pop, "herbivore": h, "omnivore": o, "carnivore": c,
        "flora_biomass": round(float(sim.flora.biomass.sum()), 1),
        "flora_cover": round(float((sim.flora.biomass > 1e-3).mean()), 4),
        "decomposer": round(float(sim.decomposers.density.sum()), 1),
        "carrion": round(float(sim.fauna.meat.sum()), 1),
        "fertility": round(float(sim.world.soil_fertility.mean()), 4),
        "nutrients": round(float(sim.world.nutrients.mean()), 4),
        "climate_osc": round(float(wx.climate_osc), 3),
        "temp": round(float(sim.world.temperature.mean()), 3),
        "species_living": len(sim.speciation.living()),
        "species_total": len(sim.speciation.species),
        "active_events": [e.to_json() for e in sim.events.active][:8],
        "warnings": sim.stats.warnings[:6],
        "runtime_genes": [{"kingdom": k, "name": g.name} for k, g in sim.runtime_gene_list()],
        "resources": res,
        "chronicle_count": sim.chronicle.count,
    }


def _cell_info(sim, x: float, y: float) -> dict:
    G = sim.world.G
    xi = int(max(0, min(G - 1, x)))
    yi = int(max(0, min(G - 1, y)))
    from .world import BIOME_NAMES
    fl = sim.flora
    d = {
        "x": xi, "y": yi, "biome": BIOME_NAMES[int(sim.world.biome[yi, xi])],
        "elevation": round(float(sim.world.elevation[yi, xi]), 3),
        "water_depth": round(float(sim.world.water_depth[yi, xi]), 3),
        "temperature": round(float(sim.world.temperature[yi, xi]), 3),
        "moisture": round(float(sim.world.moisture[yi, xi]), 3),
        "fertility": round(float(sim.world.soil_fertility[yi, xi]), 3),
        "nutrients": round(float(sim.world.nutrients[yi, xi]), 3),
        "microbes": round(float(sim.decomposers.density[yi, xi]), 3),
        "carrion": round(float(sim.fauna.meat[yi, xi]), 2),
        "fire": round(float(sim.events.fire[yi, xi]), 2),
        "plant_biomass": round(float(fl.biomass[yi, xi]), 3),
    }
    if fl.biomass[yi, xi] > 1e-3:
        d["plant_genome"] = {g.name: round(float(fl.genome.data[i, yi, xi]), 3)
                             for i, g in enumerate(fl.genome.genes)}
        d["plant_age"] = int(fl.age[yi, xi])
    return d
