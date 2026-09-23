"""Selector con búsqueda y lista editable de solicitudes de laboratorio."""
import tkinter as tk
from tkinter import ttk
from app.ui.platform_support import UI_FONT
import unicodedata

from app.forms.samo_fields import STUDIES, PACKAGES, serology_name

PACKAGE_OPTIONS = {f'{name} (paquete)': studies for name, studies in PACKAGES.items()}
SEARCH_OPTIONS = (*PACKAGE_OPTIONS, *STUDIES)


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold())
                   if not unicodedata.combining(c))


def merge_studies(current, studies):
    current = current.strip()
    existing = {normalized(serology_name(item) or item.strip())
                for item in current.replace('\n', ';').split(';')}
    additions = []
    for study in studies:
        key = normalized(serology_name(study) or study)
        if key not in existing:
            additions.append(study)
            existing.add(key)
    return '; '.join(([current] if current else []) + additions)


class LaboratoryPicker(ttk.Frame):
    def __init__(self, parent, app, value=''):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.query = tk.StringVar()
        self.search = ttk.Entry(self, textvariable=self.query)
        self.search.grid(row=0, column=0, sticky='ew')
        self.search.handles_return = True
        self.query.trace_add('write', self.filter_options)
        self.search.bind('<Down>', lambda _: self.move_suggestion(1))
        self.search.bind('<Up>', lambda _: self.move_suggestion(-1))
        self.search.bind('<Escape>', self.hide_suggestions)
        self.search.bind('<Return>', self.add_study)
        self.search.bind('<KP_Enter>', self.add_study)
        ttk.Button(self, text='Agregar', command=self.add_study).grid(row=0, column=1, padx=(6, 0))
        self.suggestions = tk.Listbox(self, height=5, exportselection=False,
                                      font=(UI_FONT, 11), takefocus=False)
        self.suggestions.grid(row=1, column=0, columnspan=2, sticky='ew')
        self.suggestions.grid_remove()
        self.suggestions.bind('<ButtonRelease-1>', self.choose_suggestion)
        ttk.Label(self, text='Buscá estudios o paquetes. Elegí con clic o con ↓ / ↑ y Enter. '
                            'Los paquetes agregan sus estudios. También podés agregar un estudio propio.',
                  wraplength=330).grid(row=2, column=0, columnspan=2, sticky='w', pady=6)
        self.selected = ttk.Frame(self)
        self.selected.columnconfigure(0, weight=1)
        self.selected.grid(row=4, column=0, columnspan=2, sticky='ew')
        self.value = tk.StringVar(value=value)
        self.value.trace_add('write', self.render_studies)
        self.app = app
        self.search.bind('<FocusIn>', app.reveal_field)
        self.clear_button = ttk.Button(self, text='Eliminar todos', command=self.clear_studies)
        self.clear_button.grid(row=3, column=0, columnspan=2, sticky='e', pady=(0, 6))
        self.render_studies()

    def append_studies(self, studies):
        current = self.value.get()
        updated = merge_studies(current, studies)
        if updated != current:
            self.value.set(updated)
            self.app.persist_session()

    def studies(self):
        return [item.strip() for item in self.value.get().replace('\n', ';').split(';')
                if item.strip()]

    def render_studies(self, *_args):
        for child in self.selected.winfo_children():
            child.destroy()
        studies = self.studies()
        self.clear_button.configure(state='normal' if studies else 'disabled')
        if not studies:
            ttk.Label(self.selected, text='Todavía no agregaste estudios.').grid(sticky='w')
        ordered = sorted(enumerate(studies), key=lambda item: bool(serology_name(item[1])))
        row = 0
        heading_added = False
        for index, study in ordered:
            short_name = serology_name(study)
            if short_name and not heading_added:
                ttk.Label(self.selected, text='Serología', style='Section.TLabel').grid(
                    row=row, column=0, columnspan=2, sticky='ew', pady=(8, 3))
                row += 1
                heading_added = True
            ttk.Label(self.selected, text=short_name or study, wraplength=300).grid(
                row=row, column=0, sticky='w', pady=3)
            button = ttk.Button(self.selected, text='Eliminar',
                                command=lambda i=index: self.remove_study(i))
            button.grid(row=row, column=1, padx=(6, 0), pady=3)
            button.bind('<FocusIn>', self.app.reveal_field)
            row += 1

    def remove_study(self, index):
        studies = self.studies()
        del studies[index]
        self.search.focus_set()
        self.value.set('; '.join(studies))
        self.app.persist_session()

    def clear_studies(self):
        self.query.set('')
        self.value.set('')
        self.search.focus_set()
        self.app.persist_session()

    def filter_options(self, *_args):
        query = normalized(self.query.get().strip())
        matches = [study for study in SEARCH_OPTIONS if query in normalized(study)] if query else []
        self.suggestions.delete(0, 'end')
        for study in matches:
            self.suggestions.insert('end', study)
        if matches:
            self.suggestions.configure(height=min(5, len(matches)))
            self.suggestions.grid()
        else:
            self.hide_suggestions()

    def hide_suggestions(self, _event=None):
        self.suggestions.selection_clear(0, 'end')
        self.suggestions.grid_remove()
        return 'break'

    def move_suggestion(self, direction):
        if not self.suggestions.winfo_ismapped():
            self.filter_options()
        size = self.suggestions.size()
        if size:
            selected = self.suggestions.curselection()
            index = max(0, min(size - 1, selected[0] + direction)) if selected else (0 if direction > 0 else size - 1)
            self.suggestions.selection_clear(0, 'end')
            self.suggestions.selection_set(index)
            self.suggestions.see(index)
        return 'break'

    def choose_suggestion(self, _event=None):
        if self.suggestions.curselection():
            return self.add_study()

    def add_study(self, _event=None):
        study = ' '.join(self.query.get().split())
        selected = self.suggestions.curselection()
        if selected:
            study = self.suggestions.get(selected[0])
        if study:
            package = next((items for name, items in PACKAGE_OPTIONS.items()
                            if normalized(name) == normalized(study)), None)
            self.append_studies(package if package is not None else (study,))
            self.query.set('')
            self.filter_options()
        self.search.focus_set()
        return 'break'
