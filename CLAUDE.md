# PRIMORDIA — project instructions

Read **PLAN.md** first. It is the complete, authoritative spec for this project; build it
slice by slice in the S0→S8 order it defines, verifying each slice in the browser viewer
(port 8710, `.claude/launch.json` name `primordia`) before moving on.

Hard rules:

- This machine is also the owner's daily desktop (RTX 3080 10 GB, 5900X, 32 GB RAM).
  Never start a long/full-scale run without the staged resource test (PLAN §10).
  Caps: VRAM < 7 GB, sustained CPU < 80%, RAM < 20 GB.
- No per-creature Python loops in the hot path — everything vectorized (numpy SoA;
  torch conv2d for fields only, with CPU fallback).
- Every mechanic must be operable from the viewer's debug dropdown — no CLI-only stubs.
- Interventions are data, never code: the `interventions/*.json` effect system must not
  execute arbitrary Python (PLAN §8.2).
- Checkpoint before risky changes; `--resume` must always work.
- End every response with a "Shipped" list and a "Still needed for full functionality"
  list.

Runtime contract with the game-master Claude session (do not break these paths):
`state/summary.json` (outbound world report), `interventions/` (inbound JSON, consumed
to `interventions/done/`), `chronicle/chronicle.md` (append-only story log).
