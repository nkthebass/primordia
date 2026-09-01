"""Plain-English event log (chronicle.md) plus a machine-readable chronicle.jsonl."""
from __future__ import annotations

import json
import os
import threading
from collections import deque

ICONS = {
    "world": "*", "season": "~", "storm": "!", "wildfire": "^", "flood": "=",
    "volcano": "V", "cold_snap": "#", "meteor": "@", "speciation": "+",
    "extinction": "x", "intervention": ">", "note": '"', "gene": "$",
    "milestone": "%", "warning": "?", "resource": "&", "checkpoint": ".",
    "tuning": "/",
}


class Chronicle:
    def __init__(self, root: str, weather=None):
        self.dir = os.path.join(root, "chronicle")
        os.makedirs(self.dir, exist_ok=True)
        self.md = os.path.join(self.dir, "chronicle.md")
        self.jsonl = os.path.join(self.dir, "chronicle.jsonl")
        self.weather = weather
        self._pending: list[dict] = []
        self._lock = threading.Lock()
        self.recent = deque(maxlen=200)
        self.count = 0
        if not os.path.exists(self.md):
            with open(self.md, "w", encoding="utf-8") as f:
                f.write("# The Chronicle of PRIMORDIA\n\n"
                        "_An honest record of everything that happened in this world._\n\n")

    # ------------------------------------------------------------------ write
    def event(self, tick: int, kind: str, text: str, extra: dict | None = None) -> None:
        stamp = self._stamp(tick)
        entry = {"tick": int(tick), "kind": kind, "text": text,
                 "stamp": stamp, "extra": extra or {}}
        with self._lock:
            self._pending.append(entry)
            self.recent.append(entry)
            self.count += 1

    def _stamp(self, tick: int) -> str:
        if self.weather is None:
            return f"t{tick}"
        return f"Year {self.weather.year(tick)}, {self.weather.season(tick)}"

    def flush(self) -> int:
        with self._lock:
            batch, self._pending = self._pending, []
        if not batch:
            return 0
        with open(self.md, "a", encoding="utf-8") as f:
            for e in batch:
                icon = ICONS.get(e["kind"], "-")
                f.write(f"`{icon}` **{e['stamp']}** (t{e['tick']}) — {e['text']}\n\n")
        with open(self.jsonl, "a", encoding="utf-8") as f:
            for e in batch:
                f.write(json.dumps(e, separators=(",", ":")) + "\n")
        return len(batch)

    def tail(self, n: int = 40) -> list[dict]:
        with self._lock:
            return list(self.recent)[-n:][::-1]

    def tail_text(self, n: int = 30) -> str:
        return "\n".join(f"[{e['stamp']}] {e['kind']}: {e['text']}"
                         for e in list(self.recent)[-n:])

    def meta(self) -> dict:
        return {"count": self.count, "recent": list(self.recent)[-200:]}

    def load(self, meta: dict) -> None:
        self.count = int(meta.get("count", 0))
        self.recent = deque(meta.get("recent", []), maxlen=200)
