"""Campos de una orden SAMO y paquetes de estudios."""
import unicodedata

TEMPLATE = 'SAMO — órdenes de laboratorio'
PPD_TEMPLATE = 'PPD y Rx de torax'
TEMPLATES = (TEMPLATE, PPD_TEMPLATE)


def apply_defaults(template, values):
    from datetime import date

    result = dict(values)
    if template == PPD_TEMPLATE:
        result.setdefault('cantidad_samo', '2')
        result.setdefault('solicitudes', 'PPD')
        if order_count(result) >= 2:
            result.setdefault('samo_2:solicitudes', 'Rx de torax de frente y perfil')
    for index in range(order_count(result)):
        key = order_prefix(index) + 'fecha_solicitud'
        if not result.get(key):
            result[key] = date.today().strftime('%d/%m/%Y')
    return result

LABELS = {
    'establecimiento': 'Establecimiento',
    'paciente_apellido_nombre': 'Paciente',
    'paciente_domicilio': 'Domicilio',
    'fecha_solicitud': 'Fecha',
    'paciente_genero_f': 'Sexo',
    'paciente_genero_m': 'Sexo masculino',
    'paciente_edad': 'Edad',
    'paciente_dni': 'N.º de documento',
    'consultorio_externo': 'C.E.',
    'sala': 'Sala',
    'cama': 'Cama',
    'condicion': 'Condición',
    'obra_social': 'Obra social o mutual',
    'numero_afiliado': 'N.º de afiliado',
    'diagnostico': 'Diagnóstico clínico',
    'solicitudes': 'Estudios solicitados',
}
# Cada copia tiene pequeñas diferencias de alineación en el escaneo.
RECTS = {
    'establecimiento': ((66, 65, 494, 79), (67, 469, 496, 483)),
    'paciente_apellido_nombre': ((66, 91, 297, 105), (67, 493, 298, 507)),
    'paciente_domicilio': ((302, 91, 486, 105), (303, 493, 487, 507)),
    'fecha_solicitud': ((492, 91, 558, 106), (494, 493, 560, 508)),
    'paciente_genero_f': ((85, 126, 95, 134), (87, 531, 97, 539)),
    'paciente_genero_m': ((85, 117, 95, 125), (87, 522, 97, 530)),
    'paciente_edad': ((96, 117, 129.3, 135), (98.5, 522, 131.7, 541)),
    'paciente_dni': ((129.3, 117, 220, 135), (131.7, 522, 222.7, 541)),
    'consultorio_externo': ((315, 118, 363, 135), (318, 523, 366, 540)),
    'sala': ((367, 118, 415, 135), (369, 523, 418, 540)),
    'cama': ((418, 118, 467, 135), (421, 523, 469, 540)),
    'condicion': ((67, 147, 169, 162), (69, 552, 171, 567)),
    'obra_social': ((174, 147, 342, 162), (177, 551, 344, 566)),
    'numero_afiliado': ((424.3, 148, 559.7, 163), (426.7, 553, 562, 569)),
    'diagnostico': ((67, 173, 510, 187), (68, 576, 512, 590)),
    'solicitudes': ((158, 218, 410, 286), (161, 621, 412, 690)),
}
CHECKBOX_FIELDS = {'paciente_genero_f', 'paciente_genero_m'}
PATIENT_FIELDS = {
    'paciente_apellido_nombre', 'paciente_domicilio', 'paciente_genero_f',
    'paciente_genero_m', 'paciente_edad', 'paciente_dni', 'obra_social', 'numero_afiliado',
    'condicion', 'diagnostico',
}
# Una orden por hoja; conservar las coordenadas de la orden superior.
RECTS = {name: (rects[0],) for name, rects in RECTS.items()}
NUMERIC_CELLS = {'paciente_edad': 2, 'paciente_dni': 8, 'numero_afiliado': 12}


def order_prefix(index):
    return '' if index == 0 else f'samo_{index + 1}:'


def order_count(values):
    try:
        count = int(values.get('cantidad_samo') or '1')
    except (TypeError, ValueError):
        raise ValueError('La cantidad de órdenes SAMO debe ser un número entero.') from None
    if count < 1:
        raise ValueError('Debe haber al menos una orden SAMO.')
    return count


def prescription_pages(values):
    count = order_count(values)
    allowed = {'cantidad_samo'} | {order_prefix(i) + key for i in range(count) for key in RECTS}
    if values.keys() - allowed:
        raise ValueError('Hay datos que no pertenecen a las órdenes SAMO.')
    pages = []
    for index in range(count):
        prefix = order_prefix(index)
        page = {key: values.get(key if key in PATIENT_FIELDS else prefix + key,
                                False if key in CHECKBOX_FIELDS else '') for key in RECTS}
        if page['paciente_genero_f'] and page['paciente_genero_m']:
            raise ValueError(f'SAMO {index + 1}: elegí un solo sexo.')
        page['solicitudes'] = format_studies(page['solicitudes'])
        pages.append(page)
    return pages


def numeric_value(name, value):
    text = str(value).strip()
    # Aceptar DNI pegados con separadores y conservar los ceros iniciales.
    if name == 'paciente_dni':
        text = text.replace('.', '').replace(' ', '')
    if text and (not text.isascii() or not text.isdecimal()):
        raise ValueError(f'{LABELS[name]}: ingresá solamente números.')
    if len(text) > NUMERIC_CELLS[name]:
        raise ValueError(f'{LABELS[name]}: hay espacio para {NUMERIC_CELLS[name]} dígitos.')
    return text


def draw_numeric_cells(page, widget, value):
    """Centra cada dígito en su casillero sin tapar la grilla del original."""
    import pymupdf as fitz

    name, rect = widget.field_name, fitz.Rect(widget.rect)
    text = numeric_value(name, value)
    page.delete_widget(widget)
    count = NUMERIC_CELLS[name]
    width = rect.width / count
    offset = count - len(text) if name == 'paciente_edad' else 0
    size = 10
    baseline = (rect.y0 + rect.y1) / 2 + size * 0.35
    for index, digit in enumerate(text, start=offset):
        x = rect.x0 + (index + 0.5) * width
        x -= fitz.get_text_length(digit, fontname='helv', fontsize=size) / 2
        page.insert_text((x, baseline), digit, fontname='helv', fontsize=size)

STUDIES = (
    'Hemograma', 'Hepatograma', 'Urea', 'Creatinina', 'Glucemia',
    'Ionograma', 'Calcio', 'Magnesio', 'Fósforo', 'Coagulograma',
    'Eritrosedimentación', 'Proteína C reactiva', 'Orina completa',
    'Urocultivo', 'Colesterol total', 'HDL colesterol', 'LDL colesterol',
    'Triglicéridos', 'Hemoglobina glicosilada', 'TSH', 'T4 libre',
    'Ferritina', 'Ferremia', 'Transferrina', 'Vitamina B12', 'Ácido fólico',
    'Ácido úrico', 'LDH', 'CPK', 'Proteinuria de 24 horas',
    'Orina de 24 h (urea y creatinina urinaria, clearence de creatinina, proteinuria y albuminuria de 24h)',
)
ETS = ('Serología HIV', 'VDRL', 'HBV (AgS, Ac-S, Ac-core)', 'HCV')
PACKAGES = {
    'Laboratorio general': ('Hemograma', 'Hepatograma', 'Urea', 'Creatinina'),
    'Serología ETS': ETS,
    'Serología control de HIV': (
        'VDRL', 'HBV (AgS, Ac-S, Ac-core)', 'HCV',
        'HSV-1', 'HSV-2', 'Chagas', 'Toxoplasmosis', 'CMV', 'VZV', 'EBV',
    ),
}
STUDIES = tuple(dict.fromkeys(STUDIES + tuple(study for studies in PACKAGES.values() for study in studies)))


def study_key(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.strip().casefold())
                   if not unicodedata.combining(c))


SEROLOGY_NAMES = {
    study_key(name.removeprefix('Serología ')): name.removeprefix('Serología ')
    for name in (*ETS, *PACKAGES['Serología control de HIV'])
}


def serology_name(study):
    """Reconoce también los nombres de borradores con el prefijo repetido."""
    key = study_key(study)
    if key.startswith('serologia '):
        return study.strip().split(' ', 1)[1].strip()
    return SEROLOGY_NAMES.get(key)


def format_studies(value):
    """El encabezado pertenece al grupo, nunca a su primer estudio."""
    studies = [item.strip() for item in value.replace('\n', ';').split(';') if item.strip()]
    serologies = [serology_name(study) for study in studies if serology_name(study)]
    other = [study for study in studies if not serology_name(study)]
    return '\n'.join(other + (['Serología: ' + ', '.join(serologies)] if serologies else []))


def draw_studies(page, widget, value):
    """Distribuye estudios entre columnas sin separar el bloque de serologías."""
    import pymupdf as fitz

    rect = fitz.Rect(widget.rect)
    middle = (rect.x0 + rect.x1) / 2
    columns = (fitz.Rect(rect.x0 + 2, rect.y0 + 2, middle - 5, rect.y1 - 2),
               fitz.Rect(middle + 5, rect.y0 + 2, rect.x1 - 2, rect.y1 - 2))
    items = [line for line in value.splitlines() if line.strip()]
    if not items:
        page.delete_widget(widget)
        return
    error = ('Los estudios solicitados no caben en las dos columnas. '
             'Quitá algunos o repartilos en otro SAMO.')
    if len(items) > 2 * int(columns[0].height / 6):
        raise ValueError(error)
    # Probar sin escribir en la página. Reducir la letra solo si ninguna
    # distribución cabe; conservar cada estudio y la serología completos.
    for step in range(31):
        size = 9 - step / 10
        candidates = []
        splits = range(1, len(items)) if len(items) > 1 else (1,)
        for split in splits:
            shape = page.new_shape()
            remaining = []
            for column, group in zip(columns, (items[:split], items[split:])):
                remaining.append(shape.insert_textbox(
                    column, '\n'.join(group), fontname='helv', fontsize=size))
            if min(remaining) >= 0:
                candidates.append((abs(remaining[0] - remaining[1]), shape))
        if candidates:
            _, shape = min(candidates, key=lambda candidate: candidate[0])
            page.delete_widget(widget)
            shape.commit()
            return
    raise ValueError(error)
