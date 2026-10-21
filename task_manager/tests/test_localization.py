"""اختبارات الترجمة وحفظ اللغة."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app import localization as L
from app.database import Database
from app.settings_service import SettingsService


class LocalizationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "loc.db")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()
        L.set_language("ar")

    def test_translation_switch(self) -> None:
        L.set_language("ar")
        self.assertEqual(L.tr("status.not_started"), "لم تبدأ")
        self.assertTrue(L.is_rtl())
        L.set_language("en")
        self.assertEqual(L.tr("status.not_started"), "Not started")
        self.assertFalse(L.is_rtl())

    def test_unknown_key_returns_key(self) -> None:
        L.set_language("en")
        self.assertEqual(L.tr("does.not.exist"), "does.not.exist")

    def test_formatting_parameters(self) -> None:
        L.set_language("en")
        self.assertEqual(L.tr("msg.added", title="X"), "Task added: X")

    def test_language_persisted_in_settings(self) -> None:
        settings = SettingsService(self.db)
        settings.set("language", "en")
        self.db.close()
        self.db = Database(Path(self.tmp.name) / "loc.db")
        reloaded = SettingsService(self.db)
        self.assertEqual(reloaded.get("language"), "en")

    def test_status_and_priority_helpers(self) -> None:
        L.set_language("ar")
        self.assertEqual(L.get_translator().priority("urgent"), "عاجلة")
        L.set_language("en")
        self.assertEqual(L.get_translator().view("today"), "Today's Tasks")

    def test_help_and_contact_keys_present(self) -> None:
        keys = [
            "menu.help",
            "menu.about",
            "menu.shortcuts",
            "menu.help_page",
            "menu.contact",
            "menu.contact.whatsapp",
            "menu.contact.email",
            "help.guide.title",
            "help.guide.body",
            "about.body",
            "msg.contact_failed",
        ]
        for lang in ("ar", "en"):
            L.set_language(lang)
            for key in keys:
                self.assertNotEqual(L.tr(key), key, f"missing key {key} for {lang}")

    def test_about_mentions_author_and_version(self) -> None:
        from app import __version__

        for lang in ("ar", "en"):
            L.set_language(lang)
            body = L.tr("about.body", version=__version__)
            self.assertIn(__version__, body)
            self.assertIn("رامز ماجد" if lang == "ar" else "Ramez Maged", body)

    def test_alert_sound_keys_present(self) -> None:
        keys = [
            "settings.alert_sound_file",
            "settings.alert_sound_default",
            "settings.alert_sound_hint",
            "sound.file_filter",
            "sound.play_failed",
            "btn.test_sound",
            "btn.default",
        ]
        for lang in ("ar", "en"):
            L.set_language(lang)
            for key in keys:
                self.assertNotEqual(L.tr(key), key, f"missing key {key} for {lang}")

    def test_language_key_parity(self) -> None:
        ar = set(L._STRINGS["ar"].keys())
        en = set(L._STRINGS["en"].keys())
        self.assertEqual(
            ar,
            en,
            f"keys only in AR: {sorted(ar - en)}; only in EN: {sorted(en - ar)}",
        )

    def test_alert_sound_file_persisted(self) -> None:
        settings = SettingsService(self.db)
        self.assertEqual(settings.get("alert_sound_file"), "")
        settings.set("alert_sound_file", "C:/sounds/my.wav")
        self.db.close()
        self.db = Database(Path(self.tmp.name) / "loc.db")
        reloaded = SettingsService(self.db)
        self.assertEqual(reloaded.get("alert_sound_file"), "C:/sounds/my.wav")


if __name__ == "__main__":
    unittest.main()
