"""مدير الخلفية والتحكم (Background manager / application controller).

يربط الخدمات (قاعدة البيانات، المهام، الإعدادات، التذكيرات، الكلام،
التنبيهات) بالواجهة، ويدير العمل في الخلفية وقائمة انتظار التنبيهات
والتواصل الآمن مع خدمة التذكيرات عبر ``wx.CallAfter``.
"""

from __future__ import annotations

import collections
import logging

import wx

from . import localization as L
from . import timeutil
from .backup_service import BackupService
from .database import Database
from .notification_service import NotificationService
from .reminder_service import ReminderScheduler, ReminderService
from .settings_service import SettingsService
from .speech_service import SpeechService
from .startup_manager import StartupManager
from .task_service import TaskService

log = logging.getLogger(__name__)


class AppController:
    def __init__(self, app: wx.App, hidden: bool = False) -> None:
        self.app = app
        self.start_hidden = hidden
        self.exit_requested = False
        self._pending_missed = False

        # الخدمات
        self.db = Database()
        self.tasks = TaskService(self.db)
        self.config = SettingsService(self.db)
        self.reminders = ReminderService(self.db, self.tasks)
        self.speech = SpeechService()
        self.notifications = NotificationService(self.config)
        self.backup = BackupService(self.db)
        self.startup = StartupManager()

        # اللغة المحفوظة
        L.set_language(self.config.get("language", "ar"))
        self.speech.select_voice(self.config.get("voice_id", ""))

        # قائمة انتظار التنبيهات
        self._queue: "collections.deque[dict]" = collections.deque()
        self._queued_oids: set[str] = set()
        self._active_oid: str | None = None

        # الإطار وأيقونة شريط المهام
        self.tray = None
        from .main_frame import MainFrame

        self.frame = MainFrame(self)
        self._create_tray()

        # خيط الجدولة
        self.scheduler = ReminderScheduler(
            self.reminders,
            on_due=lambda items: wx.CallAfter(self._deliver, items),
            on_missed=lambda items: wx.CallAfter(self._handle_missed, items),
        )

    # ------------------------------------------------------------------
    # التشغيل
    # ------------------------------------------------------------------
    def start(self) -> None:
        self.reminders.sync()
        if self.reminders_enabled:
            self.scheduler.start()
        if not self.start_hidden:
            self.show_frame()
        else:
            log.info("بدء البرنامج في الخلفية دون إظهار النافذة.")

    def _create_tray(self) -> None:
        try:
            from .tray_manager import TrayManager

            self.tray = TrayManager(self)
        except Exception as exc:  # pragma: no cover
            log.warning("تعذّر إنشاء أيقونة منطقة الإشعارات: %s", exc)
            self.tray = None

    # ------------------------------------------------------------------
    # الإظهار والإخفاء
    # ------------------------------------------------------------------
    def show_frame(self) -> None:
        if self.frame is None:
            return
        self.frame.Show(True)
        self.frame.Iconize(False)
        self.frame.Raise()
        try:
            self.frame.SetFocus()
        except Exception:
            pass
        if self._pending_missed:
            self._pending_missed = False
            wx.CallAfter(self._present_missed_dialog)

    def on_frame_hidden(self) -> None:
        if self.tray is not None:
            self.announce(L.tr("tray.hidden_info"), speak=False)
            try:
                self.tray.notify(L.tr("msg.hidden_title"), L.tr("tray.hidden_info"))
            except Exception:
                pass

    def update_tray_tooltip(self) -> None:
        if self.tray is None:
            return
        try:
            count = len(self._queue) + (1 if self._active_oid else 0)
            text = L.tr("tray.tooltip")
            if count:
                text = f"{text} ({count})"
            self.tray.update_tooltip(text)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # التنبيهات الصوتية والنطق
    # ------------------------------------------------------------------
    def speak(self, text: str, lang: str | None = None) -> None:
        if not self.config.get("sound_enabled", True):
            return
        lang = lang or self.config.get("language", "ar")
        if not self.speech.is_available:
            self._warn_no_voice()
            return
        if not self.speech.has_voice_for_language(lang):
            # لا نفرض صوتًا غير مثبت؛ نُعلم المستخدم ونستخدم الصوت الافتراضي إن وُجد
            self._warn_no_voice()
        self.speech.speak(text, lang=lang)

    def announce(self, text: str, speak: bool = True) -> None:
        """يعلن رسالة في شريط الحالة وينطقها (يُستدعى من المسار الرئيسي)."""
        try:
            if self.frame is not None:
                self.frame.SetStatusText(text, 0)
        except Exception:
            pass
        if speak and self.config.get("sound_enabled", True):
            self.speak(text)

    def _warn_no_voice(self) -> None:
        # نعرض التنبيه مرة واحدة فقط لكل جلسة
        if getattr(self, "_warned_voice", False):
            return
        self._warned_voice = True
        message = L.tr("error.no_speech_voice")
        log.warning(message)
        try:
            if self.frame is not None:
                self.frame.SetStatusText(message, 0)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # تفعيل/تعطيل التنبيهات
    # ------------------------------------------------------------------
    @property
    def reminders_enabled(self) -> bool:
        return bool(self.config.get("reminders_enabled", True))

    def set_reminders_enabled(self, enabled: bool) -> None:
        self.config.set("reminders_enabled", enabled)
        if enabled:
            self.reminders.sync()
            if not self.scheduler.is_running:
                self.scheduler.start()
        else:
            self.scheduler.stop()
        if self.frame is not None and hasattr(self.frame, "menu_toggle_reminders"):
            self.frame.menu_toggle_reminders.Check(enabled)

    def refresh_reminders(self) -> None:
        self.reminders.sync()

    # ------------------------------------------------------------------
    # قائمة انتظار التنبيهات
    # ------------------------------------------------------------------
    def _deliver(self, items: list[dict]) -> None:
        for item in items:
            oid = item["oid"]
            if oid in self._queued_oids or oid == self._active_oid:
                continue
            self._queued_oids.add(oid)
            self._queue.append(item)
        self._show_next_reminder()
        self.update_tray_tooltip()

    def _show_next_reminder(self) -> None:
        if self._active_oid is not None or not self._queue:
            return
        item = self._queue.popleft()
        self._queued_oids.discard(item["oid"])
        self._active_oid = item["oid"]
        callbacks = {
            "complete": self._reminder_complete,
            "snooze": self._reminder_snooze,
            "open": self._reminder_open,
            "close": self._reminder_closed,
        }
        self.frame.display_reminder(item, callbacks)

    def _finish_reminder(self, item: dict) -> None:
        self.frame.close_reminder_frame(item["oid"])
        if self._active_oid == item["oid"]:
            self._active_oid = None
        wx.CallAfter(self._show_next_reminder)
        self.update_tray_tooltip()

    def _reminder_complete(self, item: dict) -> None:
        task = item.get("task") or {}
        if task.get("id"):
            self.tasks.set_status(int(task["id"]), L.STATUS_COMPLETED)
            self.reminders.acknowledge_task(int(task["id"]))
            self.announce(L.tr("msg.completed", title=task.get("title", "")))
        if self.frame:
            self.frame.refresh()
        self._finish_reminder(item)

    def _reminder_snooze(self, item: dict, minutes: int) -> None:
        self.reminders.snooze(item["oid"], minutes)
        task = item.get("task") or {}
        self.announce(L.tr("reminder.snoozed", minutes=minutes, title=task.get("title", "")), speak=False)
        self._finish_reminder(item)

    def _reminder_open(self, item: dict) -> None:
        self.show_frame()
        task = item.get("task") or {}
        task_id = task.get("id")
        if self.frame and task_id:
            self.frame.set_view(L.VIEW_ALL)
            self.frame.list_ctrl.select_task(int(task_id))
            self.frame.list_ctrl.focus_list()
        self._finish_reminder(item)

    def _reminder_closed(self, item: dict) -> None:
        self._finish_reminder(item)

    # ------------------------------------------------------------------
    # التذكيرات الفائتة
    # ------------------------------------------------------------------
    def _handle_missed(self, items: list[dict]) -> None:
        if not items:
            return
        if self.frame is not None and self.frame.IsShown():
            self._present_missed_dialog()
        else:
            self._pending_missed = True
            count = len(items)
            self.announce(L.tr("reminder.missed_intro", count=count))
            if self.tray is not None:
                self.tray.notify(L.tr("reminder.missed_title"), L.tr("reminder.missed_intro", count=count))

    def _present_missed_dialog(self) -> None:
        from .reminder_dialog import MissedRemindersDialog
        items = self.reminders.list_missed()
        if not items:
            return
        lang = self.config.get("language", "ar")
        style = self.config.get("date_format", "iso")
        dlg = MissedRemindersDialog(self.frame, items, lang, style)
        result = dlg.ShowModal()
        selected = dlg.selected_items
        dismiss_all = dlg.dismiss_all
        dlg.Destroy()
        if dismiss_all or not selected:
            self.reminders.dismiss_all_missed()
            return
        for item in selected:
            reviewed = self.reminders.review_item(item["oid"])
            if reviewed:
                self._deliver([reviewed])
        # عالج المتبقي غير المحدد
        self.reminders.dismiss_all_missed()

    def show_missed_dialog(self) -> None:
        """فتح ملخص التذكيرات الفائتة يدويًا من القائمة."""
        self.show_frame()
        if not self.reminders.list_missed():
            self.announce(L.tr("reminder.no_missed"), speak=False)
            if self.frame is not None:
                wx.MessageBox(
                    L.tr("reminder.no_missed"),
                    L.tr("reminder.missed_title"),
                    wx.OK | wx.ICON_INFORMATION,
                    self.frame,
                )
            return
        self._present_missed_dialog()

    # ------------------------------------------------------------------
    # دعوات من منطقة الإشعارات
    # ------------------------------------------------------------------
    def new_task_from_tray(self) -> None:
        self.show_frame()
        if self.frame:
            self.frame.on_new_task()

    def show_upcoming(self) -> None:
        self.show_frame()
        if self.frame:
            self.frame.set_view(L.VIEW_UPCOMING)

    # ------------------------------------------------------------------
    # اللغة
    # ------------------------------------------------------------------
    def apply_language(self) -> None:
        L.set_language(self.config.get("language", "ar"))
        if self.frame is not None:
            self.frame.rebuild()
        # إعادة إنشاء أيقونة شريط المهام لترجمة قائمتها
        if self.tray is not None:
            try:
                self.tray.RemoveIcon()
                self.tray.Destroy()
            except Exception:
                pass
            self._create_tray()
        self.announce(L.tr("settings.saved"), speak=False)

    # ------------------------------------------------------------------
    # استعادة النسخة الاحتياطية
    # ------------------------------------------------------------------
    def reload_services_after_restore(self) -> None:
        self.config.load()
        L.set_language(self.config.get("language", "ar"))
        self.tasks = TaskService(self.db)
        self.reminders = ReminderService(self.db, self.tasks)
        # أعد ربط الجدولة بالخدمة الجديدة مع الحفاظ على التشغيل
        self.scheduler.service = self.reminders
        self.refresh_reminders()

    # ------------------------------------------------------------------
    # الخروج
    # ------------------------------------------------------------------
    def request_exit(self) -> None:
        if wx.MessageBox(
            L.tr("confirm.exit"),
            L.tr("confirm.exit_title"),
            wx.YES_NO | wx.ICON_QUESTION,
            self.frame,
        ) != wx.YES:
            return
        self.exit_requested = True
        self.shutdown()

    def shutdown(self) -> None:
        self.exit_requested = True
        try:
            self.scheduler.stop()
        except Exception:
            pass
        try:
            self.speech.stop()
        except Exception:
            pass
        if self.tray is not None:
            try:
                self.tray.RemoveIcon()
                self.tray.Destroy()
            except Exception:
                pass
            self.tray = None
        try:
            self.db.close()
        except Exception:
            pass
        self.app.ExitMainLoop()
