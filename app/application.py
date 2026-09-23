"""Buscador local de planillas y generación de PDFs para imprimir."""
from pathlib import Path
from datetime import date
import os
import json
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import messagebox, ttk
from app.ui.platform_support import UI_FONT, wheel_events
import unicodedata

import fitz
import copy
from app.services.patient_data import FULL_NAME_FIELDS, PatientSession
from app.services.session_storage import load_session, save_session
from app.services.professional_data import load_profiles, apply_professional
from app.ui.professional_dialog import ProfessionalDialog
from app.services.signature_data import SIGNATURE_AREAS, decode_signature, validate_png
from app.ui.pdf_preview import PdfPreview
from app.ui.app_theme import apply_theme
import app.forms.film_array_fields as film_array
import app.forms.genxpert_fields as genxpert
import app.forms.tbc_cultivo_fields as tbc
import app.forms.tarv_fields as tarv
from app.forms.tarv_form import TarvForm
import app.forms.hiv_fields as hiv
from app.forms.hiv_form import HivForm
import app.forms.samo_fields as samo
import app.forms.cisticercosis_fields as cisticercosis
from app.ui.laboratory_picker import LaboratoryPicker
from app.forms.samo_form import SamoForm

from app.paths import (TEMPLATES_DIR, FIELDS_DIR, OUTPUT_PDF, SESSION_FILE,
                       PROFILES_FILE, ensure_runtime_directories)
PCR_CHECKBOX_FIELDS = {
    field['name'] for field in json.loads((FIELDS_DIR / 'pcr_virus_fields.json').read_text(encoding='utf-8'))
    if field['type'] == 'checkbox'
}
TEMPLATES = {
    cisticercosis.TEMPLATE: TEMPLATES_DIR / 'cisticercosis_planilla_rellenable.pdf',
    samo.TEMPLATE: TEMPLATES_DIR / 'SAMO_rellenable.pdf',
    samo.PPD_TEMPLATE: TEMPLATES_DIR / 'SAMO_rellenable.pdf',
    "Hidatidosis — ficha epidemiológica": TEMPLATES_DIR / "Hidatidosis ficha epidemiologica_rellenable.pdf",
    "Toxoplasmosis — planilla": TEMPLATES_DIR / "Toxoplasmosis planilla.pdf",
    "Orden de internación": TEMPLATES_DIR / "orden_de_internacion_rellenable.pdf",
    "PCR de virus": TEMPLATES_DIR / "PCR_virus_respiratorios_planilla_rellenable.pdf",
    "Film Array": TEMPLATES_DIR / "film_array_formulario_rellenable.pdf",
    "GenXpert": TEMPLATES_DIR / "GenXpert_planilla_rellenable.pdf",
    "TBC — cultivo": TEMPLATES_DIR / "TBC_cultivo_rellenable.pdf",
    tarv.TEMPLATE: TEMPLATES_DIR / "TARV_recetario_rellenable.pdf",
    hiv.TEMPLATE: TEMPLATES_DIR / "planilla_HIV_carga_viral_CD4_rellenable.pdf",
}
LABELS = {
    "undefined": "Inmunosupresión: sí", "undefined 2": "Inmunosupresión: no",
    "Check Box2": "Embarazo: sí", "Check Box 1": "Embarazo: no",
    "TelCelular": "Teléfono / celular",
    'fiebre_lt_38': 'Fiebre < 38 °C', 'fiebre_ge_38': 'Fiebre ≥ 38 °C',
    'internado_estado': 'Internado', 'uti_estado': 'UTI',
    'arm_estado': 'ARM', 'fallecido_estado': 'Fallecido',
}
# Posiciones del SI / NO impreso, verificadas en la primera página de PCR.
PCR_PRINTED_CHOICES = {
    'internado_estado': {'Sí': (60.55, 689.23, 66.95, 697.75), 'No': (74.55, 689.23, 86.09, 697.75)},
    'uti_estado': {'Sí': (218.66, 689.23, 224.94, 697.75), 'No': (232.54, 689.23, 244.08, 697.75)},
    'arm_estado': {'Sí': (368.68, 689.23, 375.07, 697.75), 'No': (381.67, 689.23, 393.21, 697.75)},
    'fallecido_estado': {'Sí': (56.91, 700.39, 63.18, 708.91), 'No': (70.79, 700.39, 82.33, 708.91)},
}
PCR_SECTIONS = {
    'establecimiento_notificador': '1. Institución y profesional notificante',
    'tipo_documento_dni': '2. Datos del paciente',
    'residencia_provincia': '3. Residencia y domicilio',
    'fecha_primera_consulta': '4. Información clínica y síntomas',
    'caso_bronquiolitis': '5. Tipo de caso',
    'comorbilidades_presenta_si': '6. Comorbilidades',
    'oseltamivir_administrado_si': '7. Tratamiento y evolución',
    'antecedente_viaje_14_dias_si': '8. Antecedentes de viaje',
    'vacunacion_covid_19_si': '9. Vacunación',
    'muestra_hisopado_ag': '10. Laboratorio y muestras',
    'derivado_influenza_ovr_si': '11. Derivación de la muestra',
    'clasificacion_en_estudio': '12. Clasificación del caso',
    'firma_aclaracion_notificador': '13. Firma y aclaración',
}
SECTIONS = {
    "declarante_provincia": "1. Datos del declarante",
    "paciente_apellido_nombres": "2. Identificación del paciente",
    "fecha_inicio_sintomas": "3. Datos clínicos",
    "ocupacion_riesgo": "4. Datos epidemiológicos",
    "fecha_toma_muestra": "5. Exámenes de laboratorio",
    "tratamiento_farmacologico_si": "6. Control y prevención",
    "paciente_hospitalizado_si": "7. Evolución y clasificación",
}
TOXO_YES_NO_PAIRS = {'Check Box2': 'Check Box 1', 'undefined': 'undefined 2'}
TOXO_QUESTION_LABELS = {'Check Box2': 'Embarazo', 'undefined': 'Inmunosupresión'}
TOXO_RESULT_COLUMNS = (('TÉCNICA', 'Técnica'), ('RESULTADO', 'Resultado'),
                       ('FECHA', 'Fecha'), ('LABORATORIO', 'Laboratorio'))
TOXO_RESULT_FIELDS = {f'{prefix}Row{row}' for prefix, _ in TOXO_RESULT_COLUMNS
                      for row in range(1, 5)}


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold())
                   if not unicodedata.combining(c))


def label(name):
    return LABELS.get(name, name.replace('_', ' ').capitalize())


def configure_field(path, widget):
    """Corrige los indicadores de la plantilla tanto en pantalla como en el PDF."""
    if Path(path).resolve() == TEMPLATES['Film Array'].resolve() and widget.field_name in film_array.CHECKBOX_FIELDS:
        widget.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
    if Path(path).resolve() == TEMPLATES['PCR de virus'].resolve() and widget.field_name in PCR_CHECKBOX_FIELDS:
        widget.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
    if Path(path).resolve() == TEMPLATES['Toxoplasmosis — planilla'].resolve():
        if widget.field_name == 'Observaciones':
            widget.field_flags |= 4096
        elif widget.field_name == 'ESTABLECIMIENTO':
            widget.field_flags &= ~4096


def apply_form_defaults(template, values):
    result = dict(values)
    if template in samo.TEMPLATES:
        result = samo.apply_defaults(template, result)
    if template == hiv.TEMPLATE:
        result = hiv.apply_defaults(result)
    if template == tarv.TEMPLATE:
        result.setdefault('son_iguales', True)
        result.setdefault('meses', '2')
    if template == 'GenXpert':
        defaults = {
            'servicio': 'Infectología',
            'institucion_correo': 'residenciainfectohsm@gmail.com',
            'fecha_solicitud': date.today().strftime('%d/%m/%Y'),
        }
        for key, value in defaults.items():
            if not str(result.get(key) or '').strip():
                result[key] = value
    if template == 'Film Array':
        for key in film_array.CHECKBOX_FIELDS & result.keys():
            result[key] = checkbox_value(result[key])
    if template == 'PCR de virus':
        result['domicilio_calle'] = ' '.join(str(result.get(key, '')).strip()
                                             for key in ('domicilio_calle', 'domicilio_manzana')
                                             if str(result.get(key, '')).strip())
        result['domicilio_manzana'] = ''
        for key in PCR_CHECKBOX_FIELDS & result.keys():
            result[key] = checkbox_value(result[key])
        for key in PCR_PRINTED_CHOICES.keys() & result.keys():
            result[key] = normalize_pcr_choice(result[key])
    if template == 'Toxoplasmosis — planilla' and not result.get('Fecha'):
        result['Fecha'] = date.today().strftime('%d/%m/%Y')
    return result


def checkbox_value(value):
    # Compatibilidad con borradores anteriores que guardaban las marcas como texto.
    if isinstance(value, str):
        return value.strip().casefold() not in ('', '0', 'false', 'no', 'off')
    return bool(value)


def normalize_pcr_choice(value):
    return {'si': 'Sí', 'no': 'No', '': ''}.get(normalize(str(value).strip()), value)


def read_fields(path):
    fields = []
    with fitz.open(path) as doc:
        seen = set()
        for page in doc:
            for widget in page.widgets():
                configure_field(path, widget)
                if widget.field_name in seen:
                    continue
                seen.add(widget.field_name)
                fields.append({"name": widget.field_name, "type": widget.field_type,
                               "multiline": bool(widget.field_flags & 4096),
                               "choices": (['Sí', 'No'] if Path(path).resolve() == TEMPLATES['PCR de virus'].resolve()
                                           and widget.field_name in PCR_PRINTED_CHOICES else widget.choice_values or [])})
    if not fields:
        raise ValueError("Esta plantilla todavía no tiene campos configurados.")
    if Path(path).resolve() == TEMPLATES['Film Array'].resolve():
        order = {key: index for index, key in enumerate(film_array.LABELS)}
        fields.sort(key=lambda field: order.get(field['name'], len(order)))
    return fields


def fit_text_widget(widget, value):
    """Usa una letra legible y la reduce según el ancho y las líneas disponibles."""
    rect = fitz.Rect(widget.rect)
    if rect.is_empty or rect.is_infinite:
        raise ValueError(f'El campo {label(widget.field_name)} no tiene un área válida.')
    # Las plantillas tienen casilleros de apenas 8 puntos de altura. Se amplían
    # hacia arriba, conservando su borde inferior junto a la línea impresa.
    rect.y0 = min(rect.y0, rect.y1 - 13)
    widget.rect = rect
    widget.text_font = 'Helv'
    width = max(1, rect.width - 4)
    height = max(1, rect.height - 2)
    multiline = bool(widget.field_flags & 4096)
    text = str(value).replace('\r\n', '\n').replace('\r', '\n')
    if not multiline:
        text = ' '.join(text.splitlines())

    def fits(size):
        if not multiline:
            return fitz.get_text_length(text, fontname='helv', fontsize=size) <= width
        lines = 0
        for paragraph in text.split('\n'):
            lines += 1
            used = 0
            for word in paragraph.split():
                advance = fitz.get_text_length(word, fontname='helv', fontsize=size)
                if advance > width:
                    return False
                space = fitz.get_text_length(' ', fontname='helv', fontsize=size) if used else 0
                if used + space + advance > width:
                    lines += 1
                    used = 0
                    space = 0
                used += space + advance
        return lines * size * 1.4 <= height

    size = min(9.0, height / 1.2)
    while size >= 6 and not fits(size):
        size = round(size - 0.1, 2)
    if size < 6:
        raise ValueError(f'El texto de «{label(widget.field_name)}» es demasiado largo. '
                         'Acortalo para que quepa sin quedar ilegible.')
    widget.field_value = text
    widget.text_fontsize = size


def generate_pdf(source, destination, values, signature_png=None):
    """Actualiza apariencias y fija los datos en una copia, sin modificar la plantilla."""
    source, destination = Path(source), Path(destination)
    if destination.resolve() in {p.resolve() for p in TEMPLATES.values()} or destination.resolve() == source.resolve():
        raise ValueError("Elegí otro archivo de destino para conservar la plantilla original.")
    pages = tarv.prescription_pages(values) if source.resolve() == TEMPLATES[tarv.TEMPLATE].resolve() else [values]
    if source.resolve() == TEMPLATES[hiv.TEMPLATE].resolve():
        pages = [hiv.pdf_values(values)]
    is_samo = source.resolve() == TEMPLATES[samo.TEMPLATE].resolve()
    if is_samo:
        pages = samo.prescription_pages(values)
    if len(pages) == 1:
        return _generate_single_pdf(source, destination, pages[0], signature_png)
    with tempfile.TemporaryDirectory(dir=destination.parent) as folder, fitz.open() as combined:
        for number, page_values in enumerate(pages):
            path = Path(folder) / f'recetas_{number}.pdf'
            _generate_single_pdf(source, path, page_values, signature_png)
            with fitz.open(path) as partial:
                if is_samo:
                    rect = partial[0].rect
                    if number % 2 == 0:
                        sheet = combined.new_page(width=rect.width, height=rect.height)
                    clip = fitz.Rect(0, 0, rect.width, rect.height / 2)
                    target = clip + (0, rect.height / 2, 0, rect.height / 2) if number % 2 else clip
                    sheet.show_pdf_page(target, partial, 0, clip=clip)
                else:
                    combined.insert_pdf(partial)
        complete = Path(folder) / 'completo.pdf'
        combined.save(complete, garbage=4, deflate=True)
        os.replace(complete, destination)


def _generate_single_pdf(source, destination, values, signature_png=None):
    if signature_png:
        validate_png(signature_png)
        if source.name not in SIGNATURE_AREAS:
            raise ValueError('Esta plantilla no tiene un espacio de firma configurado.')
    with fitz.open(source) as doc:
        is_pcr = source.resolve() == TEMPLATES['PCR de virus'].resolve()
        if is_pcr:
            values = apply_form_defaults('PCR de virus', values)
        known = {w.field_name for p in doc for w in p.widgets()}
        if values.keys() - known:
            raise ValueError("Hay datos que no pertenecen a esta plantilla.")
        for page in doc:
            address_rect = None
            if is_pcr:
                for address_widget in page.widgets():
                    if address_widget.field_name in ('domicilio_calle', 'domicilio_manzana'):
                        address_rect = (fitz.Rect(address_widget.rect) if address_rect is None
                                        else address_rect | address_widget.rect)
            for widget in list(page.widgets()):
                configure_field(source, widget)
                if is_pcr and widget.field_name == 'domicilio_manzana':
                    page.delete_widget(widget)
                    continue
                if is_pcr and widget.field_name == 'domicilio_calle':
                    widget.rect = address_rect
                if widget.field_type == fitz.PDF_WIDGET_TYPE_SIGNATURE:
                    continue
                value = values.get(widget.field_name, '')
                if source.resolve() == TEMPLATES[samo.TEMPLATE].resolve():
                    if widget.field_name == 'solicitudes':
                        samo.draw_studies(page, widget, value)
                        continue
                    if widget.field_name in samo.NUMERIC_CELLS:
                        samo.draw_numeric_cells(page, widget, value)
                        continue
                    if widget.field_name == 'condicion' and value not in ('', 'A', 'B'):
                        raise ValueError('Elegí A o B en Condición.')
                if source.resolve() == TEMPLATES['PCR de virus'].resolve() and widget.field_name in PCR_PRINTED_CHOICES:
                    choice = normalize_pcr_choice(value)
                    if choice not in ('', 'Sí', 'No'):
                        raise ValueError(f'Elegí Sí o No en {label(widget.field_name)}.')
                    options = PCR_PRINTED_CHOICES[widget.field_name]
                    page.delete_widget(widget)
                    if choice:
                        # Tachar la alternativa descartada; dejar legible la elegida.
                        rect = fitz.Rect(options['No' if choice == 'Sí' else 'Sí'])
                        y = (rect.y0 + rect.y1) / 2
                        page.draw_line((rect.x0 - 1, y), (rect.x1 + 1, y), color=(0, 0, 0), width=1)
                    continue
                if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    # Algunas plantillas no tienen /AP: fijar /V no garantiza
                    # una marca visible. La X queda como contenido imprimible.
                    rect = fitz.Rect(widget.rect)
                    is_liver_stage = (source.resolve() == TEMPLATES[cisticercosis.TEMPLATE].resolve()
                                      and widget.field_name.startswith('estadio_higado_'))
                    if rect.is_empty or rect.is_infinite:
                        raise ValueError(f'La casilla {label(widget.field_name)} no tiene un área válida.')
                    page.delete_widget(widget)
                    if checkbox_value(value):
                        if is_liver_stage:
                            page.draw_oval(rect, color=(0, 0, 0), width=1)
                            continue
                        inset = min(rect.width, rect.height) * 0.2
                        rect = fitz.Rect(rect.x0 + inset, rect.y0 + inset,
                                         rect.x1 - inset, rect.y1 - inset)
                        shape = page.new_shape()
                        shape.draw_line(rect.tl, rect.br)
                        shape.draw_line(rect.bl, rect.tr)
                        shape.finish(color=(0, 0, 0), width=1)
                        shape.commit()
                    continue
                elif widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                    if source.resolve() == TEMPLATES['Film Array'].resolve():
                        # Esta plantilla guarda valores viejos en algunos widgets hijos.
                        # Quitarlos permite usar el valor actualizado del campo padre.
                        if doc.xref_get_key(widget.xref, 'Parent')[0] == 'xref':
                            doc.xref_set_key(widget.xref, 'V', 'null')
                    fit_text_widget(widget, value)
                    if 'fecha' in normalize(widget.field_name):
                        # El fondo forma parte de la apariencia del campo y queda
                        # debajo de la fecha al fijar los datos en el PDF final.
                        # Sin datos, conservar las guías para completar a mano.
                        widget.fill_color = (1, 1, 1) if str(value).strip() else None
                elif widget.field_type in (fitz.PDF_WIDGET_TYPE_COMBOBOX, fitz.PDF_WIDGET_TYPE_LISTBOX):
                    widget.field_value = str(value)
                    widget.text_fontsize = 0
                else:
                    raise ValueError(f"Tipo de campo todavía no compatible: {widget.field_name}")
                widget.update()
        doc.bake(annots=False, widgets=True)
        if signature_png:
            for page_number, coordinates in SIGNATURE_AREAS[source.name]:
                page = doc[page_number]
                rect = fitz.Rect(coordinates)
                if rect.is_empty or not page.rect.contains(rect):
                    raise ValueError('El espacio de firma no es válido para esta plantilla.')
                page.insert_image(rect, stream=signature_png, keep_proportion=True, overlay=True)
        # Reemplazo atómico: un fallo no deja un PDF parcialmente escrito.
        fd, temporary = tempfile.mkstemp(suffix='.pdf', dir=destination.parent)
        os.close(fd)
        try:
            doc.save(temporary, garbage=4, deflate=True)
            os.replace(temporary, destination)
        finally:
            Path(temporary).unlink(missing_ok=True)


class App(tk.Tk):
    def __init__(self):
        ensure_runtime_directories()
        super().__init__()
        self.title('Planillas · Completar y guardar PDF')
        self.geometry('1500x850')
        self.minsize(800, 540)
        self.current = None
        self.visible: list[str] = []
        self.controls = {}
        self.choice_pairs = {}
        self.drafts = {}
        self.saved = {}
        self.patient = PatientSession()
        self.name_parts = {}
        self.loaded_values = {}
        self.last_persisted = None
        self.preview_key = None
        apply_theme(self)
        try:
            previous = load_session(SESSION_FILE)
            profiles = load_profiles(PROFILES_FILE)
        except (OSError, ValueError) as exc:
            messagebox.showerror('No se pudieron recuperar los datos',
                f'{exc}\n\nLos archivos de datos se conservan sin cambios. '
                'Corregilo o renombralo antes de volver a abrir el programa.', parent=self)
            self.destroy()
            return
        dialog = ProfessionalDialog(self, profiles, PROFILES_FILE)
        if dialog.result is None:
            self.destroy()
            return
        self.professional_id, self.profiles = dialog.result
        self.professional = self.profiles[self.professional_id]
        self.patient.values = previous.get('patient', {})
        self.drafts = previous.get('drafts', {})
        self.drafts = {name: apply_professional(name, draft, self.professional, replace=True)
                       for name, draft in self.drafts.items()}
        self.saved = previous.get('saved', {})
        self.protocol('WM_DELETE_WINDOW', self.close)
        sidebar = ttk.Frame(self, padding=18)
        sidebar.pack(side='left', fill='y')
        ttk.Label(sidebar, text='Planillas', style='Title.TLabel').pack(anchor='w')
        self.professional_label = ttk.Label(sidebar, wraplength=260)
        self.professional_label.pack(anchor='w', pady=(12, 4))
        self.update_professional_label()
        ttk.Button(sidebar, text='Cambiar / editar profesional', command=self.change_professional).pack(anchor='w')
        self.include_signature = tk.BooleanVar(value=bool(self.professional.get('signature_png')))
        self.signature_checkbox = ttk.Checkbutton(sidebar, text='Incluir firma PNG en el PDF',
                                                  variable=self.include_signature)
        self.signature_checkbox.pack(anchor='w', pady=(10, 4))
        self.signature_info = ttk.Label(sidebar, wraplength=260)
        self.signature_info.pack(anchor='w')
        ttk.Label(sidebar, text='Buscar por nombre (Ctrl + F)').pack(anchor='w', pady=(20, 5))
        self.query = tk.StringVar()
        search = ttk.Entry(sidebar, textvariable=self.query, width=32)
        self.search = search
        search.pack(fill='x')
        search.bind('<Down>', self.focus_results)
        search.bind('<Return>', self.open_result)
        search.bind('<Escape>', lambda _: self.query.set(''))
        self.query.trace_add('write', lambda *_: self.filter_templates())
        self.listbox = tk.Listbox(sidebar, width=29, height=20, exportselection=False,
                                  activestyle='none', font=(UI_FONT, 10), relief='flat', borderwidth=0,
                                  background='white', foreground='#243449', selectbackground='#147d8b',
                                  selectforeground='white', highlightthickness=0)
        self.listbox.pack(fill='both', expand=True, pady=12)
        self.listbox.bind('<<ListboxSelect>>', self.select_template)
        self.listbox.bind('<Return>', self.open_result)
        self.count = ttk.Label(sidebar)
        self.count.pack(anchor='w')
        ttk.Button(sidebar, text='Atajos de teclado · F1', command=self.show_shortcuts).pack(anchor='w', pady=(10, 0))
        split = ttk.Panedwindow(self, orient='horizontal')
        split.pack(side='left', fill='both', expand=True)
        panel = ttk.Frame(split, padding=14)
        split.add(panel, weight=1)
        self.preview = PdfPreview(split)
        split.add(self.preview, weight=1)
        self.heading = ttk.Label(panel, text='Seleccioná una planilla', style='Title.TLabel', wraplength=680)
        self.heading.pack(anchor='w')
        ttk.Label(panel, text='Enter o Tab: guardar y avanzar · Shift + Tab: Volver input anterior', wraplength=440).pack(anchor='w', pady=10)
        footer = ttk.Frame(panel)
        footer.pack(side='bottom', fill='x', pady=(12, 0))
        self.status = ttk.Label(footer, text='Los datos se completan en este equipo.', wraplength=440)
        self.status.pack(side='bottom', anchor='w', pady=(8, 0))
        self.save_button = ttk.Button(footer, text='Guardar PDF (Ctrl + S)', command=self.save_pdf, state='disabled', style='Primary.TButton')
        self.save_button.pack(side='right')
        ttk.Button(footer, text='Abrir PDF (Ctrl + O)', command=self.open_saved_pdf).pack(side='right', padx=6)
        ttk.Button(footer, text='Reiniciar datos (Ctrl + R)', command=self.reset_data).pack(side='right', padx=8)
        container = ttk.Frame(panel)
        container.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(container, highlightthickness=0, background='#f3f6fb')
        scrollbar = ttk.Scrollbar(container, command=self.canvas.yview)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.form = ttk.Frame(self.canvas, padding=8)
        self.window = self.canvas.create_window((0, 0), window=self.form, anchor='nw')
        self.form.columnconfigure(1, weight=1)
        self.form.bind('<Configure>', lambda _: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self.window, width=e.width))
        for event in wheel_events(self):
            self.bind_all(event, self.scroll)
        self.filter_templates()
        initial = previous.get('current')
        self.listbox.selection_set(self.visible.index(initial) if initial in self.visible else 0)
        self.select_template()
        self.install_shortcuts(self)
        search.focus_set()

    def refresh_preview(self, path=None):
        if not self.current or not hasattr(self, 'preview'):
            return
        source = Path(path) if path is not None else OUTPUT_PDF
        reset = self.preview_key != self.current
        try:
            message = ('PDF guardado · Se actualiza al pulsar Guardar PDF.' if path is None else
                       'Plantilla de referencia · Guardá el PDF para ver los datos completados.')
            self.preview.load(source.read_bytes(), message, reset=reset)
        except Exception as exc:
            self.preview.info.configure(text=f'No se pudo actualizar el visor: {exc}')
        self.preview_key = self.current

    def update_professional_label(self):
        self.professional_label.configure(
            text=f"Profesional: {self.professional['surname']}, {self.professional['given_names']}")

    def change_professional(self):
        if not self.persist_session(report=True):
            return
        dialog = ProfessionalDialog(self, self.profiles, PROFILES_FILE, self.professional_id)
        if dialog.result is None:
            return
        self.professional_id, self.profiles = dialog.result
        self.professional = self.profiles[self.professional_id]
        self.include_signature.set(bool(self.professional.get('signature_png')))
        self.update_signature_info()
        self.drafts = {name: apply_professional(name, draft, self.professional, replace=True)
                       for name, draft in self.drafts.items()}
        self.update_professional_label()
        if self.current:
            professional_draft = ({'cantidad_samo': self.controls['cantidad_samo'].get()}
                                  if self.current in samo.TEMPLATES else {})
            fields = apply_professional(self.current, professional_draft, self.professional, replace=True)
            self.set_professional_controls(fields)
            self.loaded_values = self.session_values()
        self.persist_session(report=True)

    def update_signature_info(self):
        supported = self.current is not None and TEMPLATES[self.current].name in SIGNATURE_AREAS
        available = bool(self.professional.get('signature_png'))
        self.signature_checkbox.configure(state='normal' if supported and available else 'disabled')
        self.signature_info.configure(text=(
            'Esta planilla no tiene espacio de firma configurado.' if not supported else
            'Cargá la firma desde el perfil profesional.' if not available else
            'Se usará la imagen de firma del profesional activo.'))

    def set_professional_controls(self, values):
        for key, value in values.items():
            control = self.controls.get(key)
            if isinstance(control, tk.Text):
                control.delete('1.0', 'end')
                control.insert('1.0', value)
            elif control is not None:
                control.set(value)

    def persist_session(self, report=False):
        if self.current:
            self.remember_patient()
        data = {'version': 1, 'patient': self.patient.values,
                'drafts': self.drafts, 'saved': self.saved, 'current': self.current}
        if data == self.last_persisted:
            return True
        try:
            save_session(SESSION_FILE, data)
        except (OSError, ValueError) as exc:
            self.status.configure(text='No se pudieron guardar los datos automáticamente.')
            if report:
                messagebox.showerror('No se pudieron guardar los datos', str(exc), parent=self)
            return False
        self.last_persisted = copy.deepcopy(data)
        self.status.configure(text='Datos guardados automáticamente.')
        return True

    def install_shortcuts(self, parent):
        # Tk puede incluir etiquetas con enlaces de teclado en el recorrido
        # del foco. Solo los controles interactivos deben recibir esos enlaces.
        interactive = isinstance(parent, (tk.Entry, ttk.Entry, tk.Text,
                                          tk.Listbox, ttk.Button, ttk.Checkbutton, ttk.Radiobutton))
        if isinstance(parent, (ttk.Label, ttk.Frame, tk.Label, tk.Frame, tk.Canvas, ttk.Scrollbar)):
            parent.configure(takefocus=False)
        # El enlace del widget se ejecuta antes de los atajos propios de Text/Entry.
        for sequence, action in (('<Control-f>', self.focus_search),
                                 ('<Control-s>', self.save_pdf),
                                 ('<Control-o>', self.open_saved_pdf),
                                 ('<Control-r>', self.reset_data),
                                 ('<Control-q>', self.close),
                                 ('<F1>', self.show_shortcuts)):
            if parent is self or interactive:
                parent.bind(sequence, lambda event, callback=action: self.run_shortcut(callback))
        for child in parent.winfo_children():
            self.install_shortcuts(child)

    @staticmethod
    def run_shortcut(callback):
        callback()
        return 'break'

    def focus_search(self):
        self.search.focus_set()
        self.search.selection_range(0, 'end')

    def focus_results(self, _event=None):
        if self.visible:
            index = self.listbox.curselection()
            index = index[0] if index else 0
            self.listbox.selection_set(index)
            self.listbox.activate(index)
            self.listbox.see(index)
            self.listbox.focus_set()
            self.select_template()
        return 'break'

    def open_result(self, _event=None):
        self.focus_results()
        if self.visible and self.current == self.visible[self.listbox.curselection()[0]]:
            for child in self.form.winfo_children():
                if isinstance(child, (ttk.Entry, ttk.Combobox, ttk.Checkbutton, tk.Text)):
                    child.focus_set()
                    break
        return 'break'

    def show_shortcuts(self):
        messagebox.showinfo('Atajos de teclado',
            'Ctrl+F: buscar una planilla\n'
            'Ctrl+A: seleccionar todo el texto del campo activo\n'
            'Ctrl+← / Ctrl+→: mover el cursor palabra por palabra\n'
            'Ctrl+Shift+← / →: seleccionar por palabras\n'
            '↓ desde el buscador: ir a los resultados\n'
            '↑ / ↓ en la lista: seleccionar una planilla\n'
            'Enter desde el buscador o la lista: ir al formulario\n'
            'Esc en el buscador: limpiar la búsqueda\n'
            'Tab / Shift+Tab: campo siguiente / anterior\n'
            'Enter en un campo de una línea: guardar datos e ir al siguiente\n'
            'Tab / Shift+Tab también guardan los datos\n'
            'Espacio en una casilla: marcar o desmarcar\n'
            'Enter en un campo de varias líneas: nueva línea\n'
            'Ctrl+S: guardar PDF\n'
            'Ctrl+O: abrir el último PDF guardado\n'
            'Ctrl+R: reiniciar todos los datos (incluido el JSON)\n'
            'Ctrl+Q: guardar los datos y cerrar\n'
            'F1: mostrar esta ayuda', parent=self)

    def reveal_field(self, event):
        self.update_idletasks()
        widget = event.widget
        top = widget.winfo_rooty() - self.form.winfo_rooty()
        bottom = top + widget.winfo_height()
        visible_top = self.canvas.canvasy(0)
        visible_bottom = visible_top + self.canvas.winfo_height()
        total = max(1, self.form.winfo_height())
        if top < visible_top:
            self.canvas.yview_moveto(max(0, top - 8) / total)
        elif bottom > visible_bottom:
            self.canvas.yview_moveto((bottom + 8 - self.canvas.winfo_height()) / total)

    def move_focus(self, event, backwards=False):
        if not self.persist_session(report=True):
            return 'break'
        target = event.widget.tk_focusPrev() if backwards else event.widget.tk_focusNext()
        if target:
            target.focus_set()
        return 'break'

    def save_multiline_enter(self, _event):
        # Dejar que Text inserte el salto antes de recoger el contenido.
        self.after_idle(self.persist_session)

    def install_form_navigation(self, parent):
        if getattr(parent, 'medication_search', False):
            return
        if isinstance(parent, (tk.Entry, ttk.Entry, tk.Text, ttk.Checkbutton, ttk.Radiobutton)):
            parent.bind('<Tab>', self.move_focus)
            parent.bind('<Shift-Tab>', lambda event: self.move_focus(event, True))
            parent.bind('<ISO_Left_Tab>', lambda event: self.move_focus(event, True))
            for sequence in ('<Return>', '<KP_Enter>'):
                if getattr(parent, 'handles_return', False):
                    continue
                parent.bind(sequence, self.save_multiline_enter if isinstance(parent, tk.Text)
                            else self.move_focus)
        for child in parent.winfo_children():
            self.install_form_navigation(child)

    def scroll(self, event):
        if event.widget == self.listbox or not str(event.widget).startswith(str(self.form)) and event.widget != self.canvas:
            return
        direction = -1 if event.num == 4 or getattr(event, 'delta', 0) > 0 else 1
        self.canvas.yview_scroll(direction * 3, 'units')

    def filter_templates(self):
        self.visible = [name for name, path in TEMPLATES.items()
                        if path.exists() and normalize(self.query.get()) in normalize(name)]
        self.listbox.delete(0, 'end')
        for name in self.visible:
            self.listbox.insert('end', name)
        if self.current in self.visible:
            self.listbox.selection_set(self.visible.index(self.current))
        self.count.configure(text=f'{len(self.visible)} planillas disponibles' if self.visible else 'No hay coincidencias')

    def collect(self):
        values = {name: control.get('1.0', 'end-1c') if isinstance(control, tk.Text) else control.get()
                  for name, control in self.controls.items()}
        for first_key, (second_key, first_value, second_value) in self.choice_pairs.items():
            choice = values[first_key]
            values[first_key] = choice == first_value
            values[second_key] = choice == second_value
        for field, parts in self.name_parts.items():
            values[field] = ' '.join(part.get().strip() for part in parts.values()).strip()
        return values

    def session_values(self):
        values = self.collect()
        for field, parts in self.name_parts.items():
            values.update({f'{field}:{part}': control.get() for part, control in parts.items()})
        return values

    def remember_patient(self):
        values = self.session_values()
        self.patient.update(self.current, values, self.loaded_values)
        self.drafts[self.current] = values
        self.loaded_values = values.copy()

    def reset_data(self):
        self.patient.clear()
        self.drafts.clear()
        self.saved.clear()
        self.loaded_values.clear()
        for control in self.controls.values():
            if isinstance(control, tk.Text):
                control.delete('1.0', 'end')
            else:
                control.set(False if isinstance(control, tk.BooleanVar) else '')
        for parts in self.name_parts.values():
            for control in parts.values():
                control.set('')
        if self.current in samo.TEMPLATES:
            self.samo_form.reset()
        self.set_professional_controls(apply_professional(self.current, {}, self.professional))
        self.set_professional_controls(apply_form_defaults(self.current, {}))
        if self.current:
            self.loaded_values = self.session_values()
            self.saved[self.current] = self.collect()
        self.canvas.yview_moveto(0)
        if self.persist_session(report=True):
            self.status.configure(text='Datos reiniciados. Podés completar un nuevo paciente.')

    def build_toxo_results(self, row, fields, draft):
        ttk.Label(self.form, text='Exámenes anteriores', style='Section.TLabel').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=(20, 10))
        table = ttk.Frame(self.form)
        table.grid(row=row + 1, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        ttk.Label(table, text='N.º').grid(row=0, column=0, padx=4, pady=6)
        for column, (prefix, title) in enumerate(TOXO_RESULT_COLUMNS, start=1):
            ttk.Label(table, text=title, anchor='center').grid(
                row=0, column=column, sticky='ew', padx=2, pady=6)
            table.columnconfigure(column, weight=1, uniform='results')
        by_name = {field['name']: field for field in fields}
        for number in range(1, 5):
            ttk.Label(table, text=str(number)).grid(row=number, column=0, padx=4)
            for column, (prefix, _) in enumerate(TOXO_RESULT_COLUMNS, start=1):
                key = f'{prefix}Row{number}'
                if by_name[key]['multiline']:
                    entry = tk.Text(table, height=2, width=10, wrap='word', font=(UI_FONT, 11),
                                    relief='flat', highlightthickness=1, highlightbackground='#cbd7e5',
                                    highlightcolor='#168b96', padx=8, pady=6)
                    entry.insert('1.0', draft.get(key, ''))
                    self.controls[key] = entry
                else:
                    control = tk.StringVar(value=draft.get(key, ''))
                    self.controls[key] = control
                    entry = ttk.Entry(table, textvariable=control, width=10)
                entry.grid(row=number, column=column, sticky='nsew', padx=2, pady=2)
                entry.bind('<FocusIn>', self.reveal_field)
        return row + 2

    def build_film_antibiotics(self, row, draft):
        ttk.Label(self.form, text='2. Tratamiento antibiótico', style='Section.TLabel').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=(20, 10))
        table = ttk.Frame(self.form)
        table.grid(row=row + 1, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        for column, title in enumerate(('Tratamiento antibiótico', 'Inicio', 'Suspensión')):
            ttk.Label(table, text=title, anchor='center').grid(
                row=0, column=column, sticky='ew', padx=2, pady=6)
            table.columnconfigure(column, weight=3 if column == 0 else 1)
        for number, keys in enumerate(film_array.ANTIBIOTIC_ROWS, start=1):
            for column, key in enumerate(keys):
                control = tk.StringVar(value=draft.get(key, ''))
                self.controls[key] = control
                entry = ttk.Entry(table, textvariable=control, width=20 if column == 0 else 10)
                entry.grid(row=number, column=column, sticky='ew', padx=2, pady=2)
                entry.bind('<FocusIn>', self.reveal_field)
        return row + 2

    def select_template(self, _event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        name = self.visible[int(selection[0])]
        if name == self.current:
            return
        try:
            fields = read_fields(TEMPLATES[name])
        except Exception as exc:
            messagebox.showerror('No se pudo abrir la planilla', str(exc), parent=self)
            return
        if self.current:
            self.remember_patient()
        self.current = name
        for child in self.form.winfo_children():
            child.destroy()
        self.controls = {}
        self.choice_pairs = {}
        self.name_parts = {}
        draft = self.patient.apply(name, self.drafts.get(name, {}))
        draft = apply_form_defaults(name, draft)
        draft = apply_professional(name, draft, self.professional)
        row = 0
        if name == tarv.TEMPLATE:
            TarvForm(self.form, self, draft).grid(row=0, column=0, columnspan=2, sticky='ew')
            fields = []
        elif name == hiv.TEMPLATE:
            HivForm(self.form, self, draft).grid(row=0, column=0, columnspan=2, sticky='ew')
            fields = []
        elif name in samo.TEMPLATES:
            self.samo_form = SamoForm(self.form, self, draft)
            self.samo_form.grid(row=0, column=0, columnspan=2, sticky='ew')
            fields = []
        sections = PCR_SECTIONS if name == 'PCR de virus' else SECTIONS if name.startswith('Hidatidosis') else {}
        pairs = {key: key[:-3] + '_no' for key in PCR_CHECKBOX_FIELDS
                 if key.endswith('_si') and key[:-3] + '_no' in PCR_CHECKBOX_FIELDS} if name == 'PCR de virus' else {}
        if name == 'Toxoplasmosis — planilla':
            pairs = TOXO_YES_NO_PAIRS
        elif name == 'Film Array':
            pairs = film_array.YES_NO_PAIRS
            sections = film_array.SECTIONS
        elif name == 'GenXpert':
            pairs = dict(genxpert.YES_NO_PAIRS, paciente_genero_f='paciente_genero_m')
            sections = genxpert.SECTIONS
        elif name == 'TBC — cultivo':
            pairs = dict(tbc.YES_NO_PAIRS, paciente_genero_f='paciente_genero_m')
            sections = tbc.SECTIONS
        elif name == cisticercosis.TEMPLATE:
            pairs = dict(cisticercosis.YES_NO_PAIRS, paciente_genero_f='paciente_genero_m')
            sections = cisticercosis.SECTIONS
        elif name == samo.TEMPLATE:
            pairs = {'paciente_genero_f': 'paciente_genero_m'}
        results_built = False
        for field in fields:
            key, kind = field['name'], field['type']
            if key in pairs.values() or (name == 'PCR de virus' and key == 'domicilio_manzana'):
                continue
            if name == 'Film Array' and key in film_array.ANTIBIOTIC_FIELDS:
                if not results_built:
                    row = self.build_film_antibiotics(row, draft)
                    results_built = True
                continue
            if name == 'Toxoplasmosis — planilla' and key in TOXO_RESULT_FIELDS:
                if not results_built:
                    row = self.build_toxo_results(row, fields, draft)
                    results_built = True
                continue
            if key in sections:
                ttk.Label(self.form, text=sections[key], style='Section.TLabel').grid(
                    row=row, column=0, columnspan=2, sticky='ew', pady=(20, 10))
                row += 1
            title = ('Domicilio: calle / manzana' if name == 'PCR de virus' and key == 'domicilio_calle'
                     else label(key[:-3] if key in pairs else key))
            if name == 'Toxoplasmosis — planilla' and key in TOXO_QUESTION_LABELS:
                title = TOXO_QUESTION_LABELS[key]
            elif name == 'Film Array':
                title = film_array.LABELS.get(key, label(key))
            elif name == 'GenXpert':
                title = 'Género' if key == 'paciente_genero_f' else genxpert.LABELS.get(key, label(key))
            elif name == 'TBC — cultivo':
                title = tbc.LABELS.get(key, label(key))
            elif name == cisticercosis.TEMPLATE:
                title = 'Sexo' if key == 'paciente_genero_f' else cisticercosis.LABELS.get(key, label(key))
            elif name == samo.TEMPLATE:
                title = samo.LABELS.get(key, label(key))
            ttk.Label(self.form, text=title, wraplength=280).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=6)
            if name == samo.TEMPLATE and key == 'condicion':
                control = tk.StringVar(value=draft.get(key, ''))
                self.controls[key] = control
                widget = ttk.Frame(self.form)
                for column, (text, value) in enumerate((('A', 'A'), ('B', 'B'), ('Sin indicar', ''))):
                    ttk.Radiobutton(widget, text=text, value=value, variable=control,
                                    style='Choice.TRadiobutton').grid(row=0, column=column, padx=(0, 8))
            elif key in pairs or (name == 'PCR de virus' and key in PCR_PRINTED_CHOICES):
                choice = draft.get(key, '')
                is_gender = name in ('GenXpert', 'TBC — cultivo', samo.TEMPLATE, cisticercosis.TEMPLATE) and key == 'paciente_genero_f'
                first_value, second_value = ('Femenino', 'Masculino') if is_gender else ('Sí', 'No')
                if key in pairs:
                    self.choice_pairs[key] = (pairs[key], first_value, second_value)
                    yes, no = checkbox_value(draft.get(key, False)), checkbox_value(draft.get(pairs[key], False))
                    choice = first_value if yes and not no else second_value if no and not yes else ''
                control = tk.StringVar(value=choice)
                self.controls[key] = control
                widget = ttk.Frame(self.form)
                options = ((('Masculino', 'Masculino'), ('Femenino', 'Femenino'), ('No indicar', ''))
                           if is_gender else (('Sí', 'Sí'), ('No', 'No'), ('Sin indicar', '')))
                for column, (text, value) in enumerate(options):
                    button = ttk.Radiobutton(widget, text=text, value=value, variable=control,
                                             style='Choice.TRadiobutton')
                    button.grid(row=0, column=column, sticky='ew', padx=(0, 4))
                    button.bind('<FocusIn>', self.reveal_field)
                    widget.columnconfigure(column, weight=1)
            elif key in FULL_NAME_FIELDS.get(name, set()):
                widget = ttk.Frame(self.form)
                self.name_parts[key] = {}
                for column, (part, title) in enumerate((('surname', 'Apellido(s)'), ('given_names', 'Nombre(s)'))):
                    control = tk.StringVar(value=draft.get(f'{key}:{part}', ''))
                    self.name_parts[key][part] = control
                    ttk.Label(widget, text=title).grid(row=0, column=column, sticky='w')
                    entry = ttk.Entry(widget, textvariable=control, width=16)
                    entry.grid(row=1, column=column, sticky='ew', padx=(0, 4))
                    entry.bind('<FocusIn>', self.reveal_field)
                    widget.columnconfigure(column, weight=1)
            elif kind == fitz.PDF_WIDGET_TYPE_SIGNATURE:
                widget = ttk.Label(self.form, text='Firma PNG según la opción lateral, o manual al imprimir')
            elif kind == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                control = tk.BooleanVar(value=draft.get(key, False))
                widget = ttk.Checkbutton(self.form, variable=control)
                self.controls[key] = control
            elif name == samo.TEMPLATE and key == 'solicitudes':
                widget = LaboratoryPicker(self.form, self, draft.get(key, ''))
                self.controls[key] = widget.value
            elif field['multiline']:
                widget = tk.Text(self.form, height=16 if key == 'resumen_historia_clinica' else 4,
                                 width=25, wrap='word', font=(UI_FONT, 11),
                                 relief='flat', highlightthickness=1, highlightbackground='#cbd7e5',
                                 highlightcolor='#168b96', padx=8, pady=6)
                widget.insert('1.0', draft.get(key, ''))
                self.controls[key] = widget
            else:
                control = tk.StringVar(value=draft.get(key, ''))
                self.controls[key] = control
                widget = (ttk.Combobox(self.form, textvariable=control, values=[''] + list(field['choices']), state='readonly')
                          if field['choices'] else ttk.Entry(self.form, textvariable=control))
            widget.grid(row=row, column=1, sticky='ew', pady=6)
            widget.bind('<FocusIn>', self.reveal_field)
            row += 1
        if name == 'PCR de virus':
            ttk.Label(self.form, text='Internado, UTI, ARM y Fallecido: se tacha en el PDF la opción NO elegida.',
                      wraplength=420).grid(row=row, column=0, columnspan=2, sticky='w', pady=12)
        self.install_shortcuts(self.form)
        self.install_form_navigation(self.form)
        self.loaded_values = self.session_values()
        self.saved.setdefault(name, {key: False if isinstance(value, bool) else '' for key, value in self.collect().items()})
        self.heading.configure(text=name)
        self.update_signature_info()
        self.status.configure(text='Los datos se guardan automáticamente y se recuperan al abrir.')
        self.save_button.configure(state='normal')
        self.canvas.yview_moveto(0)
        self.persist_session()
        self.refresh_preview(TEMPLATES[name])

    def save_pdf(self):
        if self.current is None:
            return
        values = self.collect()
        # Evitar respuestas sí/no contradictorias en las plantillas con estos nombres.
        for key, value in values.items():
            if key.endswith('_si') and value and values.get(key[:-3] + '_no'):
                messagebox.showerror('Revisá las respuestas', f'Marcaste sí y no en: {label(key[:-3])}', parent=self)
                return
        destination = OUTPUT_PDF
        try:
            signature = (decode_signature(self.professional.get('signature_png', ''))
                         if self.include_signature.get() and
                         TEMPLATES[self.current].name in SIGNATURE_AREAS else None)
            generate_pdf(TEMPLATES[self.current], destination, values, signature_png=signature)
        except PermissionError:
            messagebox.showerror('No se pudo guardar',
                'No se puede escribir el PDF. Si está abierto en otro programa, cerralo y volvé a guardar.\n\n'
                f'Destino: {destination}', parent=self)
            return
        except Exception as exc:
            messagebox.showerror('No se pudo guardar', str(exc), parent=self)
            return
        self.saved[self.current] = values.copy()
        self.remember_patient()
        self.persist_session(report=True)
        self.status.configure(text=f'PDF guardado: {Path(destination).name}')
        self.refresh_preview()

    def open_saved_pdf(self):
        if not OUTPUT_PDF.is_file():
            messagebox.showinfo('Todavía no hay un PDF guardado',
                                'Pulsá Guardar PDF para generarlo primero.', parent=self)
            return
        self.open_pdf(OUTPUT_PDF)

    def open_pdf(self, path):
        """Abre el archivo actualizado sin bloquear la interfaz del formulario."""
        path = str(Path(path).resolve())

        def report_error(detail):
            messagebox.showwarning('PDF guardado; no se pudo abrir el visor',
                f'El PDF se guardó correctamente en:\n{path}\n\n{detail}\n'
                'Podés abrirlo manualmente.', parent=self)

        try:
            if sys.platform == 'win32':
                os.startfile(path)
                return
            command = 'open' if sys.platform == 'darwin' else 'xdg-open'
            process = subprocess.Popen([command, path], stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
        except OSError as exc:
            report_error(str(exc))
            return

        def check_open():
            code = process.poll()
            if code is None:
                self.after(500, check_open)
            elif code != 0:
                report_error('El visor predeterminado no pudo abrir el archivo.')

        self.after(500, check_open)

    def close(self):
        if self.persist_session(report=True):
            self.destroy()


if __name__ == '__main__':
    App().mainloop()
