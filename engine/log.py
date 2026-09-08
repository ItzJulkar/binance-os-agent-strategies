"""Append-only JSONL logger consumed by the live terminal."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class StrategyLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8")

    def _write(self, kind: str, **data: Any) -> None:
        rec = {"t": _utcnow(), "kind": kind, **data}
        self._fh.write(json.dumps(rec, default=str) + "\n")
        self._fh.flush()

    def event(self, event: str, **payload: Any) -> None:
        self._write("event", event=event, **payload)

    def snapshot(self, **payload: Any) -> None:
        self._write("snapshot", **payload)

    def close(self) -> None:
        try:
            self._fh.flush()
            self._fh.close()
        except Exception:
            return
