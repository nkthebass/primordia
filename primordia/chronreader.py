"""Browsable access to the Chronicle without loading 14 MB to answer one question.

The Chronicle is append-only and now runs to 107,000 entries across 14 MB of JSONL. The
viewer only ever showed the last 45, the raw file is too large for an editor to open, and
about ninety-five per cent of it is weather -- 49,178 storms and 25,494 floods against 659
speciations and 25 game-master notes. So there was no way to actually read the world's
history.

This keeps a compact index in memory -- tick, year, kind and the byte range of each line --
and seeks only the lines a query actually matches. The index is rebuilt when the file grows,
which for an append-only file means appending to the index rather than re-reading it.
"""
from __future__ import annotations

import io
import json
import os
import threading

# kinds that are almost all of the file and almost none of the interest
NOISE = ("storm", "flood", "season", "wildfire", "cold_snap")


class ChronicleIndex:
    def __init__(self, path: str, ticks_per_year: int = 2000):
        self.path = path
        self.tpy = max(1, int(ticks_per_year))
        self._lock = threading.Lock()
        self._entries: list[tuple[int, int, str, int, int]] = []   # tick, year, kind, off, len
        self._scanned = 0          # bytes of the file already indexed
        self._kinds: dict[str, int] = {}

    # ------------------------------------------------------------------ index
    def refresh(self) -> None:
        """Index whatever has been appended since last time."""
        with self._lock:
            try:
                size = os.path.getsize(self.path)
            except OSError:
                return
            if size < self._scanned:        # truncated or replaced: start over
                self._entries.clear()
                self._kinds.clear()
                self._scanned = 0
            if size == self._scanned:
                return
            with io.open(self.path, "rb") as f:
                f.seek(self._scanned)
                off = self._scanned
                for raw in f:
                    n = len(raw)
                    try:
                        d = json.loads(raw.decode("utf-8", "replace"))
                        tick = int(d.get("tick", 0))
                        kind = str(d.get("kind", "?"))
                    except Exception:
                        off += n
                        continue
                    self._entries.append((tick, tick // self.tpy, kind, off, n))
                    self._kinds[kind] = self._kinds.get(kind, 0) + 1
                    off += n
                self._scanned = off

    # ------------------------------------------------------------------ query
    def query(self, kinds=None, exclude_noise=True, year_from=None, year_to=None,
              q=None, limit=200, offset=0, newest_first=True) -> dict:
        self.refresh()
        ql = (q or "").strip().lower()
        want = set(kinds) if kinds else None

        sel = []
        for e in self._entries:
            tick, year, kind, _o, _n = e
            if want is not None:
                if kind not in want:
                    continue
            elif exclude_noise and kind in NOISE:
                continue
            if year_from is not None and year < year_from:
                continue
            if year_to is not None and year > year_to:
                continue
            sel.append(e)

        # text search needs the line itself, so it is applied after the cheap filters
        if ql:
            sel = [e for e in sel if ql in self._read(e).get("text", "").lower()]

        total = len(sel)
        if newest_first:
            sel = sel[::-1]
        page = sel[offset:offset + max(1, min(int(limit), 1000))]
        return {
            "total": total,
            "offset": int(offset),
            "returned": len(page),
            "kinds": dict(sorted(self._kinds.items(), key=lambda kv: -kv[1])),
            "indexed": len(self._entries),
            "entries": [self._read(e) for e in page],
        }

    def _read(self, entry) -> dict:
        _tick, _year, _kind, off, n = entry
        try:
            with io.open(self.path, "rb") as f:
                f.seek(off)
                return json.loads(f.read(n).decode("utf-8", "replace"))
        except Exception:
            return {"tick": entry[0], "kind": entry[2], "text": "(unreadable)",
                    "stamp": "", "extra": {}}
