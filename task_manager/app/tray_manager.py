"""أيقونة منطقة الإشعارات (System tray icon).

توفّر قائمة يمكن الوصول إليها من لوحة المفاتيح للتحكم بالبرنامج أثناء
عمله في الخلفية. تفشل بأمان إذا لم تتوفر منطقة الإشعارات.
"""

from __future__ import annotations

import logging

import wx
import wx.adv

from . import localization as L

log = logging.getLogger(__name__)


def _make_icon() -> wx.BitmapBundle | wx.Bitmap:
    """ينشئ أيقونة بسيطة بحرف T دون الحاجة إلى ملف خارجي."""
    size = 32
    bmp = wx.Bitmap(size, size)
    dc = wx.MemoryDC(bmp)
    dc.SetBackground(wx.Brush(wx.Colour(0, 90, 158)))
    dc.Clear()
    dc.SetTextForeground(wx.Colour(255, 255, 255))
    font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    dc.SetFont(font)
    dc.DrawText("✓", 6, 2)
    dc.SelectObject(wx.NullBitmap)
    return bmp


class TrayManager(wx.adv.TaskBarIcon):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller
        self._reminders_enabled = controller.reminders_enabled
        self._create_icon()
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, lambda e: self.controller.show_frame())
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_UP, lambda e: self.controller.show_frame())

    def _create_icon(self) -> None:
        try:
            icon = wx.Icon()
            icon.CopyFromBitmap(wx.Bitmap(_make_icon()))
            self.SetIcon(icon, L.tr("tray.tooltip"))
        except Exception as exc:  # pragma: no cover
            log.warning("تعذّر إنشاء أيقونة شريط المهام: %s", exc)

    def CreatePopupMenu(self) -> wx.Menu:
        menu = wx.Menu()
        open_item = menu.Append(wx.ID_ANY, L.tr("tray.open"))
        new_item = menu.Append(wx.ID_ANY, L.tr("tray.new_task"))
        upcoming_item = menu.Append(wx.ID_ANY, L.tr("tray.upcoming"))
        toggle_item = menu.AppendCheckItem(wx.ID_ANY, L.tr("tray.toggle_reminders"))
        toggle_item.Check(self.controller.reminders_enabled)
        menu.AppendSeparator()
        exit_item = menu.Append(wx.ID_ANY, L.tr("tray.exit"))

        self.Bind(wx.EVT_MENU, lambda e: self.controller.show_frame(), open_item)
        self.Bind(wx.EVT_MENU, lambda e: self.controller.new_task_from_tray(), new_item)
        self.Bind(wx.EVT_MENU, lambda e: self.controller.show_upcoming(), upcoming_item)
        self.Bind(wx.EVT_MENU, lambda e: self.controller.set_reminders_enabled(not self.controller.reminders_enabled), toggle_item)
        self.Bind(wx.EVT_MENU, lambda e: self.controller.request_exit(), exit_item)
        return menu

    def update_tooltip(self, text: str | None = None) -> None:
        try:
            self.SetIcon(self._current_icon(), text or L.tr("tray.tooltip"))
        except Exception:  # pragma: no cover
            pass

    def _current_icon(self) -> wx.Icon:
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap(_make_icon()))
        return icon

    def notify(self, title: str, message: str) -> None:
        """إشعار منبثق إن كان مدعومًا (لا يعتمد عليه)."""
        try:
            self.ShowBalloon(title, message, msec=5000)
        except Exception:  # pragma: no cover
            pass
