"""أدوات الوقت والتاريخ (Time utilities).

نخزّن الأوقات داخل قاعدة البيانات بصيغة ISO محلية ``YYYY-MM-DD HH:MM:SS``.
توفّر الدالة :func:`now` ساعة قابلة للاستبدال في الاختبارات دون انتظار
الوقت الحقيقي.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def now() -> datetime:
    """الساعة الحالية. يمكن استبدالها في الاختبارات عبر :func:`set_clock`."""
    return _clock()


def _default_clock() -> datetime:
    return datetime.now().replace(microsecond=0)


_clock = _default_clock


def set_clock(func) -> None:
    """تثبيت ساعة بديلة (تُستخدم في الاختبارات الحتمية)."""
    global _clock
    _clock = func


def reset_clock() -> None:
    """استعادة الساعة الحقيقية."""
    global _clock
    _clock = _default_clock


def to_db(dt: Optional[datetime]) -> Optional[str]:
    """تحويل ``datetime`` إلى نص مناسب لقاعدة البيانات."""
    if dt is None:
        return None
    return dt.replace(microsecond=0).strftime(DATETIME_FORMAT)


def from_db(value: Optional[str]) -> Optional[datetime]:
    """تحويل نص من قاعدة البيانات إلى ``datetime``."""
    if not value:
        return None
    text = value.strip()
    for fmt in (DATETIME_FORMAT, "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    # محاولة أخيرة عبر fromisoformat
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def combine(date_value, time_value) -> Optional[datetime]:
    """دمج تاريخ ووقت (كائنات ``wx.DateTime`` أو ``datetime``) في ``datetime``."""
    if date_value is None:
        return None
    if isinstance(date_value, datetime):
        y, mo, d = date_value.year, date_value.month, date_value.day
    else:
        y, mo, d = date_value.GetYear(), date_value.GetMonth() + 1, date_value.GetDay()
    hour = minute = 0
    if time_value is not None:
        if isinstance(time_value, datetime):
            hour, minute = time_value.hour, time_value.minute
        else:
            hour, minute = time_value.GetHour(), time_value.GetMinute()
    return datetime(y, mo, d, hour, minute)


_AR_MONTHS = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
]
_EN_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def format_display(dt: Optional[datetime], lang: str = "ar", style: str = "iso") -> str:
    """تنسيق تاريخ للعرض حسب اللغة والنمط المختار."""
    if dt is None:
        return ""
    if style == "long":
        months = _AR_MONTHS if lang == "ar" else _EN_MONTHS
        month = months[dt.month - 1]
        if lang == "ar":
            return f"{dt.day} {month} {dt.year} - {dt.hour:02d}:{dt.minute:02d}"
        return f"{month} {dt.day}, {dt.year} {dt.hour:02d}:{dt.minute:02d}"
    return dt.strftime("%Y-%m-%d %H:%M")


def humanize_delta(delta: timedelta, lang: str = "ar") -> str:
    """وصف المدة الزمنية بلغة مفهومة للقراءة الصوتية (بدون بادئة)."""
    total = int(delta.total_seconds())
    total = abs(total)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60

    parts_ar = []
    parts_en = []
    if days:
        parts_ar.append(f"{days} يوم" if days == 1 else f"{days} أيام")
        parts_en.append(f"{days} day" + ("s" if days != 1 else ""))
    if hours:
        parts_ar.append(f"{hours} ساعة")
        parts_en.append(f"{hours} hour" + ("s" if hours != 1 else ""))
    if minutes or not (days or hours):
        parts_ar.append(f"{minutes} دقيقة")
        parts_en.append(f"{minutes} minute" + ("s" if minutes != 1 else ""))

    if lang == "ar":
        return " و".join(parts_ar)
    return ", ".join(parts_en)
