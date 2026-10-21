"""اختبارات عمليات المهام والبحث والتصفية والتصنيفات."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from app import localization as L
from app import timeutil
from app.database import Database
from app.task_service import TaskService, ValidationError


class TaskTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "tasks.db"
        self.db = Database(self.db_path)
        self.service = TaskService(self.db)
        timeutil.set_clock(lambda: datetime(2026, 5, 10, 9, 0, 0))

    def tearDown(self) -> None:
        timeutil.reset_clock()
        self.db.close()
        self.tmp.cleanup()

    def _create(self, **kwargs) -> int:
        data = {"title": kwargs.pop("title", "مهمة")}
        data.update(kwargs)
        return self.service.create_task(data)

    def test_add_and_get(self) -> None:
        task_id = self._create(title="تسليم البحث", priority=L.PRIORITY_HIGH)
        task = self.service.get_task(task_id)
        self.assertEqual(task["title"], "تسليم البحث")
        self.assertEqual(task["priority"], L.PRIORITY_HIGH)
        self.assertEqual(task["status"], L.STATUS_NOT_STARTED)

    def test_title_required(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_task({"title": "   "})

    def test_update_task(self) -> None:
        task_id = self._create(title="قديم")
        self.service.update_task(task_id, {"title": "جديد", "notes": "ملاحظة"})
        task = self.service.get_task(task_id)
        self.assertEqual(task["title"], "جديد")
        self.assertEqual(task["notes"], "ملاحظة")

    def test_delete_task(self) -> None:
        task_id = self._create()
        self.service.delete_task(task_id)
        self.assertIsNone(self.service.get_task(task_id))

    def test_status_transitions_and_completed_at(self) -> None:
        task_id = self._create()
        self.service.set_status(task_id, L.STATUS_IN_PROGRESS)
        self.assertEqual(self.service.get_task(task_id)["status"], L.STATUS_IN_PROGRESS)
        self.service.complete_task(task_id)
        task = self.service.get_task(task_id)
        self.assertEqual(task["status"], L.STATUS_COMPLETED)
        self.assertIsNotNone(task["completed_at"])
        self.service.reopen_task(task_id)
        task = self.service.get_task(task_id)
        self.assertEqual(task["status"], L.STATUS_NOT_STARTED)
        self.assertIsNone(task["completed_at"])

    def test_completed_task_moves_to_completed_view(self) -> None:
        task_id = self._create(title="أكملني")
        self.service.complete_task(task_id)
        completed = self.service.list_tasks(view=L.VIEW_COMPLETED)
        self.assertIn(task_id, [t["id"] for t in completed])
        not_started = self.service.list_tasks(view=L.VIEW_NOT_STARTED)
        self.assertNotIn(task_id, [t["id"] for t in not_started])

    def test_task_without_due_date(self) -> None:
        task_id = self._create(title="بدون موعد")
        task = self.service.get_task(task_id)
        self.assertIsNone(task["due_at"])
        overdue = self.service.list_tasks(view=L.VIEW_OVERDUE)
        self.assertNotIn(task_id, [t["id"] for t in overdue])

    def test_search_in_fields(self) -> None:
        self._create(title="رياضيات", description="تمارين الجبر")
        self._create(title="فيزياء", notes="قوانين نيوتن")
        self.assertEqual(len(self.service.list_tasks(search="الجبر")), 1)
        self.assertEqual(len(self.service.list_tasks(search="نيوتن")), 1)
        self.assertEqual(len(self.service.list_tasks(search="مهمة")), 0)

    def test_filter_by_priority_and_status(self) -> None:
        self._create(title="أ", priority=L.PRIORITY_URGENT)
        b = self._create(title="ب", priority=L.PRIORITY_LOW)
        self.service.set_status(b, L.STATUS_IN_PROGRESS)
        urgent = self.service.list_tasks(priority_filter=L.PRIORITY_URGENT)
        self.assertEqual([t["title"] for t in urgent], ["أ"])
        in_progress = self.service.list_tasks(status_filter=L.STATUS_IN_PROGRESS)
        self.assertEqual([t["title"] for t in in_progress], ["ب"])

    def test_today_upcoming_overdue_views(self) -> None:
        now = timeutil.now()
        self._create(title="اليوم", due_at=timeutil.to_db(now + timedelta(hours=2)))
        self._create(title="قادم", due_at=timeutil.to_db(now + timedelta(days=3)))
        self._create(title="متأخر", due_at=timeutil.to_db(now - timedelta(days=1)))
        self.assertEqual([t["title"] for t in self.service.list_tasks(view=L.VIEW_TODAY)], ["اليوم"])
        self.assertIn("قادم", [t["title"] for t in self.service.list_tasks(view=L.VIEW_UPCOMING)])
        self.assertEqual([t["title"] for t in self.service.list_tasks(view=L.VIEW_OVERDUE)], ["متأخر"])

    def test_categories_and_delete_options(self) -> None:
        cat_id = self.service.ensure_category("دراسة")
        t1 = self._create(title="م1", category_id=cat_id)
        t2 = self._create(title="م2", category_id=cat_id)
        self.assertEqual(self.service.category_task_count(cat_id), 2)
        self.service.delete_category(cat_id, delete_tasks=False)
        self.assertIsNone(self.service.get_task(t1)["category_id"])
        self.assertIsNotNone(self.service.get_task(t2))

        cat2 = self.service.ensure_category("عمل")
        t3 = self._create(title="م3", category_id=cat2)
        self.service.delete_category(cat2, delete_tasks=True)
        self.assertIsNone(self.service.get_task(t3))

    def test_persistence_reload(self) -> None:
        task_id = self._create(title="محفوظة")
        self.db.close()
        self.db = Database(self.db_path)
        service = TaskService(self.db)
        self.assertEqual(service.get_task(task_id)["title"], "محفوظة")

    def test_reminder_time_uses_offset(self) -> None:
        due = datetime(2026, 5, 10, 12, 0, 0)
        task_id = self._create(
            title="تذكير",
            due_at=timeutil.to_db(due),
            remind_enabled=1,
            remind_offset_minutes=30,
        )
        task = self.service.get_task(task_id)
        self.assertEqual(self.service.reminder_time(task), datetime(2026, 5, 10, 11, 30, 0))

    def test_due_time_preserves_seconds(self) -> None:
        due = datetime(2026, 5, 10, 12, 34, 56)
        task_id = self._create(title="ثوانٍ", due_at=timeutil.to_db(due))
        task = self.service.get_task(task_id)
        self.assertEqual(task["due_at"], "2026-05-10 12:34:56")
        self.assertEqual(timeutil.from_db(task["due_at"]), due)

    def test_combine_with_datetime_objects(self) -> None:
        from app.timeutil import combine

        self.assertEqual(
            combine(datetime(2026, 5, 10), datetime(2026, 1, 1, 8, 15)),
            datetime(2026, 5, 10, 8, 15),
        )
        self.assertIsNone(combine(None, None))


if __name__ == "__main__":
    unittest.main()
