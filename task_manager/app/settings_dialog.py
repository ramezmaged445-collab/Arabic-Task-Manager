"""حوار الإعدادات (Settings dialog)."""

from __future__ import annotations

import wx

from . import accessibility, localization as L
from .task_dialog import REMINDER_OFFSETS


class SettingsDialog(wx.Dialog):
    def __init__(self, parent, settings, speech, startup) -> None:
        super().__init__(parent, title=L.tr("settings.title"), style=wx.DEFAULT_DIALOG_STYLE)
        self.settings = settings
        self.speech = speech
        self.startup = startup
        self.language_changed = False
        self._voices = []
        self._build()
        self._load()
        accessibility.apply_rtl(self)
        self.Fit()
        self.CentreOnParent()

    def _build(self) -> None:
        outer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(self)
        accessibility.set_accessible_name(self.notebook, L.tr("settings.title"))
        outer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 12)

        self.notebook.AddPage(self._page_general(), L.tr("settings.tab.general"))
        self.notebook.AddPage(self._page_reminders(), L.tr("settings.tab.reminders"))
        self.notebook.AddPage(self._page_sound(), L.tr("settings.tab.sound"))
        self.notebook.AddPage(self._page_startup(), L.tr("settings.tab.startup"))

        buttons = wx.StdDialogButtonSizer()
        save_btn = wx.Button(self, wx.ID_OK, L.tr("btn.save"))
        cancel_btn = wx.Button(self, wx.ID_CANCEL, L.tr("btn.cancel"))
        buttons.AddButton(save_btn)
        buttons.AddButton(cancel_btn)
        buttons.Realize()
        outer.Add(buttons, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.SetSizer(outer)

        self.test_btn.Bind(wx.EVT_BUTTON, self._on_test)
        save_btn.Bind(wx.EVT_BUTTON, self._on_save)

    def _make_page(self):
        panel = wx.Panel(self.notebook)
        page_sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(cols=2, vgap=8, hgap=10)
        grid.AddGrowableCol(1, 1)
        page_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 12)
        panel.SetSizer(page_sizer)

        def add(label_key, control):
            grid.Add(wx.StaticText(panel, label=L.tr(label_key)), 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(control, 1, wx.EXPAND)

        return panel, page_sizer, add

    def _page_general(self) -> wx.Panel:
        panel, _page, add = self._make_page()
        self.lang_choice = wx.Choice(panel, choices=[L.LANGUAGES["ar"], L.LANGUAGES["en"]])
        accessibility.set_accessible_name(self.lang_choice, L.tr("settings.language"))
        add("settings.language", self.lang_choice)

        self.default_priority = wx.Choice(panel, choices=[L.tr(f"priority.{p}") for p in L.PRIORITY_ORDER])
        add("settings.default_priority", self.default_priority)

        self.date_format = wx.Choice(panel, choices=[L.tr("settings.date_fmt.iso"), L.tr("settings.date_fmt.long")])
        add("settings.date_format", self.date_format)
        return panel

    def _page_reminders(self) -> wx.Panel:
        panel, _page, add = self._make_page()
        self.default_reminder = wx.Choice(panel, choices=[L.tr(k) for k, _ in REMINDER_OFFSETS if _ != -1])
        add("settings.default_reminder", self.default_reminder)

        self.auto_repeat = wx.CheckBox(panel, label=L.tr("settings.auto_repeat"))
        add("settings.auto_repeat", self.auto_repeat)

        self.repeat_spin = wx.SpinCtrl(panel, min=1, max=100000, initial=10)
        add("settings.repeat_interval", self.repeat_spin)
        return panel

    def _page_sound(self) -> wx.Panel:
        panel, page_sizer, add = self._make_page()
        self.sound_enabled = wx.CheckBox(panel, label=L.tr("settings.sound_enabled"))
        add("settings.sound_enabled", self.sound_enabled)

        self.alert_sound = wx.CheckBox(panel, label=L.tr("settings.alert_sound"))
        add("settings.alert_sound", self.alert_sound)

        # اختيار ملف صوت التنبيه الخارجي
        sound_file_row = wx.BoxSizer(wx.HORIZONTAL)
        self.alert_file_ctrl = wx.TextCtrl(panel, style=wx.TE_READONLY)
        accessibility.set_accessible_name(self.alert_file_ctrl, L.tr("settings.alert_sound_file"))
        self.alert_browse_btn = wx.Button(panel, label=L.tr("btn.browse"))
        self.alert_test_btn = wx.Button(panel, label=L.tr("btn.test_sound"))
        self.alert_default_btn = wx.Button(panel, label=L.tr("btn.default"))
        sound_file_row.Add(self.alert_file_ctrl, 1, wx.RIGHT, 6)
        sound_file_row.Add(self.alert_browse_btn, 0, wx.RIGHT, 6)
        sound_file_row.Add(self.alert_test_btn, 0, wx.RIGHT, 6)
        sound_file_row.Add(self.alert_default_btn, 0)
        add("settings.alert_sound_file", sound_file_row)

        sound_hint = wx.StaticText(panel, label=L.tr("settings.alert_sound_hint"))
        sound_hint.Wrap(520)
        page_sizer.Add(sound_hint, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        voice_row = wx.BoxSizer(wx.HORIZONTAL)
        self.voice_choice = wx.Choice(panel, choices=[L.tr("settings.voice.default")])
        self.test_btn = wx.Button(panel, label=L.tr("btn.test"))
        voice_row.Add(self.voice_choice, 1, wx.RIGHT, 6)
        voice_row.Add(self.test_btn, 0)
        add("settings.voice", voice_row)

        self.alert_browse_btn.Bind(wx.EVT_BUTTON, self._on_browse_alert)
        self.alert_test_btn.Bind(wx.EVT_BUTTON, self._on_test_alert)
        self.alert_default_btn.Bind(wx.EVT_BUTTON, self._on_default_alert)
        return panel

    def _page_startup(self) -> wx.Panel:
        panel, page_sizer, add = self._make_page()
        self.start_with_windows = wx.CheckBox(panel, label=L.tr("settings.start_with_windows"))
        add("settings.start_with_windows", self.start_with_windows)

        self.start_hidden = wx.CheckBox(panel, label=L.tr("settings.start_hidden"))
        add("settings.start_hidden", self.start_hidden)

        self.run_in_background = wx.CheckBox(panel, label=L.tr("settings.run_in_background"))
        add("settings.run_in_background", self.run_in_background)

        hint = wx.StaticText(panel, label=L.tr("settings.startup_hint"))
        hint.Wrap(520)
        page_sizer.Add(hint, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        return panel

    def _load(self) -> None:
        s = self.settings
        self.lang_choice.SetSelection(0 if s.get("language", "ar") == "ar" else 1)
        self.sound_enabled.SetValue(bool(s.get("sound_enabled", True)))
        self.alert_sound.SetValue(bool(s.get("alert_sound", True)))
        self._alert_sound_file = (s.get("alert_sound_file", "") or "").strip()
        self.alert_file_ctrl.SetValue(
            self._alert_sound_file or L.tr("settings.alert_sound_default")
        )
        offsets = [m for _, m in REMINDER_OFFSETS if _ != -1]
        want = int(s.get("default_reminder_minutes", 15) or 15)
        self.default_reminder.SetSelection(offsets.index(want) if want in offsets else 2)
        prio = s.get("default_priority", L.PRIORITY_NORMAL)
        self.default_priority.SetSelection(L.PRIORITY_ORDER.index(prio) if prio in L.PRIORITY_ORDER else 1)
        self.auto_repeat.SetValue(bool(s.get("auto_repeat", False)))
        self.repeat_spin.SetValue(int(s.get("repeat_interval_minutes", 10) or 10))
        self.date_format.SetSelection(0 if s.get("date_format", "iso") == "iso" else 1)
        self.start_with_windows.SetValue(bool(s.get("start_with_windows", False)))
        self.start_hidden.SetValue(bool(s.get("start_hidden", True)))
        self.run_in_background.SetValue(bool(s.get("run_in_background", True)))
        self._load_voices()

    def _load_voices(self) -> None:
        self._voices = self.speech.list_voices() if self.speech else []
        choices = [L.tr("settings.voice.default")]
        for v in self._voices:
            choices.append(f"{v.name} [{v.language}]")
        if not self._voices:
            choices.append(L.tr("settings.voice.none"))
        self.voice_choice.SetItems(choices)
        current = self.settings.get("voice_id", "")
        idx = 0
        for i, v in enumerate(self._voices, start=1):
            if v.token_id == current:
                idx = i
                break
        self.voice_choice.SetSelection(idx)

    def _selected_voice_id(self) -> str:
        idx = self.voice_choice.GetSelection()
        if 1 <= idx <= len(self._voices):
            return self._voices[idx - 1].token_id
        return ""

    def _on_test(self, _e) -> None:
        if not self.speech or not self.speech.is_available:
            wx.MessageBox(L.tr("error.no_speech_voice"), L.tr("settings.title"), wx.OK | wx.ICON_WARNING, self)
            return
        msg = "مرحبًا، هذا اختبار للصوت." if self.settings.get("language") == "ar" else "Hello, this is a voice test."
        self.speech.select_voice(self._selected_voice_id())
        self.speech.speak(msg, lang=self.settings.get("language", "ar"))

    def _on_browse_alert(self, _e) -> None:
        dlg = wx.FileDialog(
            self,
            L.tr("settings.alert_sound_file"),
            wildcard=L.tr("sound.file_filter"),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self._alert_sound_file = dlg.GetPath()
            self.alert_file_ctrl.SetValue(self._alert_sound_file)
        dlg.Destroy()

    def _on_default_alert(self, _e) -> None:
        self._alert_sound_file = ""
        self.alert_file_ctrl.SetValue(L.tr("settings.alert_sound_default"))

    def _on_test_alert(self, _e) -> None:
        from .notification_service import NotificationService, play_sound_file

        if self._alert_sound_file:
            if not play_sound_file(self._alert_sound_file):
                wx.MessageBox(
                    L.tr("sound.play_failed"),
                    L.tr("settings.title"),
                    wx.OK | wx.ICON_WARNING,
                    self,
                )
        else:
            NotificationService().play_test()

    def _on_save(self, _e) -> None:
        old_lang = self.settings.get("language", "ar")
        new_lang = "ar" if self.lang_choice.GetSelection() == 0 else "en"
        offsets = [m for _, m in REMINDER_OFFSETS if _ != -1]
        values = {
            "language": new_lang,
            "sound_enabled": self.sound_enabled.GetValue(),
            "alert_sound": self.alert_sound.GetValue(),
            "alert_sound_file": self._alert_sound_file,
            "default_reminder_minutes": offsets[self.default_reminder.GetSelection()],
            "default_priority": L.PRIORITY_ORDER[self.default_priority.GetSelection()],
            "auto_repeat": self.auto_repeat.GetValue(),
            "repeat_interval_minutes": self.repeat_spin.GetValue(),
            "date_format": "iso" if self.date_format.GetSelection() == 0 else "long",
            "start_with_windows": self.start_with_windows.GetValue(),
            "start_hidden": self.start_hidden.GetValue(),
            "run_in_background": self.run_in_background.GetValue(),
            "voice_id": self._selected_voice_id(),
        }
        self.settings.update(values)
        self.language_changed = new_lang != old_lang

        if self.speech:
            self.speech.select_voice(values["voice_id"])

        if self.startup:
            if values["start_with_windows"]:
                self.startup.enable(hidden=values["start_hidden"])
            else:
                self.startup.disable()
        self.EndModal(wx.ID_OK)
