# PyInstaller spec: builds dist/pac-man/ (run with `make package`).
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["pac-man.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=["mazegenerator", "pacman.ui.app"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "mypy", "flake8"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pac-man",
    debug=False,
    strip=False,
    upx=False,
    console=True,   # keeps warnings visible when launched from a terminal
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="pac-man",
)
