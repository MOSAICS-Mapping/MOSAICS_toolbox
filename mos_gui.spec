# -*- mode: python ; coding: utf-8 -*-
import sys ; sys.setrecursionlimit(sys.getrecursionlimit() * 5)
block_cipher = None


a = Analysis(['mos_gui.py'],
             pathex=['/Users/Bryce/Desktop/Postdoc_Scripts/GitHub/04_mosaics_2020_pyinstaller_miniconda'],
             binaries=[],
             datas=[
                 ('/Users/Bryce/Desktop/Postdoc_Scripts/GitHub/04_mosaics_2020_pyinstaller_miniconda/1_crop.png', 'data'),
             ],
             hiddenimports=["cmath"],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='mos_gui',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
