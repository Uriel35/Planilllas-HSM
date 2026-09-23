"""Selector y editor de perfiles profesionales locales, sin contraseña."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from app.ui.platform_support import UI_FONT
from uuid import uuid4

from app.services.professional_data import PROFILE_FIELDS, validate_profile
from app.services.session_storage import save_session
from app.services.signature_data import MAX_PNG_BYTES, encode_signature


class ProfessionalDialog(tk.Toplevel):
    def __init__(self, parent, profiles, path, selected=None):
        super().__init__(parent)
        self.title('Ingreso del profesional')
        self.resizable(False, False)
        self.result = None
        self.profiles = profiles
        self.path = path
        self.ids = list(profiles)
        panel = ttk.Frame(self, padding=20)
        panel.pack(fill='both', expand=True)
        ttk.Label(panel, text='¿Qué profesional va a completar las planillas?',
                  font=(UI_FONT, 13, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        ttk.Label(panel, text='Perfil local, sin contraseña. Los borradores del paciente se comparten en este equipo.',
                  wraplength=530).grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 12))
        names = [f"{p['surname']}, {p['given_names']} · {p.get('registration') or 'Sin matrícula'}"
                 for p in profiles.values()]
        self.selector = ttk.Combobox(panel, values=names + ['+ Registrar profesional'], state='readonly', width=55)
        self.selector.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 12))
        self.controls = {}
        for row, (key, title) in enumerate(PROFILE_FIELDS.items(), 3):
            ttk.Label(panel, text=title).grid(row=row, column=0, sticky='w', pady=4, padx=(0, 15))
            var = tk.StringVar()
            ttk.Entry(panel, textvariable=var, width=38).grid(row=row, column=1, sticky='ew', pady=4)
            self.controls[key] = var
        buttons = ttk.Frame(panel)
        signature = ttk.Frame(panel)
        signature.grid(row=3 + len(PROFILE_FIELDS), column=0, columnspan=2, sticky='w', pady=(10, 0))
        self.signature_png = ''
        self.signature_status = ttk.Label(signature)
        self.signature_status.pack(anchor='w')
        actions = ttk.Frame(signature)
        actions.pack(anchor='w', pady=4)
        ttk.Button(actions, text='Cargar PNG de firma', command=self.choose_signature).pack(side='left')
        ttk.Button(actions, text='Ver firma', command=self.preview_signature).pack(side='left', padx=6)
        ttk.Button(actions, text='Quitar firma', command=self.remove_signature).pack(side='left')
        buttons.grid(row=4 + len(PROFILE_FIELDS), column=0, columnspan=2, sticky='e', pady=(16, 0))
        ttk.Button(buttons, text='Cancelar', command=self.destroy).pack(side='left', padx=8)
        ttk.Button(buttons, text='Guardar e ingresar', command=self.submit).pack(side='left')
        self.selector.bind('<<ComboboxSelected>>', self.select)
        self.selector.current(self.ids.index(selected) if selected in self.ids else (0 if self.ids else len(self.ids)))
        self.select()
        self.bind('<Escape>', lambda _: self.destroy())
        self.bind('<Return>', lambda _: self.submit())
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()
        self.selector.focus_set()
        self.wait_window()

    def select(self, _event=None):
        index = self.selector.current()
        profile = self.profiles[self.ids[index]] if index < len(self.ids) else {}
        for key, control in self.controls.items():
            control.set(profile.get(key, ''))
        self.signature_png = profile.get('signature_png', '')
        self.update_signature_status()

    def update_signature_status(self):
        self.signature_status.configure(text='Firma PNG cargada' if self.signature_png else 'Sin firma PNG')

    def choose_signature(self):
        filename = filedialog.askopenfilename(parent=self, title='Seleccioná la firma del profesional',
                                              filetypes=[('Imagen PNG', '*.png')])
        if not filename:
            return
        try:
            with open(filename, 'rb') as stream:
                encoded = encode_signature(stream.read(MAX_PNG_BYTES + 1))
        except (OSError, ValueError) as exc:
            messagebox.showerror('No se pudo cargar la firma', str(exc), parent=self)
            return
        self.signature_png = encoded
        self.update_signature_status()

    def remove_signature(self):
        self.signature_png = ''
        self.update_signature_status()

    def preview_signature(self):
        if not self.signature_png:
            messagebox.showinfo('Firma', 'Primero cargá un PNG de firma.', parent=self)
            return
        preview = tk.Toplevel(self)
        preview.title('Firma del profesional')
        preview.transient(self)
        original = tk.PhotoImage(master=preview, data=self.signature_png)
        factor = max(1, (original.width() + 499) // 500, (original.height() + 249) // 250)
        preview.signature_image = original.subsample(factor, factor)
        tk.Label(preview, image=preview.signature_image, background='white', padx=12, pady=12).pack()
        ttk.Button(preview, text='Cerrar', command=preview.destroy).pack(pady=8)
        preview.grab_set()
        self.wait_window(preview)
        self.grab_set()

    def submit(self):
        try:
            profile = validate_profile(dict({key: var.get() for key, var in self.controls.items()},
                                            signature_png=self.signature_png))
            index = self.selector.current()
            identifier = self.ids[index] if index < len(self.ids) else uuid4().hex
            updated = dict(self.profiles)
            updated[identifier] = profile
            save_session(self.path, {'version': 1, 'profiles': updated})
        except (OSError, ValueError) as exc:
            messagebox.showerror('No se pudo guardar el profesional', str(exc), parent=self)
            return
        self.result = (identifier, updated)
        self.destroy()
