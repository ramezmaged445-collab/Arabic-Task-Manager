"""الترجمة والتعريب (Localization).

يحتوي هذا الملف على كل النصوص الظاهرة للمستخدم بالعربية والإنجليزية، حتى
يمكن تغيير لغة الواجهة دون تعديل بقية أجزاء الكود.

Sets of translatable strings for Arabic and English plus a small runtime
translator object.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# المفاتيح المشتركة (statuses / priorities)
# ---------------------------------------------------------------------------
STATUS_NOT_STARTED = "not_started"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"

PRIORITY_LOW = "low"
PRIORITY_NORMAL = "normal"
PRIORITY_HIGH = "high"
PRIORITY_URGENT = "urgent"

STATUS_ORDER = [STATUS_NOT_STARTED, STATUS_IN_PROGRESS, STATUS_COMPLETED]
PRIORITY_ORDER = [PRIORITY_LOW, PRIORITY_NORMAL, PRIORITY_HIGH, PRIORITY_URGENT]

# معرفات القوائم (Views)
VIEW_ALL = "all"
VIEW_NOT_STARTED = "not_started"
VIEW_IN_PROGRESS = "in_progress"
VIEW_COMPLETED = "completed"
VIEW_TODAY = "today"
VIEW_UPCOMING = "upcoming"
VIEW_OVERDUE = "overdue"

VIEW_ORDER = [
    VIEW_ALL,
    VIEW_NOT_STARTED,
    VIEW_IN_PROGRESS,
    VIEW_COMPLETED,
    VIEW_TODAY,
    VIEW_UPCOMING,
    VIEW_OVERDUE,
]

LANGUAGES = {"ar": "العربية", "en": "English"}

_STRINGS = {
    "ar": {
        "app.title": "مدير المهام العربي",
        "app.name": "مدير المهام",
        # القوائم العلوية
        "menu.file": "ملف",
        "menu.new_task": "مهمة جديدة\tCtrl+N",
        "menu.settings": "الإعدادات",
        "menu.backup": "نسخ احتياطي لقاعدة البيانات...",
        "menu.restore": "استعادة من نسخة احتياطية...",
        "menu.exit": "الخروج النهائي",
        "menu.help": "مساعدة",
        "menu.about": "حول البرنامج",
        "menu.shortcuts": "اختصارات لوحة المفاتيح",
        "menu.help_page": "دليل الاستخدام",
        "menu.contact": "التواصل مع المطوّر",
        "menu.contact.whatsapp": "واتساب",
        "menu.contact.email": "البريد الإلكتروني",
        "menu.task": "المهمة",
        "menu.edit": "تعديل المهمة\tCtrl+E",
        "menu.delete": "حذف المهمة\tDelete",
        "menu.view_details": "عرض التفاصيل",
        "menu.mark_completed": "تحديد كمكتملة",
        "menu.mark_in_progress": "بدء التنفيذ",
        "menu.mark_not_started": "إعادة إلى لم تبدأ",
        "menu.categories": "إدارة التصنيفات والمشروعات...",
        "menu.reminders_toggle": "تفعيل التنبيهات",
        "menu.stop_speech": "إيقاف الكلام\tCtrl+Shift+S",
        "menu.missed": "مراجعة التذكيرات الفائتة",
        "menu.views": "القوائم",
        "menu.refresh": "تحديث\tF5",
        "menu.hide": "إخفاء النافذة",
        # القوائم الجانبية
        "view.all": "جميع المهام",
        "view.not_started": "لم تبدأ",
        "view.in_progress": "قيد التنفيذ",
        "view.completed": "المكتملة",
        "view.today": "مهام اليوم",
        "view.upcoming": "المهام القادمة",
        "view.overdue": "المهام المتأخرة",
        # الأعمدة
        "col.title": "العنوان",
        "col.status": "الحالة",
        "col.priority": "الأولوية",
        "col.due": "الاستحقاق",
        "col.category": "التصنيف",
        "col.notes": "ملاحظات",
        # الحالات
        "status.not_started": "لم تبدأ",
        "status.in_progress": "قيد التنفيذ",
        "status.completed": "مكتملة",
        # الأولويات
        "priority.low": "منخفضة",
        "priority.normal": "عادية",
        "priority.high": "عالية",
        "priority.urgent": "عاجلة",
        # شريط البحث والتصفية
        "search.label": "بحث:",
        "search.hint": "اكتب نصًا للبحث في العناوين والوصف والملاحظات",
        "filter.status": "الحالة:",
        "filter.priority": "الأولوية:",
        "filter.category": "التصنيف:",
        "filter.due": "الاستحقاق:",
        "filter.sort": "الترتيب:",
        "sort.due": "الاستحقاق",
        "sort.priority": "الأولوية",
        "sort.title": "العنوان",
        "sort.created": "تاريخ الإنشاء",
        "sort.status": "الحالة",
        "filter.all": "الكل",
        "filter.no_due": "بدون موعد",
        "filter.today": "اليوم",
        "filter.week": "هذا الأسبوع",
        "filter.overdue": "متأخرة",
        "filter.clear": "مسح",
        "search.any": "أي", 
        # الأزرار
        "btn.new": "مهمة جديدة",
        "btn.edit": "تعديل",
        "btn.delete": "حذف",
        "btn.complete": "إكمال",
        "btn.details": "التفاصيل",
        "btn.close": "إغلاق",
        "btn.save": "حفظ",
        "btn.cancel": "إلغاء",
        "btn.ok": "موافق",
        "btn.yes": "نعم",
        "btn.no": "لا",
        "btn.browse": "استعراض...",
        "btn.apply": "تطبيق",
        "btn.add": "إضافة",
        "btn.rename": "إعادة تسمية",
        "btn.start": "بدء",
        "btn.stop": "إيقاف",
        "btn.test": "تجربة الصوت",
        "btn.test_sound": "تجربة صوت التنبيه",
        "btn.default": "افتراضي",
        # حوار المهمة
        "task.new_title": "مهمة جديدة",
        "task.edit_title": "تعديل المهمة",
        "task.details_title": "تفاصيل المهمة",
        "field.title": "عنوان المهمة *:",
        "field.description": "الوصف:",
        "field.status": "الحالة:",
        "field.priority": "الأولوية:",
        "field.category": "التصنيف / المشروع:",
        "field.start": "تاريخ ووقت البدء:",
        "field.due": "تاريخ ووقت الاستحقاق:",
        "field.hours": "الساعات",
        "field.minutes": "الدقائق",
        "field.seconds": "الثواني",
        "field.no_due": "بدون موعد استحقاق",
        "field.notes": "ملاحظات:",
        "field.completed_at": "تاريخ الإكمال:",
        "field.created_at": "تاريخ الإنشاء:",
        "reminder.group": "إعدادات التنبيه",
        "reminder.enabled": "تفعيل التنبيه",
        "reminder.offset": "التذكير قبل الموعد:",
        "reminder.offset.custom": "مخصص",
        "reminder.at_due": "عند الموعد",
        "reminder.m5": "قبل 5 دقائق",
        "reminder.m15": "قبل 15 دقيقة",
        "reminder.m30": "قبل 30 دقيقة",
        "reminder.h1": "قبل ساعة",
        "reminder.d1": "قبل يوم",
        "reminder.custom_minutes": "عدد الدقائق المخصصة:",
        "reminder.absolute": "تحديد وقت تنبيه مطلق",
        "field.has_start": "تحديد تاريخ ووقت البدء",
        "field.has_due": "تحديد تاريخ ووقت الاستحقاق",
        "reminder.read_aloud": "قراءة اسم المهمة صوتيًا",
        "reminder.sound": "تشغيل صوت التنبيه",
        "reminder.repeat": "تكرار التنبيه إذا لم أتفاعل",
        "reminder.repeat_interval": "الفاصل بين التكرار (دقائق):",
        "date.label": "التاريخ:",
        "time.label": "الوقت:",
        # التحقق
        "error.title_required": "عنوان المهمة مطلوب.",
        "error.bad_date": "التاريخ أو الوقت غير صالح.",
        "error.title_dialog": "خطأ في البيانات",
        "error.generic": "حدث خطأ: {msg}",
        "error.db": "خطأ في قاعدة البيانات: {msg}",
        "error.no_speech_voice": "لا يوجد صوت مناسب مثبت على الجهاز للغة المطلوبة.",
        # رسائل العمليات
        "msg.added": "تمت إضافة المهمة: {title}",
        "msg.updated": "تم تعديل المهمة: {title}",
        "msg.deleted": "تم حذف المهمة: {title}",
        "msg.completed": "تم إكمال المهمة: {title}",
        "msg.reopened": "تمت إعادة فتح المهمة: {title}",
        "msg.status_changed": "أصبحت حالة المهمة {title}: {status}",
        "confirm.delete_title": "تأكيد الحذف",
        "confirm.delete": "هل تريد حذف المهمة \"{title}\"؟ لا يمكن التراجع عن ذلك.",
        "confirm.exit_title": "الخروج النهائي",
        "confirm.exit": "الخروج سيوقف كل التذكيرات حتى تشغيل البرنامج مرة أخرى. هل تريد المتابعة؟",
        "msg.no_selection": "لم يتم تحديد أي مهمة.",
        "msg.no_tasks": "لا توجد مهام في هذه القائمة.",
        "msg.backup_done": "تم إنشاء نسخة احتياطية في: {path}",
        "msg.backup_failed": "فشل إنشاء النسخة الاحتياطية: {msg}",
        "msg.restore_confirm": "سيتم استبدال قاعدة البيانات الحالية بالنسخة المختارة. سيتم حفظ نسخة من الوضع الحالي. المتابعة؟",
        "msg.restore_done": "تمت استعادة قاعدة البيانات. سيتم تحديث الواجهة.",
        "msg.restore_failed": "فشلت الاستعادة: {msg}",
        "msg.invalid_backup": "الملف المختار ليس نسخة احتياطية صالحة.",
        # التذكيرات
        "reminder.dialog_title": "تذكير بمهمة",
        "reminder.due_now": "موعد المهمة قد حان الآن.",
        "reminder.due_in": "متبقي {delta} على موعد المهمة.",
        "reminder.overdue_by": "تأخر الموعد بمقدار {delta}.",
        "reminder.speak_ar": "تذكير بمهمة: {title}. {when}",
        "reminder.speak_en": "Task reminder: {title}. {when}",
        "reminder.complete": "تحديد كمكتملة",
        "reminder.snooze5": "تأجيل 5 دقائق",
        "reminder.snooze15": "تأجيل 15 دقيقة",
        "reminder.snooze60": "تأجيل ساعة",
        "reminder.open": "فتح التفاصيل",
        "reminder.close": "إغلاق التنبيه",
        "reminder.missed_title": "تذكيرات فائتة",
        "reminder.missed_intro": "هناك {count} تذكير فائت. اختر ما تريد مراجعته.",
        "reminder.no_missed": "لا توجد تذكيرات فائتة.",
        "reminder.stopped": "تم إيقاف الكلام.",
        "reminder.review_selected": "مراجعة المحدد",
        "reminder.dismiss_all": "تجاهل الكل",
        "reminder.snoozed": "تم تأجيل التنبيه {minutes} دقيقة: {title}",
        # الإعدادات
        "settings.title": "الإعدادات",
        "settings.tab.general": "عام",
        "settings.tab.reminders": "التذكيرات",
        "settings.tab.sound": "الصوت",
        "settings.tab.startup": "بدء التشغيل والخلفية",
        "settings.language": "لغة الواجهة:",
        "settings.sound_enabled": "تفعيل التنبيهات الصوتية",
        "settings.alert_sound": "تشغيل صوت التنبيه",
        "settings.alert_sound_file": "ملف صوت التنبيه:",
        "settings.alert_sound_default": "نغمة البرنامج الافتراضية",
        "settings.alert_sound_hint": "اتركه فارغًا لاستخدام نغمة البرنامج الافتراضية. يمكنك اختيار ملف صوتي من جهازك (WAV أو MP3 أو WMA ...) وتجربته قبل الحفظ، وسيُستخدم لجميع التنبيهات.",
        "sound.file_filter": "ملفات صوتية|*.wav;*.mp3;*.wma;*.mid;*.midi|كل الملفات|*.*",
        "sound.play_failed": "تعذّر تشغيل هذا الملف الصوتي. تأكد أن الصيغة مدعومة في نظامك.",
        "settings.default_reminder": "مدة التذكير الافتراضية:",
        "settings.default_priority": "الأولوية الافتراضية:",
        "settings.auto_repeat": "تكرار التنبيه تلقائيًا حتى التفاعل",
        "settings.repeat_interval": "الفاصل الافتراضي للتكرار (دقائق):",
        "settings.date_format": "طريقة عرض التاريخ والوقت:",
        "settings.start_with_windows": "التشغيل مع بدء Windows",
        "settings.start_hidden": "البدء مخفيًا في الخلفية",
        "settings.run_in_background": "الاستمرار في الخلفية عند إغلاق النافذة",
        "settings.voice": "الصوت المستخدم لقراءة النصوص:",
        "settings.voice.default": "افتراضي النظام",
        "settings.voice.none": "(لا يوجد صوت مثبت)",
        "settings.saved": "تم حفظ الإعدادات.",
        "settings.startup_hint": "ملاحظة: التشغيل مع Windows يبدأ البرنامج عند تسجيل الدخول، لكن التذكيرات لا تعمل والجهاز مغلق تمامًا، بل تحتاج إلى تشغيل البرنامج في الخلفية.",
        "settings.date_fmt.iso": "سنة-شهر-يوم وقت",
        "settings.date_fmt.long": "تاريخ مطوّل",
        # التصنيفات
        "category.title": "إدارة التصنيفات والمشروعات",
        "category.name": "الاسم:",
        "category.list": "التصنيفات:",
        "category.add": "إضافة تصنيف",
        "category.rename": "إعادة تسمية",
        "category.delete": "حذف",
        "category.none": "بدون تصنيف",
        "category.delete_has_tasks": "هذا التصنيف مرتبط بـ {count} مهمة. كيف تريد التعامل معها؟",
        "category.move_to_none": "إزالة التصنيف عن المهام (تصبح بدون تصنيف)",
        "category.delete_tasks": "حذف المهام المرتبطة أيضًا",
        "category.required_name": "اسم التصنيف مطلوب.",
        # الخلفية
        "tray.open": "فتح البرنامج",
        "tray.new_task": "إضافة مهمة جديدة",
        "tray.upcoming": "عرض المهام القادمة",
        "tray.toggle_reminders": "تفعيل/تعطيل التنبيهات",
        "tray.exit": "الخروج النهائي",
        "tray.tooltip": "مدير المهام العربي",
        "tray.hidden_info": "سيبقى البرنامج يعمل في الخلفية ويرسل التنبيهات. افتحه من أيقونة شريط المهام بجانب الساعة.",
        "tray.not_available": "تعذّر إنشاء أيقونة منطقة الإشعارات، لذا لن يتم إخفاء النافذة لتفادي تعذّر الوصول إليها. يمكنك تعطيل خيار التشغيل في الخلفية من الإعدادات.",
        "msg.hidden_title": "البرنامج في الخلفية",
        # المساعدة
        "help.title": "اختصارات لوحة المفاتيح",
        "help.body": (
            "Ctrl+N: مهمة جديدة\n"
            "Ctrl+E: تعديل المهمة المحددة\n"
            "Delete: حذف المهمة المحددة\n"
            "Ctrl+F: الانتقال إلى البحث\n"
            "Ctrl+1: قائمة لم تبدأ\n"
            "Ctrl+2: قائمة قيد التنفيذ\n"
            "Ctrl+3: قائمة المكتملة\n"
            "Ctrl+4: جميع المهام\n"
            "F5: تحديث القائمة\n"
            "Escape: إغلاق الحوار الحالي\n"
        ),
        "about.body": (
            "مدير المهام العربي\n"
            "الإصدار {version}\n\n"
            "برنامج بسيط لإدارة المهام والمواعيد مع تذكيرات منطوقة ودعم لقارئ الشاشة، "
            "يعمل بالعربية والإنجليزية.\n\n"
            "تم إنشاؤه بواسطة رامز ماجد."
        ),
        "help.guide.title": "دليل الاستخدام",
        "help.guide.body": (
            "مرحبًا بك في مدير المهام العربي.\n\n"
            "1) إضافة مهمة: من قائمة الملف اختر \"مهمة جديدة\" أو اضغط Ctrl+N. اكتب عنوان المهمة، "
            "وأضِف الوصف والملاحظات إن رغبت، وحدّد الأولوية والتصنيف والموعد والتذكير.\n\n"
            "2) التذكيرات: عند تحديد وقت تذكير سينبّهك البرنامج في الوقت المحدد بكلام منطوق "
            "وبنافذة تنبيه. يمكنك إكمال المهمة أو تأجيل التذكير.\n\n"
            "3) التعديل والحذف: اختر مهمة من الجدول ثم عدّلها (Ctrl+E) أو احذفها (Delete).\n\n"
            "4) القوائم: استخدم قائمة \"القوائم\" للتنقل بين: جميع المهام، لم تبدأ، قيد التنفيذ، "
            "المكتملة، مهام اليوم، المهام القادمة، والمهام المتأخرة.\n\n"
            "5) البحث والتصفية: استخدم مربع البحث في الأعلى، ومن عناصر التصفية اختر الحالة "
            "والأولوية والتصنيف ونطاق الاستحقاق.\n\n"
            "6) التصنيفات: من قائمة \"المهمة\" اختر \"إدارة التصنيفات والمشروعات\" لإضافة أو تعديل "
            "أو حذف التصنيفات.\n\n"
            "7) الإعدادات: من قائمة \"الملف\" اختر \"الإعدادات\" لضبط اللغة والصوت والتذكير "
            "الافتراضي وبدء التشغيل مع Windows والتشغيل في الخلفية.\n\n"
            "8) الخلفية: عند إغلاق النافذة يستمر البرنامج في العمل من منطقة الإشعارات ليصلك "
            "التذكير. للخروج نهائيًا اختر \"الخروج النهائي\" من قائمة الملف.\n\n"
            "9) النسخ الاحتياطي: من قائمة \"الملف\" يمكنك أخذ نسخة احتياطية أو الاستعادة منها.\n\n"
            "لمزيد من التفاصيل حول اختصارات لوحة المفاتيح، افتح \"اختصارات لوحة المفاتيح\" من قائمة المساعدة."
        ),
        "msg.contact_failed": "تعذّر فتح الرابط تلقائيًا.\nيمكنك نسخه يدويًا:\n{url}",
    },
    "en": {
        "app.title": "Arabic Task Manager",
        "app.name": "Task Manager",
        "menu.file": "&File",
        "menu.new_task": "&New Task\tCtrl+N",
        "menu.settings": "&Settings",
        "menu.backup": "&Backup Database...",
        "menu.restore": "&Restore from Backup...",
        "menu.exit": "E&xit Permanently",
        "menu.help": "&Help",
        "menu.about": "&About",
        "menu.shortcuts": "&Keyboard Shortcuts",
        "menu.help_page": "&User Guide",
        "menu.contact": "&Contact Developer",
        "menu.contact.whatsapp": "WhatsApp",
        "menu.contact.email": "Email",
        "menu.task": "&Task",
        "menu.edit": "&Edit Task\tCtrl+E",
        "menu.delete": "&Delete Task\tDelete",
        "menu.view_details": "View &Details",
        "menu.mark_completed": "Mark &Completed",
        "menu.mark_in_progress": "Mark In &Progress",
        "menu.mark_not_started": "Mark &Not Started",
        "menu.categories": "Manage &Categories / Projects...",
        "menu.reminders_toggle": "Enable &Reminders",
        "menu.stop_speech": "Stop &Speech\tCtrl+Shift+S",
        "menu.missed": "Review Missed Reminders",
        "menu.views": "&Views",
        "menu.refresh": "&Refresh\tF5",
        "menu.hide": "&Hide Window",
        "view.all": "All Tasks",
        "view.not_started": "Not Started",
        "view.in_progress": "In Progress",
        "view.completed": "Completed",
        "view.today": "Today's Tasks",
        "view.upcoming": "Upcoming Tasks",
        "view.overdue": "Overdue Tasks",
        "col.title": "Title",
        "col.status": "Status",
        "col.priority": "Priority",
        "col.due": "Due",
        "col.category": "Category",
        "col.notes": "Notes",
        "status.not_started": "Not started",
        "status.in_progress": "In progress",
        "status.completed": "Completed",
        "priority.low": "Low",
        "priority.normal": "Normal",
        "priority.high": "High",
        "priority.urgent": "Urgent",
        "search.label": "Search:",
        "search.hint": "Type text to search titles, description and notes",
        "filter.status": "Status:",
        "filter.priority": "Priority:",
        "filter.category": "Category:",
        "filter.due": "Due:",
        "filter.sort": "Sort:",
        "sort.due": "Due date",
        "sort.priority": "Priority",
        "sort.title": "Title",
        "sort.created": "Date created",
        "sort.status": "Status",
        "filter.all": "All",
        "filter.no_due": "No due date",
        "filter.today": "Today",
        "filter.week": "This week",
        "filter.overdue": "Overdue",
        "filter.clear": "Clear",
        "search.any": "Any",
        "btn.new": "New Task",
        "btn.edit": "Edit",
        "btn.delete": "Delete",
        "btn.complete": "Complete",
        "btn.details": "Details",
        "btn.close": "Close",
        "btn.save": "Save",
        "btn.cancel": "Cancel",
        "btn.ok": "OK",
        "btn.yes": "Yes",
        "btn.no": "No",
        "btn.browse": "Browse...",
        "btn.apply": "Apply",
        "btn.add": "Add",
        "btn.rename": "Rename",
        "btn.start": "Start",
        "btn.stop": "Stop",
        "btn.test": "Test voice",
        "btn.test_sound": "Test alert sound",
        "btn.default": "Default",
        "task.new_title": "New Task",
        "task.edit_title": "Edit Task",
        "task.details_title": "Task Details",
        "field.title": "Task title *:",
        "field.description": "Description:",
        "field.status": "Status:",
        "field.priority": "Priority:",
        "field.category": "Category / Project:",
        "field.start": "Start date and time:",
        "field.due": "Due date and time:",
        "field.hours": "Hours",
        "field.minutes": "Minutes",
        "field.seconds": "Seconds",
        "field.no_due": "No due date",
        "field.notes": "Notes:",
        "field.completed_at": "Completed at:",
        "field.created_at": "Created at:",
        "reminder.group": "Reminder settings",
        "reminder.enabled": "Enable reminder",
        "reminder.offset": "Remind before due:",
        "reminder.offset.custom": "Custom",
        "reminder.at_due": "At due time",
        "reminder.m5": "5 minutes before",
        "reminder.m15": "15 minutes before",
        "reminder.m30": "30 minutes before",
        "reminder.h1": "1 hour before",
        "reminder.d1": "1 day before",
        "reminder.custom_minutes": "Custom minutes:",
        "reminder.absolute": "Set an absolute reminder time",
        "field.has_start": "Set start date and time",
        "field.has_due": "Set due date and time",
        "reminder.read_aloud": "Read task title aloud",
        "reminder.sound": "Play alert sound",
        "reminder.repeat": "Repeat if not acknowledged",
        "reminder.repeat_interval": "Repeat interval (minutes):",
        "date.label": "Date:",
        "time.label": "Time:",
        "error.title_required": "Task title is required.",
        "error.bad_date": "Invalid date or time.",
        "error.title_dialog": "Invalid data",
        "error.generic": "An error occurred: {msg}",
        "error.db": "Database error: {msg}",
        "error.no_speech_voice": "No suitable speech voice is installed for the requested language.",
        "msg.added": "Task added: {title}",
        "msg.updated": "Task updated: {title}",
        "msg.deleted": "Task deleted: {title}",
        "msg.completed": "Task completed: {title}",
        "msg.reopened": "Task reopened: {title}",
        "msg.status_changed": "Task {title} is now: {status}",
        "confirm.delete_title": "Confirm delete",
        "confirm.delete": "Delete task \"{title}\"? This cannot be undone.",
        "confirm.exit_title": "Exit application",
        "confirm.exit": "Exiting will stop all reminders until you start the app again. Continue?",
        "msg.no_selection": "No task selected.",
        "msg.no_tasks": "There are no tasks in this list.",
        "msg.backup_done": "Backup created at: {path}",
        "msg.backup_failed": "Backup failed: {msg}",
        "msg.restore_confirm": "The current database will be replaced by the selected backup. A copy of the current state will be kept. Continue?",
        "msg.restore_done": "Database restored. The interface will refresh.",
        "msg.restore_failed": "Restore failed: {msg}",
        "msg.invalid_backup": "The selected file is not a valid backup.",
        "reminder.dialog_title": "Task reminder",
        "reminder.due_now": "The task is due now.",
        "reminder.due_in": "The task is due {delta}.",
        "reminder.overdue_by": "The task is overdue by {delta}.",
        "reminder.speak_ar": "تذكير بمهمة: {title}. {when}",
        "reminder.speak_en": "Task reminder: {title}. {when}",
        "reminder.complete": "Mark completed",
        "reminder.snooze5": "Snooze 5 minutes",
        "reminder.snooze15": "Snooze 15 minutes",
        "reminder.snooze60": "Snooze 1 hour",
        "reminder.open": "Open details",
        "reminder.close": "Close reminder",
        "reminder.missed_title": "Missed reminders",
        "reminder.missed_intro": "There are {count} missed reminders. Choose which to review.",
        "reminder.no_missed": "No missed reminders.",
        "reminder.stopped": "Speech stopped.",
        "reminder.review_selected": "Review selected",
        "reminder.dismiss_all": "Dismiss all",
        "reminder.snoozed": "Reminder snoozed {minutes} minutes: {title}",
        "settings.title": "Settings",
        "settings.tab.general": "General",
        "settings.tab.reminders": "Reminders",
        "settings.tab.sound": "Sound",
        "settings.tab.startup": "Startup & Background",
        "settings.language": "Interface language:",
        "settings.sound_enabled": "Enable sound reminders",
        "settings.alert_sound": "Play alert sound",
        "settings.alert_sound_file": "Alert sound file:",
        "settings.alert_sound_default": "Program default tone",
        "settings.alert_sound_hint": "Leave empty to use the program's default tone. You can pick a sound file from your device (WAV, MP3, WMA ...) and test it before saving; it will be used for all alerts.",
        "sound.file_filter": "Sound files|*.wav;*.mp3;*.wma;*.mid;*.midi|All files|*.*",
        "sound.play_failed": "Could not play this sound file. Make sure the format is supported on your system.",
        "settings.default_reminder": "Default reminder lead time:",
        "settings.default_priority": "Default priority:",
        "settings.auto_repeat": "Auto-repeat until acknowledged",
        "settings.repeat_interval": "Default repeat interval (minutes):",
        "settings.date_format": "Date and time display format:",
        "settings.start_with_windows": "Start with Windows",
        "settings.start_hidden": "Start hidden in background",
        "settings.run_in_background": "Keep running in background when window is closed",
        "settings.voice": "Voice used to read text:",
        "settings.voice.default": "System default",
        "settings.voice.none": "(no voice installed)",
        "settings.saved": "Settings saved.",
        "settings.startup_hint": "Note: Start with Windows launches the app at sign-in, but reminders cannot work while the computer is fully off; the app must be running in the background to deliver real-time alerts.",
        "settings.date_fmt.iso": "Year-Month-Day time",
        "settings.date_fmt.long": "Long date",
        "category.title": "Manage Categories / Projects",
        "category.name": "Name:",
        "category.list": "Categories:",
        "category.add": "Add category",
        "category.rename": "Rename",
        "category.delete": "Delete",
        "category.none": "No category",
        "category.delete_has_tasks": "This category is used by {count} task(s). How should they be handled?",
        "category.move_to_none": "Remove category from tasks (become uncategorized)",
        "category.delete_tasks": "Also delete the related tasks",
        "category.required_name": "Category name is required.",
        "tray.open": "Open application",
        "tray.new_task": "Add new task",
        "tray.upcoming": "Show upcoming tasks",
        "tray.toggle_reminders": "Enable/disable reminders",
        "tray.exit": "Exit permanently",
        "tray.tooltip": "Arabic Task Manager",
        "tray.hidden_info": "The app keeps running in the background and will deliver reminders. Reopen it from the tray icon near the clock.",
        "tray.not_available": "The system tray icon could not be created, so the window will not be hidden to avoid losing access to the app. You can disable background mode in Settings.",
        "msg.hidden_title": "Running in background",
        "help.title": "Keyboard Shortcuts",
        "help.body": (
            "Ctrl+N: New task\n"
            "Ctrl+E: Edit selected task\n"
            "Delete: Delete selected task\n"
            "Ctrl+F: Focus search box\n"
            "Ctrl+1: Not started view\n"
            "Ctrl+2: In progress view\n"
            "Ctrl+3: Completed view\n"
            "Ctrl+4: All tasks view\n"
            "F5: Refresh list\n"
            "Escape: Close current dialog\n"
        ),
        "about.body": (
            "Arabic Task Manager\n"
            "Version {version}\n\n"
            "A simple task and schedule manager with spoken reminders and screen reader "
            "support, available in Arabic and English.\n\n"
            "Created by Ramez Maged."
        ),
        "help.guide.title": "User Guide",
        "help.guide.body": (
            "Welcome to Arabic Task Manager.\n\n"
            "1) Add a task: from the File menu choose \"New Task\" or press Ctrl+N. Enter a "
            "title, optionally add a description and notes, and set the priority, category, "
            "due time, and reminder.\n\n"
            "2) Reminders: when you set a reminder time, the app alerts you at the right "
            "moment with spoken text and a reminder window. You can complete the task or "
            "snooze the reminder.\n\n"
            "3) Edit and delete: select a task in the list, then edit it (Ctrl+E) or delete "
            "it (Delete).\n\n"
            "4) Views: use the Views menu to switch between All, Not Started, In Progress, "
            "Completed, Today, Upcoming, and Overdue.\n\n"
            "5) Search and filter: use the search box at the top, and the filter controls for "
            "status, priority, category, and due range.\n\n"
            "6) Categories: from the Task menu choose \"Manage Categories / Projects\" to add, "
            "edit, or delete categories.\n\n"
            "7) Settings: from the File menu choose \"Settings\" to configure the language, "
            "sound, default reminder, start with Windows, and background running.\n\n"
            "8) Background: when you close the window the app keeps running from the system "
            "tray so reminders still arrive. To quit permanently choose \"Exit Permanently\" "
            "from the File menu.\n\n"
            "9) Backup: from the File menu you can create or restore a database backup.\n\n"
            "For more details about keyboard keys, open \"Keyboard Shortcuts\" from the Help menu."
        ),
        "msg.contact_failed": "Could not open the link automatically.\nYou can copy it manually:\n{url}",
    },
}


class Translator:
    """كائن الترجمة الفعّال الذي يحفظ اللغة الحالية."""

    def __init__(self, language: str = "ar") -> None:
        self._lang = language if language in _STRINGS else "ar"

    @property
    def language(self) -> str:
        return self._lang

    def set_language(self, language: str) -> None:
        if language in _STRINGS:
            self._lang = language

    @property
    def is_rtl(self) -> bool:
        return self._lang == "ar"

    def tr(self, key: str, **kwargs) -> str:
        """يعيد النص المترجم للمفتاح، مع دعم التنسيق بالمعاملات."""
        table = _STRINGS.get(self._lang, {})
        text = table.get(key)
        if text is None:
            text = _STRINGS["en"].get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text

    def status(self, value: str) -> str:
        return self.tr(f"status.{value}")

    def priority(self, value: str) -> str:
        return self.tr(f"priority.{value}")

    def view(self, value: str) -> str:
        return self.tr(f"view.{value}")


# كائن عام يستخدمه البرنامج بأكمله
_translator = Translator("ar")


def get_translator() -> Translator:
    return _translator


def set_language(language: str) -> None:
    _translator.set_language(language)


def tr(key: str, **kwargs) -> str:
    return _translator.tr(key, **kwargs)


def is_rtl() -> bool:
    return _translator.is_rtl
