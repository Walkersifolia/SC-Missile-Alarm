# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: 星际公民玩家自己的闹钟生成器 (onedir, DeepSeek 黑白风格)
from PyInstaller.utils.hooks import collect_data_files
import os

ROOT = os.path.dirname(os.path.abspath(SPEC))

# customtkinter 数据文件 (assets/*.json, *.otf 等)
ctk_datas = collect_data_files('customtkinter')

# 素材目录 (45+ wav, 按船厂分类)
materials_dir = os.path.join(ROOT, 'materials')
assert os.path.isdir(materials_dir), f'素材目录不存在: {materials_dir}'

# 应用图标 (星际公民 logo)
icon_path = os.path.join(ROOT, 'assets', 'app_icon.ico')

a = Analysis(
    [os.path.join(ROOT, 'app.py')],
    pathex=[ROOT],
    binaries=[],
    datas=ctk_datas + [(materials_dir, 'materials'), (os.path.join(ROOT, 'assets'), 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MissileAlert',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # 无控制台窗口 (GUI 应用)
    disable_windowed_traceback=False,
    icon=icon_path,         # 应用图标 (星际公民 logo)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='MissileAlert',
)
