"""خدمة النسخ الاحتياطي والاستعادة (Backup service).

تنشئ نسخًا احتياطية متسقة من قاعدة بيانات SQLite، وتتحقق من صلاحية أي
نسخة قبل استعادتها، مع حفظ نسخة أمان من الوضع الحالي قبل الاستبدال.
"""

from __future__ import annotations

import shutil
import sqlite3
import time
from pathlib import Path

from . import paths
from .database import Database


class BackupError(Exception):
    pass


def _validate_sqlite(path: Path) -> bool:
    """يتحقق من أن الملف قاعدة SQLite صالحة تحتوي جداولنا المتوقعة."""
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        conn = sqlite3.connect(str(path))
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('tasks','categories','settings')"
            )
            names = {row[0] for row in cur.fetchall()}
            return "tasks" in names
        finally:
            conn.close()
    except sqlite3.Error:
        return False


class BackupService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_backup(self, destination: str | Path | None = None) -> Path:
        """ينشئ نسخة احتياطية، ويعيد مسارها."""
        if destination is None:
            stamp = time.strftime("%Y%m%d-%H%M%S")
            destination = paths.backups_dir() / f"tasks-backup-{stamp}.db"
        destination = Path(destination)
        if destination.is_dir():
            stamp = time.strftime("%Y%m%d-%H%M%S")
            destination = destination / f"tasks-backup-{stamp}.db"
        if destination.suffix.lower() != ".db":
            destination = destination.with_suffix(destination.suffix + ".db")
        try:
            self.db.backup_to(destination)
        except Exception as exc:  # pragma: no cover
            raise BackupError(str(exc)) from exc
        if not _validate_sqlite(destination):
            raise BackupError("invalid backup")
        return destination

    def restore_backup(self, source: str | Path) -> Path:
        """يستعيد نسخة احتياطية، مع حفظ نسخة أمان من الوضع الحالي."""
        source = Path(source)
        if not _validate_sqlite(source):
            raise BackupError("invalid backup")

        # نسخة أمان من قاعدة البيانات الحالية
        safety = self.create_backup()

        # إغلاق الاتصال الحالي ثم استبدال الملف
        current = Path(self.db.path)
        self.db.close()
        try:
            shutil.copy2(source, current)
        finally:
            self.db.connect()
        return safety
