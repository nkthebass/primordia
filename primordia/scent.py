"""Pheromone / scent fields.

Three channels: two kin channels (species-ID hashed into channel 0/1 so creatures can
smell "their kind" without a per-species field) and one global blood channel deposited
by combat and corpses.
"""
from __future__ import annotations

import numpy as np

from . import fields

KIN_A, KIN_B, BLOOD = 0, 1, 2


class Scent:
    def __init__(self, cfg, world):
        self.cfg = cfg
        self.world = world
        G = world.G
        self.G = G
        self.n = int(cfg.scent["channels"])
        self.field = np.zeros((self.n, G, G), np.float32)
        self.grad_cache: list[tuple[np.ndarray, np.ndarray]] = []
        self.stack = fields.FieldStack((G, G))

    @staticmethod
    def channel_for(species_id: np.ndarray) -> np.ndarray:
        """Stable hash of species id -> kin channel 0/1."""
        return (species_id.astype(np.int64) * 2654435761 >> 13 & 1).astype(np.int64)

    def _scatter(self, plane: np.ndarray, ys, xs, amt) -> None:
        g = plane.shape[1]
        flat = np.bincount((ys.astype(np.int64) * g + xs), weights=amt,
                           minlength=plane.size)
        plane += flat.reshape(plane.shape).astype(plane.dtype, copy=False)

    def deposit(self, ch: np.ndarray, ys: np.ndarray, xs: np.ndarray, amt) -> None:
        if len(ys) == 0:
            return
        amt = np.broadcast_to(np.asarray(amt, np.float64), ys.shape)
        for i in range(min(self.n, 2)):
            m = ch == i
            if m.any():
                self._scatter(self.field[i], ys[m], xs[m], amt[m])

    def deposit_blood(self, ys: np.ndarray, xs: np.ndarray, amt) -> None:
        if len(ys) == 0:
            return
        self._scatter(self.field[BLOOD], ys, xs,
                      np.broadcast_to(np.asarray(amt, np.float64), ys.shape))

    def step(self) -> None:
        c = self.cfg.scent
        d = float(c["diffuse"])
        dec = 1.0 - float(c["decay"])
        planes = self.stack.diffuse_many([self.field[i] for i in range(self.n)],
                                         [d] * self.n)
        for i, pl in enumerate(planes):
            self.field[i] = pl * dec
        np.clip(self.field, 0.0, 40.0, out=self.field)
        self.grad_cache = [fields.gradient(self.field[i]) for i in range(self.n)]

    def sample_gradient(self, ch: np.ndarray, ys: np.ndarray, xs: np.ndarray,
                        blood_weight: np.ndarray | None = None):
        """Per-creature scent gradient (gx, gy).

        Channel is the creature's own kin channel; `blood_weight` (the diet gene) blends
        the blood-scent gradient in on top, so a herbivore follows its herd and a
        carnivore follows the smell of a kill.  Continuous in the gene -- no branch on
        trophic role (PLAN 6.3/6.5).
        """
        if not self.grad_cache:
            z = np.zeros(len(ys), np.float32)
            return z, z.copy()
        gx = np.zeros(len(ys), np.float32)
        gy = np.zeros(len(ys), np.float32)
        for i in range(min(self.n, 2)):
            m = ch == i
            if m.any():
                gxi, gyi = self.grad_cache[i]
                gx[m] = gxi[ys[m], xs[m]]
                gy[m] = gyi[ys[m], xs[m]]
        if blood_weight is not None and self.n > BLOOD:
            bx, by = self.grad_cache[BLOOD]
            w = np.clip(blood_weight, 0.0, 1.0)
            gx = gx * (1.0 - w) + bx[ys, xs] * w
            gy = gy * (1.0 - w) + by[ys, xs] * w
        return gx, gy

    def sample(self, i: int, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
        return self.field[i][ys, xs]

    def foreign(self, ch: np.ndarray, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
        """Magnitude of the *other* kin channel + blood: 'something not mine is here'."""
        a = self.field[KIN_A][ys, xs]
        b = self.field[KIN_B][ys, xs]
        mine = np.where(ch == 0, a, b)
        other = np.where(ch == 0, b, a)
        return (other + 0.5 * self.field[BLOOD][ys, xs] - 0.0 * mine).astype(np.float32)

    def state(self) -> dict:
        return {"scent_field": self.field}

    def load(self, npz, meta: dict) -> None:
        self.field = npz["scent_field"]
        self.n = self.field.shape[0]
