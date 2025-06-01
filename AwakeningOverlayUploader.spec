# AwakeningOverlayUploader.spec
# -*- mode: python ; coding: utf-8 -*-
import os
import glob
from PyInstaller.utils.hooks import copy_metadata

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas = [
        *[(f, 'credentials') for f in glob.glob('credentials/*')],
        ('icon/aimi.ico', 'icon'),
        ],
    hiddenimports=['google_auth_oauthlib', 'google.auth', 'google.oauth2'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AwakeningOverlayUploader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX
    console=True,  # Set to True if you need a console window for debugging
    icon='icon/aimi.ico',  # Path to your icon file
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX
    name='AwakeningOverlayUploader'
)
