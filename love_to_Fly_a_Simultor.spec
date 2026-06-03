# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for love_to_Fly_a_Simultor
# Build:  pyinstaller love_to_Fly_a_Simultor.spec

from pathlib import Path

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[str(Path('.').resolve())],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('settings.json', '.') if Path('settings.json').exists() else ('src', 'src'),
    ],
    hiddenimports=['pygame', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='love_to_Fly',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='love_to_Fly',
)
