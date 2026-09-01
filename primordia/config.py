"""Config loading / merging / hot-reloadable dotted-path access."""
from __future__ import annotations

import copy
import json
import os
import threading
from typing import Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_PATH = os.path.join(ROOT, "config", "default.json")

# Config leaves that interventions / the viewer may retune at runtime.
HOT_RELOADABLE = (
    "weather.", "events.", "flora.", "decomposer.", "fauna.", "energy.",
    "genetics.", "speciation.", "scent.", "sim.", "monitor.",
)


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    """Dict-backed config with dotted-path get/set and a lock for live tuning."""

    def __init__(self, data: dict):
        self._d = data
        self._lock = threading.Lock()

    # ---- construction -------------------------------------------------
    @classmethod
    def load(cls, path: str | None = None, overrides: dict | None = None) -> "Config":
        with open(DEFAULT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if path and os.path.exists(path) and os.path.abspath(path) != DEFAULT_PATH:
            with open(path, "r", encoding="utf-8") as f:
                data = _deep_merge(data, json.load(f))
        if overrides:
            data = _deep_merge(data, overrides)
        return cls(data)

    # ---- access -------------------------------------------------------
    def __getitem__(self, key: str) -> Any:
        return self._d[key]

    def get(self, path: str, default: Any = None) -> Any:
        node: Any = self._d
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, path: str, value: Any, *, enforce_hot: bool = False) -> None:
        if enforce_hot and not any(path.startswith(p) for p in HOT_RELOADABLE):
            raise ValueError(f"config path '{path}' is not hot-reloadable")
        parts = path.split(".")
        with self._lock:
            node = self._d
            for part in parts[:-1]:
                if part not in node or not isinstance(node[part], dict):
                    node[part] = {}
                node = node[part]
            if parts[-1] not in node and enforce_hot:
                raise ValueError(f"unknown config leaf '{path}'")
            node[parts[-1]] = value

    def as_dict(self) -> dict:
        return copy.deepcopy(self._d)

    def replace(self, data: dict) -> None:
        with self._lock:
            self._d = copy.deepcopy(data)

    # convenience section accessors (fresh dict view; cheap enough off hot path)
    @property
    def world(self) -> dict: return self._d["world"]

    @property
    def weather(self) -> dict: return self._d["weather"]

    @property
    def events(self) -> dict: return self._d["events"]

    @property
    def flora(self) -> dict: return self._d["flora"]

    @property
    def decomposer(self) -> dict: return self._d["decomposer"]

    @property
    def fauna(self) -> dict: return self._d["fauna"]

    @property
    def energy(self) -> dict: return self._d["energy"]

    @property
    def genetics(self) -> dict: return self._d["genetics"]

    @property
    def speciation(self) -> dict: return self._d["speciation"]

    @property
    def scent(self) -> dict: return self._d["scent"]

    @property
    def sim(self) -> dict: return self._d["sim"]

    @property
    def monitor(self) -> dict: return self._d["monitor"]

    @property
    def server(self) -> dict: return self._d["server"]
