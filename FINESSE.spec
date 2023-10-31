# -*- mode: python ; coding: utf-8 -*-
import docs.gen_user_guide as gen_guide

block_cipher = None

gen_guide.generate_html()

a = Analysis(
    ["stub.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("finesse/gui/images/*.png", "finesse/gui/images"),
        (
            "finesse/hardware/plugins/em27/diag_autom.htm",
            "finesse/hardware/plugins/em27",
        ),
        ("docs/user_guide.html", "docs"),
    ],
    hiddenimports=["finesse.gui.images"],
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
    name="FINESSE",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
