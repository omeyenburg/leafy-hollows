# -*- mode: python ; coding: utf-8 -*-
import platform

name = "Hello World"

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('scripts', 'scripts'), ('data', 'data')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Hello World',
)

if platform.system() == "Darwin":
    app = BUNDLE(
        coll,
        name=name + '.app',
        icon='./icon/icon.icns',
        bundle_identifier=None,
    )
else:
    app = BUNDLE(
        coll,
        name=name + '.exe',
        icon='./icon/icon/ico',
        bundle_identifier=None,
    )