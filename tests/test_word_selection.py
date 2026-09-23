"""Regresión de selección: interfaz limitada a los comandos soportados por ttk."""
from types import SimpleNamespace
import unittest

from app.ui.text_navigation import move_word, select_all_text


class EntryStub:
    """No ofrece selection_from/to: ttk tampoco implementa esos comandos Tcl."""
    def __init__(self):
        self.text = 'María   Pérez Ana'
        self.cursor = 0
        self.selection = None

    def cget(self, option):
        return 'normal'

    def get(self):
        return self.text

    def index(self, index):
        if index == 'insert':
            return self.cursor
        if index == 'end':
            return len(self.text)
        if index in ('sel.first', 'sel.last'):
            if self.selection is None:
                raise AssertionError('No hay selección')
            return self.selection[0 if index == 'sel.first' else 1]
        return int(index)

    def selection_present(self):
        return self.selection is not None

    def selection_clear(self):
        self.selection = None

    def selection_range(self, first, last):
        self.selection = (self.index(first), self.index(last))

    def icursor(self, index):
        self.cursor = self.index(index)

    def xview(self, index):
        pass


class WordSelectionTests(unittest.TestCase):
    def setUp(self):
        self.widget = EntryStub()
        self.event = SimpleNamespace(widget=self.widget)

    def move(self, backwards=False, select=True):
        self.assertEqual(move_word(self.event, backwards, select), 'break')

    def test_extend_shrink_and_clear(self):
        self.move()
        self.assertEqual(self.widget.selection, (0, 8))
        self.move()
        self.assertEqual(self.widget.selection, (0, 14))
        self.move(backwards=True)
        self.assertEqual(self.widget.selection, (0, 8))
        self.move(backwards=True)
        self.assertIsNone(self.widget.selection)
        self.assertEqual(self.widget.cursor, 0)

    def test_reverse_across_anchor_and_move_without_shift(self):
        self.widget.cursor = 8
        self.move(backwards=True)
        self.assertEqual(self.widget.selection, (0, 8))
        self.move()
        self.assertIsNone(self.widget.selection)
        self.move()
        self.assertEqual(self.widget.selection, (8, 14))
        self.move(select=False)
        self.assertIsNone(self.widget.selection)
        self.assertEqual(self.widget.cursor, len(self.widget.text))

    def test_shrink_selection_after_select_all(self):
        self.assertEqual(select_all_text(self.event), 'break')
        self.assertEqual(self.widget.selection, (0, len(self.widget.text)))
        self.move(backwards=True)
        self.assertEqual(self.widget.selection, (0, 14))
