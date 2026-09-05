"""Entry point: arg parsing, staged resource test, sim thread + uvicorn server."""
from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import threading
import time

import uvicorn

from . import checkpoint as ckpt
from . import fields
from .config import Config
from .monitor import Monitor
from .sim import Sim, ROOT

STAGES = [
    {"name": "small",  "size": 192, "max_pop": 5000,  "founders": 45},
    {"name": "medium", "size": 288, "max_pop": 10000, "founders": 70},
    {"name": "full",   "size": 384, "max_pop": 20000, "founders": 110},
]


def parse_args(argv=None):
    p = argparse.ArgumentParser("primordia", description="A closed evolving world.")
    p.add_argument("--config", default=None, help="extra JSON config layered on defaults")
    p.add_argument("--resume", action="store_true", help="restore state/checkpoint_latest")
    p.add_argument("--fresh", action="store_true", help="ignore any existing checkpoint")
    p.add_argument("--stage-test", action="store_true",
                   help="run the staged resource test and exit (PLAN 10)")
    p.add_argument("--stage-seconds", type=float, default=60.0)
    p.add_argument("--size", type=int, default=None, help="override world.size")
    p.add_argument("--max-pop", type=int, default=None)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--headless", action="store_true", help="no web server")
    p.add_argument("--ticks", type=int, default=0, help="headless: run N ticks then exit")
    p.add_argument("--no-monitor", action="store_true")
    p.add_argument("--report", default=None, help="headless: write a run report here")
    return p.parse_args(argv)


def build_config(args) -> Config:
    over: dict = {}
    if args.size:
        over.setdefault("world", {})["size"] = args.size
    if args.max_pop:
        over.setdefault("fauna", {})["max_pop"] = args.max_pop
    if args.seed is not None:
        over["seed"] = args.seed
    if args.port:
        over.setdefault("server", {})["port"] = args.port
    return Config.load(args.config, over)



def port_holder(port: int) -> str:
    """Best-effort description of whatever already owns a port."""
    try:
        out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True,
                             timeout=6).stdout
    except Exception:
        return ""
    for line in out.splitlines():
        if f":{port} " in line and "LISTENING" in line.upper():
            pid = line.split()[-1]
            name = ""
            try:
                t = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                                   capture_output=True, text=True, timeout=6).stdout
                name = t.split()[0] if t.strip() else ""
            except Exception:
                pass
            return f"PID {pid}" + (f" ({name})" if name else "")
    return ""


def port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


# --------------------------------------------------------------------- staging
def stage_test(args) -> int:
    """Run each stage for N seconds and print a verdict table.  Never full-launches
    a configuration this box cannot carry."""
    base = build_config(args)
    caps = base.monitor
    rows = []
    print(f"\nPRIMORDIA staged resource test  ({args.stage_seconds:.0f}s per stage)")
    print(f"caps: VRAM<{caps['vram_cap_gb']}GB  CPU<{caps['cpu_cap_pct']}%  "
          f"RAM<{caps['ram_cap_gb']}GB  GPU<{caps['gpu_temp_cap_c']}C")
    print(f"field backend: {fields.init_backend(base.get('device', 'auto'))}\n")
    for st in STAGES:
        cfg = build_config(args)
        cfg.set("world.size", st["size"])
        cfg.set("fauna.max_pop", st["max_pop"])
        cfg.set("fauna.founders_per_type", st["founders"])
        cfg.set("sim.checkpoint_seconds", 10 ** 9)
        cfg.set("sim.snapshot_every", 10 ** 9)
        cfg.set("sim.summary_every", 10 ** 9)
        sim = Sim(cfg, ROOT, with_monitor=True)
        # a benchmark must never touch the running world's saved state
        sim.checkpoints_enabled = False
        sim.monitor.reset_peak()
        sim.monitor.start()
        print(f"  [{st['name']:6s}] {st['size']}^2 grid, cap {st['max_pop']} ... ", end="", flush=True)
        t_boot = time.time()
        sim.bootstrap()
        boot = time.time() - t_boot
        t0 = time.time()
        ticks = 0
        while time.time() - t0 < args.stage_seconds:
            sim.step()
            ticks += 1
        w = sim.monitor.window(args.stage_seconds + 5)
        sim.monitor.stop()
        tps = ticks / max(1e-6, time.time() - t0)
        verdict = []
        if w.get("vram_max", 0) > float(caps["vram_cap_gb"]):
            verdict.append("VRAM")
        if w.get("cpu_avg", 0) > float(caps["cpu_cap_pct"]):
            verdict.append("CPU")
        if w.get("ram_max", 0) > float(caps["ram_cap_gb"]):
            verdict.append("RAM")
        if w.get("gpu_temp_max", 0) > float(caps["gpu_temp_cap_c"]):
            verdict.append("GPUTEMP")
        ok = not verdict
        rows.append({"stage": st["name"], "size": st["size"], "max_pop": st["max_pop"],
                     "pop": sim.fauna.pop, "tps": tps, "boot_s": boot,
                     "cpu_avg": w.get("cpu_avg", 0), "cpu_max": w.get("cpu_max", 0),
                     "ram_max": w.get("ram_max", 0), "vram_max": w.get("vram_max", 0),
                     "gpu_temp": w.get("gpu_temp_max", 0), "ok": ok,
                     "fail": ",".join(verdict) or "-"})
        print("PASS" if ok else f"FAIL ({','.join(verdict)})")
        del sim

    print("\n" + "-" * 96)
    print(f"{'stage':8s} {'grid':>6s} {'cap':>7s} {'pop':>7s} {'tps':>8s} {'boot s':>7s} "
          f"{'cpu avg':>8s} {'cpu max':>8s} {'ram GB':>7s} {'vram GB':>8s} {'gpu C':>6s}  verdict")
    print("-" * 96)
    for r in rows:
        print(f"{r['stage']:8s} {r['size']:>5d}² {r['max_pop']:>7d} {r['pop']:>7d} "
              f"{r['tps']:>8.1f} {r['boot_s']:>7.1f} {r['cpu_avg']:>8.1f} {r['cpu_max']:>8.1f} "
              f"{r['ram_max']:>7.2f} {r['vram_max']:>8.2f} {r['gpu_temp']:>6.0f}  "
              f"{'PASS' if r['ok'] else 'FAIL ' + r['fail']}")
    print("-" * 96)
    passing = [r for r in rows if r["ok"]]
    if not passing:
        print("\nNo stage passed.  Do NOT launch a long run on this box as configured.")
        return 1
    best = passing[-1]
    print(f"\nRecommended full-launch configuration: {best['stage']} "
          f"({best['size']}² grid, max_pop {best['max_pop']}, ~{best['tps']:.0f} ticks/s)")
    print(f"  python -m primordia.main --size {best['size']} --max-pop {best['max_pop']}")
    if len(passing) < len(rows):
        print(f"  ({len(rows) - len(passing)} larger stage(s) exceeded the caps and are refused.)")
    path = os.path.join(ROOT, "state", "stage_test.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"PRIMORDIA staged resource test  {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"backend {fields.backend()}  caps {dict(caps)}\n\n")
        for r in rows:
            f.write(f"{r}\n")
        f.write(f"\nrecommended: --size {best['size']} --max-pop {best['max_pop']}\n")
    print(f"  table written to {path}")
    return 0


# ------------------------------------------------------------------------ main
def main(argv=None) -> int:
    args = parse_args(argv)
    if args.stage_test:
        return stage_test(args)

    cfg = build_config(args)

    # Bind-check before touching the world.  A viewer that fails to bind *after* the
    # resume has already advanced and re-saved the world is a confusing way to lose a
    # run: the process exits non-zero having done real work.  Refuse up front instead.
    if not args.headless:
        host, port = cfg.server["host"], int(cfg.server["port"])
        if not port_free(host, port):
            who = port_holder(port)
            print(f"[primordia] port {port} on {host} is already in use"
                  + (f" by {who}" if who else "") + ".")
            print(f"[primordia] the world was NOT loaded and nothing was changed. Either "
                  f"stop that process, or start this one on another port with "
                  f"--port <n>.")
            return 2

    # A checkpoint describes a world of a particular size.  Resuming it into a simulation
    # built at some other size loads the arrays and then dies on a shape mismatch several
    # ticks later, so the saved world's geometry wins over anything on the command line.
    if args.resume and not args.fresh and ckpt.exists(ROOT):
        try:
            head = ckpt.load_meta(ROOT)
            saved = head.get("config", {})
            for path, label in (("world.size", "--size"),
                                ("fauna.max_pop", "--max-pop")):
                sec, key = path.split(".")
                want = saved.get(sec, {}).get(key)
                if path == "fauna.max_pop":
                    # the allocated capacity, not the config value: the watchdog lowers
                    # max_pop under load and that lowered number is what gets saved, while
                    # the arrays on disk are still the size they were allocated at
                    want = head.get("fauna", {}).get("cap", want)
                if want is None:
                    continue
                have = cfg.get(path)
                if have != want:
                    print(f"[primordia] {label} {have} ignored: the saved world is "
                          f"{want}; resuming it as it was")
                cfg.set(path, want)
        except Exception as e:
            print(f"[primordia] could not read the checkpoint header ({e}); "
                  f"starting fresh instead")
            args.resume = False

    backend = fields.init_backend(cfg.get("device", "auto"))
    sim = Sim(cfg, ROOT, with_monitor=not args.no_monitor)

    resumed = False
    if args.resume and not args.fresh:
        if ckpt.exists(ROOT):
            t = sim.resume()
            print(f"[primordia] resumed at tick {t} ({sim.fauna.pop} creatures, "
                  f"{len(sim.speciation.living())} species)")
            resumed = True
        else:
            print("[primordia] --resume requested but no checkpoint found; starting fresh")
    if not resumed:
        print(f"[primordia] generating a new world ({sim.world.G}² cells, "
              f"seed {cfg['seed']}, backend {backend}, "
              f"fields via {sim.field_path} — {fields.field_note()}) ...")
        t0 = time.time()
        sim.bootstrap()
        print(f"[primordia] bootstrapped in {time.time() - t0:.1f}s: "
              f"{int((sim.flora.biomass > 1e-3).sum())} plants, {sim.fauna.pop} creatures")

    if sim.monitor:
        sim.monitor.start()

    stop = threading.Event()

    def shutdown(*_):
        if stop.is_set():
            return
        stop.set()
        print("\n[primordia] shutting down; saving world ...")
        sim.shutdown()

    signal.signal(signal.SIGINT, lambda *a: (shutdown(), sys.exit(0)))
    try:
        signal.signal(signal.SIGTERM, lambda *a: (shutdown(), sys.exit(0)))
    except (ValueError, AttributeError):
        pass

    if args.headless:
        n = args.ticks or 10 ** 12
        try:
            for _ in range(n):
                sim.step()
        except KeyboardInterrupt:
            pass
        if args.report:
            write_report(sim, args.report)
        shutdown()
        return 0

    thread = threading.Thread(target=sim.run_forever, name="sim", daemon=True)
    thread.start()

    from .server import create_app
    app = create_app(sim)
    host = cfg.server["host"]
    port = int(cfg.server["port"])
    print(f"[primordia] viewer at http://{host}:{port}")
    try:
        uvicorn.run(app, host=host, port=port, log_level="warning", access_log=False)
    finally:
        shutdown()
    return 0


def write_report(sim, path: str) -> None:
    import json
    d = sim.stats.summary(sim.tick)
    d["series"] = sim.stats.series(400)
    d["stage"] = {"grid": sim.world.G, "max_pop": sim.fauna.cap}
    if sim.monitor:
        d["resource_window"] = sim.monitor.window(10 ** 6)
        d["resource_peak"] = sim.monitor.peak
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    print(f"[primordia] report written to {path}")


if __name__ == "__main__":
    raise SystemExit(main())
