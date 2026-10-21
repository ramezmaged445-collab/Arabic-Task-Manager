"""مسارات التطبيق (Application paths).

يحدد مكان حفظ قاعدة البيانات والإعدادات والنسخ الاحتياطية داخل مجلد بيانات
المستخدم حتى لا نفقد البيانات عند تحديث البرنامج.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_DIR_NAME = "ArabicTaskManager"


def _base_dir() -> Path:
    """يعيد المجلد الأساسي لبيانات المستخدم على Windows."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_DIR_NAME
    # بديل عند غياب APPDATA (مثل بيئات الاختبار)
    return Path.home() / (".config") / APP_DIR_NAME


def app_data_dir() -> Path:
    """مجلد بيانات التطبيق، يُنشأ تلقائيًا عند الحاجة."""
    path = _base_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    """مسار ملف قاعدة بيانات SQLite."""
    override = os.environ.get("TM_DB_PATH")
    if override:
        return Path(override)
    return app_data_dir() / "tasks.db"


def backups_dir() -> Path:
    """مجلد النسخ الاحتياطية الافتراضي."""
    path = app_data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    """مجلد السجلات."""
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path
