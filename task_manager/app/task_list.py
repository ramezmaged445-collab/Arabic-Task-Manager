"""قائمة عرض المهام (Task list widget).

يعرض المهام في ``wx.ListCtrl`` بأعمدة واضحة تُقرأ بواسطة NVDA، ويوفّر
اختيارًا برمجيًا للمهمة مع الحفاظ على التركيز وعدم نقله بشكل مفاجئ.
"""

from __future__ import annotations

import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

from . import accessibility, localization as L, timeutil


class TaskListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, parent: wx.Window) -> None:
        wx.ListCtrl.__init__(
            self,
            parent,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN,
        )
        ListCtrlAutoWidthMixin.__init__(self)
        self._task_ids: list[int] = []
        self._build_columns()
        accessibility.set_accessible_name(self, L.tr("view.all"))

    def _build_columns(self) -> None:
        self.ClearAll()
        self.InsertColumn(0, L.tr("col.status"), width=120)
        self.InsertColumn(1, L.tr("col.priority"), width=100)
        self.InsertColumn(2, L.tr("col.title"), width=320)
        self.InsertColumn(3, L.tr("col.due"), width=170)
        self.InsertColumn(4, L.tr("col.category"), width=150)

    def rebuild_columns(self) -> None:
        self._build_columns()

    def set_tasks(self, tasks: list[dict], lang: str, date_style: str) -> None:
        """يملأ القائمة بالمهام مع الحفاظ على التحديد قدر الإمكان."""
        selected = self.get_selected_task_id()
        self.Freeze()
        try:
            self.DeleteAllItems()
            self._task_ids = []
            for index, task in enumerate(tasks):
                self.InsertItem(index, L.tr(f"status.{task['status']}"))
                self.SetItem(index, 1, L.tr(f"priority.{task['priority']}"))
                self.SetItem(index, 2, task["title"])
                due = timeutil.from_db(task.get("due_at"))
                self.SetItem(index, 3, timeutil.format_display(due, lang, date_style))
                self.SetItem(index, 4, task.get("category_name") or "")
                self._task_ids.append(int(task["id"]))
            self.SetColumnWidth(2, wx.LIST_AUTOSIZE_USEHEADER if not tasks else self.GetColumnWidth(2))
        finally:
            self.Thaw()
        if selected is not None:
            self.select_task(selected)

    def get_selected_task_id(self) -> int | None:
        idx = self.GetFirstSelected()
        if idx < 0 or idx >= len(self._task_ids):
            return None
        return self._task_ids[idx]

    def select_task(self, task_id: int) -> None:
        try:
            idx = self._task_ids.index(task_id)
        except ValueError:
            return
        for i in range(self.GetItemCount()):
            self.Select(i, False)
        self.Select(idx, True)
        self.Focus(idx)
        self.EnsureVisible(idx)

    def focus_list(self) -> None:
        self.SetFocus()

    def set_empty_message(self, message: str) -> None:
        accessibility.set_accessible_name(self, message)
