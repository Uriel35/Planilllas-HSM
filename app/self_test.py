"""Prueba del paquete distribuible con datos sintéticos y archivos temporales."""
import json
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import ttk
import traceback

import fitz

from app.application import TEMPLATES, apply_form_defaults, generate_pdf, read_fields
from app.services.session_storage import load_session, save_session
from app.ui.app_theme import apply_theme
from app.ui.pdf_preview import PdfPreview


def run(report_path):
    root = None
    report = {'ok': False, 'templates': 0}
    try:
        root = tk.Tk()
        root.withdraw()
        apply_theme(root)
        checked = tk.BooleanVar(root, False)
        checkbox = ttk.Checkbutton(root, variable=checked)
        checkbox.invoke()
        assert checked.get(), 'La casilla no cambia de estado.'
        preview = PdfPreview(root)
        with tempfile.TemporaryDirectory(prefix='planillas-prueba-') as folder:
            folder = Path(folder)
            session = {'version': 1, 'patient': {'surname': 'Prueba áéíóú'}, 'drafts': {}, 'saved': {}}
            save_session(folder / 'sesión.json', session)
            assert load_session(folder / 'sesión.json') == session
            for index, (name, template) in enumerate(TEMPLATES.items()):
                assert read_fields(template), f'Plantilla sin campos: {name}'
                target = folder / f'planilla {index}.pdf'
                generate_pdf(template, target, apply_form_defaults(name, {}))
                with fitz.open(target) as document:
                    assert len(document) and not any(list(p.widgets()) for p in document)
                preview.load(target.read_bytes(), name, reset=True)
                root.update_idletasks()
                assert preview.images, f'No se renderizó: {name}'
                report['templates'] += 1
            preview.destroy()
        report['ok'] = True
    except Exception:
        report['error'] = traceback.format_exc()
    finally:
        if root is not None:
            root.destroy()
    Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['ok'] else 1
