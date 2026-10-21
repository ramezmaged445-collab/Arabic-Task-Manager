"""اختبارات خدمة التنبيه الصوتي (ملف صوتي مخصص)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.notification_service import NotificationService, play_sound_file


class _FakeSettings:
    def __init__(self, values: dict) -> None:
        self._values = values

    def get(self, key, default=None):
        return self._values.get(key, default)


class NotificationServiceTestCase(unittest.TestCase):
    def test_play_sound_file_empty_returns_false(self) -> None:
        self.assertFalse(play_sound_file(""))
        self.assertFalse(play_sound_file("   ".strip()))

    def test_play_sound_file_missing_returns_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "nope.wav")
            self.assertFalse(play_sound_file(missing))

    def test_play_sound_file_directory_returns_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(play_sound_file(tmp))

    def test_custom_file_reads_from_settings(self) -> None:
        svc = NotificationService(_FakeSettings({"alert_sound_file": "  C:/a/b.mp3  "}))
        self.assertEqual(svc._custom_file(), "C:/a/b.mp3")

    def test_custom_file_empty_when_no_settings(self) -> None:
        self.assertEqual(NotificationService()._custom_file(), "")

    def test_set_settings_updates_source(self) -> None:
        svc = NotificationService()
        svc.set_settings(_FakeSettings({"alert_sound_file": "x.wav"}))
        self.assertEqual(svc._custom_file(), "x.wav")

    def test_custom_file_invalid_value_is_safe(self) -> None:
        svc = NotificationService(_FakeSettings({"alert_sound_file": None}))
        self.assertEqual(svc._custom_file(), "")


if __name__ == "__main__":
    unittest.main()
