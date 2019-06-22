@ECHO OFF

python -m PyInstaller  --clean --distpath=./ ./src/qtyoutube-dl.spec
