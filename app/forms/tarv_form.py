"""Edición de dos recetas con borrador independiente para la segunda."""
import tkinter as tk
from tkinter import ttk

import app.forms.tarv_fields as tarv
from app.ui.medication_picker import MedicationPicker
from app.ui.patient_code_form import PatientCodeMixin


class TarvForm(PatientCodeMixin, ttk.Frame):
    def __init__(self, parent, app, draft):
        super().__init__(parent)
        self.app = app
        self.columnconfigure(0, weight=1)
        self.same = tk.BooleanVar(value=tarv.same_prescriptions(draft))
        app.controls['son_iguales'] = self.same
        self.months = tk.StringVar(value=str(draft.get('meses') or '2'))
        app.controls['meses'] = self.months
        options = ttk.Frame(self)
        options.grid(row=0, column=0, sticky='ew')
        ttk.Label(options, text='Meses').pack(side='left', padx=(0, 8))
        months = ttk.Combobox(options, textvariable=self.months, values=tarv.MONTH_OPTIONS,
                              state='readonly', width=5)
        months.pack(side='left')
        months.bind('<<ComboboxSelected>>', lambda _: app.persist_session())
        for spec in tarv.FIELDS:
            if spec['type'] == 'signature' or spec['name'] in tarv.REASONS:
                continue
            for prefix in ('', tarv.SECOND_PREFIX):
                key = prefix + spec['name']
                value = draft.get(key, False if spec['type'] == 'checkbox' else '')
                app.controls[key] = (tk.BooleanVar(value=value) if spec['type'] == 'checkbox'
                                     else tk.StringVar(value=value))
        for prefix in ('', tarv.SECOND_PREFIX):
            selected = [key for key in tarv.REASONS if draft.get(prefix + key)]
            value = draft.get(prefix + 'motivo', selected[0] if len(selected) == 1 else '')
            app.controls[prefix + 'motivo'] = tk.StringVar(value=value)
        ttk.Checkbutton(options, text='Son iguales', variable=self.same,
                        command=app.persist_session).pack(side='left', padx=12, pady=6)
        self.date_hint = tk.StringVar()
        ttk.Label(self, textvariable=self.date_hint, wraplength=540).grid(row=1, column=0, sticky='w')
        self.build_patient(draft)
        self.build_recipe(self, '', 'Primera receta', 3)
        self.second = ttk.Frame(self)
        self.second.columnconfigure(0, weight=1)
        self.second.grid(row=4, column=0, sticky='ew')
        self.build_recipe(self.second, tarv.SECOND_PREFIX, 'Segunda receta', 0)
        self.update_mode()
        self.traces = []
        for control in (self.same, self.months, app.controls['fecha_receta']):
            self.traces.append((control, control.trace_add('write', self.update_mode)))
        for key in ('paciente_nombres', 'paciente_apellido', 'paciente_fecha_nacimiento', 'paciente_genero_f'):
            control = app.controls[key]
            self.traces.append((control, control.trace_add('write', self.update_code)))
        self.update_code()
        self.bind('<Destroy>', self.cleanup, add='+')

    def cleanup(self, event):
        if event.widget is self:
            for control, token in self.traces:
                control.trace_remove('write', token)

    def update_mode(self, *_):
        if self.same.get():
            self.second.grid_remove()
            try:
                value = tarv.next_month(self.app.controls['fecha_receta'].get())
                text = ('Fecha de la segunda receta: ' + value if value else
                        'La segunda receta tendrá la misma medicación y la fecha un mes después.')
            except ValueError as exc:
                text = str(exc)
            self.date_hint.set(text)
        else:
            self.second.grid()
            self.date_hint.set('Completá la fecha y la medicación de cada receta. Código y DNI son compartidos.')
        if self.months.get() in tarv.MONTH_OPTIONS:
            self.date_hint.set(self.date_hint.get() + f' Se generarán {int(self.months.get()) // 2} hojas.')

    def build_recipe(self, parent, prefix, title, position):
        frame = ttk.Frame(parent)
        frame.grid(row=position, column=0, sticky='ew')
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=title, style='Section.TLabel').grid(
            row=0, column=0, columnspan=2, sticky='ew', pady=(16, 8))
        row = 1
        for spec in tarv.FIELDS:
            key = spec['name']
            if key in tarv.MEDICATION_FIELDS or key in tarv.OTHER_FIELDS or key in tarv.REASONS or spec['type'] == 'signature':
                continue
            if prefix and key in ('paciente_codigo', 'paciente_dni'):
                continue
            control = self.app.controls[prefix + key]
            ttk.Label(frame, text=spec['label']).grid(row=row, column=0, sticky='w', padx=(0, 10))
            widget = (ttk.Checkbutton(frame, variable=control) if spec['type'] == 'checkbox'
                      else ttk.Entry(frame, textvariable=control))
            if key == 'paciente_codigo':
                widget.configure(state='readonly')
            widget.grid(row=row, column=1, sticky='ew', pady=5)
            widget.bind('<FocusIn>', self.app.reveal_field)
            row += 1
        reasons = ttk.Frame(frame)
        reasons.grid(row=row, column=0, columnspan=2, sticky='ew', pady=8)
        for index, key in enumerate(tarv.REASONS):
            button = ttk.Radiobutton(reasons, text=tarv.LABELS[key], value=key,
                                     variable=self.app.controls[prefix + 'motivo'],
                                     style='Choice.TRadiobutton', command=self.app.persist_session)
            button.grid(row=index // 2, column=index % 2, sticky='ew', padx=3, pady=3)
            button.bind('<FocusIn>', self.app.reveal_field)
            reasons.columnconfigure(index % 2, weight=1)
        row += 1
        controls = {key: self.app.controls[prefix + key] for key in tarv.MEDICATION_FIELDS}
        picker = MedicationPicker(frame, controls, self.app.persist_session,
                                  self.app.reveal_field, self.app.install_shortcuts)
        picker.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        table = ttk.Frame(frame)
        table.grid(row=row + 1, column=0, columnspan=2, sticky='ew')
        for column, title in enumerate(('Otros medicamentos', 'Dosis diaria', 'Días de tratamiento')):
            table.columnconfigure(column, weight=3 if column == 0 else 1)
            ttk.Label(table, text=title).grid(row=0, column=column, sticky='w')
        for number in range(1, 5):
            for column, part in enumerate(('medicamento', 'dosis', 'dias')):
                entry = ttk.Entry(table, textvariable=self.app.controls[f'{prefix}otro_{number}_{part}'],
                                  width=22 if column == 0 else 10)
                entry.grid(row=number, column=column, sticky='ew', padx=(0, 4), pady=4)
                entry.bind('<FocusIn>', self.app.reveal_field)
