"""Formulario VIH con identificación y código compartidos con TARV."""
import tkinter as tk
from tkinter import ttk
from app.ui.platform_support import UI_FONT

import app.forms.hiv_fields as hiv
from app.ui.patient_code_form import PatientCodeMixin


class HivForm(PatientCodeMixin, ttk.Frame):
    def __init__(self, parent, app, draft):
        super().__init__(parent)
        self.app = app
        self.iua_widgets = []
        self.columnconfigure(0, weight=1)
        app.controls['paciente_codigo'] = tk.StringVar()
        self.build_patient(draft)
        identity = ttk.Frame(self)
        identity.grid(row=3, column=0, sticky='ew')
        ttk.Label(identity, text='Código automático').pack(side='left', padx=(0, 8))
        ttk.Entry(identity, textvariable=app.controls['paciente_codigo'], state='readonly').pack(fill='x')
        table = ttk.Frame(self)
        table.grid(row=4, column=0, sticky='ew')
        table.columnconfigure(1, weight=1)
        grouped = {key for _, options in hiv.GROUPS.values() for _, key in options if key}
        row = 0
        for spec in hiv.FIELDS:
            key = spec['name']
            if key in hiv.CODE_FIELDS or key in hiv.IUA_FIELDS.values():
                continue
            if key in grouped:
                for group, (title, options) in hiv.GROUPS.items():
                    if key != options[0][1]:
                        continue
                    control = tk.StringVar(value=draft.get(group, ''))
                    app.controls[group] = control
                    ttk.Label(table, text=title).grid(row=row, column=0, sticky='w')
                    buttons = ttk.Frame(table)
                    buttons.grid(row=row, column=1, sticky='ew', pady=6)
                    for column, (caption, value) in enumerate(options):
                        button = ttk.Radiobutton(buttons, text=caption, variable=control, value=value,
                                                 style='Choice.TRadiobutton', command=app.persist_session)
                        button.grid(row=0, column=column, sticky='ew', padx=2)
                        buttons.columnconfigure(column, weight=1)
                        button.bind('<FocusIn>', app.reveal_field)
                    row += 1
                continue
            if key in ('region_sanitaria', 'paciente_dni', 'carga_viral', 'numero_muestra'):
                title = {'region_sanitaria': 'Institución de procedencia', 'paciente_dni': 'Documento',
                         'carga_viral': 'Determinaciones solicitadas',
                         'numero_muestra': 'A llenar por el laboratorio'}[key]
                ttk.Label(table, text=title, style='Section.TLabel').grid(
                    row=row, column=0, columnspan=2, sticky='ew', pady=(16, 8))
                row += 1
            ttk.Label(table, text=spec['label'], wraplength=240).grid(row=row, column=0, sticky='w', padx=(0, 8))
            if spec['type'] == 'signature':
                widget = ttk.Label(table, text='Firma PNG del perfil o firma manual al imprimir', wraplength=300)
            elif spec['multiline']:
                widget = tk.Text(table, height=3, width=28, wrap='word', font=(UI_FONT, 11))
                widget.insert('1.0', draft.get(key, ''))
                app.controls[key] = widget
            else:
                control = (tk.BooleanVar(value=draft.get(key, False)) if spec['type'] == 'checkbox'
                           else tk.StringVar(value=draft.get(key, '')))
                app.controls[key] = control
                widget = (ttk.Checkbutton(table, variable=control) if spec['type'] == 'checkbox'
                          else ttk.Entry(table, textvariable=control))
                if key == 'servicio_correo':
                    widget.configure(state='readonly')
                if key in hiv.IUA_FIELDS:
                    widget.destroy()
                    widget = ttk.Frame(table)
                    ttk.Checkbutton(widget, variable=control).pack(side='left')
                    iua = ttk.Frame(widget)
                    iua.pack(side='left', fill='x', expand=True, padx=(8, 0))
                    iua_key = hiv.IUA_FIELDS[key]
                    ttk.Label(iua, text=hiv.LABELS[iua_key]).pack(side='left', padx=(0, 6))
                    iua_control = tk.StringVar(value=draft.get(iua_key, ''))
                    app.controls[iua_key] = iua_control
                    validate = (self.register(lambda value: not value or value.isascii() and value.isdigit()), '%P')
                    entry = ttk.Entry(iua, textvariable=iua_control, width=16,
                                      validate='key', validatecommand=validate)
                    entry.pack(side='left', fill='x', expand=True)
                    entry.bind('<FocusIn>', app.reveal_field)
                    self.iua_widgets.append(iua)
            widget.grid(row=row, column=1, sticky='ew', pady=6)
            widget.bind('<FocusIn>', app.reveal_field)
            row += 1
        self.traces = []
        for key in ('paciente_nombres', 'paciente_apellido', 'paciente_fecha_nacimiento', 'paciente_genero_f'):
            control = app.controls[key]
            self.traces.append((control, control.trace_add('write', self.update_code)))
        self.update_code()
        control = app.controls['finalidad']
        self.traces.append((control, control.trace_add('write', self.update_email)))
        self.update_email()
        self.bind('<Destroy>', self.cleanup, add='+')

    def update_email(self, *_):
        purpose = self.app.controls['finalidad'].get()
        self.app.controls['servicio_correo'].set(hiv.SERVICE_EMAILS.get(purpose, ''))
        for widget in self.iua_widgets:
            if purpose == 'finalidad_seguimiento':
                widget.pack(side='left', fill='x', expand=True, padx=(8, 0))
            else:
                widget.pack_forget()

    def cleanup(self, event):
        if event.widget is self:
            for control, token in self.traces:
                control.trace_remove('write', token)
