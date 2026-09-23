"""Atajos de selección y navegación para todos los controles de texto de Tk."""
import re
import tkinter as tk


def select_all_text(event):
    widget = event.widget
    if isinstance(widget, tk.Text):
        widget.tag_add('sel', '1.0', 'end-1c')
        widget.mark_set('insert', 'end-1c')
        widget.mark_set('word_anchor', '1.0')
        widget.see('insert')
    else:
        widget.selection_range(0, 'end')
        widget.icursor('end')
    return 'break'


def move_word(event, backwards=False, select=False):
    widget = event.widget
    if str(widget.cget('state')) in ('disabled', 'readonly'):
        return 'break'
    multiline = isinstance(widget, tk.Text)
    if multiline:
        content = widget.get('1.0', 'end-1c')
        position = len(widget.get('1.0', 'insert'))
    else:
        content = widget.get()
        position = widget.index('insert')
    starts = [match.start() for match in re.finditer(r'\w+|[^\w\s]+', content)]
    target = (max((i for i in starts if i < position), default=0) if backwards
              else min((i for i in starts if i > position), default=len(content)))
    if multiline:
        if select:
            if not widget.tag_ranges('sel') or 'word_anchor' not in widget.mark_names():
                widget.mark_set('word_anchor', 'insert')
            anchor = widget.index('word_anchor')
        widget.tag_remove('sel', '1.0', 'end')
        index = f'1.0 + {target} chars'
        if select:
            first, last = (anchor, index) if widget.compare(anchor, '<', index) else (index, anchor)
            widget.tag_add('sel', first, last)
        widget.mark_set('insert', index)
        widget.see('insert')
    else:
        if select:
            if not widget.selection_present():
                widget.selection_from(position)
            widget.selection_to(target)
        else:
            widget.selection_clear()
        widget.icursor(target)
        widget.xview(target)
    return 'break'


def install_word_navigation(root):
    # Los enlaces de clase alcanzan también widgets y diálogos creados después.
    for classname in ('Entry', 'TEntry', 'Text', 'TCombobox', 'Spinbox', 'TSpinbox'):
        root.bind_class(classname, '<Control-a>', select_all_text)
        root.bind_class(classname, '<Control-A>', select_all_text)
        for key, backwards in [('Left', True), ('Right', False)]:
            for shift in (False, True):
                sequence = '<Control-' + ('Shift-' if shift else '') + key + '>'
                root.bind_class(classname, sequence,
                                lambda event, b=backwards, s=shift: move_word(event, b, s))
