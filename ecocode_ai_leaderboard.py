"""Simple JSON leaderboard for hackathon gamification."""

from __future__ import annotations

import json
import os
import time
from typing import Any

ROOT = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(ROOT, "leaderboard.json")


def load_entries() -> list[dict[str, Any]]:
    if not os.path.isfile(PATH):
        return []
    try:
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def add_entry(name: str, green_score: float, reduction_pct: float | None, note: str = "") -> None:
    entries = load_entries()
    entries.append(
        {
            "name": (name or "Anonymous")[:40],
            "green_score": round(float(green_score), 1),
            "reduction_pct": None if reduction_pct is None else round(float(reduction_pct), 1),
            "note": note[:120],
            "ts": time.time(),
        }
    )
    entries.sort(key=lambda x: x.get("green_score", 0), reverse=True)
    entries = entries[:30]
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
