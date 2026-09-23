"""Pequeñas diferencias de presentación y eventos entre sistemas."""
import sys

UI_FONT = 'Segoe UI' if sys.platform == 'win32' else 'Sans'


def wheel_events(widget):
    if widget.tk.call('tk', 'windowingsystem') == 'x11':
        return ('<MouseWheel>', '<Button-4>', '<Button-5>')
    return ('<MouseWheel>',)
