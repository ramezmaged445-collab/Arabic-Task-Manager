"""اختبارات جدولة التذكيرات: الاستحقاق، التكرار، التأجيل، منع التكرار، الفائت."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from app import localization as L
from app import timeutil
from app.database import Database
from app.reminder_service import (
    ReminderScheduler,
    ReminderService,
    STATUS_FIRED,
    STATUS_MISSED,
    STATUS_REVIEWED,
)
from app.task_service import TaskService


class Clock:
    """ساعة وهمية حتمية للاختبارات."""

    def __init__(self, start: datetime) -> None:
        self.value = start

    def __call__(self) -> datetime:
        return self.value

    def advance(self, **kwargs) -> None:
        self.value = self.value + timedelta(**kwargs)


class ReminderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "rem.db")
        self.tasks = TaskService(self.db)
        self.clock = Clock(datetime(2026, 5, 10, 9, 0, 0))
        self.reminders = ReminderService(self.db, self.tasks, clock=self.clock)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def _task_with_due(self, **kwargs) -> int:
        data = {
            "title": kwargs.pop("title", "مهمة"),
            "due_at": timeutil.to_db(kwargs.pop("due_at")),
            "remind_enabled": 1,
            "remind_offset_minutes": kwargs.pop("offset", 15),
            "repeat_enabled": kwargs.pop("repeat", 0),
            "repeat_interval_minutes": kwargs.pop("interval", 10),
        }
        data.update(kwargs)
        return self.tasks.create_task(data)

    def test_occurrence_created_and_fires_once(self) -> None:
        due = datetime(2026, 5, 10, 9, 30, 0)
        self._task_with_due(due_at=due, offset=15)  # تذكير 9:15
        result = self.reminders.tick()
        self.assertEqual(result["due"], [])
        self.clock.advance(minutes=15)
        first = self.reminders.tick()
        self.assertEqual(len(first["due"]), 1)
        # منع التكرار: الدورة التالية لا تعيد التنبيه
        second = self.reminders.tick()
        self.assertEqual(second["due"], [])

    def test_no_reminder_when_disabled_or_completed(self) -> None:
        due = datetime(2026, 5, 10, 9, 5, 0)
        task_id = self._task_with_due(due_at=due, offset=0)
        self.tasks.complete_task(task_id)
        self.clock.advance(minutes=10)
        result = self.reminders.tick()
        self.assertEqual(result["due"], [])

    def test_repeat_scheduling(self) -> None:
        due = datetime(2026, 5, 10, 9, 0, 0)
        self._task_with_due(due_at=due, offset=0, repeat=1, interval=10)
        first = self.reminders.tick()
        self.assertEqual(len(first["due"]), 1)
        self.clock.advance(minutes=5)
        self.assertEqual(self.reminders.tick()["due"], [])
        self.clock.advance(minutes=5)  # 9:10
        second = self.reminders.tick()
        self.assertEqual(len(second["due"]), 1)

    def test_snooze(self) -> None:
        due = datetime(2026, 5, 10, 9, 0, 0)
        self._task_with_due(due_at=due, offset=0)
        first = self.reminders.tick()
        oid = first["due"][0]["oid"]
        self.reminders.snooze(oid, 5)
        self.clock.advance(minutes=4)
        self.assertEqual(self.reminders.tick()["due"], [])
        self.clock.advance(minutes=1)
        self.assertEqual(len(self.reminders.tick()["due"]), 1)

    def test_missed_detection_on_startup(self) -> None:
        due = datetime(2026, 5, 10, 6, 0, 0)
        self._task_with_due(due_at=due, offset=0)  # فات منذ 3 ساعات
        result = self.reminders.tick(startup=True)
        self.assertEqual(result["due"], [])
        self.assertEqual(len(result["missed"]), 1)
        missed = self.reminders.list_missed()
        self.assertEqual(len(missed), 1)
        self.assertEqual(missed[0]["status"], STATUS_MISSED)

    def test_review_missed_item(self) -> None:
        due = datetime(2026, 5, 10, 6, 0, 0)
        self._task_with_due(due_at=due, offset=0)
        self.reminders.tick(startup=True)
        missed = self.reminders.list_missed()
        reviewed = self.reminders.review_item(missed[0]["oid"])
        self.assertIsNotNone(reviewed)
        self.assertEqual(reviewed["status"], STATUS_REVIEWED)
        self.assertEqual(self.reminders.list_missed(), [])

    def test_dismiss_all_missed(self) -> None:
        due = datetime(2026, 5, 10, 6, 0, 0)
        self._task_with_due(due_at=due, offset=0)
        self.reminders.tick(startup=True)
        self.reminders.dismiss_all_missed()
        self.assertEqual(self.reminders.list_missed(), [])

    def test_acknowledge_task_reopens_after_complete(self) -> None:
        due = datetime(2026, 5, 10, 11, 0, 0)
        task_id = self._task_with_due(due_at=due, offset=0)
        self.reminders.sync()
        self.reminders.acknowledge_task(task_id)
        self.clock.advance(hours=3)
        self.assertEqual(self.reminders.tick()["due"], [])

    def test_absolute_reminder_time(self) -> None:
        task_id = self.tasks.create_task(
            {
                "title": "مطلق",
                "remind_enabled": 1,
                "remind_at": timeutil.to_db(datetime(2026, 5, 10, 9, 0, 0)),
            }
        )
        result = self.reminders.tick()
        self.assertEqual(len(result["due"]), 1)
        self.assertEqual(result["due"][0]["task_id"], task_id)

    def test_scheduler_run_once(self) -> None:
        due = datetime(2026, 5, 10, 9, 0, 0)
        self._task_with_due(due_at=due, offset=0)
        scheduler = ReminderScheduler(self.reminders, on_due=lambda items: None)
        result = scheduler.run_once(startup=True)
        self.assertEqual(len(result["due"]), 1)


if __name__ == "__main__":
    unittest.main()
