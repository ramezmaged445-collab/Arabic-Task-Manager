"""خدمة المهام (Task service).

توفّر كل عمليات إضافة وعرض وتعديل وحذف المهام والبحث والتصفية وإدارة
التصنيفات، بعيدًا عن واجهة المستخدم.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from . import localization as L
from . import timeutil
from .database import Database


class ValidationError(Exception):
    """خطأ في صحة البيانات يُعرض للمستخدم عبر الواجهة."""

    def __init__(self, message_key: str) -> None:
        super().__init__(message_key)
        self.message_key = message_key


class TaskService:
    def __init__(self, db: Database) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # التصنيفات
    # ------------------------------------------------------------------
    def list_categories(self) -> list[dict]:
        rows = self.db.query_all(
            "SELECT id, name FROM categories ORDER BY name COLLATE NOCASE"
        )
        return [dict(r) for r in rows]

    def category_name(self, category_id: Optional[int]) -> Optional[str]:
        if not category_id:
            return None
        row = self.db.query_one("SELECT name FROM categories WHERE id = ?", (category_id,))
        return row["name"] if row else None

    def ensure_category(self, name: str) -> int:
        name = name.strip()
        if not name:
            raise ValidationError("category.required_name")
        existing = self.db.query_one(
            "SELECT id FROM categories WHERE name = ? COLLATE NOCASE", (name,)
        )
        if existing:
            return int(existing["id"])
        cur = self.db.execute(
            "INSERT INTO categories (name, created_at) VALUES (?, ?)",
            (name, timeutil.to_db(timeutil.now())),
        )
        return int(cur.lastrowid)

    def rename_category(self, category_id: int, new_name: str) -> None:
        new_name = new_name.strip()
        if not new_name:
            raise ValidationError("category.required_name")
        self.db.execute(
            "UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id)
        )

    def category_task_count(self, category_id: int) -> int:
        row = self.db.query_one(
            "SELECT COUNT(*) AS c FROM tasks WHERE category_id = ?", (category_id,)
        )
        return int(row["c"]) if row else 0

    def delete_category(self, category_id: int, delete_tasks: bool) -> None:
        with self.db.transaction() as conn:
            if delete_tasks:
                conn.execute("DELETE FROM tasks WHERE category_id = ?", (category_id,))
            else:
                conn.execute(
                    "UPDATE tasks SET category_id = NULL WHERE category_id = ?",
                    (category_id,),
                )
            conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))

    # ------------------------------------------------------------------
    # المهام — قراءة
    # ------------------------------------------------------------------
    def get_task(self, task_id: int) -> Optional[dict]:
        row = self.db.query_one(
            """
            SELECT t.*, c.name AS category_name
            FROM tasks t LEFT JOIN categories c ON c.id = t.category_id
            WHERE t.id = ?
            """,
            (task_id,),
        )
        return self._row_to_task(row) if row else None

    def list_tasks(
        self,
        view: str = L.VIEW_ALL,
        search: str = "",
        status_filter: str = "",
        priority_filter: str = "",
        category_filter: str = "",
        due_filter: str = "",
        sort_by: str = "due",
        now: Optional[datetime] = None,
    ) -> list[dict]:
        now = now or timeutil.now()
        sql = [
            """
            SELECT t.*, c.name AS category_name
            FROM tasks t LEFT JOIN categories c ON c.id = t.category_id
            WHERE 1=1
            """
        ]
        params: list[Any] = []

        # القائمة (View)
        if view == L.VIEW_NOT_STARTED:
            sql.append("AND t.status = 'not_started'")
        elif view == L.VIEW_IN_PROGRESS:
            sql.append("AND t.status = 'in_progress'")
        elif view == L.VIEW_COMPLETED:
            sql.append("AND t.status = 'completed'")
        elif view == L.VIEW_TODAY:
            sql.append("AND t.status != 'completed' AND t.due_at IS NOT NULL")
        elif view == L.VIEW_UPCOMING:
            sql.append("AND t.status != 'completed' AND t.due_at IS NOT NULL")
        elif view == L.VIEW_OVERDUE:
            sql.append("AND t.status != 'completed' AND t.due_at IS NOT NULL")

        # البحث النصي
        if search:
            like = f"%{search}%"
            sql.append(
                "AND (t.title LIKE ? OR t.description LIKE ? OR t.notes LIKE ? "
                "OR c.name LIKE ?)"
            )
            params.extend([like, like, like, like])

        # تصفية الحالة
        if status_filter:
            sql.append("AND t.status = ?")
            params.append(status_filter)

        # تصفية الأولوية
        if priority_filter:
            sql.append("AND t.priority = ?")
            params.append(priority_filter)

        # تصفية التصنيف
        if category_filter == "__none__":
            sql.append("AND t.category_id IS NULL")
        elif category_filter:
            sql.append("AND t.category_id = ?")
            params.append(int(category_filter))

        # تصفية تاريخ الاستحقاق
        if due_filter == "none":
            sql.append("AND t.due_at IS NULL")
        elif due_filter == "today":
            sql.append("AND date(t.due_at) = date(?)")
            params.append(timeutil.to_db(now))
        elif due_filter == "week":
            end = now + timedelta(days=7)
            sql.append("AND t.due_at IS NOT NULL AND t.due_at <= ?")
            params.append(timeutil.to_db(end))
        elif due_filter == "overdue":
            sql.append("AND t.status != 'completed' AND t.due_at IS NOT NULL AND t.due_at < ?")
            params.append(timeutil.to_db(now))

        # الترتيب
        order = "ORDER BY "
        if sort_by == "priority":
            order += (
                "CASE t.priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 "
                "WHEN 'normal' THEN 2 ELSE 3 END, t.due_at IS NULL, t.due_at"
            )
        elif sort_by == "title":
            order += "t.title COLLATE NOCASE"
        elif sort_by == "created":
            order += "t.created_at DESC"
        elif sort_by == "status":
            order += (
                "CASE t.status WHEN 'not_started' THEN 0 WHEN 'in_progress' THEN 1 "
                "ELSE 2 END, t.due_at IS NULL, t.due_at"
            )
        else:  # due
            order += "t.due_at IS NULL, t.due_at, t.title COLLATE NOCASE"

        sql.append(order)
        rows = self.db.query_all(" ".join(sql), params)
        tasks = [self._row_to_task(r) for r in rows]

        # تصفية القوائم الزمنية المحسوبة (اليوم/القادمة/المتأخرة)
        if view == L.VIEW_TODAY:
            tasks = [t for t in tasks if self._is_today(t, now)]
        elif view == L.VIEW_UPCOMING:
            tasks = [t for t in tasks if self._is_upcoming(t, now)]
        elif view == L.VIEW_OVERDUE:
            tasks = [t for t in tasks if self._is_overdue(t, now)]
        return tasks

    def _is_today(self, task: dict, now: datetime) -> bool:
        due = timeutil.from_db(task.get("due_at"))
        return bool(due and due.date() == now.date())

    def _is_upcoming(self, task: dict, now: datetime) -> bool:
        due = timeutil.from_db(task.get("due_at"))
        if not due:
            return False
        return now < due <= now + timedelta(days=7)

    def _is_overdue(self, task: dict, now: datetime) -> bool:
        due = timeutil.from_db(task.get("due_at"))
        return bool(due and due < now and task.get("status") != L.STATUS_COMPLETED)

    # ------------------------------------------------------------------
    # المهام — كتابة
    # ------------------------------------------------------------------
    def create_task(self, data: dict) -> int:
        data = self.validate(data)
        now_text = timeutil.to_db(timeutil.now())
        cur = self.db.execute(
            """
            INSERT INTO tasks (
                title, description, status, priority, created_at, updated_at,
                start_at, due_at, category_id, notes, completed_at,
                remind_enabled, remind_offset_minutes, remind_at,
                read_aloud, alert_sound, repeat_enabled, repeat_interval_minutes,
                recurrence
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                data["title"],
                data.get("description", ""),
                data.get("status", L.STATUS_NOT_STARTED),
                data.get("priority", L.PRIORITY_NORMAL),
                now_text,
                now_text,
                data.get("start_at"),
                data.get("due_at"),
                data.get("category_id"),
                data.get("notes", ""),
                data.get("completed_at"),
                int(bool(data.get("remind_enabled", 0))),
                int(data.get("remind_offset_minutes", 15)),
                data.get("remind_at"),
                int(bool(data.get("read_aloud", 1))),
                int(bool(data.get("alert_sound", 1))),
                int(bool(data.get("repeat_enabled", 0))),
                int(data.get("repeat_interval_minutes", 10)),
                data.get("recurrence"),
            ),
        )
        return int(cur.lastrowid)

    def update_task(self, task_id: int, data: dict) -> None:
        data = self.validate(data)
        self.db.execute(
            """
            UPDATE tasks SET
                title = ?, description = ?, status = ?, priority = ?,
                updated_at = ?, start_at = ?, due_at = ?, category_id = ?,
                notes = ?, completed_at = ?, remind_enabled = ?,
                remind_offset_minutes = ?, remind_at = ?, read_aloud = ?,
                alert_sound = ?, repeat_enabled = ?, repeat_interval_minutes = ?,
                recurrence = ?
            WHERE id = ?
            """,
            (
                data["title"],
                data.get("description", ""),
                data.get("status", L.STATUS_NOT_STARTED),
                data.get("priority", L.PRIORITY_NORMAL),
                timeutil.to_db(timeutil.now()),
                data.get("start_at"),
                data.get("due_at"),
                data.get("category_id"),
                data.get("notes", ""),
                data.get("completed_at"),
                int(bool(data.get("remind_enabled", 0))),
                int(data.get("remind_offset_minutes", 15)),
                data.get("remind_at"),
                int(bool(data.get("read_aloud", 1))),
                int(bool(data.get("alert_sound", 1))),
                int(bool(data.get("repeat_enabled", 0))),
                int(data.get("repeat_interval_minutes", 10)),
                data.get("recurrence"),
                task_id,
            ),
        )

    def delete_task(self, task_id: int) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM reminder_occurrences WHERE task_id = ?", (task_id,))
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def set_status(self, task_id: int, status: str) -> None:
        completed_at = None
        if status == L.STATUS_COMPLETED:
            completed_at = timeutil.to_db(timeutil.now())
        self.db.execute(
            "UPDATE tasks SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
            (status, completed_at, timeutil.to_db(timeutil.now()), task_id),
        )

    def complete_task(self, task_id: int) -> None:
        self.set_status(task_id, L.STATUS_COMPLETED)

    def reopen_task(self, task_id: int, status: str = L.STATUS_NOT_STARTED) -> None:
        self.set_status(task_id, status)

    # ------------------------------------------------------------------
    # التحقق من الصحة
    # ------------------------------------------------------------------
    def validate(self, data: dict) -> dict:
        title = (data.get("title") or "").strip()
        if not title:
            raise ValidationError("error.title_required")
        data = dict(data)
        data["title"] = title

        for field in ("start_at", "due_at", "remind_at", "completed_at"):
            value = data.get(field)
            if value and timeutil.from_db(value) is None:
                raise ValidationError("error.bad_date")

        status = data.get("status", L.STATUS_NOT_STARTED)
        if status not in L.STATUS_ORDER:
            data["status"] = L.STATUS_NOT_STARTED
        priority = data.get("priority", L.PRIORITY_NORMAL)
        if priority not in L.PRIORITY_ORDER:
            data["priority"] = L.PRIORITY_NORMAL

        offset = data.get("remind_offset_minutes", 15)
        try:
            data["remind_offset_minutes"] = max(0, int(offset))
        except (TypeError, ValueError):
            data["remind_offset_minutes"] = 15

        interval = data.get("repeat_interval_minutes", 10)
        try:
            data["repeat_interval_minutes"] = max(1, int(interval))
        except (TypeError, ValueError):
            data["repeat_interval_minutes"] = 10
        return data

    # ------------------------------------------------------------------
    # مساعدات
    # ------------------------------------------------------------------
    def _row_to_task(self, row) -> dict:
        task = dict(row)
        task["remind_enabled"] = bool(task.get("remind_enabled"))
        task["read_aloud"] = bool(task.get("read_aloud"))
        task["alert_sound"] = bool(task.get("alert_sound"))
        task["repeat_enabled"] = bool(task.get("repeat_enabled"))
        return task

    def reminder_time(self, task: dict) -> Optional[datetime]:
        """يحسب وقت التذكير: وقت مطلق إن وُجد، وإلا وقت الاستحقاق ناقص المدة."""
        remind_at = timeutil.from_db(task.get("remind_at"))
        if remind_at:
            return remind_at
        due = timeutil.from_db(task.get("due_at"))
        if due:
            return due - timedelta(minutes=int(task.get("remind_offset_minutes") or 0))
        return None
