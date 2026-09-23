"""Rutas del proyecto independientes del directorio desde el que se ejecuta."""
from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESOURCES_DIR = PROJECT_ROOT / 'resources'
TEMPLATES_DIR = RESOURCES_DIR / 'templates'
ORIGINALS_DIR = RESOURCES_DIR / 'originals'
FIELDS_DIR = RESOURCES_DIR / 'fields'


def writable_root():
    """El ejecutable guarda datos fuera del paquete y de Program Files."""
    if not getattr(sys, 'frozen', False):
        return PROJECT_ROOT
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local') / 'PlanillasPDF'
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'PlanillasPDF'
    return Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local' / 'share') / 'PlanillasPDF'


USER_DIR = writable_root()
DATA_DIR = USER_DIR / 'data'
OUTPUT_DIR = USER_DIR / 'output'
SESSION_FILE = DATA_DIR / 'datos_formularios.json'
PROFILES_FILE = DATA_DIR / 'profesionales.json'
OUTPUT_PDF = OUTPUT_DIR / 'planilla_llena.pdf'


def ensure_runtime_directories():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
