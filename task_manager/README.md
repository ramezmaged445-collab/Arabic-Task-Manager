# مدير المهام العربي — Arabic Task Manager

برنامج سطح مكتب لإدارة المهام بلغة **Python** وواجهة **wxPython**، مع تنبيهات
صوتية (كلام عبر Windows SAPI)، وامتثال لقارئ الشاشة **NVDA**، ودعم كامل
لللغتين **العربية** و**الإنجليزية**، وحفظ البيانات في **SQLite**، وإمكانية
العمل في الخلفية عند إغلاق النافذة.

A desktop task manager built with **Python + wxPython**, featuring spoken
reminders (Windows SAPI), screen-reader accessibility (NVDA), full
**Arabic/English** localization, **SQLite** storage, and background operation.

---

## 1) المتطلبات / Requirements

- نظام Windows 10/11.
- Python 3.9 أو أحدث (تم التطوير والاختبار على Python 3.11).
- المكتبات في `requirements.txt` (تبعيات وقت التشغيل فقط):
  - `wxPython` (إلزامية الواجهة).
  - `pywin32` (اختيارية لكن مُستحسنة: الكلام، اختصارات بدء التشغيل، منع النسخ المتعددة).
  - باقي الوحدات من مكتبة Python القياسية (`sqlite3`, `threading`, `winsound`, `ctypes`, ...).
- `pyinstaller` ليست تبعية للتشغيل؛ تُثبَّت عند الحاجة فقط لبناء ملف EXE (القسم 8).

---

## 2) التثبيت / Installation

### أ) تثبيت Python
نزّل Python من <https://www.python.org/downloads/windows/> واختر **Add Python to PATH** أثناء التثبيت.

### ب) إنشاء بيئة افتراضية وتفعيلها

```powershell
cd "D:\Task management\task_manager"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> إذا ظهرت رسالة سياسة تنفيذ السكربتات، شغّل مرة واحدة:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### ج) تثبيت المكتبات

```powershell
python -m pip install --upgrade pip
pip install wxPython pywin32
# اختياري لبناء EXE:
pip install pyinstaller
```

> **wxPython:** إن فشل تثبيت الحزمة الجاهزة، استخدم ملف الـ wheel الرسمي من
> <https://extras.wxpython.org/wxPython4/extras/stable/> المطابق لإصدار Python لديك.

### د) تشغيل البرنامج

```powershell
python main.py            # تشغيل عادي (يفتح النافذة)
python main.py --hidden   # تشغيل في الخلفية دون إظهار النافذة
```

---

## 3) أماكن حفظ البيانات / Data locations

تُحفظ البيانات في مجلد بيانات المستخدم:

```
%APPDATA%\ArabicTaskManager\
    tasks.db              # قاعدة بيانات SQLite (المهام، الإعدادات، سجل التذكيرات)
    backups\              # النسخ الاحتياطية
    logs\task_manager.log # ملف السجل
```

لأغراض الاختبار يمكن تجاوز المسار عبر متغير البيئة `TM_DB_PATH`.

---

## 4) العمل في الخلفية / Background operation

- عند إغلاق النافذة الرئيسية بالزر **X**، تُخفى النافذة ويستمر البرنامج في
  العمل وإرسال التنبيهات.
- للعودة، انقر نقرًا مزدوجًا على أيقونة **شريط المهام** بجانب الساعة.
- إن لم تتوفر أيقونة منطقة الإشعارات، أعد التشغيل لفتح النافذة.
- للخروج النهائي (يوقف التذكيرات): القائمة **ملف ← الخروج النهائي**.

> التذكيرات لا تعمل والجهاز مغلق تمامًا؛ يحتاج البرنامج إلى العمل في الخلفية
> لإرسال التنبيهات في الوقت الفعلي.

---

## 4.b) تخصيص صوت التنبيه / Custom alert sound

من **الإعدادات ← تبويب «الصوت»**:
- **تشغيل صوت التنبيه**: تفعيل أو تعطيل نغمة التنبيه.
- **ملف صوت التنبيه**: اضغط **استعراض...** لاختيار ملف صوتي من جهازك
  (WAV / MP3 / WMA / MIDI ...)، ثم **تجربة صوت التنبيه** لسماعه قبل الحفظ.
- **افتراضي**: للعودة إلى نغمة البرنامج الأصلية.
- يُحفظ اختيارك ويُستخدم في كل التنبيهات. وإن تعذّر تشغيل الملف المختار
  (صيغة غير مدعومة أو ملف مفقود) يعود البرنامج تلقائيًا إلى النغمة الافتراضية.

---

## 5) التشغيل مع بدء Windows / Start with Windows

من **ملف ← الإعدادات**: علّم **التشغيل مع بدء Windows** (و**البدء مخفيًا في
الخلفية** إن رغبت). ينشئ البرنامج اختصارًا داخل مجلد بدء التشغيل للمستخدم
دون طلب صلاحيات المسؤول. إلغاء التعليم يحذف الاختصار.

---

## 6) النسخ الاحتياطي والاستعادة / Backup & Restore

- **ملف ← نسخ احتياطي لقاعدة البيانات...** لحفظ نسخة `.db` في أي مكان تختاره.
- **ملف ← استعادة من نسخة احتياطية...** لاستبدال القاعدة الحالية.
- قبل الاستعادة يتحقق البرنامج من صلاحية الملف ويحفظ نسخة أمان من الوضع الحالي.

---

## 7) اختصارات لوحة المفاتيح / Keyboard shortcuts

| الاختصار | الوظيفة |
|---|---|
| `Ctrl+N` | مهمة جديدة |
| `Ctrl+E` | تعديل المهمة المحددة |
| `Delete` | حذف المهمة المحددة (بعد التأكيد) |
| `Ctrl+F` | الانتقال إلى حقل البحث |
| `Ctrl+1` | قائمة «لم تبدأ» |
| `Ctrl+2` | قائمة «قيد التنفيذ» |
| `Ctrl+3` | قائمة «المكتملة» |
| `Ctrl+4` | قائمة «جميع المهام» |
| `F5` | تحديث القائمة |
| `Escape` | إغلاق الحوار الحالي |

اختصارات NVDA الأساسية (مثل `NVDA+...`) لا تتعارض مع هذه الاختصارات.

---

## 8) البناء إلى EXE بـ PyInstaller / Building an EXE

ملف المواصفات `task_manager.spec` جاهز. لبنائه:

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm task_manager.spec
```

الناتج:

```
dist\ArabicTaskManager.exe
```

ملاحظات:
- استخدم `--windowed` (مُضمّن في المواصفات) لتفادي نافذة الكونسول.
- لتضمين أيقونة مخصصة ضع ملف `app.ico` بجوار المواصفات.
- التنبيهات الصوتية تعمل بعد التغليف لأن السكربت يستدعي محرّك SAPI الموجود في
  النظام مباشرة (لا حاجة لتضمين أصوات).
- لا تنسَ نسخ مجلد `wx` المرافق تلقائيًا (يتولى PyInstaller ذلك عبر خطافات wx).

---

## 8.b) إنشاء ملف التثبيت (Setup EXE) بـ Inno Setup

بعد بناء `dist\ArabicTaskManager.exe`، استخدم سكربت `installer.iss` لإنشاء مثبّت
Windows كامل (اختصارات + إزالة تثبيت + خيار حذف البيانات):

```powershell
# ثبّت Inno Setup 6 أولاً إن لم يكن مثبتًا (مثال عبر winget):
winget install --id JRSoftware.InnoSetup --scope user
# ثم:
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer.iss
```

الناتج:

```
installer\ArabicTaskManager-Setup-1.0.0.exe
```

ملاحظات حول المثبّت:
- التثبيت لكل مستخدم (بلا صلاحيات مدير) في
  `%LOCALAPPDATA%\Programs\Arabic Task Manager` افتراضيًا، مع دعم التثبيت لجميع
  المستخدمين عند التشغيل كمسؤول.
- واجهة المثبّت متوفرة بالعربية والإنجليزية.
- اختصار في قائمة ابدأ، واختصار اختياري على سطح المكتب.
- عند إزالة التثبيت يُسأل المستخدم إن كان يريد حذف بياناته
  (`%APPDATA%\ArabicTaskManager`).

---


## 9) البنية / Project structure

```
task_manager/
    main.py                 # نقطة الدخول
    task_manager.spec       # ملف PyInstaller
    requirements.txt
    README.md
    app/
        background_manager.py   # ربط الخدمات + العمل في الخلفية
        main_frame.py           # النافذة الرئيسية
        task_dialog.py          # حوار المهمة
        task_list.py            # جدول المهام
        reminder_dialog.py      # نوافذ التنبيه والفائت
        settings_dialog.py      # الإعدادات
        category_dialog.py      # التصنيفات
        tray_manager.py         # أيقونة شريط المهام
        reminder_service.py     # جدولة التذكيرات ومنع التكرار
        speech_service.py       # الكلام (SAPI)
        notification_service.py # صوت التنبيه
        localization.py         # الترجمات عربي/إنجليزي
        database.py             # SQLite + الترقيات
        task_service.py         # منطق المهام
        settings_service.py     # الإعدادات
        startup_manager.py      # التشغيل مع Windows
        backup_service.py       # النسخ والاستعادة
        single_instance.py      # منع النسخ المتعددة
        accessibility.py        # مساعدات NVDA
        paths.py / timeutil.py  # أدوات مساعدة
    tests/                  # اختبارات آلية (unittest)
```

---

## 10) الاختبارات / Tests

```powershell
python -m unittest discover -s tests -v
```

تغطي الاختبارات: إضافة/تعديل/حذف المهمة، تغيير الحالة والإكمال، البحث
والتصفية، المهام بلا موعد، الحفظ وإعادة التحميل، جدولة التذكيرات والتكرار
والتأجيل ومنع التكرار والفائت، الترجمة وحفظ اللغة، النسخة الواحدة، التشغيل مع
Windows، واستمرار الجدولة في الخلفية. تُستخدم **ساعة وهمية** لاختبار المواعيد
بشكل حتمي.

---

## 11) إمكانية الوصول / Accessibility notes

- جميع العناصر تحمل أسماء واضحة لقارئ الشاشة، والتنقل الكامل بلوحة المفاتيح
  عبر `Tab`/`Shift+Tab`.
- لا تُستخدم الألوان وحدها للدلالة على الحالة (الحالة نصية في العمود الأول).
- لا تسرق نوافذ التنبيه التركيز؛ تُعرض وتُقرأ صوتيًا مع إشارة في شريط المهام.
- إذا لم يتوفر صوت عربي/إنجليزي مثبت، يظهر تنبيه واضح في شريط الحالة دون
  افتراض وجود صوت غير موجود.

**تنبيه صريح:** لم يُتحقّق من سلوك NVDA الفعلي داخل بيئة التطوير هذه (لا تتوفر
بيئة NVDA تفاعلية). استُخدمت عناصر wxPython القياسية وممارسات إمكانية الوصول
المعروفة، مع اختبار البناء والتشغيل آليًا. يُنصح باختبار يدوي فعلي مع NVDA.
