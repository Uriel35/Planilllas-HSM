"""Rutas del ejecutable y diferencias entre plataformas, sin datos reales."""
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from app import paths
from app.ui.platform_support import wheel_events


class PlatformTests(unittest.TestCase):
    def test_source_keeps_existing_project_data(self):
        with patch.object(sys, 'frozen', False, create=True):
            self.assertEqual(paths.writable_root(), paths.PROJECT_ROOT)

    def test_windows_executable_uses_local_appdata(self):
        with tempfile.TemporaryDirectory(prefix='Prueba con tildes á ') as folder:
            with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'platform', 'win32'), \
                    patch.dict(os.environ, {'LOCALAPPDATA': folder}):
                self.assertEqual(paths.writable_root(), Path(folder) / 'PlanillasPDF')
                self.assertNotEqual(paths.writable_root(), paths.PROJECT_ROOT)

    def test_windows_fallback(self):
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'platform', 'win32'), \
                patch.dict(os.environ, {}, clear=True), patch.object(Path, 'home', return_value=Path('/usuario')):
            self.assertEqual(paths.writable_root(), Path('/usuario/AppData/Local/PlanillasPDF'))

    def test_wheel_bindings(self):
        for system in ('win32', 'aqua', 'x11'):
            widget = SimpleNamespace(tk=Mock())
            widget.tk.call.return_value = system
            expected = ('<MouseWheel>', '<Button-4>', '<Button-5>') if system == 'x11' else ('<MouseWheel>',)
            self.assertEqual(wheel_events(widget), expected)

    def test_templates_are_available(self):
        from app.application import TEMPLATES, read_fields
        for name, path in TEMPLATES.items():
            with self.subTest(template=name):
                self.assertTrue(path.is_absolute())
                self.assertTrue(read_fields(path))
