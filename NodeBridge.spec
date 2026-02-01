# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE

block_cipher = None

# ============================================
# Path to node.exe
# ============================================
NODE_EXE = r'nodejs_portable\node.exe'
# ============================================

node_binaries = []
node_datas = []

# Check and add node.exe
if os.path.exists(NODE_EXE):
    print(f"Found node.exe: {NODE_EXE}")
    node_binaries.append((NODE_EXE, 'nodejs'))
else:
    print(f"WARNING: node.exe not found at: {NODE_EXE}")
    print("EXE will be built WITHOUT embedded Node.js!")

# Add server.js
if os.path.exists('server.js'):
    print("Found server.js")
    node_datas.append(('server.js', '.'))
else:
    print("WARNING: server.js not found!")

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
    console=False,  # False - hides console (for GUI apps), True - shows console (for debugging)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
