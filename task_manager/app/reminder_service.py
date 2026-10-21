"""خدمة التذكيرات وجدولتها (Reminder service & scheduler).

تفصل منطق حساب مواعيد التذكير والتكرار ومنع التكرار عن الواجهة، مع خيط
جدولة مستقل يستخدم ``Event.wait`` (وليس ``time.sleep`` في مسار الواجهة)
حتى لا تتجمّد واجهة المستخدم.

كل مرة مجدولة للتذكير تحصل على معرّف فريد محفوظ في قاعدة البيانات، ما
يمنع تكرار التنبيه نفسه حتى بعد إعادة تشغيل البرنامج.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional

from . import localization as L
from . import timeutil
from .database import Database
from .task_service import TaskService

log = logging.getLogger(__name__)

MISSED_GRACE = timedelta(seconds=90)

STATUS_PENDING = "pending"
STATUS_FIRED = "fired"
STATUS_MISSED = "missed"
STATUS_REVIEWED = "reviewed"
STATUS_DISMISSED = "dismissed"
STATUS_COMPLETED = "completed"


def reminder_message(task: dict, now: Optional[datetime] = None, lang: str = "ar") -> str:
    """يبني نص التنبيه المنطوق/المعروض حسب اللغة والوقت المتبقي."""
    now = now or timeutil.now()
    title = task.get("title", "")
    due = timeutil.from_db(task.get("due_at"))
    if due is None:
        when = (
            "حان وقت تذكيرك بهذه المهمة."
            if lang == "ar"
            else "It is time for this task reminder."
        )
    else:
        delta = due - now
        if abs(delta.total_seconds()) < 60:
            when = "موعد المهمة قد حان الآن." if lang == "ar" else "The task is due now."
        else:
            human = timeutil.humanize_delta(delta, lang)
            if lang == "ar":
                when = (
                    f"متبقي {human} على موعد المهمة."
                    if delta.total_seconds() > 0
                    else f"تأخر الموعد بمقدار {human}."
                )
            else:
                when = (
                    f"The task is due {human}."
                    if delta.total_seconds() > 0
                    else f"The task is overdue by {human}."
                )
    if lang == "ar":
        return f"تذكير بمهمة: {title}. {when}"
    return f"Task reminder: {title}. {when}"


class ReminderService:
    def __init__(
        self,
        db: Database,
        task_service: TaskService,
        clock: Callable[[], datetime] = timeutil.now,
    ) -> None:
        self.db = db
        self.tasks = task_service
        self.clock = clock

    # ------------------------------------------------------------------
    # توليد وإدارة المرات المجدولة
    # ------------------------------------------------------------------
    @staticmethod
    def occurrence_key(task_id: int, fire_dt: datetime) -> str:
        return f"{task_id}:{int(fire_dt.timestamp())}"

    def sync(self, now: Optional[datetime] = None) -> None:
        """يتأكد من وجود مرة مجدولة لكل مهمة مفعّل تذكيرها، وينظّف الملغاة."""
        now = now or self.clock()
        enabled_tasks = self.db.query_all(
            "SELECT * FROM tasks WHERE remind_enabled = 1 AND status != 'completed'"
        )
        valid_keys: set[str] = set()
        for raw in enabled_tasks:
            task = dict(raw)
            fire = self.tasks.reminder_time(task)
            if fire is None:
                continue
            key = self.occurrence_key(task["id"], fire)
            valid_keys.add(key)
            exists = self.db.query_one(
                "SELECT oid FROM reminder_occurrences WHERE oid = ?", (key,)
            )
            if not exists:
                self.db.execute(
                    "INSERT INTO reminder_occurrences "
                    "(oid, task_id, fire_at, kind, status, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (
                        key,
                        task["id"],
                        timeutil.to_db(fire),
                        "reminder",
                        STATUS_PENDING,
                        timeutil.to_db(now),
                        timeutil.to_db(now),
                    ),
                )

        # إزالة المرات المعلّقة التي لم تعد صالحة (أُكملت المهمة أو أُلغي التذكير)
        # مع الحفاظ على مرات التكرار والتأجيل
        pending = self.db.query_all(
            "SELECT oid, task_id, kind FROM reminder_occurrences WHERE status = ?",
            (STATUS_PENDING,),
        )
        for row in pending:
            if row["kind"] in ("repeat", "snooze"):
                continue
            if row["oid"] not in valid_keys:
                self.db.execute(
                    "UPDATE reminder_occurrences SET status = ?, updated_at = ? WHERE oid = ?",
                    (STATUS_DISMISSED, timeutil.to_db(now), row["oid"]),
                )

    def _row_to_item(self, row) -> dict:
        task = self.tasks.get_task(row["task_id"])
        return {
            "oid": row["oid"],
            "task_id": row["task_id"],
            "fire_at": row["fire_at"],
            "status": row["status"],
            "task": task,
        }

    def tick(
        self, now: Optional[datetime] = None, startup: bool = False
    ) -> dict[str, list[dict]]:
        """ينفّذ دورة جدولة. يعيد التذكيرات المستحقة والفائتة."""
        now = now or self.clock()
        self.sync(now)
        rows = self.db.query_all(
            "SELECT * FROM reminder_occurrences "
            "WHERE status = ? AND fire_at <= ? ORDER BY fire_at",
            (STATUS_PENDING, timeutil.to_db(now)),
        )
        due: list[dict] = []
        missed: list[dict] = []
        for row in rows:
            fire = timeutil.from_db(row["fire_at"])
            if startup and fire is not None and (now - fire) > MISSED_GRACE:
                self.db.execute(
                    "UPDATE reminder_occurrences SET status = ?, updated_at = ? WHERE oid = ?",
                    (STATUS_MISSED, timeutil.to_db(now), row["oid"]),
                )
                missed.append(self._row_to_item(row))
            else:
                self._fire_row(row, now)
                due.append(self._row_to_item(row))
        return {"due": due, "missed": missed}

    def _fire_row(self, row, now: datetime) -> None:
        self.db.execute(
            "UPDATE reminder_occurrences SET status = ?, updated_at = ? WHERE oid = ?",
            (STATUS_FIRED, timeutil.to_db(now), row["oid"]),
        )
        self.log_action(row["task_id"], row["oid"], "fired")
        self._schedule_repeat(row["task_id"], now)

    def _schedule_repeat(self, task_id: int, now: datetime) -> None:
        task = self.tasks.get_task(task_id)
        if not task or not task.get("repeat_enabled"):
            return
        if task.get("status") == L.STATUS_COMPLETED:
            return
        interval = max(1, int(task.get("repeat_interval_minutes") or 10))
        next_fire = now + timedelta(minutes=interval)
        key = self.occurrence_key(task_id, next_fire)
        exists = self.db.query_one(
            "SELECT oid FROM reminder_occurrences WHERE oid = ?", (key,)
        )
        if not exists:
            self.db.execute(
                "INSERT INTO reminder_occurrences "
                "(oid, task_id, fire_at, kind, status, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    key,
                    task_id,
                    timeutil.to_db(next_fire),
                    "repeat",
                    STATUS_PENDING,
                    timeutil.to_db(now),
                    timeutil.to_db(now),
                ),
            )

    # ------------------------------------------------------------------
    def snooze(self, oid: str, minutes: int, now: Optional[datetime] = None) -> None:
        now = now or self.clock()
        new_fire = now + timedelta(minutes=minutes)
        self.db.execute(
            "UPDATE reminder_occurrences SET fire_at = ?, status = ?, kind = ?, updated_at = ? "
            "WHERE oid = ?",
            (timeutil.to_db(new_fire), STATUS_PENDING, "snooze", timeutil.to_db(now), oid),
        )
        row = self.db.query_one("SELECT task_id FROM reminder_occurrences WHERE oid = ?", (oid,))
        if row:
            self.log_action(row["task_id"], oid, "snoozed", str(minutes))

    def acknowledge_task(self, task_id: int, now: Optional[datetime] = None) -> None:
        """يُلغي كل التذكيرات المعلّقة لمهمة (عند إكمالها أو التعامل معها)."""
        now = now or self.clock()
        self.db.execute(
            "UPDATE reminder_occurrences SET status = ?, updated_at = ? "
            "WHERE task_id = ? AND status IN (?, ?, ?)",
            (
                STATUS_COMPLETED,
                timeutil.to_db(now),
                task_id,
                STATUS_PENDING,
                STATUS_MISSED,
                STATUS_FIRED,
            ),
        )

    def mark_status(self, oid: str, status: str, now: Optional[datetime] = None) -> None:
        now = now or self.clock()
        self.db.execute(
            "UPDATE reminder_occurrences SET status = ?, updated_at = ? WHERE oid = ?",
            (status, timeutil.to_db(now), oid),
        )

    # ------------------------------------------------------------------
    # التذكيرات الفائتة
    # ------------------------------------------------------------------
    def list_missed(self, now: Optional[datetime] = None, days: int = 14) -> list[dict]:
        now = now or self.clock()
        cutoff = now - timedelta(days=days)
        rows = self.db.query_all(
            "SELECT o.* FROM reminder_occurrences o "
            "JOIN tasks t ON t.id = o.task_id "
            "WHERE o.status = ? AND t.status != 'completed' AND o.fire_at >= ? "
            "ORDER BY o.fire_at DESC",
            (STATUS_MISSED, timeutil.to_db(cutoff)),
        )
        return [self._row_to_item(r) for r in rows]

    def review_item(self, oid: str, now: Optional[datetime] = None) -> Optional[dict]:
        now = now or self.clock()
        row = self.db.query_one("SELECT * FROM reminder_occurrences WHERE oid = ?", (oid,))
        if not row:
            return None
        self.mark_status(oid, STATUS_REVIEWED, now)
        item = self._row_to_item(row)
        item["status"] = STATUS_REVIEWED
        return item

    def dismiss_all_missed(self, now: Optional[datetime] = None) -> None:
        now = now or self.clock()
        self.db.execute(
            "UPDATE reminder_occurrences SET status = ?, updated_at = ? WHERE status = ?",
            (STATUS_DISMISSED, timeutil.to_db(now), STATUS_MISSED),
        )

    # ------------------------------------------------------------------
    def log_action(self, task_id: Optional[int], oid: Optional[str], action: str, detail: str = "") -> None:
        self.db.execute(
            "INSERT INTO reminder_log (task_id, oid, action, detail, created_at) "
            "VALUES (?,?,?,?,?)",
            (task_id, oid, action, detail, timeutil.to_db(self.clock())),
        )


class ReminderScheduler:
    """خيط جدولة يستدعي callback عند استحقاق تذكير دون تجميد الواجهة."""

    def __init__(
        self,
        service: ReminderService,
        on_due: Callable[[list[dict]], None],
        on_missed: Callable[[list[dict]], None] | None = None,
        interval_seconds: float = 15.0,
    ) -> None:
        self.service = service
        self.on_due = on_due
        self.on_missed = on_missed
        self.interval = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._first = True

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="reminder-scheduler", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def run_once(self, now: Optional[datetime] = None, startup: bool = False) -> dict:
        """دورة واحدة (تُستخدم مباشرة في الاختبارات)."""
        return self.service.tick(now, startup=startup)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                startup = self._first
                result = self.service.tick(startup=startup)
                if startup and result["missed"] and self.on_missed:
                    self.on_missed(result["missed"])
                if result["due"] and self.on_due:
                    self.on_due(result["due"])
                self._first = False
            except Exception as exc:  # pragma: no cover
                log.exception("خطأ في دورة الجدولة: %s", exc)
            self._stop.wait(self.interval)
