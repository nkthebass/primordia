"""Matter is conserved.  PLAN section 1: nothing enters or leaves the world.

Three things this file learned the hard way, all of them worth keeping:

* A single before/after total is not a test.  The flows through soil and fauna are large
  enough to hide a real leak inside their noise, and the 1% threshold this started with
  passed both bugs it was written to catch.  So the tick is run by hand and the world is
  totalled after each phase, which makes a leak name the subsystem that caused it.
* It must not resume the live world.  Sensitivity to a seeding leak depends on how much
  flora is actually seeding, so against a checkpoint that changes hour to hour the same
  bug was caught one run and missed the next.  It builds its own world instead.
* It must total in float64.  The grids are float32 and the world runs to a million units;
  summing in float32 puts about 0.01 of error on every read, the same size as the deltas
  being measured, which made an earlier version report a housekeeping leak that was not
  there.
"""
import os, shutil, sys, tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from primordia.config import Config           # noqa: E402
from primordia.sim import Sim                 # noqa: E402

N = 900
KINDS = ("storm", "wildfire", "flood", "volcano", "meteor", "cold_snap")
# Fauna and housekeeping move real matter between pools every tick and show more noise
# than the rest; everything else should barely register.
LIMIT = {"fauna": 0.006, "housekeeping": 0.004}
DEFAULT_LIMIT = 0.001
NET_LIMIT = 0.0008


def build(root):
    cfg = Config.load(None, {"world": {"size": 128}, "fauna": {"max_pop": 6000},
                             # heavy seeding on purpose: the seeding leak only shows when
                             # seeds actually collide on occupied cells
                             "flora": {"seed_prob": 0.05},
                             "sim": {"green_up_ticks": 300, "checkpoint_seconds": 1e9,
                                     "snapshot_every": 10 ** 9,
                                     "summary_every": 10 ** 9}})
    s = Sim(cfg, root=root, with_monitor=False)
    s.bootstrap()
    s.checkpoints_enabled = False
    for _ in range(2500):                      # let flora and fauna actually establish
        s.step()
    # Age the soil by hand.  A fresh world never fills its nutrient pool, so the overflow
    # path -- the one that used to delete matter on every tick of a saturated world -- is
    # simply never taken, and this file passed the pre-lithosphere clip without noticing.
    # The reference world sits at 98%% of the cap; put the test world there too.
    s.world.nutrients[:] = 0.98 * float(cfg.world["nutrient_cap"])
    s.world.soil_fertility[:] = np.minimum(
        s.world.soil_fertility + 0.5, float(cfg.world["fertility_cap"]))
    return s


def seeding_conserves(s, M):
    """Seeding, exercised directly.

    The whole-world loop above cannot reach this path: seeds mostly land on empty ground,
    where the displaced-plant term is zero, and a world with saturated soil never takes the
    branch where a cell cannot afford its seedling.  Both of the bugs that lived here need
    dense flora and poor soil at the same time, so build exactly that and call reproduction
    on its own.
    """
    fl, wr = s.flora, s.world
    rng = fl.rng
    # Dense and mature everywhere so seeds collide, but *uneven*: competition_edge is
    # 1.25, so a uniform field lets no seed beat its occupant and nothing germinates at
    # all.  Strong plants displacing weak ones is the case where the displaced-plant
    # term is non-zero, which is the bug.
    fl.biomass[:] = rng.uniform(0.4, 3.0, fl.biomass.shape).astype(fl.biomass.dtype)
    fl.age[:] = 50.0
    # half the map cannot pay for a seedling, which is the branch the old clip papered over
    wr.soil_fertility[:] = 1.0
    wr.soil_fertility[:, : wr.G // 2] = 0.0
    before = M()
    total_seeds = 0
    for t in range(40):
        total_seeds += fl._reproduce(1000 + t, 1)
    after = M()
    drift = after - before
    pct = abs(drift) / max(before, 1.0) * 100.0
    print("seeding: %d seeds over 40 rounds, matter %+.4f (%.6f%%)"
          % (total_seeds, drift, pct))
    if total_seeds < 50:
        print("  FAIL: seeding did not run, so this proves nothing")
        return 1
    if pct > 0.0005:
        print("  <<< LEAK: seeding is not matter-conservative")
        return 1
    print("  ok")
    return 0


def run():
    root = tempfile.mkdtemp(prefix="prim_matter_")
    try:
        s = build(root)
        wr, fl, fa, wx = s.world, s.flora, s.fauna, s.weather

        def M():
            return (float(wr.nutrients.sum(dtype=np.float64))
                    + float(wr.soil_fertility.sum(dtype=np.float64))
                    + float(wr.lithosphere)
                    + float(fl.biomass.sum(dtype=np.float64)) * fl.matter_per_biomass
                    + float(fa.matter[fa.alive_idx].sum(dtype=np.float64))
                    + float(fa.meat_matter.sum(dtype=np.float64)))

        acc, forced, m0 = {}, 0, M()
        for i in range(N):
            tick = s.tick
            ctx = {"is_night": wx.is_night, "season": wx.season(tick)}
            m = M()

            def mark(name, before):
                now = M()
                acc[name] = acc.get(name, 0.0) + (now - before)
                return now

            wx.step(tick);                      m = mark("weather", m)
            if i % 45 == 44:
                k = KINDS[(i // 45) % len(KINDS)]
                if s.events.trigger(k, int(s.rng.integers(0, wr.G)),
                                    int(s.rng.integers(0, wr.G)),
                                    intensity=0.8, tick=tick):
                    forced += 1
            s.events.maybe_trigger(tick);       m = mark("disasters", m)
            fl.step(tick, wx.sunlight, ctx);    m = mark("flora", m)
            s.decomposers.step(tick);           m = mark("decomposers", m)
            s.scent.step();                     m = mark("scent", m)
            fa.decay_corpses();                 m = mark("corpses", m)
            rows = fa.alive_idx
            if len(rows):
                st = fa.build_stats(rows, s._world_ctx(rows, ctx))
                inp, cy, cx, prey, prey_d, threat, threat_d = fa.perceive(rows, ctx, st)
                out = fa.brain.forward(rows, inp)
                fa.last_inputs, fa.last_outputs = inp, out
                # act, metabolize and _refresh are one phase and must be marked as one:
                # births land in `alive` during act but not in `alive_idx` until the
                # refresh, so marking between them books every newborn as a loss followed
                # by an equal gain -- two 0.0136%% "leaks" that were pure bookkeeping.
                fa.act(rows, out, cy, cx, prey, prey_d, ctx, st, tick)
                fa.metabolize(rows, ctx, st, tick)
                fa._refresh()
                m = mark("fauna", m)
            s.tick = tick + 1
            s._housekeeping(s.tick);            m = mark("housekeeping", m)

        m1 = M()
        scale = max(m0, 1.0) / 100.0            # 1 unit == 1% of the world's matter
        per_k = 1000.0 / N
        print("%d ticks, %d forced disasters, %d creatures, flora %.0f"
              % (N, forced, fa.pop, float(fl.biomass.sum())))
        print("total %.1f -> %.1f   net %+.4f%% per 1000 ticks"
              % (m0, m1, (m1 - m0) / scale * per_k))

        bad = []
        print("per phase, %% of world matter per 1000 ticks:")
        for k, v in sorted(acc.items(), key=lambda kv: -abs(kv[1])):
            pct = v / scale * per_k
            lim = LIMIT.get(k, DEFAULT_LIMIT)
            flag = "" if abs(pct) <= lim else "   <<< LEAK (limit %.3f%%)" % lim
            if flag:
                bad.append(k)
            print("  %-13s %+10.3f   %+.4f%%%s" % (k, v, pct, flag))

        bad += ["seeding"] * seeding_conserves(s, M)

        net = abs((m1 - m0) / scale * per_k)
        if net > NET_LIMIT:
            bad.append("net")
            print("net drift %.4f%% per 1000 ticks exceeds %.4f%%" % (net, NET_LIMIT))
        if bad:
            print("FAIL: " + ", ".join(sorted(set(bad))))
            return 1
        print("PASS")
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(run())
