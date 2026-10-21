# -*- mode: python ; coding: utf-8 -*-
"""ملف PyInstaller لبناء مدير المهام العربي (نسخة ملف واحد).

Build with:
    python -m PyInstaller --clean --noconfirm task_manager.spec
Output:
    dist/ArabicTaskManager.exe
"""

import os

block_cipher = None

# حِزم pywin32 الاختيارية المطلوبة وقت التشغيل.
# PyInstaller يوفّر خطافًا مدمجًا لحزمة wx، لذا لا نحتاج جمع وحداتها.
hiddenimports = [
    "win32com",
    "win32com.client",
    "pythoncom",
    "win32event",
    "win32api",
    "winerror",
    "win32timezone",
]

analysis = Analysis(
    ["main.py"],
    pathex=[os.path.abspath(os.getcwd())],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "numpy"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    [],
    name="ArabicTaskManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # بلا نافذة كونسول (تطبيق رسومي)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="app.ico",  # ضع أيقونة هنا إن توفرت
)
