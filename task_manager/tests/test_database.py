"""اختبارات قاعدة البيانات والنسخ الاحتياطي والاستعادة."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.backup_service import BackupError, BackupService
from app.database import SCHEMA_VERSION, Database
from app.settings_service import SettingsService


class DatabaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.db"
        self.db = Database(self.db_path)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_schema_created_and_version(self) -> None:
        tables = {
            r["name"]
            for r in self.db.query_all("SELECT name FROM sqlite_master WHERE type='table'")
        }
        for expected in ("tasks", "categories", "reminder_occurrences", "reminder_log", "settings"):
            self.assertIn(expected, tables)
        row = self.db.query_one("PRAGMA user_version")
        self.assertEqual(int(row[0]), SCHEMA_VERSION)

    def test_foreign_key_cascade_on_delete(self) -> None:
        self.db.execute(
            "INSERT INTO tasks (title, created_at) VALUES (?, ?)", ("t", "2026-01-01 00:00:00")
        )
        task_id = self.db.query_one("SELECT id FROM tasks")["id"]
        self.db.execute(
            "INSERT INTO reminder_occurrences (oid, task_id, fire_at) VALUES (?,?,?)",
            ("1:1", task_id, "2026-01-01 00:00:00"),
        )
        self.db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.assertEqual(self.db.query_all("SELECT * FROM reminder_occurrences"), [])

    def test_settings_persist(self) -> None:
        settings = SettingsService(self.db)
        settings.set("language", "en")
        settings.update({"default_reminder_minutes": 30})
        # إعادة التحميل من نفس الملف
        self.db.close()
        self.db = Database(self.db_path)
        reloaded = SettingsService(self.db)
        self.assertEqual(reloaded.get("language"), "en")
        self.assertEqual(reloaded.get("default_reminder_minutes"), 30)

    def test_backup_and_restore(self) -> None:
        settings = SettingsService(self.db)
        settings.set("language", "en")
        self.db.execute(
            "INSERT INTO tasks (title, created_at) VALUES (?, ?)", ("مهمة", "2026-01-01 00:00:00")
        )
        backup = BackupService(self.db)
        path = backup.create_backup(Path(self.tmp.name) / "backup.db")
        self.assertTrue(path.exists())

        # نعدّل بعد النسخة ثم نستعيد
        self.db.execute("DELETE FROM tasks")
        backup.restore_backup(path)
        rows = self.db.query_all("SELECT title FROM tasks")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "مهمة")

    def test_invalid_backup_rejected(self) -> None:
        bad = Path(self.tmp.name) / "bad.db"
        bad.write_text("not a database", encoding="utf-8")
        backup = BackupService(self.db)
        with self.assertRaises(BackupError):
            backup.restore_backup(bad)

    def test_migration_preserves_data(self) -> None:
        # محاكاة قاعدة قديمة ثم تشغيل الترقية
        old_path = Path(self.tmp.name) / "old.db"
        conn = sqlite3.connect(str(old_path))
        conn.execute("CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT, created_at TEXT)")
        conn.execute("INSERT INTO tasks (title, created_at) VALUES ('قديم','2020-01-01 00:00:00')")
        conn.commit()
        conn.close()
        upgraded = Database(old_path)
        try:
            row = upgraded.query_one("SELECT title FROM tasks")
            self.assertEqual(row["title"], "قديم")
            columns = {r["name"] for r in upgraded.query_all("PRAGMA table_info(tasks)")}
            self.assertIn("recurrence", columns)
            self.assertIn("remind_at", columns)
        finally:
            upgraded.close()


if __name__ == "__main__":
    unittest.main()
