"""النافذة الرئيسية (Main frame).

تبني كل عناصر الواجهة: القوائم، شريط البحث والتصفية، قائمة العروض، جدول
المهام، والأزرار، وتربطها بخدمات البرنامج. كل عنصر قابل للاستخدام من لوحة
المفاتيح وله اسم واضح لقارئ الشاشة.
"""

from __future__ import annotations

import webbrowser

import wx

from . import accessibility, localization as L, timeutil
from . import reminder_dialog
from .reminder_service import reminder_message
from .task_dialog import TaskDialog
from .task_list import TaskListCtrl
from .task_service import ValidationError

VIEW_KEYS = [
    L.VIEW_ALL,
    L.VIEW_NOT_STARTED,
    L.VIEW_IN_PROGRESS,
    L.VIEW_COMPLETED,
    L.VIEW_TODAY,
    L.VIEW_UPCOMING,
    L.VIEW_OVERDUE,
]

SORT_KEYS = ["due", "priority", "title", "created", "status"]

# بيانات التواصل مع المطوّر
WHATSAPP_NUMBER = "201223947858"  # بصيغة دولية بلا "+" (الرقم: +201223947858)
CONTACT_EMAIL = "ramezmaged445@gmail.com"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"



class MainFrame(wx.Frame):
    def __init__(self, controller) -> None:
        style = wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER
        super().__init__(None, title=L.tr("app.title"), size=(1024, 700), style=style)
        self.controller = controller
        self.current_view = controller.config.get("last_view", L.VIEW_ALL)
        if self.current_view not in VIEW_KEYS:
            self.current_view = L.VIEW_ALL
        self._reminder_frames: dict[str, object] = {}
        self._status = self.CreateStatusBar(2)
        self._status.SetStatusWidths([-3, -1])
        self._build_ui()
        self._build_menu()
        accessibility.apply_rtl(self)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.refresh()

    # ------------------------------------------------------------------
    # القوائم
    # ------------------------------------------------------------------
    def _build_menu(self) -> None:
        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, L.tr("menu.new_task"))
        file_menu.Append(wx.ID_PREFERENCES, L.tr("menu.settings"))
        file_menu.AppendSeparator()
        self.menu_backup = file_menu.Append(wx.ID_ANY, L.tr("menu.backup"))
        self.menu_restore = file_menu.Append(wx.ID_ANY, L.tr("menu.restore"))
        file_menu.AppendSeparator()
        self.menu_hide = file_menu.Append(wx.ID_ANY, L.tr("menu.hide"))
        self.menu_exit = file_menu.Append(wx.ID_EXIT, L.tr("menu.exit"))
        menu_bar.Append(file_menu, L.tr("menu.file"))

        task_menu = wx.Menu()
        self.menu_edit = task_menu.Append(wx.ID_EDIT, L.tr("menu.edit"))
        self.menu_delete = task_menu.Append(wx.ID_DELETE, L.tr("menu.delete"))
        self.menu_details = task_menu.Append(wx.ID_ANY, L.tr("menu.view_details"))
        task_menu.AppendSeparator()
        self.menu_mark_completed = task_menu.Append(wx.ID_ANY, L.tr("menu.mark_completed"))
        self.menu_mark_progress = task_menu.Append(wx.ID_ANY, L.tr("menu.mark_in_progress"))
        self.menu_mark_notstarted = task_menu.Append(wx.ID_ANY, L.tr("menu.mark_not_started"))
        task_menu.AppendSeparator()
        self.menu_categories = task_menu.Append(wx.ID_ANY, L.tr("menu.categories"))
        menu_bar.Append(task_menu, L.tr("menu.task"))

        views_menu = wx.Menu()
        self._view_menu_ids = {}
        for key in VIEW_KEYS:
            item_id = wx.NewIdRef()
            views_menu.Append(item_id, L.tr(f"view.{key}"))
            self._view_menu_ids[key] = item_id
            self.Bind(wx.EVT_MENU, lambda e, k=key: self.set_view(k), id=item_id)
        views_menu.AppendSeparator()
        self.menu_refresh = views_menu.Append(wx.ID_REFRESH, L.tr("menu.refresh"))
        views_menu.AppendSeparator()
        self.menu_toggle_reminders = views_menu.AppendCheckItem(wx.ID_ANY, L.tr("menu.reminders_toggle"))
        self.menu_toggle_reminders.Check(self.controller.reminders_enabled)
        self.menu_stop_speech = views_menu.Append(wx.ID_ANY, L.tr("menu.stop_speech"))
        self.menu_missed = views_menu.Append(wx.ID_ANY, L.tr("menu.missed"))
        menu_bar.Append(views_menu, L.tr("menu.views"))

        help_menu = wx.Menu()
        self.menu_guide = help_menu.Append(wx.ID_ANY, L.tr("menu.help_page"))
        self.menu_shortcuts = help_menu.Append(wx.ID_HELP, L.tr("menu.shortcuts"))
        help_menu.AppendSeparator()
        self.menu_about = help_menu.Append(wx.ID_ABOUT, L.tr("menu.about"))
        help_menu.AppendSeparator()

        contact_menu = wx.Menu()
        self.menu_whatsapp = contact_menu.Append(wx.ID_ANY, L.tr("menu.contact.whatsapp"))
        self.menu_email = contact_menu.Append(wx.ID_ANY, L.tr("menu.contact.email"))
        help_menu.AppendSubMenu(contact_menu, L.tr("menu.contact"))

        menu_bar.Append(help_menu, L.tr("menu.help"))

        self.SetMenuBar(menu_bar)

        # ربط الأحداث
        self.Bind(wx.EVT_MENU, lambda e: self.on_new_task(), id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, lambda e: self.on_settings(), id=wx.ID_PREFERENCES)
        self.Bind(wx.EVT_MENU, lambda e: self.on_backup(), self.menu_backup)
        self.Bind(wx.EVT_MENU, lambda e: self.on_restore(), self.menu_restore)
        self.Bind(wx.EVT_MENU, lambda e: self.on_hide(), self.menu_hide)
        self.Bind(wx.EVT_MENU, lambda e: self.controller.request_exit(), self.menu_exit)
        self.Bind(wx.EVT_MENU, lambda e: self.on_edit(), self.menu_edit)
        self.Bind(wx.EVT_MENU, lambda e: self.on_delete(), self.menu_delete)
        self.Bind(wx.EVT_MENU, lambda e: self.on_details(), self.menu_details)
        self.Bind(wx.EVT_MENU, lambda e: self.on_set_status(L.STATUS_COMPLETED), self.menu_mark_completed)
        self.Bind(wx.EVT_MENU, lambda e: self.on_set_status(L.STATUS_IN_PROGRESS), self.menu_mark_progress)
        self.Bind(wx.EVT_MENU, lambda e: self.on_set_status(L.STATUS_NOT_STARTED), self.menu_mark_notstarted)
        self.Bind(wx.EVT_MENU, lambda e: self.on_categories(), self.menu_categories)
        self.Bind(wx.EVT_MENU, lambda e: self.refresh(), self.menu_refresh)
        self.Bind(wx.EVT_MENU, lambda e: self.on_toggle_reminders(), self.menu_toggle_reminders)
        self.Bind(wx.EVT_MENU, lambda e: self.on_stop_speech(), self.menu_stop_speech)
        self.Bind(wx.EVT_MENU, lambda e: self.controller.show_missed_dialog(), self.menu_missed)
        self.Bind(wx.EVT_MENU, lambda e: self.on_shortcuts(), id=wx.ID_HELP)
        self.Bind(wx.EVT_MENU, lambda e: self.on_about(), id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, lambda e: self.on_user_guide(), self.menu_guide)
        self.Bind(wx.EVT_MENU, lambda e: self.on_contact_whatsapp(), self.menu_whatsapp)
        self.Bind(wx.EVT_MENU, lambda e: self.on_contact_email(), self.menu_email)

        accel = [
            (wx.ACCEL_CTRL, ord("N"), wx.ID_NEW),
            (wx.ACCEL_CTRL, ord("E"), wx.ID_EDIT),
            (wx.ACCEL_CTRL, ord("F"), self._search_id),
            (wx.ACCEL_CTRL, ord("1"), self._view_menu_ids[L.VIEW_NOT_STARTED]),
            (wx.ACCEL_CTRL, ord("2"), self._view_menu_ids[L.VIEW_IN_PROGRESS]),
            (wx.ACCEL_CTRL, ord("3"), self._view_menu_ids[L.VIEW_COMPLETED]),
            (wx.ACCEL_CTRL, ord("4"), self._view_menu_ids[L.VIEW_ALL]),
            (wx.ACCEL_NORMAL, wx.WXK_F5, wx.ID_REFRESH),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, wx.ID_DELETE),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("S"), self.menu_stop_speech.GetId()),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accel))
        self.Bind(wx.EVT_MENU, lambda e: self.focus_search(), id=self._search_id)

    # ------------------------------------------------------------------
    # الواجهة
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.panel = wx.Panel(self)
        outer = wx.BoxSizer(wx.VERTICAL)

        outer.Add(self._build_filter_panel(self.panel), 0, wx.EXPAND | wx.ALL, 6)

        body = wx.BoxSizer(wx.HORIZONTAL)
        body.Add(self._build_sidebar(self.panel), 0, wx.EXPAND | wx.RIGHT, 6)
        body.Add(self._build_task_area(self.panel), 1, wx.EXPAND)
        outer.Add(body, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)

        outer.Add(self._build_action_bar(self.panel), 0, wx.EXPAND | wx.ALL, 6)
        self.panel.SetSizer(outer)

    def _build_filter_panel(self, parent) -> wx.Sizer:
        box = wx.StaticBoxSizer(wx.HORIZONTAL, parent, L.tr("search.label"))
        box_parent = box.GetStaticBox()

        self.search_ctrl = wx.SearchCtrl(box_parent, style=wx.TE_PROCESS_ENTER)
        self._search_id = self.search_ctrl.GetId()
        self.search_ctrl.ShowCancelButton(True)
        self.search_ctrl.SetDescriptiveText(L.tr("search.hint"))
        accessibility.set_accessible_name(self.search_ctrl, L.tr("search.label"))
        box.Add(self.search_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        self.status_filter = wx.Choice(
            box_parent, choices=[L.tr("filter.all")] + [L.tr(f"status.{s}") for s in L.STATUS_ORDER]
        )
        self.status_filter.SetSelection(0)
        self._add_filter(box, box_parent, "filter.status", self.status_filter)

        self.priority_filter = wx.Choice(
            box_parent, choices=[L.tr("filter.all")] + [L.tr(f"priority.{p}") for p in L.PRIORITY_ORDER]
        )
        self.priority_filter.SetSelection(0)
        self._add_filter(box, box_parent, "filter.priority", self.priority_filter)

        self.category_filter = wx.Choice(box_parent, choices=[L.tr("filter.all")])
        self._reload_category_filter()
        self._add_filter(box, box_parent, "filter.category", self.category_filter)

        self.due_filter = wx.Choice(
            box_parent,
            choices=[
                L.tr("filter.all"),
                L.tr("filter.no_due"),
                L.tr("filter.today"),
                L.tr("filter.week"),
                L.tr("filter.overdue"),
            ],
        )
        self.due_filter.SetSelection(0)
        self._add_filter(box, box_parent, "filter.due", self.due_filter)

        self.sort_choice = wx.Choice(box_parent, choices=[L.tr(f"sort.{k}") for k in SORT_KEYS])
        sort_by = self.controller.config.get("sort_by", "due")
        self.sort_choice.SetSelection(SORT_KEYS.index(sort_by) if sort_by in SORT_KEYS else 0)
        self._add_filter(box, box_parent, "filter.sort", self.sort_choice)

        clear_btn = wx.Button(box_parent, label=L.tr("filter.clear"))
        box.Add(clear_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        self.search_ctrl.Bind(wx.EVT_TEXT, lambda e: self._schedule_refresh())
        self.search_ctrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self._on_clear)
        for ctrl in (self.status_filter, self.priority_filter, self.category_filter, self.due_filter, self.sort_choice):
            ctrl.Bind(wx.EVT_CHOICE, lambda e: self.refresh())
        clear_btn.Bind(wx.EVT_BUTTON, self._on_clear)
        return box

    def _add_filter(self, box, parent, label_key, control, label_key_override=None) -> None:
        box.Add(
            wx.StaticText(parent, label=L.tr(label_key_override or label_key)),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT,
            4,
        )
        accessibility.set_accessible_name(control, L.tr(label_key_override or label_key))
        box.Add(control, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

    def _build_sidebar(self, parent) -> wx.Sizer:
        box = wx.StaticBoxSizer(wx.VERTICAL, parent, L.tr("menu.views"))
        box_parent = box.GetStaticBox()
        self.view_listbox = wx.ListBox(box_parent, choices=[L.tr(f"view.{k}") for k in VIEW_KEYS])
        accessibility.set_accessible_name(self.view_listbox, L.tr("menu.views"))
        if self.current_view in VIEW_KEYS:
            self.view_listbox.SetSelection(VIEW_KEYS.index(self.current_view))
        box.Add(self.view_listbox, 1, wx.EXPAND | wx.ALL, 4)
        self.view_listbox.Bind(wx.EVT_LISTBOX, self._on_view_select)
        self.view_listbox.SetMinSize((180, -1))
        return box

    def _build_task_area(self, parent) -> wx.Sizer:
        box = wx.BoxSizer(wx.VERTICAL)
        self.list_ctrl = TaskListCtrl(parent)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda e: self.on_details())
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_item_selected)
        self.list_ctrl.Bind(wx.EVT_KEY_DOWN, self._on_list_key)
        box.Add(self.list_ctrl, 1, wx.EXPAND)
        return box

    def _build_action_bar(self, parent) -> wx.Sizer:
        bar = wx.BoxSizer(wx.HORIZONTAL)
        self.new_btn = wx.Button(parent, label=L.tr("btn.new"))
        self.edit_btn = wx.Button(parent, label=L.tr("btn.edit"))
        self.delete_btn = wx.Button(parent, label=L.tr("btn.delete"))
        self.complete_btn = wx.Button(parent, label=L.tr("btn.complete"))
        self.details_btn = wx.Button(parent, label=L.tr("btn.details"))
        for btn in (self.new_btn, self.edit_btn, self.delete_btn, self.complete_btn, self.details_btn):
            bar.Add(btn, 0, wx.RIGHT, 6)
        self.new_btn.Bind(wx.EVT_BUTTON, lambda e: self.on_new_task())
        self.edit_btn.Bind(wx.EVT_BUTTON, lambda e: self.on_edit())
        self.delete_btn.Bind(wx.EVT_BUTTON, lambda e: self.on_delete())
        self.complete_btn.Bind(wx.EVT_BUTTON, lambda e: self.on_set_status(L.STATUS_COMPLETED))
        self.details_btn.Bind(wx.EVT_BUTTON, lambda e: self.on_details())
        return bar

    def _reload_category_filter(self) -> None:
        cats = self.controller.tasks.list_categories()
        self._category_map = {"__all__": None, "__none__": "__none__"}
        choices = [L.tr("filter.all")]
        for c in cats:
            choices.append(c["name"])
            self._category_map[str(c["id"])] = c["name"]
        choices.append(L.tr("category.none"))
        # آخر عنصر يمثل بدون تصنيف
        self._category_choices = choices
        self.category_filter.SetItems(choices)
        self.category_filter.SetSelection(0)

    # ------------------------------------------------------------------
    # التحديث والعرض
    # ------------------------------------------------------------------
    def _schedule_refresh(self) -> None:
        self.refresh()

    def refresh(self, keep_selection: bool = True) -> None:
        settings = self.controller.config
        lang = settings.get("language", "ar")
        date_style = settings.get("date_format", "iso")

        status_filter = ""
        sel = self.status_filter.GetSelection()
        if sel > 0:
            status_filter = L.STATUS_ORDER[sel - 1]

        priority_filter = ""
        sel = self.priority_filter.GetSelection()
        if sel > 0:
            priority_filter = L.PRIORITY_ORDER[sel - 1]

        category_filter = ""
        sel = self.category_filter.GetSelection()
        if sel > 0:
            if sel == len(self._category_choices) - 1:
                category_filter = "__none__"
            else:
                # ابحث عن المفتاح المطابق
                for key, name in self._category_map.items():
                    if name == self._category_choices[sel]:
                        category_filter = key
                        break

        due_filter_map = ["", "none", "today", "week", "overdue"]
        due_sel = self.due_filter.GetSelection()
        due_filter = due_filter_map[due_sel] if 0 <= due_sel < len(due_filter_map) else ""

        sort_by = SORT_KEYS[self.sort_choice.GetSelection()]
        self.controller.config.set("sort_by", sort_by)

        tasks = self.controller.tasks.list_tasks(
            view=self.current_view,
            search=self.search_ctrl.GetValue().strip(),
            status_filter=status_filter,
            priority_filter=priority_filter,
            category_filter=category_filter,
            due_filter=due_filter,
            sort_by=sort_by,
        )
        self.list_ctrl.set_tasks(tasks, lang, date_style)
        self._update_status(len(tasks))

    def focus_search(self) -> None:
        self.search_ctrl.SetFocus()
        self.search_ctrl.SelectAll()

    def _update_status(self, count: int) -> None:
        view_label = L.tr(f"view.{self.current_view}")
        if count:
            self.SetStatusText(f"{view_label}: {count}", 0)
        else:
            self.SetStatusText(L.tr("msg.no_tasks"), 0)
        self.controller.update_tray_tooltip()

    def _on_item_selected(self, event) -> None:
        task_id = self.list_ctrl.get_selected_task_id()
        if task_id is None:
            return
        task = self.controller.tasks.get_task(task_id)
        if not task:
            return
        due = timeutil.from_db(task.get("due_at"))
        style = self.controller.config.get("date_format", "iso")
        lang = self.controller.config.get("language", "ar")
        due_text = timeutil.format_display(due, lang, style) or "-"
        summary = (
            f"{task['title']} — {L.tr('status.' + task['status'])} — "
            f"{L.tr('priority.' + task['priority'])} — {due_text}"
        )
        self.SetStatusText(summary, 1)
        event.Skip()

    def _on_view_select(self, _event) -> None:
        idx = self.view_listbox.GetSelection()
        if 0 <= idx < len(VIEW_KEYS):
            self.current_view = VIEW_KEYS[idx]
            self.controller.config.set("last_view", self.current_view)
            self.refresh()

    def set_view(self, view: str) -> None:
        self.current_view = view
        self.controller.config.set("last_view", view)
        if view in VIEW_KEYS:
            self.view_listbox.SetSelection(VIEW_KEYS.index(view))
        self.refresh()

    def _on_clear(self, _event) -> None:
        self.search_ctrl.SetValue("")
        self.status_filter.SetSelection(0)
        self.priority_filter.SetSelection(0)
        self.category_filter.SetSelection(0)
        self.due_filter.SetSelection(0)
        self.refresh()

    def _on_list_key(self, event) -> None:
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.on_details()
        else:
            event.Skip()

    # ------------------------------------------------------------------
    # عمليات المهام
    # ------------------------------------------------------------------
    def _selected_task_id(self) -> int | None:
        return self.list_ctrl.get_selected_task_id()

    def on_new_task(self) -> None:
        dlg = TaskDialog(self, self.controller.tasks, self.controller.config)
        if dlg.ShowModal() == wx.ID_OK and dlg.result_task_id:
            self.controller.refresh_reminders()
            self.refresh()
            task = self.controller.tasks.get_task(dlg.result_task_id)
            if task:
                self.controller.announce(L.tr("msg.added", title=task["title"]))
        dlg.Destroy()

    def on_edit(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            self._info(L.tr("msg.no_selection"))
            return
        task = self.controller.tasks.get_task(task_id)
        dlg = TaskDialog(self, self.controller.tasks, self.controller.config, task=task)
        if dlg.ShowModal() == wx.ID_OK:
            self.controller.refresh_reminders()
            self.refresh()
            self.controller.announce(L.tr("msg.updated", title=task["title"]))
        dlg.Destroy()

    def on_details(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            self._info(L.tr("msg.no_selection"))
            return
        task = self.controller.tasks.get_task(task_id)
        dlg = TaskDialog(self, self.controller.tasks, self.controller.config, task=task, read_only=True)
        dlg.ShowModal()
        dlg.Destroy()

    def on_delete(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            self._info(L.tr("msg.no_selection"))
            return
        task = self.controller.tasks.get_task(task_id)
        if not task:
            return
        confirm = wx.MessageBox(
            L.tr("confirm.delete", title=task["title"]),
            L.tr("confirm.delete_title"),
            wx.YES_NO | wx.ICON_QUESTION,
            self,
        )
        if confirm != wx.YES:
            return
        self.controller.tasks.delete_task(task_id)
        self.controller.reminders.acknowledge_task(task_id)
        self.refresh()
        self.controller.announce(L.tr("msg.deleted", title=task["title"]))

    def on_set_status(self, status: str) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            self._info(L.tr("msg.no_selection"))
            return
        task = self.controller.tasks.get_task(task_id)
        if not task:
            return
        if task["status"] == status:
            return
        self.controller.tasks.set_status(task_id, status)
        if status == L.STATUS_COMPLETED:
            self.controller.reminders.acknowledge_task(task_id)
            message = L.tr("msg.completed", title=task["title"])
        else:
            message = L.tr("msg.status_changed", title=task["title"], status=L.tr(f"status.{status}"))
        self.controller.refresh_reminders()
        self.refresh()
        self.controller.announce(message)

    def on_categories(self) -> None:
        from .category_dialog import CategoryDialog

        dlg = CategoryDialog(self, self.controller.tasks)
        dlg.ShowModal()
        dlg.Destroy()
        self._reload_category_filter()
        self.refresh()

    def on_toggle_reminders(self) -> None:
        enabled = self.menu_toggle_reminders.IsChecked()
        self.controller.set_reminders_enabled(enabled)
        state = L.tr("menu.reminders_toggle")
        self.controller.announce(f"{state}: {'ON' if enabled else 'OFF'}")

    def on_stop_speech(self) -> None:
        self.controller.speech.stop()
        self.controller.announce(L.tr("reminder.stopped"), speak=False)

    # ------------------------------------------------------------------
    # النسخ الاحتياطي والإعدادات والمساعدة
    # ------------------------------------------------------------------
    def on_settings(self) -> None:
        from .settings_dialog import SettingsDialog

        dlg = SettingsDialog(self, self.controller.config, self.controller.speech, self.controller.startup)
        result = dlg.ShowModal()
        changed_lang = dlg.language_changed
        dlg.Destroy()
        if result == wx.ID_OK:
            if changed_lang:
                self.controller.apply_language()
            else:
                self.refresh()
            self.controller.announce(L.tr("settings.saved"))

    def on_backup(self) -> None:
        with wx.FileDialog(
            self,
            L.tr("menu.backup"),
            wildcard="SQLite DB (*.db)|*.db",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            defaultFile="tasks-backup.db",
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            path = dlg.GetPath()
        try:
            saved = self.controller.backup.create_backup(path)
            wx.MessageBox(L.tr("msg.backup_done", path=str(saved)), L.tr("menu.backup"), wx.OK | wx.ICON_INFORMATION, self)
        except Exception as exc:
            wx.MessageBox(L.tr("msg.backup_failed", msg=str(exc)), L.tr("error.title_dialog"), wx.OK | wx.ICON_ERROR, self)

    def on_restore(self) -> None:
        with wx.FileDialog(
            self,
            L.tr("menu.restore"),
            wildcard="SQLite DB (*.db)|*.db",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            path = dlg.GetPath()
        if wx.MessageBox(L.tr("msg.restore_confirm"), L.tr("menu.restore"), wx.YES_NO | wx.ICON_WARNING, self) != wx.YES:
            return
        try:
            self.controller.backup.restore_backup(path)
            self.controller.reload_services_after_restore()
            self._reload_category_filter()
            self.refresh()
            wx.MessageBox(L.tr("msg.restore_done"), L.tr("menu.restore"), wx.OK | wx.ICON_INFORMATION, self)
        except Exception as exc:
            wx.MessageBox(L.tr("msg.restore_failed", msg=str(exc)), L.tr("error.title_dialog"), wx.OK | wx.ICON_ERROR, self)

    def on_shortcuts(self) -> None:
        wx.MessageBox(L.tr("help.body"), L.tr("help.title"), wx.OK | wx.ICON_INFORMATION, self)

    def on_about(self) -> None:
        from . import __version__

        wx.MessageBox(
            L.tr("about.body", version=__version__),
            L.tr("menu.about"),
            wx.OK | wx.ICON_INFORMATION,
            self,
        )

    def on_user_guide(self) -> None:
        dlg = wx.Dialog(self, title=L.tr("help.guide.title"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        sizer = wx.BoxSizer(wx.VERTICAL)

        text = wx.TextCtrl(
            dlg,
            value=L.tr("help.guide.body"),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_BESTWRAP,
        )
        text.SetMinSize((600, 440))
        accessibility.set_accessible_name(text, L.tr("help.guide.title"))
        sizer.Add(text, 1, wx.EXPAND | wx.ALL, 10)

        text.SetInsertionPoint(0)
        sizer.Add(dlg.CreateButtonSizer(wx.OK), 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        dlg.SetSizer(sizer)
        accessibility.apply_rtl(dlg)
        dlg.Fit()
        dlg.CentreOnParent()
        dlg.ShowModal()
        dlg.Destroy()

    def on_contact_whatsapp(self) -> None:
        self._open_link(WHATSAPP_URL, L.tr("menu.contact.whatsapp"))

    def on_contact_email(self) -> None:
        self._open_link(f"mailto:{CONTACT_EMAIL}", L.tr("menu.contact.email"))

    def _open_link(self, url: str, label: str) -> None:
        try:
            opened = webbrowser.open(url)
        except Exception:
            opened = False
        if not opened:
            wx.MessageBox(
                L.tr("msg.contact_failed", url=url),
                label,
                wx.OK | wx.ICON_ERROR,
                self,
            )

    # ------------------------------------------------------------------
    # الإخفاء والإغلاق
    # ------------------------------------------------------------------
    def on_hide(self) -> None:
        self.Hide()
        self.controller.on_frame_hidden()

    def _on_close(self, event) -> None:
        if self.controller.exit_requested:
            event.Skip()
            return
        can_hide = self.controller.config.get("run_in_background", True)
        if can_hide and self.controller.tray is not None:
            # الإخفاء إلى منطقة الإشعارات مع استمرار التذكيرات
            event.Veto()
            self.Hide()
            self.controller.on_frame_hidden()
        elif can_hide and self.controller.tray is None:
            # لا تتوفر أيقونة منطقة الإشعارات → لا نخفي تفاديًا لتعذّر الوصول
            event.Veto()
            wx.MessageBox(
                L.tr("tray.not_available"),
                L.tr("msg.hidden_title"),
                wx.OK | wx.ICON_WARNING,
                self,
            )
        else:
            event.Veto()
            self.controller.request_exit()

    def _info(self, message: str) -> None:
        self.controller.announce(message)
        wx.MessageBox(message, L.tr("app.title"), wx.OK | wx.ICON_INFORMATION, self)

    # ------------------------------------------------------------------
    # التذكيرات
    # ------------------------------------------------------------------
    def display_reminder(self, item: dict, callbacks: dict) -> "reminder_dialog.ReminderFrame":
        settings = self.controller.config
        lang = settings.get("language", "ar")
        task = item.get("task") or {}
        message = reminder_message(task, timeutil.now(), lang)

        if settings.get("sound_enabled", True) and task.get("alert_sound", True) and settings.get("alert_sound", True):
            self.controller.notifications.play_alert()
        if settings.get("sound_enabled", True) and task.get("read_aloud", True):
            self.controller.speak(message, lang)

        frame = reminder_dialog.ReminderFrame(
            self,
            item,
            message,
            on_complete=callbacks["complete"],
            on_snooze=callbacks["snooze"],
            on_open=callbacks["open"],
            on_close=callbacks["close"],
        )
        self._reminder_frames[item["oid"]] = frame
        frame.show_without_focus()
        return frame

    def close_reminder_frame(self, oid: str) -> None:
        frame = self._reminder_frames.pop(oid, None)
        if frame is not None:
            try:
                frame.Destroy()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # إعادة البناء عند تغيير اللغة
    # ------------------------------------------------------------------
    def rebuild(self) -> None:
        self._build_menu()
        self.panel.Destroy()
        self._build_ui()
        self.Bind(wx.EVT_CLOSE, self._on_close)
        accessibility.apply_rtl(self)
        self.refresh()
