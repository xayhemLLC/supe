# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Supe.

Builds standalone executables for:
- Windows: supe.exe
- macOS: supe (universal binary)
- Linux: supe

Usage:
    pyinstaller supe.spec
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all submodules
hidden_imports = (
    collect_submodules('ab') +
    collect_submodules('tasc') +
    collect_submodules('tascer') +
    collect_submodules('supe') +
    ['click', 'rich', 'rich.console', 'rich.panel', 'rich.table']
)

# Data files to include
datas = [
    ('README.md', '.'),
    ('docs', 'docs'),
]

a = Analysis(
    ['supe/cli.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'numpy',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='supe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)

# macOS app bundle (optional)
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Supe.app',
        icon=None,
        bundle_identifier='com.supe.cli',
        info_plist={
            'CFBundleShortVersionString': '0.1.0',
            'CFBundleVersion': '0.1.0',
            'NSHighResolutionCapable': True,
        },
    )
