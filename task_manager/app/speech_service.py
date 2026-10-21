"""خدمة الكلام (Speech / TTS service).

تستخدم واجهة Windows SAPI عبر ``pywin32`` لتحويل النص إلى كلام دون الحاجة
إلى مكتبات خارجية إضافية. تدعم اختيار الصوت والتحقق من توفّر صوت مناسب
للغة المطلوبة، وتعمل بشكل غير متزامن حتى لا تجمّد الواجهة.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

log = logging.getLogger(__name__)

try:  # pragma: no cover - يعتمد على النظام
    import pythoncom
    import win32com.client

    _HAS_WIN32 = True
except Exception:  # pragma: no cover
    pythoncom = None
    win32com = None
    _HAS_WIN32 = False

# أعلام SAPI
SVSF_ASYNC = 1
SVSF_PURGE_BEFORE_SPEAK = 2
SPF_DEFAULT = 0


@dataclass
class Voice:
    token_id: str
    name: str
    description: str
    language: str  # 'ar' أو 'en' أو 'unknown'


# خرائط لغات Windows (LCID) إلى رمز مبسّط
_ARABIC_LCIDS = {0x0401, 0x0801, 0x0C01, 0x1001, 0x1401, 0x1801, 0x1C01, 0x2001, 0x2401, 0x2801, 0x2C01, 0x3001, 0x3401, 0x3801, 0x3C01, 0x4001}
_ENGLISH_LCIDS = {0x0409, 0x0809, 0x0C09, 0x1009, 0x1409, 0x1809, 0x1C09, 0x2009, 0x2409, 0x2809, 0x2C09, 0x3009, 0x3409}


class SpeechService:
    """غلاف آمن حول محرّك كلام Windows."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._voice = None
        self._voices: list[Voice] = []
        self._selected_id: str = ""
        self._co_initialized = False

    # ------------------------------------------------------------------
    def _ensure_com(self) -> None:
        """تهيئة COM داخل الخيط الحالي عند الحاجة."""
        if _HAS_WIN32 and not self._co_initialized:
            try:
                pythoncom.CoInitialize()
                self._co_initialized = True
            except Exception:  # pragma: no cover
                pass

    def _get_voice(self):
        if not _HAS_WIN32:
            return None
        if self._voice is None:
            self._ensure_com()
            try:
                self._voice = win32com.client.Dispatch("SAPI.SpVoice")
            except Exception as exc:  # pragma: no cover
                log.warning("تعذّر إنشاء محرّك الكلام: %s", exc)
                self._voice = None
        return self._voice

    @property
    def is_available(self) -> bool:
        return _HAS_WIN32 and self._get_voice() is not None

    # ------------------------------------------------------------------
    def list_voices(self) -> list[Voice]:
        """يعيد قائمة الأصوات المتاحة على النظام."""
        voice = self._get_voice()
        if voice is None:
            return []
        if self._voices:
            return self._voices
        result: list[Voice] = []
        try:
            for token in voice.GetVoices():
                try:
                    desc = token.GetDescription()
                except Exception:
                    desc = ""
                try:
                    token_id = token.Id
                except Exception:
                    token_id = desc
                lang = self._detect_language(token, desc)
                result.append(
                    Voice(token_id=token_id, name=desc, description=desc, language=lang)
                )
        except Exception as exc:  # pragma: no cover
            log.warning("تعذّر تعداد الأصوات: %s", exc)
        self._voices = result
        return result

    def _detect_language(self, token, description: str) -> str:
        text = (description or "").lower()
        try:
            raw = token.GetAttribute("Language")
            if raw:
                lcid = int(str(raw), 16)
                if lcid in _ARABIC_LCIDS:
                    return "ar"
                if lcid in _ENGLISH_LCIDS:
                    return "en"
        except Exception:
            pass
        if "arabic" in text or "عرب" in text:
            return "ar"
        if "english" in text or "en-us" in text or "en-gb" in text:
            return "en"
        return "unknown"

    def voice_for_language(self, lang: str) -> Voice | None:
        """يبحث عن صوت مطابق للغة، وإلا عن صوت 'unknown'، وإلا أي صوت."""
        voices = self.list_voices()
        if not voices:
            return None
        for v in voices:
            if v.language == lang:
                return v
        for v in voices:
            if v.language == "unknown":
                return v
        return voices[0]

    def has_voice_for_language(self, lang: str) -> bool:
        return any(v.language == lang for v in self.list_voices())

    # ------------------------------------------------------------------
    def select_voice(self, token_id: str) -> bool:
        """تحديد الصوت المستخدم. يعيد True عند النجاح."""
        self._selected_id = token_id or ""
        voice = self._get_voice()
        if voice is None:
            return False
        if not token_id:
            return True
        try:
            tokens = voice.GetVoices()
            for i in range(tokens.Count):
                token = tokens.Item(i)
                if getattr(token, "Id", None) == token_id:
                    voice.Voice = token
                    return True
        except Exception as exc:  # pragma: no cover
            log.warning("تعذّر تحديد الصوت: %s", exc)
        return False

    def _apply_voice_for_language(self, voice, lang: str) -> None:
        chosen = self._selected_id
        if chosen:
            # إن كان هناك صوت محدد يدويًا نحاول استخدامه
            try:
                tokens = voice.GetVoices()
                for i in range(tokens.Count):
                    token = tokens.Item(i)
                    if getattr(token, "Id", None) == chosen:
                        if (self._detect_language(token, token.GetDescription())) in ("unknown", lang):
                            voice.Voice = token
                            return
            except Exception:
                pass
        match = self.voice_for_language(lang)
        if match is None:
            return
        try:
            tokens = voice.GetVoices()
            for i in range(tokens.Count):
                token = tokens.Item(i)
                if getattr(token, "Id", None) == match.token_id:
                    voice.Voice = token
                    return
        except Exception:
            pass

    # ------------------------------------------------------------------
    def speak(self, text: str, lang: str = "ar", async_: bool = True) -> bool:
        """ينطق النص. يعيد False إذا لم يتوفر محرّك كلام."""
        if not text:
            return False
        with self._lock:
            voice = self._get_voice()
            if voice is None:
                return False
            try:
                self._apply_voice_for_language(voice, lang)
                flags = SVSF_ASYNC if async_ else 0
                flags |= SVSF_PURGE_BEFORE_SPEAK
                voice.Speak(text, flags)
                return True
            except Exception as exc:  # pragma: no cover
                log.warning("فشل النطق: %s", exc)
                return False

    def stop(self) -> None:
        with self._lock:
            voice = self._get_voice()
            if voice is None:
                return
            try:
                # PurgeBeforeSpeak مع نص فارغ يوقف الكلام الحالي
                voice.Speak("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
            except Exception:  # pragma: no cover
                pass
