"""Órdenes SAMO con paciente compartido y una pestaña por formulario."""
from datetime import date
import tkinter as tk
from tkinter import simpledialog, ttk

import app.forms.samo_fields as samo
from app.ui.laboratory_picker import LaboratoryPicker


class SamoForm(ttk.Frame):
    def __init__(self, parent, app, draft):
        super().__init__(parent)
        self.app = app
        self.columnconfigure(0, weight=1)
        self.count = tk.StringVar(value=str(samo.order_count(draft)))
        app.controls['cantidad_samo'] = self.count
        actions = ttk.Frame(self)
        actions.grid(row=0, column=0, sticky='ew', pady=8)
        ttk.Button(actions, text='Cantidad de SAMOS', command=self.choose_count).pack(side='left', padx=(0, 8))
        ttk.Button(actions, text='Agregar SAMO', command=self.add_order).pack(side='left')
        self.remove_button = ttk.Button(actions, text='Quitar último SAMO', command=self.remove_order)
        self.remove_button.pack(side='left', padx=8)
        self.summary = tk.StringVar()
        ttk.Label(self, textvariable=self.summary,
                  wraplength=480).grid(row=1, column=0, sticky='w', pady=6)
        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=2, column=0, sticky='ew')
        self.tabs.enable_traversal()
        ttk.Label(self, text='Cambiar de SAMO: Alt + → (siguiente) / Alt + ← (anterior).',
                  wraplength=480).grid(row=3, column=0, sticky='w', pady=6)
        self.orders = []
        for index in range(samo.order_count(draft)):
            self.build_order(index, draft)
        self.update_buttons()
        self.install_tab_shortcuts(self)

    def build_order(self, index, draft):
        app = self.app
        prefix = samo.order_prefix(index)
        frame = ttk.Frame(self.tabs, padding=8)
        frame.columnconfigure(1, weight=1)
        before = (set(app.controls), set(app.choice_pairs), set(app.name_parts))
        row = 0
        for name, title in samo.LABELS.items():
            if name == 'paciente_genero_m':
                continue
            key = prefix + name
            ttk.Label(frame, text=title).grid(row=row, column=0, sticky='w', padx=(0, 12), pady=5)
            if name == 'paciente_apellido_nombre':
                widget = ttk.Frame(frame)
                app.name_parts[key] = {}
                for column, (part, caption) in enumerate((('surname', 'Apellido(s)'), ('given_names', 'Nombre(s)'))):
                    fallback = draft.get(key, '') if part == 'surname' else ''
                    control = (app.name_parts[name][part] if index else
                               tk.StringVar(value=draft.get(f'{key}:{part}', fallback)))
                    app.name_parts[key][part] = control
                    ttk.Label(widget, text=caption).grid(row=0, column=column, sticky='w')
                    entry = ttk.Entry(widget, textvariable=control, width=16)
                    entry.grid(row=1, column=column, sticky='ew', padx=(0, 4))
                    entry.bind('<FocusIn>', app.reveal_field)
                    widget.columnconfigure(column, weight=1)
            elif name in ('paciente_genero_f', 'condicion'):
                widget = ttk.Frame(frame)
                if name == 'paciente_genero_f':
                    male = prefix + 'paciente_genero_m'
                    female_value, male_value = draft.get(key, False), draft.get(male, False)
                    choice = 'Femenino' if female_value and not male_value else 'Masculino' if male_value and not female_value else ''
                    app.choice_pairs[key] = (male, 'Femenino', 'Masculino')
                    options = ('Masculino', 'Femenino')
                else:
                    choice = draft.get(key, '')
                    options = ('A', 'B')
                control = (app.controls[name] if index and name in samo.PATIENT_FIELDS else
                           tk.StringVar(value=choice))
                app.controls[key] = control
                for column, option in enumerate((*options, '')):
                    button = ttk.Radiobutton(widget, text=option or 'Sin indicar', value=option,
                                             variable=control, style='Choice.TRadiobutton',
                                             command=app.persist_session)
                    button.grid(row=0, column=column, padx=(0, 6))
                    button.bind('<FocusIn>', app.reveal_field)
            elif name == 'solicitudes':
                widget = LaboratoryPicker(frame, app, draft.get(key, ''))
                app.controls[key] = widget.value
            else:
                control = (app.controls[name] if index and name in samo.PATIENT_FIELDS else
                           tk.StringVar(value=draft.get(key, '')))
                app.controls[key] = control
                widget = ttk.Entry(frame, textvariable=control)
            widget.grid(row=row, column=1, sticky='ew', pady=5)
            widget.bind('<FocusIn>', app.reveal_field)
            row += 1
        owned = (set(app.controls) - before[0], set(app.choice_pairs) - before[1],
                 set(app.name_parts) - before[2])
        self.orders.append((frame, owned))
        self.tabs.add(frame, text=f'SAMO {index + 1}')
        self.install_tab_shortcuts(frame)

    def install_tab_shortcuts(self, widget):
        # Interceptar antes de los atajos propios de Entry y Text.
        widget.bind('<Control-Next>', lambda _event: self.change_tab(1))
        widget.bind('<Control-Prior>', lambda _event: self.change_tab(-1))
        widget.bind('<Alt-Right>', lambda _event: self.change_tab(1))
        widget.bind('<Alt-Left>', lambda _event: self.change_tab(-1))
        for child in widget.winfo_children():
            self.install_tab_shortcuts(child)

    def change_tab(self, direction):
        tabs = self.tabs.tabs()
        if tabs:
            index = (self.tabs.index('current') + direction) % len(tabs)
            self.tabs.select(tabs[index])
            # Sacar el foco del campo de la pestaña que acaba de ocultarse.
            self.tabs.focus_set()
        return 'break'

    def update_buttons(self):
        self.count.set(str(len(self.orders)))
        self.remove_button.configure(state='normal' if len(self.orders) > 1 else 'disabled')
        count = len(self.orders)
        self.summary.set(f'{count} SAMO(s) en {(count + 1) // 2} página(s). '
                         'Dos por página. Datos del paciente, condición y diagnóstico compartidos; '
                         'estudios independientes.')

    def choose_count(self):
        count = simpledialog.askinteger('Cantidad de SAMOS', '¿Cuántos SAMOS querés?',
                                        parent=self, initialvalue=len(self.orders), minvalue=1)
        if count is None:
            return
        while len(self.orders) < count:
            self.add_order(persist=False)
        while len(self.orders) > count:
            self.drop_last()
        self.update_buttons()
        self.app.persist_session()

    def add_order(self, persist=True):
        prefix = samo.order_prefix(len(self.orders))
        draft = {prefix + 'fecha_solicitud': date.today().strftime('%d/%m/%Y'),
                 prefix + 'establecimiento': self.app.professional.get('institution', '')}
        self.build_order(len(self.orders), draft)
        self.update_buttons()
        frame = self.orders[-1][0]
        self.app.install_shortcuts(frame)
        self.app.install_form_navigation(frame)
        self.tabs.select(frame)
        self.app.canvas.yview_moveto(0)
        if persist:
            self.app.persist_session()

    def remove_order(self):
        if len(self.orders) <= 1:
            return
        self.drop_last()
        self.update_buttons()
        self.app.persist_session()

    def drop_last(self):
        frame, owned = self.orders.pop()
        for mapping, keys in zip((self.app.controls, self.app.choice_pairs, self.app.name_parts), owned):
            for key in keys:
                mapping.pop(key, None)
        self.tabs.forget(frame)
        frame.destroy()

    def reset(self):
        while len(self.orders) > 1:
            self.drop_last()
        if self.app.current == samo.PPD_TEMPLATE:
            self.add_order(persist=False)
        self.update_buttons()
        self.tabs.select(self.orders[0][0])
