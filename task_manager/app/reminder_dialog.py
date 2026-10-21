"""نوافذ التنبيه والتذكيرات الفائتة (Reminder popups)."""

from __future__ import annotations

from typing import Callable

import wx

from . import accessibility, localization as L, timeutil


class ReminderFrame(wx.Frame):
    """نافذة تنبيه غير حاجبة، لا تسرق التركيز من المستخدم."""

    def __init__(
        self,
        parent: wx.Window | None,
        item: dict,
        message: str,
        on_complete: Callable[[dict], None],
        on_snooze: Callable[[dict, int], None],
        on_open: Callable[[dict], None],
        on_close: Callable[[dict], None],
    ) -> None:
        style = wx.DEFAULT_FRAME_STYLE & ~(wx.STAY_ON_TOP | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        super().__init__(parent, title=L.tr("reminder.dialog_title"), style=style)
        self.item = item
        self._on_complete = on_complete
        self._on_snooze = on_snooze
        self._on_open = on_open
        self._on_close = on_close

        panel = wx.Panel(self)
        outer = wx.BoxSizer(wx.VERTICAL)
        text = wx.StaticText(panel, label=message)
        text.Wrap(460)
        accessibility.set_accessible_name(text, message)
        outer.Add(text, 0, wx.EXPAND | wx.ALL, 12)

        self.complete_btn = wx.Button(panel, label=L.tr("reminder.complete"))
        self.snooze5_btn = wx.Button(panel, label=L.tr("reminder.snooze5"))
        self.snooze15_btn = wx.Button(panel, label=L.tr("reminder.snooze15"))
        self.snooze60_btn = wx.Button(panel, label=L.tr("reminder.snooze60"))
        self.open_btn = wx.Button(panel, label=L.tr("reminder.open"))
        self.close_btn = wx.Button(panel, label=L.tr("reminder.close"))
        for b in (self.complete_btn, self.snooze5_btn, self.snooze15_btn,
                  self.snooze60_btn, self.open_btn, self.close_btn):
            outer.Add(b, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        panel.SetSizer(outer)
        self.Fit()
        accessibility.apply_rtl(self)
        self.CentreOnScreen()

        self.complete_btn.Bind(wx.EVT_BUTTON, lambda e: self._complete())
        self.snooze5_btn.Bind(wx.EVT_BUTTON, lambda e: self._snooze(5))
        self.snooze15_btn.Bind(wx.EVT_BUTTON, lambda e: self._snooze(15))
        self.snooze60_btn.Bind(wx.EVT_BUTTON, lambda e: self._snooze(60))
        self.open_btn.Bind(wx.EVT_BUTTON, lambda e: self._open())
        self.close_btn.Bind(wx.EVT_BUTTON, lambda e: self._close())
        self.Bind(wx.EVT_CLOSE, lambda e: self._close())
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)

    def _on_key(self, event) -> None:
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self._close()
        else:
            event.Skip()

    def show_without_focus(self) -> None:
        """يُظهر النافذة دون سرقة التركيز، مع لفت انتباه لطيف."""
        self.Show(True)
        try:
            self.RequestUserAttention(wx.USER_ATTENTION_INFO)
        except Exception:
            pass

    def _complete(self) -> None:
        self._on_complete(self.item)
        self._finish()

    def _snooze(self, minutes: int) -> None:
        self._on_snooze(self.item, minutes)
        self._finish()

    def _open(self) -> None:
        self._on_open(self.item)
        self._finish()

    def _close(self) -> None:
        self._on_close(self.item)
        self._finish()

    def _finish(self) -> None:
        if self.IsShown():
            self.Hide()
        self.Destroy()


class MissedRemindersDialog(wx.Dialog):
    """ملخص التذكيرات الفائتة مع إمكانية اختيار ما تُراد مراجعته."""

    def __init__(self, parent, items: list[dict], lang: str, date_style: str) -> None:
        super().__init__(parent, title=L.tr("reminder.missed_title"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.items = items
        self.selected_items: list[dict] = []
        self.dismiss_all = False

        panel = wx.Panel(self)
        outer = wx.BoxSizer(wx.VERTICAL)
        intro = wx.StaticText(panel, label=L.tr("reminder.missed_intro", count=len(items)))
        outer.Add(intro, 0, wx.ALL, 10)

        choices = []
        self._labels = []
        for item in items:
            task = item.get("task") or {}
            fire = timeutil.from_db(item.get("fire_at"))
            label = f"{task.get('title', '?')} — {timeutil.format_display(fire, lang, date_style)}"
            choices.append(label)
            self._labels.append(label)
        self.checklist = wx.CheckListBox(panel, choices=choices)
        accessibility.set_accessible_name(self.checklist, L.tr("reminder.missed_title"))
        outer.Add(self.checklist, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self.review_btn = wx.Button(panel, label=L.tr("reminder.review_selected"))
        self.dismiss_btn = wx.Button(panel, label=L.tr("reminder.dismiss_all"))
        btn_row.Add(self.review_btn, 0, wx.RIGHT, 6)
        btn_row.Add(self.dismiss_btn, 0)
        outer.Add(btn_row, 0, wx.ALL, 10)
        panel.SetSizer(outer)

        accessibility.apply_rtl(self)
        self.SetMinSize((520, 360))
        self.Fit()
        self.CentreOnParent()

        self.review_btn.Bind(wx.EVT_BUTTON, self._on_review)
        self.dismiss_btn.Bind(wx.EVT_BUTTON, self._on_dismiss)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)

    def _on_key(self, event) -> None:
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self._on_dismiss(None)
        else:
            event.Skip()

    def _on_review(self, _e) -> None:
        checked = self.checklist.GetCheckedItems()
        self.selected_items = [self.items[i] for i in checked]
        self.EndModal(wx.ID_OK)

    def _on_dismiss(self, _e) -> None:
        self.dismiss_all = True
        self.EndModal(wx.ID_CANCEL)
