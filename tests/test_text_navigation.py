"""Pruebas de teclado con Tk real cuando hay una pantalla disponible."""
import tkinter as tk
from tkinter import ttk
import unittest
import os
from app.ui.text_navigation import install_word_navigation


class WordNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as exc:
            if os.environ.get('REQUIRE_GUI_TESTS') == '1':
                raise
            raise unittest.SkipTest(f'Sin pantalla Tk: {exc}')
        install_word_navigation(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.callback_errors = []
        original = self.root.report_callback_exception
        self.root.report_callback_exception = lambda kind, value, tb: self.callback_errors.append(str(value))
        self.addCleanup(setattr, self.root, 'report_callback_exception', original)

    def tearDown(self):
        self.assertEqual(self.callback_errors, [], 'Falló un atajo de Tk')

    def test_all_editable_classes(self):
        for kind in (tk.Entry, ttk.Entry, tk.Text, ttk.Combobox, tk.Spinbox, ttk.Spinbox):
            with self.subTest(kind=kind):
                widget = kind(self.root)
                widget.pack()
                self.root.update()
                widget.focus_force()
                self.root.update()
                if isinstance(widget, tk.Text):
                    widget.insert('1.0', 'María   Pérez\nAna')
                    widget.mark_set('insert', '1.0')
                    position = lambda: len(widget.get('1.0', 'insert'))
                else:
                    widget.delete(0, 'end')
                    widget.insert(0, 'María   Pérez Ana')
                    widget.icursor(0)
                    position = lambda: widget.index('insert')
                for key, expected in [('Right', 8), ('Right', 14), ('Left', 8), ('Left', 0), ('Left', 0)]:
                    widget.event_generate('<Control-' + key + '>')
                    self.assertEqual(position(), expected)
                widget.event_generate('<Control-Shift-Right>')
                selected = (widget.get('sel.first', 'sel.last') if isinstance(widget, tk.Text)
                            else widget.get()[widget.index('sel.first'):widget.index('sel.last')])
                self.assertEqual(selected, 'María   ')
                widget.event_generate('<Control-a>')
                selected = (widget.get('sel.first', 'sel.last') if isinstance(widget, tk.Text)
                            else widget.get()[widget.index('sel.first'):widget.index('sel.last')])
                self.assertEqual(selected, 'María   Pérez\nAna' if isinstance(widget, tk.Text)
                                 else 'María   Pérez Ana')
                for key, expected in [('Left', 'María   Pérez\n' if isinstance(widget, tk.Text)
                                       else 'María   Pérez '), ('Left', 'María   '),
                                      ('Right', 'María   Pérez\n' if isinstance(widget, tk.Text)
                                       else 'María   Pérez ')]:
                    widget.event_generate('<Control-Shift-' + key + '>')
                    selected = (widget.get('sel.first', 'sel.last') if isinstance(widget, tk.Text)
                                else widget.get()[widget.index('sel.first'):widget.index('sel.last')])
                    self.assertEqual(selected, expected)
                widget.destroy()
