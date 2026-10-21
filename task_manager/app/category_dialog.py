"""حوار إدارة التصنيفات والمشروعات (Category dialog)."""

from __future__ import annotations

import wx

from . import accessibility, localization as L
from .task_service import TaskService, ValidationError


class CategoryDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, service: TaskService) -> None:
        super().__init__(parent, title=L.tr("category.title"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.service = service
        self._build()
        self._reload()
        accessibility.apply_rtl(self)
        self.SetMinSize((420, 380))
        self.Fit()
        self.CentreOnParent()

    def _build(self) -> None:
        panel = wx.Panel(self)
        outer = wx.BoxSizer(wx.VERTICAL)

        outer.Add(wx.StaticText(panel, label=L.tr("category.list")), 0, wx.ALL, 8)
        self.listbox = wx.ListBox(panel)
        accessibility.set_accessible_name(self.listbox, L.tr("category.list"))
        outer.Add(self.listbox, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        name_row = wx.BoxSizer(wx.HORIZONTAL)
        self.name_ctrl = wx.TextCtrl(panel)
        accessibility.set_accessible_name(self.name_ctrl, L.tr("category.name"))
        name_row.Add(wx.StaticText(panel, label=L.tr("category.name")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        name_row.Add(self.name_ctrl, 1)
        outer.Add(name_row, 0, wx.EXPAND | wx.ALL, 8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self.add_btn = wx.Button(panel, label=L.tr("category.add"))
        self.rename_btn = wx.Button(panel, label=L.tr("category.rename"))
        self.delete_btn = wx.Button(panel, label=L.tr("btn.delete"))
        close_btn = wx.Button(panel, wx.ID_CLOSE, L.tr("btn.close"))
        for b in (self.add_btn, self.rename_btn, self.delete_btn):
            btn_row.Add(b, 0, wx.RIGHT, 6)
        btn_row.AddStretchSpacer()
        btn_row.Add(close_btn, 0)
        outer.Add(btn_row, 0, wx.EXPAND | wx.ALL, 8)

        panel.SetSizer(outer)

        self.add_btn.Bind(wx.EVT_BUTTON, self._on_add)
        self.rename_btn.Bind(wx.EVT_BUTTON, self._on_rename)
        self.delete_btn.Bind(wx.EVT_BUTTON, self._on_delete)
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))
        self.listbox.Bind(wx.EVT_LISTBOX, self._on_select)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)

    def _on_key(self, event) -> None:
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CLOSE)
        else:
            event.Skip()

    def _reload(self) -> None:
        self._categories = self.service.list_categories()
        self.listbox.Set([c["name"] for c in self._categories])
        if self._categories:
            self.listbox.SetSelection(0)

    def _selected(self):
        idx = self.listbox.GetSelection()
        if 0 <= idx < len(self._categories):
            return self._categories[idx]
        return None

    def _on_select(self, _e) -> None:
        cat = self._selected()
        if cat:
            self.name_ctrl.SetValue(cat["name"])

    def _on_add(self, _e) -> None:
        name = self.name_ctrl.GetValue().strip()
        try:
            self.service.ensure_category(name)
        except ValidationError as exc:
            self._error(L.tr(exc.message_key))
            return
        self.name_ctrl.SetValue("")
        self._reload()

    def _on_rename(self, _e) -> None:
        cat = self._selected()
        if not cat:
            self._info(L.tr("msg.no_selection"))
            return
        name = self.name_ctrl.GetValue().strip()
        try:
            self.service.rename_category(int(cat["id"]), name)
        except ValidationError as exc:
            self._error(L.tr(exc.message_key))
            return
        self._reload()

    def _on_delete(self, _e) -> None:
        cat = self._selected()
        if not cat:
            self._info(L.tr("msg.no_selection"))
            return
        count = self.service.category_task_count(int(cat["id"]))
        if count:
            dlg = wx.MessageDialog(
                self,
                L.tr("category.delete_has_tasks", count=count),
                L.tr("category.title"),
                wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION,
            )
            dlg.SetYesNoLabels(L.tr("category.move_to_none"), L.tr("category.delete_tasks"))
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_CANCEL:
                return
            self.service.delete_category(int(cat["id"]), delete_tasks=(result == wx.ID_NO))
        else:
            self.service.delete_category(int(cat["id"]), delete_tasks=False)
        self._reload()

    def _error(self, message: str) -> None:
        wx.MessageBox(message, L.tr("error.title_dialog"), wx.OK | wx.ICON_ERROR, self)

    def _info(self, message: str) -> None:
        wx.MessageBox(message, L.tr("category.title"), wx.OK | wx.ICON_INFORMATION, self)
