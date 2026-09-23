"""Entradas compartidas para calcular el código del paciente."""
import tkinter as tk
from tkinter import ttk
import app.forms.tarv_fields as tarv


class PatientCodeMixin:
    def build_patient(self, draft):
        frame = ttk.Frame(self)
        frame.grid(row=2, column=0, sticky='ew', pady=10)
        frame.columnconfigure(1, weight=1)
        for row, (key, title) in enumerate((('paciente_nombres', 'Nombre(s)'),
                                           ('paciente_apellido', 'Apellido(s)'),
                                           ('paciente_fecha_nacimiento', 'Nacimiento (DD/MM/AAAA)'))):
            control = tk.StringVar(value=draft.get(key, ''))
            self.app.controls[key] = control
            ttk.Label(frame, text=title).grid(row=row, column=0, sticky='w', padx=(0, 10))
            entry = ttk.Entry(frame, textvariable=control)
            entry.grid(row=row, column=1, sticky='ew', pady=5)
            entry.bind('<FocusIn>', self.app.reveal_field)
        female, male = draft.get('paciente_genero_f', False), draft.get('paciente_genero_m', False)
        control = tk.StringVar(value='F' if female and not male else 'M' if male and not female else '')
        self.app.controls['paciente_genero_f'] = control
        self.app.choice_pairs['paciente_genero_f'] = ('paciente_genero_m', 'F', 'M')
        ttk.Label(frame, text='Sexo').grid(row=3, column=0, sticky='w')
        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=1, sticky='ew')
        for column, (title, value) in enumerate((('M', 'M'), ('F', 'F'), ('Sin indicar', ''))):
            button = ttk.Radiobutton(buttons, text=title, value=value, variable=control,
                                     style='Choice.TRadiobutton', command=self.app.persist_session)
            button.grid(row=0, column=column, sticky='ew', padx=3)
            buttons.columnconfigure(column, weight=1)
            button.bind('<FocusIn>', self.app.reveal_field)
        self.code_hint = tk.StringVar()
        ttk.Label(frame, textvariable=self.code_hint, wraplength=540).grid(
            row=4, column=0, columnspan=2, sticky='w', pady=5)

    def update_code(self, *_):
        controls = self.app.controls
        try:
            code = tarv.patient_code(*(controls[key].get() for key in
                                       ('paciente_nombres', 'paciente_apellido',
                                        'paciente_fecha_nacimiento', 'paciente_genero_f')))
            self.code_hint.set('Código calculado automáticamente con el primer nombre y el apellido.')
        except ValueError as exc:
            code = ''
            self.code_hint.set(str(exc))
        controls['paciente_codigo'].set(code)

