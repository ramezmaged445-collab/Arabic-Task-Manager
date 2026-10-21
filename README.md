# Arabic Task Manager — مدير المهام العربي

مدير مهام عربي/إنجليزي خفيف لسطح مكتب ويندوز: تنبيهات منطوقة، تشغيل في الخلفية، دعم كامل للوحة المفاتيح وقارئ الشاشة NVDA، وبدء تلقائي مع ويندوز. يعمل بدون إنترنت ويحفظ بياناتك محليًا.

A lightweight Arabic/English Windows desktop task manager with spoken reminders, background operation, full keyboard/NVDA accessibility, and start-with-Windows. Offline-first, data stored locally.

## التحميل / Download

- **المثبّت / Installer:** [ArabicTaskManager-Setup-1.0.0.exe](https://github.com/ramezmaged445-collab/Arabic-Task-Manager/releases/download/v-1/ArabicTaskManager-Setup-1.0.0.exe)
- **النسخة المحمولة / Portable:** [ArabicTaskManager.exe](https://github.com/ramezmaged445-collab/Arabic-Task-Manager/releases/download/v-1/ArabicTaskManager.exe)
- **كل الإصدارات:** [Releases](https://github.com/ramezmaged445-collab/Arabic-Task-Manager/releases)

## المزايا / Features

- واجهة عربية وإنجليزية كاملة.
- إضافة/تعديل/حذف المهام، تصنيفات، أولويات، وتواريخ استحقاق.
- تذكيرات منطوقة (SAPI) ونغمة تنبيه مخصّصة (WAV/MP3/WMA/MIDI).
- تشغيل في الخلفية من أيقونة النظام + بدء تلقائي مع ويندوز.
- إتاحة كاملة للكيبورد وقارئ الشاشة NVDA.
- تخزين محلي SQLite وبدون إنترنت.

## التشغيل من المصدر / Run from source

```powershell
pip install -r requirements.txt
python main.py            # فتح النافذة
python main.py --hidden   # البدء في الخلفية
```

## بنية المشروع / Project structure

```
task_manager/
├─ app/               # وحدات التطبيق (الواجهة، الخدمات، قاعدة البيانات)
├─ tests/             # اختبارات unittest
├─ main.py            # نقطة الدخول
├─ task_manager.spec  # إعداد PyInstaller
├─ installer.iss      # إعداد مثبّت Inno Setup
├─ requirements.txt
├─ README.md          # دليل الاستخدام الكامل
├─ CHANGELOG.md
└─ LICENSE
```

## البناء / Build

```powershell
python -m PyInstaller --clean --noconfirm task_manager.spec
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer.iss
```

## الرخصة / License

MIT — انظر [LICENSE](task_manager/LICENSE).
