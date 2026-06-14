# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/love_nic/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('projeto/src/img', 'projeto/src/img'),
        ('projeto/src/mp3', 'projeto/src/mp3'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='love_nic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='projeto/src/img/love_nic.ico',
    version='version_info.txt',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
