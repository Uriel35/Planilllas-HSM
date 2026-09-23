"""Construye todos los formularios con datos sintéticos en una pantalla real."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app import application


class ApplicationGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
            root.destroy()
        except tk.TclError as exc:
            if os.environ.get('REQUIRE_GUI_TESTS') == '1':
                raise
            raise unittest.SkipTest(f'Sin pantalla Tk: {exc}')

    def test_all_forms_and_preview(self):
        profile = {'surname': 'Prueba', 'given_names': 'Windows', 'signature_png': ''}
        dialog = SimpleNamespace(result=('test', {'test': profile}))
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            with patch.object(application, 'SESSION_FILE', folder / 'session.json'), \
                    patch.object(application, 'PROFILES_FILE', folder / 'profiles.json'), \
                    patch.object(application, 'OUTPUT_PDF', folder / 'salida.pdf'), \
                    patch.object(application, 'ensure_runtime_directories'), \
                    patch.object(application, 'ProfessionalDialog', return_value=dialog), \
                    patch.object(application.messagebox, 'showerror', side_effect=AssertionError('Error en la interfaz')):
                app = application.App()
                try:
                    for index, name in enumerate(app.visible):
                        with self.subTest(template=name):
                            app.listbox.selection_clear(0, 'end')
                            app.listbox.selection_set(index)
                            app.select_template()
                            app.update_idletasks()
                            self.assertEqual(app.current, name)
                            self.assertTrue(app.controls)
                            self.assertTrue(app.preview.images)
                    self.assertTrue(app.persist_session())
                finally:
                    app.destroy()
