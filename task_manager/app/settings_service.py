"""خدمة الإعدادات (Settings service).

تُخزّن الإعدادات داخل جدول ``settings`` في قاعدة البيانات، وتُحمّل عند
بدء البرنامج فتبقى اللغة والتفضيلات محفوظة بين التشغيلات.
"""

from __future__ import annotations

import json
from typing import Any

from .database import Database

DEFAULTS: dict[str, Any] = {
    "language": "ar",
    "sound_enabled": True,
    "alert_sound": True,
    "alert_sound_file": "",
    "reminders_enabled": True,
    "default_reminder_minutes": 15,
    "default_priority": "normal",
    "auto_repeat": False,
    "repeat_interval_minutes": 10,
    "date_format": "iso",
    "start_with_windows": False,
    "start_hidden": True,
    "run_in_background": True,
    "voice_id": "",
    "last_view": "all",
    "sort_by": "due",
}


class SettingsService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self._cache: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        self._cache = dict(DEFAULTS)
        rows = self.db.query_all("SELECT key, value FROM settings")
        for row in rows:
            try:
                self._cache[row["key"]] = json.loads(row["value"])
            except (ValueError, TypeError):
                self._cache[row["key"]] = row["value"]

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._cache:
            return self._cache[key]
        return DEFAULTS.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self.db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, json.dumps(value, ensure_ascii=False)),
        )

    def update(self, values: dict[str, Any]) -> None:
        with self.db.transaction() as conn:
            for key, value in values.items():
                self._cache[key] = value
                conn.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, json.dumps(value, ensure_ascii=False)),
                )

    def as_dict(self) -> dict[str, Any]:
        return dict(self._cache)
