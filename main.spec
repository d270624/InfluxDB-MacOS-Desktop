# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
import os
import sys
path = os.path.dirname(sys.argv[0])

a = Analysis(['main.py','create_database.py','create_ui.py','history_ui.py','new_connect_ui.py','ui.py'],
             pathex=['/Volumes/soft/InfluxDBClientDesktop'],
             binaries=[],
             datas=[('images','images'),('db','db')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='InfluxDBClient',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,icon=path + '/images/main.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='InfluxDBClient')
