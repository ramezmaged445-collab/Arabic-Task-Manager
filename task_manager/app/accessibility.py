"""مساعدات إمكانية الوصول (Accessibility helpers).

دوال صغيرة تضبط أسماء العناصر ووصفها لقارئ الشاشة، وتطبّق اتجاه الكتابة
من اليمين إلى اليسار عند اللغة العربية.
"""

from __future__ import annotations

import wx

from . import localization as L


def label(window: wx.Window, text: str, name: str | None = None) -> None:
    """يضبط الاسم/الوصف الذي يقرؤه قارئ الشاشة."""
    try:
        window.SetName(name or text)
    except Exception:
        pass
    try:
        window.SetToolTip(text)
    except Exception:
        pass


def set_accessible_name(window: wx.Window, name: str) -> None:
    try:
        window.SetName(name)
    except Exception:
        pass


def apply_rtl(window: wx.Window) -> None:
    """يطبّق اتجاه RTL أو LTR حسب اللغة الحالية."""
    try:
        direction = wx.Layout_RightToLeft if L.is_rtl() else wx.Layout_LeftToRight
        window.SetLayoutDirection(direction)
    except Exception:
        pass


def make_label(parent: wx.Window, text: str, label_for: wx.Window | None = None) -> wx.StaticText:
    """ينشئ تسمية ويربطها بالعنصر الذي تشرحه."""
    static = wx.StaticText(parent, label=text)
    if label_for is not None:
        try:
            static.SetLabelFor(label_for)
        except Exception:
            pass
    return static
