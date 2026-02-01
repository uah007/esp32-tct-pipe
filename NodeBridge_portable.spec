# -*- mode: python ; coding: utf-8 -*-
#
# NodeBridge.spec - PORTABLE VERSION
# 
# Этот вариант использует портативную версию Node.js
# Скачайте node-vXX.XX.XX-win-x64.zip с nodejs.org
# Распакуйте в папку 'nodejs_portable' рядом с этим файлом
#

import os

block_cipher = None

# Пути к портативному Node.js
PORTABLE_NODE_DIR = 'nodejs_portable'

# Собираем файлы для включения
node_binaries = []
node_datas = []

# Проверяем наличие портативного Node.js
if os.path.exists(PORTABLE_NODE_DIR):
    print(f"✓ Найден портативный Node.js в {PORTABLE_NODE_DIR}")
    
    # Добавляем node.exe
    node_exe = os.path.join(PORTABLE_NODE_DIR, 'node.exe')
    if os.path.exists(node_exe):
        node_binaries.append((node_exe, 'nodejs'))
        print(f"  ✓ node.exe добавлен")
    
    # Добавляем все DLL файлы
    for file in os.listdir(PORTABLE_NODE_DIR):
        if file.endswith('.dll'):
            dll_path = os.path.join(PORTABLE_NODE_DIR, file)
            node_binaries.append((dll_path, 'nodejs'))
            print(f"  ✓ {file} добавлен")
else:
    print(f"⚠️  ВНИМАНИЕ: Портативный Node.js не найден в {PORTABLE_NODE_DIR}")
    print("   EXE будет собран БЕЗ встроенного Node.js!")
    print("   Инструкция:")
    print("   1. Скачайте node-vXX.XX.XX-win-x64.zip с https://nodejs.org")
    print("   2. Распакуйте в папку 'nodejs_portable'")
    print("   3. Запустите сборку заново")

# Добавляем server.js если он есть
if os.path.exists('server.js'):
    node_datas.append(('server.js', '.'))
    print("✓ server.js добавлен")
else:
    print("⚠️  server.js не найден! Добавьте его перед сборкой")

a = Analysis(
    ['src\\main.pyw'],
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
