"""Local, fault-tolerant player progress and settings storage."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_SAVE: dict[str, Any] = {
    "high_score": 0, "coins": 0, "unlocked": ["runner"], "selected": "runner",
    "achievements": [], "settings": {"music": True, "sfx": True, "music_volume": 0.3, "sfx_volume": 0.8},
    "stats": {"runs": 0, "distance": 0, "coins": 0, "best_combo": 0, "avoided": 0, "powerups": 0},
}


class SaveManager:
    def __init__(self) -> None:
        root = Path(os.getenv("LOCALAPPDATA", Path.home() / ".local" / "share")) / "PixelEra"
        self.path = root / "save.json"
        self.data = self.load()

    def load(self) -> dict[str, Any]:
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(saved, dict):
                raise ValueError("Save root must be an object")
            merged = json.loads(json.dumps(DEFAULT_SAVE))
            for key, value in saved.items():
                if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key].update(value)
                else:
                    merged[key] = value
            return merged
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return json.loads(json.dumps(DEFAULT_SAVE))

    def write(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(".tmp")
            temp.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
            temp.replace(self.path)
        except OSError:
            # The game remains playable when the profile directory is read-only.
            pass

