# Ejecutar desde la raíz: python -m PyInstaller packaging/PlanillasPDF.spec
from pathlib import Path

root = Path(SPECPATH).parent
# Incluir únicamente los recursos de la aplicación; nunca data/ ni output/.
datas = [
    (str(root / 'resources' / 'templates'), 'resources/templates'),
    (str(root / 'resources' / 'fields'), 'resources/fields'),
]
a = Analysis(
    [str(root / 'main.py')], pathex=[str(root)], datas=datas,
    binaries=[], hiddenimports=[], hookspath=[], hooksconfig={},
    runtime_hooks=[], excludes=['pdfrw'], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name='PlanillasPDF',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='PlanillasPDF')
