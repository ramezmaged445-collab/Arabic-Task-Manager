"""خدمة التنبيه الصوتي (Notification / alert sound service).

تشغّل نغمة تنبيه قصيرة دون تجميد الواجهة. تدعم:
- نغمة البرنامج الافتراضية (نبرتان بسيطتان عبر ``winsound``).
- ملف صوتي خارجي يختاره المستخدم (WAV / MP3 / WMA / MIDI ...) يُشغَّل عبر
  واجهة MCI في ``winmm`` دون الحاجة إلى مكتبات خارجية.

كل التشغيل غير متزامن حتى لا تُجمَّد الواجهة.
"""

from __future__ import annotations

import logging
import os
import threading

log = logging.getLogger(__name__)

try:
    import winsound  # pragma: no cover - خاص بـ Windows
except Exception:  # pragma: no cover
    winsound = None

_MCI_ALIAS = "tm_alert_sound"


def _play_via_mci(path: str) -> bool:
    """يشغّل ملفًا صوتيًا عبر واجهة MCI في Windows دون تجميد.

    تعيد ``True`` عند النجاح. تدعم صيغًا متعددة (wav/mp3/wma/mid) حسب
    الأجهزة/الترميزات المتوفرة في النظام.
    """
    try:
        import ctypes  # pragma: no cover - على Windows فقط

        winmm = ctypes.windll.winmm  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        return False

    try:
        # أوقف أي تشغيل سابق لنفس المُعرّف
        winmm.mciSendStringW(f"close {_MCI_ALIAS}", None, 0, None)
        open_cmds = (
            f'open "{path}" alias {_MCI_ALIAS}',
            f'open "{path}" type mpegvideo alias {_MCI_ALIAS}',
            f'open "{path}" type waveaudio alias {_MCI_ALIAS}',
        )
        for cmd in open_cmds:
            if winmm.mciSendStringW(cmd, None, 0, None) == 0:
                if winmm.mciSendStringW(f"play {_MCI_ALIAS}", None, 0, None) == 0:
                    return True
                winmm.mciSendStringW(f"close {_MCI_ALIAS}", None, 0, None)
    except Exception:  # pragma: no cover
        return False
    return False


def play_sound_file(path: str) -> bool:
    """يشغّل ملفًا صوتيًا خارجيًا. تعيد ``True`` إذا بدأ التشغيل بنجاح.

    تُجرّب MCI أولًا (لصيغ متعددة)، ثم ``winsound`` كخطة بديلة لملفات WAV.
    """
    if not path:
        return False
    try:
        if not os.path.isfile(path):
            return False
    except Exception:
        return False

    if _play_via_mci(path):
        return True

    if winsound is not None and path.lower().endswith(".wav"):
        try:
            winsound.PlaySound(
                path,
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
            return True
        except Exception:
            log.debug("تعذّر تشغيل ملف WAV عبر winsound")
    return False


class NotificationService:
    def __init__(self, settings=None) -> None:
        self.settings = settings
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()

    @property
    def is_available(self) -> bool:
        return winsound is not None

    def set_settings(self, settings) -> None:
        self.settings = settings

    def _custom_file(self) -> str:
        if self.settings is None:
            return ""
        try:
            return (self.settings.get("alert_sound_file", "") or "").strip()
        except Exception:
            return ""

    def play_alert(self, blocking: bool = False) -> None:
        """يشغّل نغمة التنبيه. بشكل افتراضي في خيط منفصل."""
        custom = self._custom_file()
        if blocking:
            self._play_once(custom)
        else:
            self._thread = threading.Thread(
                target=self._play_once, args=(custom,), daemon=True
            )
            self._thread.start()

    def _play_once(self, custom: str) -> None:
        if custom and play_sound_file(custom):
            return
        self._play_sequence()

    def _play_sequence(self) -> None:
        if winsound is None:
            # بديل: تنبيه النظام إن لم يتوفر winsound
            try:
                import ctypes  # pragma: no cover

                ctypes.windll.user32.MessageBeep(0x00000040)
            except Exception:  # pragma: no cover
                pass
            return
        try:
            # نغمة لطيفة قصيرة تعمل حتى عند كتم أصوات النظام
            winsound.Beep(880, 180)
            winsound.Beep(1180, 240)
        except Exception:
            try:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:  # pragma: no cover
                log.debug("تعذّر تشغيل صوت التنبيه")

    def play_test(self) -> None:
        self.play_alert(blocking=False)
