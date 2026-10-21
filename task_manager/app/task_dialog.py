"""حوار إضافة/تعديل/عرض المهمة (Task dialog).

يوفّر نموذجًا كاملًا لبيانات المهمة مع إعدادات التنبيه، ويكون قابلاً
للاستخدام بالكامل من لوحة المفاتيح وقارئ الشاشة.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import wx
import wx.adv
from wx.lib.scrolledpanel import ScrolledPanel

from . import accessibility, localization as L, timeutil
from .task_service import TaskService, ValidationError

# خيارات التذكير المسبق (label_key, minutes) — -1 تعني مخصص
REMINDER_OFFSETS = [
    ("reminder.at_due", 0),
    ("reminder.m5", 5),
    ("reminder.m15", 15),
    ("reminder.m30", 30),
    ("reminder.h1", 60),
    ("reminder.d1", 1440),
    ("reminder.offset.custom", -1),
]


def _py_to_wxdate(value: datetime) -> wx.DateTime:
    return wx.DateTime.FromDMY(value.day, value.month - 1, value.year, value.hour, value.minute)


class TimeSpin(wx.Panel):
    """خانات الوقت: الساعات : الدقائق : الثواني.

    - السهم لأعلى/لأسفل يزيد/ينقص قيمة الخانة الحالية.
    - السهم لليمين ينقل التركيز إلى الخانة التالية، واليسار إلى السابقة.
    """

    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent)
        self.hour = wx.SpinCtrl(self, min=0, max=23, initial=0, style=wx.SP_ARROW_KEYS, size=(58, -1))
        self.minute = wx.SpinCtrl(self, min=0, max=59, initial=0, style=wx.SP_ARROW_KEYS, size=(58, -1))
        self.second = wx.SpinCtrl(self, min=0, max=59, initial=0, style=wx.SP_ARROW_KEYS, size=(58, -1))
        self._fields = [self.hour, self.minute, self.second]
        self._name_keys = ["field.hours", "field.minutes", "field.seconds"]

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.hour, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(wx.StaticText(self, label=":"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 2)
        sizer.Add(self.minute, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(wx.StaticText(self, label=":"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 2)
        sizer.Add(self.second, 0, wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(sizer)

        for idx, spin in enumerate(self._fields):
            accessibility.set_accessible_name(spin, L.tr(self._name_keys[idx]))
            spin.Bind(wx.EVT_KEY_DOWN, lambda e, i=idx: self._on_key(e, i))

    def _on_key(self, event: wx.KeyEvent, idx: int) -> None:
        key = event.GetKeyCode()
        if key == wx.WXK_RIGHT:
            self._move_focus(idx + 1)
        elif key == wx.WXK_LEFT:
            self._move_focus(idx - 1)
        else:
            event.Skip()

    def _move_focus(self, idx: int) -> None:
        if 0 <= idx < len(self._fields):
            self._fields[idx].SetFocus()
            try:
                self._fields[idx].SelectAll()
            except Exception:
                pass

    def get_time(self) -> tuple[int, int, int]:
        return self.hour.GetValue(), self.minute.GetValue(), self.second.GetValue()

    def set_time(self, value: Optional[datetime]) -> None:
        value = value or timeutil.now()
        self.hour.SetValue(value.hour)
        self.minute.SetValue(value.minute)
        self.second.SetValue(value.second)

    def enable(self, state: bool) -> None:
        for spin in self._fields:
            spin.Enable(state)


class DateTimeRow:
    """صف يحتوي على مربع اختيار + منتقي تاريخ + خانات وقت (ساعة:دقيقة:ثانية)."""

    def __init__(self, parent, sizer, label_key: str, checkbox_key: str):
        self.enabled = wx.CheckBox(parent, label=L.tr(checkbox_key))
        self.label = wx.StaticText(parent, label=L.tr(label_key))
        self.date_picker = wx.adv.DatePickerCtrl(parent, style=wx.adv.DP_DROPDOWN)
        self.time_spin = TimeSpin(parent)
        accessibility.set_accessible_name(self.date_picker, L.tr(label_key))
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(self.enabled, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        row.Add(self.date_picker, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row.Add(self.time_spin, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.label, 0, wx.TOP | wx.BOTTOM, 2)
        sizer.Add(row, 0, wx.EXPAND | wx.BOTTOM, 6)
        self.enabled.Bind(wx.EVT_CHECKBOX, self._on_toggle)
        self._on_toggle(None)
        self.set_value(None)

    def _on_toggle(self, _event) -> None:
        self.set_enabled(self.enabled.IsChecked())

    def set_enabled(self, state: bool) -> None:
        self.date_picker.Enable(state)
        self.time_spin.enable(state)

    def set_value(self, value: Optional[datetime]) -> None:
        if value is None:
            self.enabled.SetValue(False)
            now = timeutil.now()
            self.date_picker.SetValue(_py_to_wxdate(now))
            self.time_spin.set_time(now)
        else:
            self.enabled.SetValue(True)
            self.date_picker.SetValue(_py_to_wxdate(value))
            self.time_spin.set_time(value)
        self._on_toggle(None)

    def get_value(self) -> Optional[str]:
        if not self.enabled.IsChecked():
            return None
        date = self.date_picker.GetValue()
        hour, minute, second = self.time_spin.get_time()
        dt = datetime(date.GetYear(), date.GetMonth() + 1, date.GetDay(), hour, minute, second)
        return timeutil.to_db(dt)

    def focus(self) -> None:
        self.enabled.SetFocus()



class TaskDialog(wx.Dialog):
    def __init__(
        self,
        parent: wx.Window,
        service: TaskService,
        settings,
        task: Optional[dict] = None,
        read_only: bool = False,
    ) -> None:
        title = L.tr("task.details_title") if read_only else (
            L.tr("task.edit_title") if task else L.tr("task.new_title")
        )
        super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.service = service
        self.settings = settings
        self.task = task
        self.read_only = read_only
        self.result_task_id: Optional[int] = None
        self._build()
        if task:
            self._load(task)
        else:
            self._apply_defaults()
        accessibility.apply_rtl(self)
        self._setup_size()
        self.title_ctrl.SetFocus()

    def _setup_size(self) -> None:
        """حجم مناسب للشاشة مع ضمان ظهور أزرار الحفظ والإلغاء دائمًا."""
        area = wx.Display().GetClientArea()
        width = max(520, min(660, area.width - 40))
        height = max(480, min(800, area.height - 60))
        self.SetSize((width, height))
        self.SetMinSize((480, 420))
        self.CentreOnParent()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        outer = wx.BoxSizer(wx.VERTICAL)
        scrolled = ScrolledPanel(self, style=wx.TAB_TRAVERSAL)
        content = wx.BoxSizer(wx.VERTICAL)

        form = wx.FlexGridSizer(cols=1, vgap=4, hgap=4)
        form.AddGrowableCol(0, 1)

        form.Add(wx.StaticText(scrolled, label=L.tr("field.title")), 0)
        self.title_ctrl = wx.TextCtrl(scrolled)
        accessibility.set_accessible_name(self.title_ctrl, L.tr("field.title"))
        form.Add(self.title_ctrl, 0, wx.EXPAND)

        form.Add(wx.StaticText(scrolled, label=L.tr("field.description")), 0)
        self.desc_ctrl = wx.TextCtrl(scrolled, style=wx.TE_MULTILINE, size=(-1, 60))
        accessibility.set_accessible_name(self.desc_ctrl, L.tr("field.description"))
        form.Add(self.desc_ctrl, 0, wx.EXPAND)

        row1 = wx.BoxSizer(wx.HORIZONTAL)
        row1.Add(wx.StaticText(scrolled, label=L.tr("field.status")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.status_choice = wx.Choice(scrolled, choices=[L.tr(f"status.{s}") for s in L.STATUS_ORDER])
        self.status_choice.SetSelection(0)
        accessibility.set_accessible_name(self.status_choice, L.tr("field.status"))
        row1.Add(self.status_choice, 1, wx.RIGHT, 12)
        row1.Add(wx.StaticText(scrolled, label=L.tr("field.priority")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.priority_choice = wx.Choice(scrolled, choices=[L.tr(f"priority.{p}") for p in L.PRIORITY_ORDER])
        self.priority_choice.SetSelection(L.PRIORITY_ORDER.index(L.PRIORITY_NORMAL))
        accessibility.set_accessible_name(self.priority_choice, L.tr("field.priority"))
        row1.Add(self.priority_choice, 1)
        form.Add(row1, 0, wx.EXPAND)

        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row2.Add(wx.StaticText(scrolled, label=L.tr("field.category")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.category_combo = wx.ComboBox(scrolled, style=wx.CB_DROPDOWN)
        self._reload_categories()
        accessibility.set_accessible_name(self.category_combo, L.tr("field.category"))
        row2.Add(self.category_combo, 1)
        form.Add(row2, 0, wx.EXPAND)

        self.start_row = DateTimeRow(scrolled, form, "field.start", "field.has_start")
        self.due_row = DateTimeRow(scrolled, form, "field.due", "field.has_due")

        form.Add(wx.StaticText(scrolled, label=L.tr("field.notes")), 0)
        self.notes_ctrl = wx.TextCtrl(scrolled, style=wx.TE_MULTILINE, size=(-1, 60))
        accessibility.set_accessible_name(self.notes_ctrl, L.tr("field.notes"))
        form.Add(self.notes_ctrl, 0, wx.EXPAND)

        content.Add(form, 0, wx.EXPAND | wx.ALL, 10)

        # إعدادات التنبيه
        box = wx.StaticBoxSizer(wx.VERTICAL, scrolled, L.tr("reminder.group"))
        box_parent = box.GetStaticBox()

        self.remind_enabled = wx.CheckBox(box_parent, label=L.tr("reminder.enabled"))
        box.Add(self.remind_enabled, 0, wx.ALL, 4)

        off_row = wx.BoxSizer(wx.HORIZONTAL)
        off_row.Add(wx.StaticText(box_parent, label=L.tr("reminder.offset")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.offset_choice = wx.Choice(box_parent, choices=[L.tr(k) for k, _ in REMINDER_OFFSETS])
        self.offset_choice.SetSelection(2)
        off_row.Add(self.offset_choice, 1, wx.RIGHT, 12)
        self.custom_spin = wx.SpinCtrl(box_parent, min=0, max=100000, initial=15)
        accessibility.set_accessible_name(self.custom_spin, L.tr("reminder.custom_minutes"))
        off_row.Add(self.custom_spin, 0)
        box.Add(off_row, 0, wx.EXPAND | wx.ALL, 4)

        self.absolute_cb = wx.CheckBox(box_parent, label=L.tr("reminder.absolute"))
        box.Add(self.absolute_cb, 0, wx.ALL, 4)
        self.absolute_row = DateTimeRow(box_parent, box, "field.due", "reminder.absolute")

        opts = wx.BoxSizer(wx.HORIZONTAL)
        self.read_aloud_cb = wx.CheckBox(box_parent, label=L.tr("reminder.read_aloud"))
        self.read_aloud_cb.SetValue(True)
        self.sound_cb = wx.CheckBox(box_parent, label=L.tr("reminder.sound"))
        self.sound_cb.SetValue(True)
        opts.Add(self.read_aloud_cb, 1, wx.ALL, 4)
        opts.Add(self.sound_cb, 1, wx.ALL, 4)
        box.Add(opts, 0, wx.EXPAND)

        rep_row = wx.BoxSizer(wx.HORIZONTAL)
        self.repeat_cb = wx.CheckBox(box_parent, label=L.tr("reminder.repeat"))
        self.repeat_spin = wx.SpinCtrl(box_parent, min=1, max=100000, initial=10)
        accessibility.set_accessible_name(self.repeat_spin, L.tr("reminder.repeat_interval"))
        rep_row.Add(self.repeat_cb, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        rep_row.Add(wx.StaticText(box_parent, label=L.tr("reminder.repeat_interval")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        rep_row.Add(self.repeat_spin, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        box.Add(rep_row, 0, wx.EXPAND)

        content.Add(box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        scrolled.SetSizer(content)
        scrolled.SetupScrolling(scroll_x=False, scroll_y=True)
        outer.Add(scrolled, 1, wx.EXPAND)

        # الأزرار (خارج منطقة التمرير لتظل ظاهرة دائمًا على أي حجم شاشة)
        buttons = wx.StdDialogButtonSizer()
        if self.read_only:
            self.close_btn = wx.Button(self, wx.ID_CLOSE, L.tr("btn.close"))
            buttons.AddButton(self.close_btn)
            buttons.Realize()
            self.close_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))
        else:
            self.save_btn = wx.Button(self, wx.ID_SAVE, L.tr("btn.save"))
            self.cancel_btn = wx.Button(self, wx.ID_CANCEL, L.tr("btn.cancel"))
            buttons.AddButton(self.save_btn)
            buttons.AddButton(self.cancel_btn)
            buttons.Realize()
            self.save_btn.Bind(wx.EVT_BUTTON, self._on_save)
            self.save_btn.SetDefault()
        outer.Add(buttons, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(outer)

        self.offset_choice.Bind(wx.EVT_CHOICE, self._on_offset_change)
        self.remind_enabled.Bind(wx.EVT_CHECKBOX, self._on_remind_toggle)
        self.absolute_cb.Bind(wx.EVT_CHECKBOX, self._on_absolute_toggle)
        self._on_offset_change(None)
        self._on_remind_toggle(None)

    def _reload_categories(self) -> None:
        names = [c["name"] for c in self.service.list_categories()]
        self.category_combo.SetItems([L.tr("category.none")] + names)

    def _on_remind_toggle(self, _e) -> None:
        state = self.remind_enabled.IsChecked()
        for w in (self.offset_choice, self.custom_spin, self.read_aloud_cb,
                  self.sound_cb, self.repeat_cb, self.repeat_spin, self.absolute_cb):
            w.Enable(state)
        self._on_offset_change(None)
        self._on_absolute_toggle(None)

    def _on_offset_change(self, _e) -> None:
        idx = self.offset_choice.GetSelection()
        custom = 0 <= idx < len(REMINDER_OFFSETS) and REMINDER_OFFSETS[idx][1] == -1
        self.custom_spin.Enable(self.remind_enabled.IsChecked() and custom)

    def _on_absolute_toggle(self, _e) -> None:
        if self.absolute_cb.IsChecked():
            self.absolute_row.enabled.SetValue(True)
            self._set_absolute_controls(True)
        else:
            self._set_absolute_controls(False)

    def _set_absolute_controls(self, state: bool) -> None:
        self.absolute_row.set_enabled(state)

    # ------------------------------------------------------------------
    def _apply_defaults(self) -> None:
        offsets = [m for _, m in REMINDER_OFFSETS]

        def _match_minutes(value):
            return value if value in offsets else -1

        want = int(self.settings.get("default_reminder_minutes", 15) or 0)
        idx = offsets.index(_match_minutes(want)) if _match_minutes(want) in offsets else -1
        if idx < 0:
            self.offset_choice.SetSelection(len(REMINDER_OFFSETS) - 1)
            self.custom_spin.SetValue(int(want))
        else:
            self.offset_choice.SetSelection(idx)
        prio = self.settings.get("default_priority", L.PRIORITY_NORMAL)
        if prio in L.PRIORITY_ORDER:
            self.priority_choice.SetSelection(L.PRIORITY_ORDER.index(prio))
        self.repeat_spin.SetValue(int(self.settings.get("repeat_interval_minutes", 10) or 10))
        if self.settings.get("auto_repeat", False):
            self.repeat_cb.SetValue(True)
        self._on_remind_toggle(None)

    def _load(self, task: dict) -> None:
        self.title_ctrl.SetValue(task["title"])
        self.desc_ctrl.SetValue(task.get("description") or "")
        self.notes_ctrl.SetValue(task.get("notes") or "")
        if task["status"] in L.STATUS_ORDER:
            self.status_choice.SetSelection(L.STATUS_ORDER.index(task["status"]))
        if task["priority"] in L.PRIORITY_ORDER:
            self.priority_choice.SetSelection(L.PRIORITY_ORDER.index(task["priority"]))
        cat_id = task.get("category_id")
        if cat_id:
            cat_name = task.get("category_name")
            if cat_name:
                self.category_combo.SetValue(cat_name)
        self.start_row.set_value(timeutil.from_db(task.get("start_at")))
        self.due_row.set_value(timeutil.from_db(task.get("due_at")))

        self.remind_enabled.SetValue(bool(task.get("remind_enabled")))
        offset = int(task.get("remind_offset_minutes") or 15)
        minutes = [m for _, m in REMINDER_OFFSETS]
        if offset in minutes and offset != -1:
            self.offset_choice.SetSelection(minutes.index(offset))
        else:
            self.offset_choice.SetSelection(len(REMINDER_OFFSETS) - 1)
            self.custom_spin.SetValue(offset)
        self.read_aloud_cb.SetValue(bool(task.get("read_aloud")))
        self.sound_cb.SetValue(bool(task.get("alert_sound")))
        self.repeat_cb.SetValue(bool(task.get("repeat_enabled")))
        self.repeat_spin.SetValue(int(task.get("repeat_interval_minutes") or 10))
        remind_at = timeutil.from_db(task.get("remind_at"))
        if remind_at:
            self.absolute_cb.SetValue(True)
            self.absolute_row.set_value(remind_at)
        self._on_remind_toggle(None)

    # ------------------------------------------------------------------
    def _collect(self) -> dict:
        idx = self.offset_choice.GetSelection()
        if 0 <= idx < len(REMINDER_OFFSETS) and REMINDER_OFFSETS[idx][1] == -1:
            offset = self.custom_spin.GetValue()
        else:
            offset = REMINDER_OFFSETS[idx][1] if 0 <= idx < len(REMINDER_OFFSETS) else 15
        cat_text = self.category_combo.GetValue().strip()
        category_id = None
        if cat_text and cat_text != L.tr("category.none"):
            category_id = self.service.ensure_category(cat_text)
        return {
            "title": self.title_ctrl.GetValue(),
            "description": self.desc_ctrl.GetValue(),
            "notes": self.notes_ctrl.GetValue(),
            "status": L.STATUS_ORDER[self.status_choice.GetSelection()],
            "priority": L.PRIORITY_ORDER[self.priority_choice.GetSelection()],
            "category_id": category_id,
            "start_at": self.start_row.get_value(),
            "due_at": self.due_row.get_value(),
            "remind_enabled": 1 if self.remind_enabled.IsChecked() else 0,
            "remind_offset_minutes": offset,
            "remind_at": self.absolute_row.get_value() if self.absolute_cb.IsChecked() else None,
            "read_aloud": 1 if self.read_aloud_cb.IsChecked() else 0,
            "alert_sound": 1 if self.sound_cb.IsChecked() else 0,
            "repeat_enabled": 1 if self.repeat_cb.IsChecked() else 0,
            "repeat_interval_minutes": self.repeat_spin.GetValue(),
        }

    def _on_save(self, _event) -> None:
        data = self._collect()
        try:
            if self.task:
                self.service.update_task(int(self.task["id"]), data)
                self.result_task_id = int(self.task["id"])
            else:
                self.result_task_id = self.service.create_task(data)
        except ValidationError as exc:
            wx.MessageBox(
                L.tr(exc.message_key),
                L.tr("error.title_dialog"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            self.title_ctrl.SetFocus()
            return
        except Exception as exc:  # pragma: no cover
            wx.MessageBox(
                L.tr("error.generic", msg=str(exc)),
                L.tr("error.title_dialog"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return
        self.EndModal(wx.ID_OK)
