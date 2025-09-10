# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('flet') + [('database/sistema.db', 'app_resources/database'), ('assets/icon.ico', 'assets'), ('config.json', '.')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('flet')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Ensure our local packages are bundled
hiddenimports += [
    'database',
    'database.database',
    'repositories',
    'utils',
    'views',
]


a = Analysis(
    ['main.py'],
    pathex=['C:\\Users\\saide\\sinc\\pdv3'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='PDV',
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
    icon=['assets\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PDV',
)
