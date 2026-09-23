"""Filas de búsqueda TARV respaldadas por las casillas del borrador."""
import tkinter as tk
from tkinter import ttk
from app.ui.platform_support import UI_FONT

from app.forms.tarv_fields import MEDICATIONS, search_medications


class MedicationPicker(ttk.Frame):
    def __init__(self, parent, controls, on_change, on_focus, install_shortcuts):
        super().__init__(parent)
        self.controls = controls
        self.on_change = on_change
        self.on_focus = on_focus
        self.install_shortcuts = install_shortcuts
        self.rows = []
        self.updating = False
        self.traces = []
        ttk.Label(self, text='Buscá por nombre o dosis y elegí una opción para marcar su casilla.',
                  wraplength=540).pack(anchor='w', pady=(0, 6))
        self.body = ttk.Frame(self)
        self.body.pack(fill='x')
        self.add_button = ttk.Button(self, text='Agregar medicamento', command=self.add_row)
        self.add_button.pack(anchor='w', pady=6)
        self.restore()
        for control in controls.values():
            token = control.trace_add('write', self.external_change)
            self.traces.append((control, token))
        self.bind('<Destroy>', self.cleanup, add='+')

    def cleanup(self, event):
        if event.widget is self:
            for control, token in self.traces:
                control.trace_remove('write', token)

    def external_change(self, *_):
        if not self.updating:
            self.restore()

    def restore(self):
        for child in self.body.winfo_children():
            child.destroy()
        self.rows = []
        for key, title, *_ in MEDICATIONS:
            if self.controls['med_' + key].get():
                self.add_row(key, title)
        if not self.rows:
            self.add_row()

    def add_row(self, key='', title=''):
        if len(self.rows) >= len(MEDICATIONS):
            return
        frame = ttk.Frame(self.body)
        frame.pack(fill='x', pady=5)
        frame.columnconfigure(0, weight=1)
        query = tk.StringVar(value=title)
        entry = ttk.Entry(frame, textvariable=query)
        entry.grid(row=0, column=0, sticky='ew')
        entry.bind('<FocusIn>', self.on_focus)
        results = tk.Listbox(frame, height=4, exportselection=False, font=(UI_FONT, 10))
        state = dict(frame=frame, query=query, entry=entry, results=results,
                     key=key, matches=[], selected=tk.StringVar(value=title))
        self.rows.append(state)
        ttk.Button(frame, text='Quitar', command=lambda: self.remove(state)).grid(row=0, column=1, padx=(6, 0))
        ttk.Label(frame, textvariable=state['selected'], wraplength=520).grid(row=2, column=0, columnspan=2, sticky='w')
        query.trace_add('write', lambda *_: self.filter(state))
        entry.bind('<Down>', lambda _: self.focus_results(state))
        entry.bind('<Return>', lambda _: self.choose(state))
        entry.bind('<KP_Enter>', lambda _: self.choose(state))
        entry.bind('<Escape>', lambda _: self.cancel(state))
        entry.bind('<Tab>', lambda _: self.leave(state))
        entry.bind('<Shift-Tab>', lambda _: self.leave(state))
        entry.bind('<ISO_Left_Tab>', lambda _: self.leave(state))
        results.bind('<Return>', lambda _: self.choose(state))
        results.bind('<KP_Enter>', lambda _: self.choose(state))
        results.bind('<ButtonRelease-1>', lambda _: self.choose(state))
        results.bind('<Escape>', lambda _: self.cancel(state))
        # La navegación general debe conservar Enter para seleccionar resultados.
        entry.medication_search = True
        self.install_shortcuts(frame)
        self.add_button.configure(state='disabled' if len(self.rows) == len(MEDICATIONS) else 'normal')
        if not key:
            entry.focus_set()

    def filter(self, state):
        used = {row['key'] for row in self.rows if row is not state}
        state['matches'] = [item for item in search_medications(state['query'].get()) if item[0] not in used]
        results = state['results']
        results.delete(0, 'end')
        for _, title, _, presentation in state['matches']:
            results.insert('end', f'{title} · presentación: {presentation} comp.')
        results.configure(height=max(1, min(5, len(state['matches']))))
        results.grid(row=1, column=0, columnspan=2, sticky='ew', pady=3)
        state['selected'].set(('Seleccionado: ' + next(item[1] for item in MEDICATIONS if item[0] == state['key']))
                              if state['key'] else 'Elegí un resultado para marcar su casilla.')
        if not state['matches']:
            state['selected'].set('Sin coincidencias. Podés usar «Otros medicamentos» para texto libre.')

    def focus_results(self, state):
        self.filter(state)
        if state['matches']:
            state['results'].selection_set(0)
            state['results'].activate(0)
            state['results'].focus_set()
        return 'break'

    def choose(self, state):
        selection = state['results'].curselection()
        if not selection and len(state['matches']) != 1:
            return self.focus_results(state)
        item = state['matches'][selection[0] if selection else 0]
        if any(row is not state and row['key'] == item[0] for row in self.rows):
            self.filter(state)
            return 'break'
        self.updating = True
        try:
            if state['key']:
                self.controls['med_' + state['key']].set(False)
            state['key'] = item[0]
            self.controls['med_' + item[0]].set(True)
        finally:
            self.updating = False
        self.cancel(state)
        self.on_change()
        return 'break'

    def cancel(self, state):
        title = next((item[1] for item in MEDICATIONS if item[0] == state['key']), '')
        state['query'].set(title)
        state['selected'].set(title)
        state['results'].grid_remove()
        state['entry'].focus_set()
        return 'break'

    def leave(self, state):
        self.cancel(state)
        self.on_change()

    def remove(self, state):
        self.updating = True
        try:
            if state['key']:
                self.controls['med_' + state['key']].set(False)
        finally:
            self.updating = False
        self.rows.remove(state)
        state['frame'].destroy()
        self.add_button.configure(state='normal')
        self.on_change()
