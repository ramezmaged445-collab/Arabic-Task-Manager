"""قاعدة بيانات SQLite (Database layer).

يتولى هذا الملف إنشاء قاعدة البيانات وترقيتها (migrations) وتوفير اتصال
آمن يعمل من عدة خيوط (threads) مع تفعيل المفاتيح الأجنبية.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from . import paths

SCHEMA_VERSION = 3

_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'not_started',
        priority TEXT NOT NULL DEFAULT 'normal',
        created_at TEXT NOT NULL,
        updated_at TEXT,
        start_at TEXT,
        due_at TEXT,
        category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
        notes TEXT DEFAULT '',
        completed_at TEXT,
        remind_enabled INTEGER NOT NULL DEFAULT 0,
        remind_offset_minutes INTEGER NOT NULL DEFAULT 15,
        remind_at TEXT,
        read_aloud INTEGER NOT NULL DEFAULT 1,
        alert_sound INTEGER NOT NULL DEFAULT 1,
        repeat_enabled INTEGER NOT NULL DEFAULT 0,
        repeat_interval_minutes INTEGER NOT NULL DEFAULT 10,
        recurrence TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reminder_occurrences (
        oid TEXT PRIMARY KEY,
        task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
        fire_at TEXT NOT NULL,
        kind TEXT NOT NULL DEFAULT 'reminder',
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reminder_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        oid TEXT,
        action TEXT NOT NULL,
        detail TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """,
]

_INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_at)",
    "CREATE INDEX IF NOT EXISTS idx_occ_fire ON reminder_occurrences(fire_at, status)",
    "CREATE INDEX IF NOT EXISTS idx_occ_task ON reminder_occurrences(task_id)",
]

# الأعمدة المطلوبة في جدول المهام مع تعريفها الافتراضي (لترقية القواعد القديمة)
_TASK_COLUMNS = {
    "description": "TEXT DEFAULT ''",
    "status": "TEXT NOT NULL DEFAULT 'not_started'",
    "priority": "TEXT NOT NULL DEFAULT 'normal'",
    "updated_at": "TEXT",
    "start_at": "TEXT",
    "due_at": "TEXT",
    "category_id": "INTEGER REFERENCES categories(id) ON DELETE SET NULL",
    "notes": "TEXT DEFAULT ''",
    "completed_at": "TEXT",
    "remind_enabled": "INTEGER NOT NULL DEFAULT 0",
    "remind_offset_minutes": "INTEGER NOT NULL DEFAULT 15",
    "remind_at": "TEXT",
    "read_aloud": "INTEGER NOT NULL DEFAULT 1",
    "alert_sound": "INTEGER NOT NULL DEFAULT 1",
    "repeat_enabled": "INTEGER NOT NULL DEFAULT 0",
    "repeat_interval_minutes": "INTEGER NOT NULL DEFAULT 10",
    "recurrence": "TEXT",
}


class Database:
    """غلاف بسيط حول اتصال SQLite آمن للخيوط."""

    def __init__(self, path: Optional[str | Path] = None) -> None:
        self.path = Path(path) if path else paths.database_path()
        self._lock = threading.RLock()
        self._conn: Optional[sqlite3.Connection] = None
        self.connect()

    def connect(self) -> None:
        assert self.path is not None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self.path),
            check_same_thread=False,
            isolation_level=None,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA busy_timeout = 5000")
        self._migrate()

    # ------------------------------------------------------------------
    # ترقية البنية
    # ------------------------------------------------------------------
    def _migrate(self) -> None:
        with self._lock:
            for statement in _SCHEMA_STATEMENTS:
                self._conn.execute(statement)
            current = self._get_user_version()
            if current < SCHEMA_VERSION:
                self._apply_migrations(current)
                self._set_user_version(SCHEMA_VERSION)
            # إنشاء الفهارس بعد التأكد من وجود الأعمدة
            for statement in _INDEX_STATEMENTS:
                self._conn.execute(statement)

    def _get_user_version(self) -> int:
        row = self._conn.execute("PRAGMA user_version").fetchone()
        return int(row[0]) if row else 0

    def _set_user_version(self, version: int) -> None:
        self._conn.execute(f"PRAGMA user_version = {int(version)}")

    def _apply_migrations(self, from_version: int) -> None:
        """ترقيات تدريجية تحافظ على بيانات المستخدم."""
        columns = {
            row["name"]
            for row in self._conn.execute("PRAGMA table_info(tasks)").fetchall()
        }
        for name, definition in _TASK_COLUMNS.items():
            if name not in columns:
                self._conn.execute(f"ALTER TABLE tasks ADD COLUMN {name} {definition}")

    # ------------------------------------------------------------------
    # تنفيذ الاستعلامات
    # ------------------------------------------------------------------
    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """مدير سياق لتنفيذ عدة عمليات داخل معاملة واحدة."""
        with self._lock:
            self._conn.execute("BEGIN")
            try:
                yield self._conn
            except Exception:
                self._conn.execute("ROLLBACK")
                raise
            else:
                self._conn.execute("COMMIT")

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.execute(sql, tuple(params))

    def executemany(self, sql: str, seq: Iterable[Iterable[Any]]) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.executemany(sql, [tuple(p) for p in seq])

    def query_one(self, sql: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            return cur.fetchone()

    def query_all(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            return cur.fetchall()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.commit()
                finally:
                    self._conn.close()
                self._conn = None

    def backup_to(self, destination: str | Path) -> None:
        """إنشاء نسخة احتياطية متسقة للقاعدة الحالية."""
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            target = sqlite3.connect(str(destination))
            try:
                self._conn.backup(target)
            finally:
                target.close()
