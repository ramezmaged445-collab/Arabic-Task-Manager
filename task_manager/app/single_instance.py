"""منع تشغيل أكثر من نسخة (Single instance guard).

يمنع إنشاء نسخ متعددة من البرنامج دون داعٍ، مع وسيلة بديلة عند غياب
واجهات Windows البرمجية.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

MUTEX_NAME = "Local\\ArabicTaskManager_SingleInstance"


class SingleInstance:
    def __init__(self, name: str = MUTEX_NAME, lock_dir: Path | None = None) -> None:
        self.name = name
        self._handle = None
        self._lock_file = None
        self._already_running = False
        self._use_mutex = True
        self._lock_path = None
        if lock_dir is not None:
            self._lock_path = Path(lock_dir) / "instance.lock"

    def acquire(self) -> bool:
        """يعيد True إذا كانت هذه هي النسخة الأولى."""
        if self._try_mutex():
            return not self._already_running
        return self._try_lockfile()

    def _try_mutex(self) -> bool:
        try:
            import win32api  # type: ignore
            import win32event  # type: ignore
            import winerror  # type: ignore

            self._handle = win32event.CreateMutex(None, False, self.name)
            self._already_running = win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS
            self._use_mutex = True
            return True
        except Exception as exc:
            log.info("تعذّر استخدام Mutex (%s)، سنستخدم قفل ملف.", exc)
            self._use_mutex = False
            return False

    def _try_lockfile(self) -> bool:
        if self._lock_path is None:
            from . import paths

            self._lock_path = paths.app_data_dir() / "instance.lock"
        try:
            self._lock_file = open(self._lock_path, "a+")
            try:
                import msvcrt

                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                self._already_running = True
            return not self._already_running
        except OSError as exc:  # pragma: no cover
            log.warning("تعذّر إنشاء قفل الملف: %s", exc)
            self._already_running = True
            return False

    @property
    def already_running(self) -> bool:
        return self._already_running

    def release(self) -> None:
        if self._handle is not None:
            try:
                import win32api

                win32api.CloseHandle(self._handle)
            except Exception:  # pragma: no cover
                pass
            self._handle = None
        if self._lock_file is not None:
            try:
                import msvcrt

                self._lock_file.seek(0)
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception:  # pragma: no cover
                pass
            try:
                self._lock_file.close()
            except Exception:  # pragma: no cover
                pass
            self._lock_file = None
