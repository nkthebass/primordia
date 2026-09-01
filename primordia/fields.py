"""Grid field operations (diffusion / advection / blur).

torch+CUDA when available, graceful fallback to scipy/numpy on CPU.  Everything here
is whole-array vectorized; no per-cell Python.
"""
from __future__ import annotations

import numpy as np

_BACKEND = None
_DEVICE = "cpu"
torch = None


def init_backend(prefer: str = "auto") -> str:
    """Pick the field backend once at startup.  Returns 'cuda' | 'cpu-torch' | 'cpu-numpy'."""
    global _BACKEND, _DEVICE, torch
    if _BACKEND is not None:
        return _BACKEND
    if prefer != "cpu":
        try:
            import torch as _t  # noqa
            torch = _t
            if prefer in ("auto", "cuda") and torch.cuda.is_available():
                try:
                    torch.zeros(8, device="cuda").sum().item()
                    _DEVICE = "cuda"
                    _BACKEND = "cuda"
                except Exception:
                    _DEVICE, _BACKEND = "cpu", "cpu-torch"
            else:
                _DEVICE, _BACKEND = "cpu", "cpu-torch"
        except Exception:
            torch = None
            _BACKEND = "cpu-numpy"
    else:
        _BACKEND = "cpu-numpy"
    if _BACKEND is None:
        _BACKEND = "cpu-numpy"
    return _BACKEND


def backend() -> str:
    return _BACKEND or init_backend()


# Which path actually runs the per-tick field maths.  torch+CUDA is detected and kept
# as the fallback contract, but at these grid sizes the host<->device copy dominates a
# 3x3 stencil, so the choice is made by measurement rather than assumption.
_FIELD_PATH = None
_FIELD_NOTE = ""


def choose_field_path(shape: tuple[int, int]) -> str:
    global _FIELD_PATH, _FIELD_NOTE
    if _FIELD_PATH is not None:
        return _FIELD_PATH
    if backend() != "cuda":
        _FIELD_PATH, _FIELD_NOTE = "numpy", "no CUDA"
        return _FIELD_PATH
    import time
    probe = [np.random.rand(*shape).astype(np.float32) for _ in range(3)]
    rates = [0.1] * 3
    st = FieldStack(shape, force="torch")
    try:
        st.diffuse_many([a.copy() for a in probe], rates)          # warm-up
        t = time.perf_counter()
        for _ in range(20):
            st.diffuse_many([a.copy() for a in probe], rates)
        gpu = time.perf_counter() - t
    except Exception:
        gpu = float("inf")
    st2 = FieldStack(shape, force="numpy")
    t = time.perf_counter()
    for _ in range(20):
        st2.diffuse_many([a.copy() for a in probe], rates)
    cpu = time.perf_counter() - t
    if gpu < cpu:
        _FIELD_PATH = "torch"
        _FIELD_NOTE = f"cuda {cpu / max(gpu, 1e-9):.1f}x faster than numpy"
    else:
        _FIELD_PATH = "numpy"
        _FIELD_NOTE = f"numpy {gpu / max(cpu, 1e-9):.1f}x faster than cuda here"
    return _FIELD_PATH


def field_note() -> str:
    return _FIELD_NOTE


def device() -> str:
    return _DEVICE


def vram_used_gb() -> float:
    if _BACKEND == "cuda" and torch is not None:
        try:
            return torch.cuda.memory_reserved() / 1e9
        except Exception:
            return 0.0
    return 0.0


# --------------------------------------------------------------------------
# core ops.  All take/return float32 numpy arrays shaped (H, W) and wrap on x
# (cylindrical world) while clamping on y (poles).
# --------------------------------------------------------------------------

def _neigh_sum(a: np.ndarray) -> np.ndarray:
    """4-neighbour sum with wrap-x / edge-y."""
    up = np.empty_like(a); up[1:] = a[:-1]; up[0] = a[0]
    dn = np.empty_like(a); dn[:-1] = a[1:]; dn[-1] = a[-1]
    lf = np.roll(a, 1, axis=1)
    rt = np.roll(a, -1, axis=1)
    return up + dn + lf + rt


def diffuse(a: np.ndarray, rate: float, iters: int = 1) -> np.ndarray:
    """Explicit 4-point Laplacian diffusion.  rate in [0, 0.25] per iter."""
    if rate <= 0.0:
        return a
    out = a
    for _ in range(max(1, iters)):
        out = out + rate * (_neigh_sum(out) - 4.0 * out)
    return out.astype(np.float32, copy=False)


def blur(a: np.ndarray, strength: float) -> np.ndarray:
    """Simple isotropic blur toward the neighbourhood mean."""
    if strength <= 0.0:
        return a
    m = _neigh_sum(a) * 0.25
    return ((1.0 - strength) * a + strength * m).astype(np.float32, copy=False)


def advect(a: np.ndarray, vx: float, vy: float) -> np.ndarray:
    """Semi-Lagrangian advection by a uniform wind vector (bilinear backtrace)."""
    if abs(vx) < 1e-6 and abs(vy) < 1e-6:
        return a
    h, w = a.shape
    ix = int(np.floor(vx)); fx = float(vx - ix)
    iy = int(np.floor(vy)); fy = float(vy - iy)
    # backtrace: sample from (y - vy, x - vx)
    def shift(dy: int, dx: int) -> np.ndarray:
        s = np.roll(a, -dx, axis=1)
        if dy:
            out = np.empty_like(s)
            if dy > 0:
                out[dy:] = s[:-dy]; out[:dy] = s[0]
            else:
                out[:dy] = s[-dy:]; out[dy:] = s[-1]
            return out
        return s
    a00 = shift(-iy, -ix)
    a10 = shift(-iy - 1, -ix)
    a01 = shift(-iy, -ix - 1)
    a11 = shift(-iy - 1, -ix - 1)
    top = a00 * (1 - fx) + a01 * fx
    bot = a10 * (1 - fx) + a11 * fx
    return (top * (1 - fy) + bot * fy).astype(np.float32, copy=False)


def gradient(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Central-difference gradient (gx, gy)."""
    gx = (np.roll(a, -1, axis=1) - np.roll(a, 1, axis=1)) * 0.5
    gy = np.empty_like(a)
    gy[1:-1] = (a[2:] - a[:-2]) * 0.5
    gy[0] = a[1] - a[0]
    gy[-1] = a[-1] - a[-2]
    return gx.astype(np.float32, copy=False), gy.astype(np.float32, copy=False)


# --------------------------------------------------------------------------
# torch-accelerated batch diffusion: several fields diffused at once on the GPU.
# --------------------------------------------------------------------------
class FieldStack:
    """Diffuses N same-shaped fields in one batched conv2d when CUDA is live."""

    def __init__(self, shape: tuple[int, int], force: str | None = None):
        self.shape = shape
        if force is not None:
            self.use_torch = (force == "torch") and backend() == "cuda"
        else:
            self.use_torch = choose_field_path(shape) == "torch"
        if self.use_torch:
            k = torch.tensor([[0.0, 1.0, 0.0], [1.0, -4.0, 1.0], [0.0, 1.0, 0.0]],
                             dtype=torch.float32, device=_DEVICE)
            self.kernel = k.view(1, 1, 3, 3)

    def diffuse_many(self, arrays: list[np.ndarray], rates: list[float],
                     iters: int = 1) -> list[np.ndarray]:
        if not arrays:
            return arrays
        if not self.use_torch:
            return [diffuse(a, r, iters) for a, r in zip(arrays, rates)]
        try:
            n = len(arrays)
            t = torch.from_numpy(np.stack(arrays)).to(_DEVICE).view(n, 1, *self.shape)
            rr = torch.tensor(rates, dtype=torch.float32, device=_DEVICE).view(n, 1, 1, 1)
            kern = self.kernel.expand(1, 1, 3, 3)
            for _ in range(max(1, iters)):
                p = torch.nn.functional.pad(t, (1, 1, 0, 0), mode="circular")
                p = torch.nn.functional.pad(p, (0, 0, 1, 1), mode="replicate")
                lap = torch.nn.functional.conv2d(p, kern)
                t = t + rr * lap
            out = t.view(n, *self.shape).cpu().numpy()
            return [out[i].astype(np.float32, copy=False) for i in range(n)]
        except Exception:
            self.use_torch = False
            return [diffuse(a, r, iters) for a, r in zip(arrays, rates)]
