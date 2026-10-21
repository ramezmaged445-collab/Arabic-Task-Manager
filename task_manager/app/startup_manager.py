"""إدارة التشغيل مع بدء Windows (Startup manager).

يستخدم اختصارًا (‎.lnk‎) داخل مجلد بدء التشغيل الخاص بالمستخدم، دون الحاجة
إلى صلاحيات المسؤول. عند التفعيل يبدأ البرنامج مع تسجيل الدخول، ويمكنه
البدء مخفيًا في الخلفية.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)

SHORTCUT_NAME = "ArabicTaskManager.lnk"
RUN_VALUE_NAME = "ArabicTaskManager"


def _startup_folder() -> Path:
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _launch_command(hidden: bool, dry_run: bool = False) -> str:
    """يبني أمر التشغيل المناسب (سكربت Python أو ملف EXE مُجمّع)."""
    if getattr(sys, "frozen", False):
        exe = sys.executable
        args = " --hidden" if hidden else ""
        return f'"{exe}"{args}'
    # تشغيل عبر pythonw.exe لتفادي نافذة الكونسول
    exe = sys.executable
    pythonw = Path(exe).with_name("pythonw.exe")
    interpreter = str(pythonw) if pythonw.exists() else exe
    main_py = Path(__file__).resolve().parent.parent / "main.py"
    args = " --hidden" if hidden else ""
    return f'"{interpreter}" "{main_py}"{args}'


def _working_dir() -> str:
    return str(Path(__file__).resolve().parent.parent)


class StartupManager:
    def __init__(self, name: str = SHORTCUT_NAME) -> None:
        self.name = name

    @property
    def shortcut_path(self) -> Path:
        return _startup_folder() / self.name

    def is_enabled(self) -> bool:
        return self.shortcut_path.exists()

    def enable(self, hidden: bool = True) -> bool:
        """ينشئ الاختصار. يعيد True عند النجاح."""
        folder = _startup_folder()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover
            log.warning("تعذّر إنشاء مجلد بدء التشغيل: %s", exc)
            return False
        path = self.shortcut_path
        try:
            import win32com.client  # type: ignore

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(path))
            if getattr(sys, "frozen", False):
                shortcut.Targetpath = sys.executable
                shortcut.Arguments = "--hidden" if hidden else ""
            else:
                pythonw = Path(sys.executable).with_name("pythonw.exe")
                shortcut.Targetpath = str(pythonw) if pythonw.exists() else sys.executable
                main_py = Path(__file__).resolve().parent.parent / "main.py"
                shortcut.Arguments = f'"{main_py}"' + (" --hidden" if hidden else "")
            shortcut.WorkingDirectory = _working_dir()
            shortcut.IconLocation = sys.executable
            shortcut.Description = "Arabic Task Manager"
            shortcut.save()
            return path.exists()
        except Exception as exc:
            log.warning("تعذّر إنشاء اختصار بدء التشغيل (%s)، سنستخدم ملف دفعي.", exc)
            return self._enable_via_batch(hidden)

    def _enable_via_batch(self, hidden: bool) -> bool:
        """بديل موثوق عند تعذّر إنشاء الاختصار."""
        batch = folder_path = _startup_folder() / "ArabicTaskManager.cmd"
        try:
            folder_path.parent.mkdir(parents=True, exist_ok=True)
            start = "start \"\" " if hidden else ""
            content = f"@echo off\r\n{start}{_launch_command(hidden)}\r\n"
            batch.write_text(content, encoding="utf-8")
            return batch.exists()
        except OSError as exc:  # pragma: no cover
            log.warning("فشل البديل البَتَشي: %s", exc)
            return False

    def disable(self) -> bool:
        """يحذف الاختصار والبدائل. يعيد True إذا لم يبقَ أثر."""
        removed = True
        for path in (
            self.shortcut_path,
            _startup_folder() / "ArabicTaskManager.cmd",
        ):
            try:
                if path.exists():
                    path.unlink()
            except OSError as exc:  # pragma: no cover
                log.warning("تعذّر حذف %s: %s", path, exc)
                removed = False
        return removed

    def update_hidden(self, hidden: bool) -> bool:
        if self.is_enabled():
            return self.enable(hidden=hidden)
        return True
