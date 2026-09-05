"""Matter is conserved.  PLAN section 1: nothing enters or leaves the world.

A single before/after total is a poor guard -- the flows through fauna and soil are large
enough that a real leak hides inside their noise, and the 1% threshold this file first
shipped with would have passed both bugs it was written to catch.  So the check is
per-phase: run the tick by hand, total the world after each stage, and hold every stage to
near zero.  A leak then names the subsystem that caused it.
"""
import sys, numpy as np
sys.path.insert(0, r"C:\Users\noahc\Documents\PRIMORDIA")
from primordia.config import Config
from primordia.sim import Sim

cfg = Config.load(None, {"sim": {"checkpoint_seconds": 1e9, "snapshot_every": 10**9,
                                 "summary_every": 10**9}})
s = Sim(cfg, with_monitor=False)
s.checkpoints_enabled = False
s.resume()
s.step()
wx, wr, fl, fa = s.weather, s.world, s.flora, s.fauna

def M():
    return (float(wr.nutrients.sum()) + float(wr.soil_fertility.sum())
            + float(wr.lithosphere) + float(fl.biomass.sum() * fl.matter_per_biomass)
            + float(fa.matter[fa.alive_idx].sum()) + float(fa.meat_matter.sum()))

N = 600
KINDS = ("storm", "wildfire", "flood", "volcano", "meteor", "cold_snap")
FORCED = 0
acc, m0 = {}, M()
for i in range(N):
    tick = s.tick
    ctx = {"is_night": wx.is_night, "season": wx.season(tick)}
    m = M()
    def mark(name, before):
        now = M()
        acc[name] = acc.get(name, 0.0) + (now - before)
        return now
    wx.step(tick);                    m = mark("weather", m)
    # Every disaster kind, on a fixed rotation: leaving storms out let a bug that deleted
    # torn foliage on the most frequent event in the world pass unnoticed.  The rate is
    # deliberately restrained -- forcing one every twelve ticks flattened the population
    # and the flora with it, and a world with nothing growing in it cannot show a leak in
    # how seedlings are paid for.
    if i % 30 == 29:
        k = KINDS[(i // 12) % len(KINDS)]
        if s.events.trigger(k, int(s.rng.integers(0, wr.G)),
                            int(s.rng.integers(0, wr.G)), intensity=1.0, tick=tick):
            FORCED += 1
    s.events.maybe_trigger(tick);     m = mark("disasters", m)
    fl.step(tick, wx.sunlight, ctx);  m = mark("flora", m)
    s.decomposers.step(tick);         m = mark("decomposers", m)
    s.scent.step();                   m = mark("scent", m)
    fa.decay_corpses();               m = mark("corpses", m)
    rows = fa.alive_idx
    if len(rows):
        st = fa.build_stats(rows, s._world_ctx(rows, ctx))
        inp, cy, cx, prey, prey_d, threat, threat_d = fa.perceive(rows, ctx, st)
        out = fa.brain.forward(rows, inp)
        fa.last_inputs, fa.last_outputs = inp, out
        fa.act(rows, out, cy, cx, prey, prey_d, ctx, st, tick); m = mark("fauna", m)
        fa.metabolize(rows, ctx, st, tick);                     m = mark("fauna", m)
        fa._refresh()
    s.tick = tick + 1
    s._housekeeping(s.tick);          m = mark("housekeeping", m)

m1 = M()
scale = max(m0, 1.0) / 100.0          # one unit == 1% of the world's matter
print("%d ticks, %d forced disasters, %d creatures" % (N, FORCED, fa.pop))
print("total %.1f -> %.1f   net %+.4f%% per 1000 ticks"
      % (m0, m1, (m1 - m0) / scale * (1000.0 / N)))

# Limits sit just above what a clean run actually measures, because a loose threshold is
# the same as no test: at 0.004%% this file passed both the storm bug (0.0149%%) and the
# seeding bug (0.0017%%) it exists to catch.  Fauna and housekeeping move real matter
# between pools every tick and legitimately show more noise than the rest.
LIMIT = {"fauna": 0.008, "housekeeping": 0.004}
bad = []
print("per phase, %% of world matter per 1000 ticks:")
for k, v in sorted(acc.items(), key=lambda kv: -abs(kv[1])):
    pct = v / scale * (1000.0 / N)
    lim = LIMIT.get(k, 0.001)
    flag = "" if abs(pct) <= lim else "   <<< LEAK (limit %.3f%%)" % lim
    if flag:
        bad.append(k)
    print("  %-13s %+10.3f   %+.4f%%%s" % (k, v, pct, flag))

net = abs((m1 - m0) / scale * (1000.0 / N))
if net > 0.0008:
    bad.append("net")
    print("net drift %.4f%% per 1000 ticks exceeds 0.0008%%" % net)
print("PASS" if not bad else "FAIL: " + ", ".join(sorted(set(bad))))
