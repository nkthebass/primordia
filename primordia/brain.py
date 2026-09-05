"""Batched tiny-MLP neuroevolution.

Every creature carries its own 13-8-6 MLP as plain genes.  One forward pass for the
whole population is two batched matmuls -- no Python loop over creatures ever.
"""
from __future__ import annotations

import numpy as np

from .genetics import Gene

N_IN = 13
N_HID = 8
N_OUT = 6
N_W1 = N_IN * N_HID          # 104
N_B1 = N_HID                 # 8
N_W2 = N_HID * N_OUT         # 48
N_B2 = N_OUT                 # 6
N_BRAIN = N_W1 + N_B1 + N_W2 + N_B2   # 166

INPUT_NAMES = (
    "energy_frac", "age_frac", "plant_food_here", "meat_food_here",
    "prey_dx", "prey_dy", "threat_dx", "threat_dy",
    "kin_scent_dx", "kin_scent_dy", "foreign_scent", "temp_delta", "is_night",
)
OUTPUT_NAMES = ("move_x", "move_y", "eat", "attack", "flee_gain", "breed_desire")


def brain_genes(decay: float = 0.015) -> list[Gene]:
    """166 weight genes, mutating faster than body genes and decaying toward zero.

    The decay is what keeps the network responsive.  A weight under weak selection is an
    unbiased random walk between its bounds, and after two thousand years of that the
    weights were spread almost uniformly across the full +-4 range with 2.7% pressed
    against the clip.  Pre-activations of that size saturate tanh, so every output pinned
    to +-1 regardless of what the thirteen senses reported and the whole fauna drove in
    one fixed direction until it hit the edge of the world.
    """
    return [Gene(f"w{i:03d}", 0.0, 0.7, 0.13, -4.0, 4.0, heritable=True, decay=decay)
            for i in range(N_BRAIN)]


class Brain:
    """Views into the genome matrix; holds no state of its own."""

    def __init__(self, schema):
        self.schema = schema
        self.start = schema.index["w000"]
        self.end = self.start + N_BRAIN
        assert schema.index[f"w{N_BRAIN - 1:03d}"] == self.end - 1, "brain genes must be contiguous"

    def forward(self, rows: np.ndarray, inputs: np.ndarray) -> np.ndarray:
        """inputs: (n, 13) float32 -> outputs: (n, 6) in [-1, 1]."""
        n = len(rows)
        if n == 0:
            return np.zeros((0, N_OUT), np.float32)
        g = self.schema.data[rows, self.start:self.end]
        o = 0
        w1 = g[:, o:o + N_W1].reshape(n, N_IN, N_HID); o += N_W1
        b1 = g[:, o:o + N_B1]; o += N_B1
        w2 = g[:, o:o + N_W2].reshape(n, N_HID, N_OUT); o += N_W2
        b2 = g[:, o:o + N_B2]
        # optimize=False on purpose: for a two-operand contraction the path search costs
        # more than it can ever save, and this runs every tick over the whole population
        h = np.tanh(np.einsum("ni,nih->nh", inputs, w1, optimize=False) + b1)
        out = np.tanh(np.einsum("nh,nho->no", h, w2, optimize=False) + b2)
        return out.astype(np.float32, copy=False)
