# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Пути к Node.js (будут упакованы в EXE)
# ВАЖНО: Укажите правильный путь к вашей установке Node.js
NODE_DIR = r'C:\Program Files\nodejs'  # Стандартный путь установки Node.js

# Собираем все файлы Node.js для включения в EXE
node_binaries = []
node_datas = []

if os.path.exists(NODE_DIR):
    # Добавляем основные исполняемые файлы Node.js
    node_exe = os.path.join(NODE_DIR, 'node.exe')
    if os.path.exists(node_exe):
        node_binaries.append((node_exe, 'nodejs'))
    
    # Добавляем node_modules если они есть
    node_modules = os.path.join(NODE_DIR, 'node_modules')
    if os.path.exists(node_modules):
        for root, dirs, files in os.walk(node_modules):
            for file in files:
                src = os.path.join(root, file)
                rel_path = os.path.relpath(root, NODE_DIR)
                node_datas.append((src, os.path.join('nodejs', rel_path)))

# Добавляем server.js если он есть в проекте
if os.path.exists('server.js'):
    node_datas.append(('server.js', '.'))

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=node_binaries,
    datas=node_datas,
    hiddenimports=['paho.mqtt.client'],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NodeBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False - без консоли, True - с консолью (для отладки)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Можно добавить путь к .ico файлу: icon='assets\\icon.ico'
)
