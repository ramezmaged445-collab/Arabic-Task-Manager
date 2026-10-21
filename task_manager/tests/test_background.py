"""اختبارات الخلفية: النسخة الواحدة، التشغيل مع Windows، استمرار الجدولة."""

from __future__ import annotations

import os
import tempfile
import threading
import time
import unittest
from datetime import datetime
from pathlib import Path

from app import timeutil
from app.database import Database
from app.reminder_service import ReminderScheduler, ReminderService
from app.single_instance import SingleInstance
from app.startup_manager import StartupManager
from app.task_service import TaskService


class SingleInstanceTestCase(unittest.TestCase):
    def test_second_instance_is_rejected(self) -> None:
        name = "Global\\ArabicTaskManager_Test_%d" % os.getpid()
        first = SingleInstance(name=name)
        second = SingleInstance(name=name)
        self.assertTrue(first.acquire())
        self.assertFalse(second.acquire())
        first.release()
        second.release()


class StartupManagerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self._old_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = self.tmp.name

    def tearDown(self) -> None:
        if self._old_appdata is not None:
            os.environ["APPDATA"] = self._old_appdata
        else:
            os.environ.pop("APPDATA", None)
        self.tmp.cleanup()

    def test_enable_and_disable(self) -> None:
        manager = StartupManager(name="TestArabicTaskManager.lnk")
        self.assertFalse(manager.is_enabled())
        self.assertTrue(manager.enable(hidden=True))
        self.assertTrue(manager.is_enabled())
        self.assertTrue(manager.disable())
        self.assertFalse(manager.is_enabled())


class BackgroundSchedulingTestCase(unittest.TestCase):
    """يتحقق من استمرار الجدولة دون واجهة (نافذة مخفية)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "bg.db")
        self.tasks = TaskService(self.db)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_scheduler_thread_fires(self) -> None:
        now = timeutil.now()
        self.tasks.create_task(
            {
                "title": "خلفية",
                "remind_enabled": 1,
                "remind_at": timeutil.to_db(now),
            }
        )
        fired: list[dict] = []
        event = threading.Event()

        def on_due(items):
            fired.extend(items)
            event.set()

        service = ReminderService(self.db, self.tasks)
        scheduler = ReminderScheduler(service, on_due=on_due, interval_seconds=0.05)
        scheduler.start()
        try:
            self.assertTrue(event.wait(timeout=3.0), "لم يتم إطلاق التذكير في الخلفية")
        finally:
            scheduler.stop()
        self.assertEqual(len(fired), 1)
        self.assertFalse(scheduler.is_running)

    def test_run_once_after_hide_keeps_working(self) -> None:
        now = timeutil.now()
        self.tasks.create_task(
            {
                "title": "مستمر",
                "remind_enabled": 1,
                "remind_at": timeutil.to_db(now),
            }
        )
        service = ReminderService(self.db, self.tasks)
        scheduler = ReminderScheduler(service, on_due=lambda i: None)
        # نافذة مخفية لا تؤثر على دورة الجدولة
        first = scheduler.run_once(startup=True)
        self.assertEqual(len(first["due"]), 1)


if __name__ == "__main__":
    unittest.main()
