# Check-in log

Periodic engine health checks on the running world — distinct from `interventions/done/`,
which is the game-master tending the *ecology*. This log is about whether the machinery is
sound: is the simulation alive, is matter conserved, has anything gone non-finite, is the
disk holding.

Newest first. `matter` is the invariant — this world is closed, so it should not move.

| date | year | pop | H/O/C | species | matter | verdict |
|---|---:|---:|---|---:|---|---|
| 2026-09-10 | 12,507 | 177 | 140/37/0 | 4 | 1.27326e+06 | healthy — carnivores between episodes; still armed (2.26 vs 2.14) |
| 2026-09-10 | 12,461 | 551 | 404/123/24 | 4 | 1.27326e+06 | healthy — carnivores back and armed, best 2.441 vs 2.052 |
| 2026-09-10 | 12,292 | 411 | 393/18/0 | 3 | 1.27326e+06 | healthy — carnivores at zero (*read as "tier lost" at the time; it was a trough*) |
| 2026-09-09 | 11,360 | 422 | 262/154/6 | 7 | 1.27328e+06 | healthy — carnivores crashing 46 → 6, weapon still widespread |
| 2026-09-09 | 11,264 | 452 | 340/66/46 | 5 | 1.27328e+06 | healthy — population slide reversed, predator tier holding |
| 2026-09-09 | 11,171 | 245 | 160/54/31 | 10 | 1.27328e+06 | healthy — **first evolved carnivores**, zero warnings |
| 2026-09-08 | 8,927 | 499 | — | 6 | 1.27335e+06 | healthy — recovered from the second NaN death |

## Correction — the carnivore tier was never lost

Three separate check-ins recorded the carnivore tier as lost, once with the note that
`shear_tooth` had been "purged" from 0.617 to 0.078. That reading was wrong, and the
Chronicle says so plainly once the whole record is looked at rather than the moment in
front of you.

Carnivores have been present in **5,120 of 15,077 recorded years — 34% of this world's
history** — across 47 episodes lasting five years or more. The longest ran 202 years and
peaked at 729 individuals:

| years | duration | peak |
|---|---:|---:|
| 11,697–11,898 | 202 years | 729 |
| 12,422–12,441 | 20 years | 50 |
| 12,460–12,468 | 9 years | 28 |
| 12,493–12,503 | 11 years | 21 |

This is a predator–prey limit cycle with a period of roughly 10–30 years, not a tier that
cannot establish. Every "extinction" I recorded was a trough sampled at the wrong moment.
The lesson for anything reading this file: a single check-in cannot distinguish a cycle
from a collapse, and this world's cycles are shorter than the gaps between checks.

## Incidents

**2026-09-08 — the world died twice.** Went non-finite at year 8525, twice, and the second
time ran on dead for 832 years writing NaN over every checkpoint. Root cause was not
ecological: eating is vectorised, so every animal on a shared cell read the same
availability and took its own share of the whole. Crowded, a cell served N times what it
held — and since carrion carries matter that is credited to the eater, and the eater's
matter returns as carrion when it dies, the duplicate compounded around that loop. Total
matter reached 7.9e37 and overflowed float32. Fixed by rationing per-cell demand; the world
was restored from the year 8500 archive. See `WORLD-LOG.md` for the timeline branch marker.

**2026-09-08 — the disk filled to 99.9%.** The world archived a full 28 MB checkpoint every
simulated year, which at fifty ticks a second is one every forty seconds of wall clock:
123 GB across 4,632 files. Archives are now thinned on write — newest 40 years plus one per
century.

**2026-09-09 — speciation had been impossible since year 964.** `max_species` counted every
species record ever created, including the extinct, so once 200 had *ever* existed the gate
read `200 < 200` and no new species could form again. Six thousand years of the era table in
`WORLD-LOG.md` show zero speciations because of it. The world's collapse to a single species
had been read as stagnation; it was a dead cap. The gate now counts the living.

## How to refresh

```bash
.venv\Scripts\python.exe tools\worldlog.py
```

Reads `state/summary.json` and `chronicle/chronicle.md`, writes `WORLD-LOG.md`. Safe to run
against a live simulation — it never writes to the world.
