"""Incremental genetic clustering, procedural naming, phylogeny."""
from __future__ import annotations

import numpy as np

PREFIX = ["ve", "cor", "gna", "thal", "rhu", "kri", "sil", "ama", "dor", "pyr", "xan",
          "lum", "fer", "obl", "nyx", "cal", "myr", "zeph", "hal", "ter", "vol", "urs",
          "spin", "glau", "arg", "bry", "chal", "den", "eos", "fulg"]
MID = ["o", "i", "a", "u", "ae", "e", "y", "ei", "au", "ou"]
SUFF = ["lox", "phus", "dens", "ther", "pter", "gnath", "morph", "chir", "pod", "saur",
        "cera", "rhax", "mys", "don", "stoma", "nyx", "bius", "phor", "tes", "cus"]
EPI = ["rubrum", "album", "nigrum", "velox", "gravis", "minor", "major", "australe",
       "boreale", "pallidum", "ferox", "placidum", "aureum", "viride", "caeruleum",
       "umbratile", "solaris", "nocturnum", "arenae", "silvae", "montanum", "litoris",
       "profundum", "vagans", "tenax", "fragile", "acutum", "obtusum", "gelidum",
       "torridum"]
SUBEPI = ["primum", "secundum", "tertium", "borealis", "australis", "orientalis",
          "occidentalis", "minimus", "maximus", "insularis", "campestris", "alpinus"]


class Species:
    __slots__ = ("id", "name", "parent", "hue", "founded", "extinct", "centroid",
                 "pop", "pop_series", "peak_pop", "diet_mean", "traits", "rank",
                 "last_seen", "total_born")

    def __init__(self, sid, name, parent, hue, founded, centroid, rank="species"):
        self.id = int(sid)
        self.name = name
        self.parent = int(parent)
        self.hue = float(hue)
        self.founded = int(founded)
        self.extinct = -1
        self.centroid = centroid
        self.pop = 0
        self.peak_pop = 0
        self.pop_series: list[tuple[int, int]] = []
        self.diet_mean = 0.0
        self.traits: dict = {}
        self.rank = rank
        self.last_seen = int(founded)
        self.total_born = 0

    def to_json(self) -> dict:
        return {"id": self.id, "name": self.name, "parent": self.parent,
                "hue": self.hue, "founded": self.founded, "extinct": self.extinct,
                "centroid": np.asarray(self.centroid).tolist(), "pop": self.pop,
                "peak_pop": self.peak_pop, "pop_series": self.pop_series[-400:],
                "diet_mean": self.diet_mean, "traits": self.traits, "rank": self.rank,
                "last_seen": self.last_seen, "total_born": self.total_born}

    @staticmethod
    def from_json(d: dict) -> "Species":
        s = Species(d["id"], d["name"], d["parent"], d["hue"], d["founded"],
                    np.array(d["centroid"], np.float32), d.get("rank", "species"))
        s.extinct = d.get("extinct", -1)
        s.pop = d.get("pop", 0)
        s.peak_pop = d.get("peak_pop", 0)
        s.pop_series = [tuple(p) for p in d.get("pop_series", [])]
        s.diet_mean = d.get("diet_mean", 0.0)
        s.traits = d.get("traits", {})
        s.last_seen = d.get("last_seen", s.founded)
        s.total_born = d.get("total_born", 0)
        return s


class Speciation:
    """Assigns every creature to a species by distance to per-species centroids."""

    # body genes that count toward genetic distance, and their weights
    WEIGHTS = {
        "size": 1.4, "speed": 1.0, "metabolism_eff": 0.6, "sense_range": 0.7,
        "camouflage": 0.7, "armor": 0.9, "fangs": 1.1, "toxin_tolerance": 0.6,
        "heat_tol": 0.5, "cold_tol": 0.5, "lifespan": 0.5, "repro_threshold": 0.4,
        "repro_invest": 0.4, "sexual": 1.0, "social": 0.8, "scent_deposit": 0.4,
        "swim": 0.9, "diet": 2.2,
    }
    RUNTIME_WEIGHT = 0.35

    def __init__(self, cfg, fauna, rng, chronicle):
        self.cfg = cfg
        self.fauna = fauna
        self.rng = rng
        self.chronicle = chronicle
        self.species: dict[int, Species] = {}
        self._next_id = 1
        self._rebuild_cols()
        root = Species(0, "Primordium vulgare", -1, 0.33, 0,
                       np.zeros(len(self.cols), np.float32), "species")
        self.species[0] = root
        self.used_names: set[str] = {root.name}

    def _rebuild_cols(self) -> None:
        """Recompute the genetic-distance feature columns.

        A runtime-added gene widens the vector and renormalises every weight, so any
        centroids already recorded have to be carried across -- otherwise the next
        clustering pass compares 19-dim creatures against 18-dim species and either
        crashes or invents a world-wide speciation event out of pure bookkeeping.
        """
        sch = self.fauna.schema
        old_cols = getattr(self, "cols", None)
        old_wnorm = getattr(self, "wnorm", None)

        cols, ws = [], []
        for name, w in self.WEIGHTS.items():
            if sch.has(name):
                cols.append(sch.index[name]); ws.append(w)
        for g in sch.genes:
            if g.effects and g.name not in self.WEIGHTS:
                cols.append(sch.index[g.name]); ws.append(self.RUNTIME_WEIGHT)
        self.cols = np.array(cols, np.int64)
        self.w = np.array(ws, np.float32)
        self.wnorm = self.w / max(1e-6, float(np.sqrt((self.w ** 2).sum())))

        if old_cols is None or len(old_cols) == len(self.cols):
            return
        pos = {int(c): i for i, c in enumerate(old_cols)}
        for sp in getattr(self, "species", {}).values():
            v_old = np.asarray(sp.centroid, np.float32)
            v_new = np.empty(len(self.cols), np.float32)
            for j, c in enumerate(self.cols):
                k = pos.get(int(c))
                if k is not None and k < len(v_old) and old_wnorm is not None:
                    scale = self.wnorm[j] / max(1e-9, float(old_wnorm[k]))
                    v_new[j] = v_old[k] * scale
                else:
                    gene = sch.genes[int(c)]
                    v_new[j] = gene.init_mean * self.wnorm[j]
            sp.centroid = v_new

    # ------------------------------------------------------------------ naming
    def _gen_name(self, parent: Species | None, rank: str) -> str:
        r = self.rng
        for _ in range(64):
            if rank == "subspecies" and parent is not None:
                base = " ".join(parent.name.split()[:2])
                nm = f"{base} {SUBEPI[int(r.integers(0, len(SUBEPI)))]}"
            elif parent is not None and parent.id != 0 and r.random() < 0.55:
                genus = parent.name.split()[0]
                nm = f"{genus} {EPI[int(r.integers(0, len(EPI)))]}"
            else:
                genus = (PREFIX[int(r.integers(0, len(PREFIX)))]
                         + MID[int(r.integers(0, len(MID)))]
                         + SUFF[int(r.integers(0, len(SUFF)))]).capitalize()
                nm = f"{genus} {EPI[int(r.integers(0, len(EPI)))]}"
            if nm not in self.used_names:
                self.used_names.add(nm)
                return nm
        # A parent genus carries only len(EPI) epithets, and lineages here run twenty
        # deep, so inherited genera exhaust within a few hundred species and every
        # descendant after that fell through to "Incognitum 143".  Coin a fresh genus
        # instead -- the syllable tables hold 6000 of them.
        for _ in range(400):
            genus = (PREFIX[int(r.integers(0, len(PREFIX)))]
                     + MID[int(r.integers(0, len(MID)))]
                     + SUFF[int(r.integers(0, len(SUFF)))]).capitalize()
            nm = f"{genus} {EPI[int(r.integers(0, len(EPI)))]}"
            if nm not in self.used_names:
                self.used_names.add(nm)
                return nm
        nm = f"Incognitum {self._next_id}"
        self.used_names.add(nm)
        return nm

    # ------------------------------------------------------------------ update
    def update(self, tick: int) -> list[dict]:
        fa = self.fauna
        news: list[dict] = []
        rows = fa.alive_idx
        if len(rows) == 0:
            for s in self.species.values():
                if s.pop and s.extinct < 0 and s.id != 0:
                    s.extinct = tick
                s.pop = 0
            return news

        vec = fa.schema.data[np.ix_(rows, self.cols)] * self.wnorm

        ids = sorted(k for k, s in self.species.items() if s.extinct < 0)
        cents = np.stack([np.asarray(self.species[i].centroid, np.float32) for i in ids])
        # nearest centroid
        d2 = ((vec[:, None, :] - cents[None, :, :]) ** 2).sum(-1) if len(ids) * len(rows) < 4_000_000 \
            else self._chunked_d2(vec, cents)
        nearest = np.argmin(d2, axis=1)
        mind = np.sqrt(d2[np.arange(len(rows)), nearest])
        assigned = np.array(ids, np.int64)[nearest]

        split_d = float(self.cfg.speciation["species_split_dist"])
        sub_d = float(self.cfg.speciation["subspecies_dist"])
        min_pop = int(self.cfg.speciation["min_species_pop"])

        outliers = mind > sub_d
        if outliers.any() and len(self.species) < int(self.cfg.speciation["max_species"]):
            news += self._split(rows, vec, assigned, mind, outliers, tick, split_d, sub_d, min_pop)

        fa.species[rows] = assigned.astype(np.int32)
        self._recompute(rows, vec, tick)
        return news

    @staticmethod
    def _chunked_d2(vec, cents):
        out = np.empty((len(vec), len(cents)), np.float32)
        step = max(1, 2_000_000 // max(1, len(cents)))
        for i in range(0, len(vec), step):
            out[i:i + step] = ((vec[i:i + step, None, :] - cents[None]) ** 2).sum(-1)
        return out

    def _split(self, rows, vec, assigned, mind, outliers, tick, split_d, sub_d, min_pop):
        """Seed new clusters from the furthest outliers and pull neighbours in."""
        news = []
        cand = np.nonzero(outliers)[0]
        order = cand[np.argsort(-mind[cand])]
        taken = np.zeros(len(rows), bool)
        for j in order[:6]:
            if taken[j]:
                continue
            seed = vec[j]
            dist = np.sqrt(((vec - seed) ** 2).sum(-1))
            member = (dist < sub_d * 0.8) & outliers & ~taken
            n = int(member.sum())
            if n < min_pop:
                continue
            parent_id = int(assigned[j])
            parent = self.species.get(parent_id) or self.species[0]
            rank = "species" if mind[j] > split_d else "subspecies"
            # subspecies stay visually close to their parent; a full species takes a
            # clear step around the wheel so the map is readable at a glance
            if rank == "subspecies":
                shift = float(self.rng.normal(0, 0.035))
            else:
                shift = float(self.rng.choice([-1.0, 1.0])
                              * self.rng.uniform(0.17, 0.31))
            hue = (parent.hue + shift) % 1.0
            sid = self._next_id
            self._next_id += 1
            centroid = vec[member].mean(0).astype(np.float32)
            sp = Species(sid, self._gen_name(parent, rank), parent_id, hue, tick,
                         centroid, rank)
            self.species[sid] = sp
            assigned[member] = sid
            taken |= member
            news.append({"id": sid, "name": sp.name, "parent": parent.name,
                         "rank": rank, "pop": n, "tick": tick})
            if self.chronicle:
                self.chronicle.event(
                    tick, "speciation",
                    f"A new {rank} splits from {parent.name}: {sp.name} ({n} individuals).",
                    {"species": sid, "parent": parent_id})
            if len(self.species) >= int(self.cfg.speciation["max_species"]):
                break
        return news

    def _recompute(self, rows, vec, tick: int) -> None:
        fa = self.fauna
        sids = fa.species[rows]
        diet = fa.gene("diet", rows)
        for sid, sp in self.species.items():
            m = sids == sid
            n = int(m.sum())
            prev = sp.pop
            sp.pop = n
            if n:
                sp.last_seen = tick
                sp.peak_pop = max(sp.peak_pop, n)
                sp.centroid = (0.85 * np.asarray(sp.centroid, np.float32)
                               + 0.15 * vec[m].mean(0)).astype(np.float32)
                sp.diet_mean = float(diet[m].mean())
                sp.traits = {k: round(float(fa.gene(k, rows[m]).mean()), 3)
                             for k in ("size", "speed", "fangs", "armor", "social",
                                       "sense_range", "camouflage", "swim", "sexual")}
                sp.extinct = -1
            elif prev > 0 and sp.extinct < 0 and sid != 0:
                sp.extinct = tick
                if self.chronicle:
                    self.chronicle.event(tick, "extinction",
                                         f"{sp.name} is extinct after {tick - sp.founded} ticks.",
                                         {"species": sid})
            sp.pop_series.append((tick, n))
            if len(sp.pop_series) > 4000:
                del sp.pop_series[:len(sp.pop_series) - 4000]

    # ---------------------------------------------------------------- reporting
    def living(self) -> list[Species]:
        return sorted((s for s in self.species.values() if s.pop > 0),
                      key=lambda s: -s.pop)

    def hues(self) -> np.ndarray:
        n = max(self.species) + 1 if self.species else 1
        out = np.zeros(n, np.float32)
        for i, s in self.species.items():
            out[i] = s.hue
        return out

    def tree(self) -> list[dict]:
        return [s.to_json() for s in sorted(self.species.values(), key=lambda s: s.id)]

    def meta(self) -> dict:
        return {"species": [s.to_json() for s in self.species.values()],
                "next_id": self._next_id}

    def load(self, meta: dict) -> None:
        self.species = {}
        for d in meta["species"]:
            s = Species.from_json(d)
            self.species[s.id] = s
        self._next_id = int(meta["next_id"])
        self.used_names = {s.name for s in self.species.values()}
        self._rebuild_cols()
