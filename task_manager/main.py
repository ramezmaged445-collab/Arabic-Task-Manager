"""نقطة الدخول للبرنامج (Application entry point).

التشغيل:
    python main.py            # فتح النافذة الرئيسية
    python main.py --hidden   # البدء في الخلفية (يُستخدم مع بدء Windows)
"""

from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler

import wx


def _setup_logging() -> None:
    from app import paths

    log_file = paths.logs_dir() / "task_manager.log"
    handler = RotatingFileHandler(log_file, maxBytes=512_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Arabic Task Manager")
    parser.add_argument("--hidden", action="store_true", help="ابدأ في الخلفية دون إظهار النافذة")
    return parser.parse_args(argv)


class TaskManagerApp(wx.App):
    def __init__(self, hidden: bool) -> None:
        self._hidden = hidden
        self.controller = None
        super().__init__(redirect=False)

    def OnInit(self) -> bool:  # noqa: N802
        self.SetAppName("ArabicTaskManager")
        from app.background_manager import AppController
        from app.single_instance import SingleInstance

        self.instance = SingleInstance()
        if not self.instance.acquire():
            wx.MessageBox(
                "البرنامج قيد التشغيل بالفعل.\nThe application is already running.",
                "Arabic Task Manager",
                wx.OK | wx.ICON_INFORMATION,
            )
            return False

        self.controller = AppController(self, hidden=self._hidden)
        self.controller.start()
        return True

    def OnExit(self) -> int:  # noqa: N802
        try:
            if self.controller is not None:
                self.controller.shutdown()
        except Exception:
            logging.exception("خطأ عند الخروج")
        try:
            self.instance.release()
        except Exception:
            pass
        return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = _parse_args(argv)
    _setup_logging()

    # تهيئة COM للخيط الرئيسي (مطلوب لـ SAPI)
    try:
        import pythoncom

        pythoncom.CoInitialize()
    except Exception:
        pass

    # تحسين دقة العرض
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = TaskManagerApp(hidden=args.hidden)
    app.MainLoop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
