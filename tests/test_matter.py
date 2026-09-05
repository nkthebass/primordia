"""Matter is conserved: PLAN section 1 says nothing enters or leaves."""
import sys, numpy as np
sys.path.insert(0, r"C:\Users\noahc\Documents\PRIMORDIA")
from primordia.config import Config
from primordia.sim import Sim

cfg = Config.load(None, {"sim": {"checkpoint_seconds": 1e9, "snapshot_every": 10**9,
                                 "summary_every": 10**9}})
s = Sim(cfg, with_monitor=False); s.checkpoints_enabled = False; s.resume(); s.step()

def total():
    m = s.stats._matter()
    return m["total"], m

t0, m0 = total()
print("start ", {k: v for k, v in m0.items()})
FORCED = 0
for i in range(4000):
    s.step()
    if i % 200 == 199:            # force disasters so the reservoir is exercised
        try:
            k = str(s.rng.choice(["volcano", "meteor", "flood"]))
            if s.events.trigger(k, int(s.rng.integers(0, s.world.G)),
                                int(s.rng.integers(0, s.world.G)),
                                intensity=1.0, tick=s.tick):
                FORCED += 1
        except Exception:
            pass
t1, m1 = total()
print("end   ", {k: v for k, v in m1.items()})
drift = (t1 - t0) / max(t0, 1.0)
print("forced disasters: %d" % FORCED)
print("total %.1f -> %.1f   drift %+.4f%%" % (t0, t1, 100 * drift))
print("PASS" if abs(drift) < 0.01 else "FAIL: matter is not conserved")
