# -*- mode: python -*-

#require PyInstaller 3.4, sip 
#python3 -m PyInstaller  --distpath ./ qtyoutube-dl.spec

block_cipher = None
#This will build a very large file (256MB), not good for loading experence!!

#options = [ ('v', None, 'OPTION'), ('W ignore', None, 'OPTION') ]
a = Analysis(['qtyoutube-dl.py'],
             pathex=[],
             binaries=[],
             datas=[('qtyoutube-dl.ui', '.'),('qtyoutube-dl.ico', '.'),
                    ('images/*', 'images/')],
             hiddenimports=["PyQt5.QtWidgets", "PyQt5.uic", "PyQt5.QtGui",
                            "PyQt5.QtCore", "twodict"],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='qtyoutube-dl',
          debug=False, strip=False,
          upx=False, console=False,
          icon='src/qtyoutube-dl.ico',
          version=None)
