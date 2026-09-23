"""Catálogo y posiciones del recetario TARV original (puntos PDF)."""
import unicodedata
import calendar
from datetime import datetime

TEMPLATE = 'TARV — recetario'

# No inferir dosis: la presentación impresa no es una indicación mensual.
# Clave estable, rótulo, fila vertical y presentación del documento.
MEDICATIONS = (
    ('lamivudina_300', 'Lamivudina 300 mg', 105.4, '30'),
    ('abacavir_lamivudina', 'Abacavir + lamivudina 600/300 mg', 122.56, '30'),
    ('tdf_emtricitabina', 'Tenofovir DF + emtricitabina 300/200 mg', 139.72, '30'),
    ('taf_emtricitabina', 'Tenofovir alafenamida / emtricitabina 25/200 mg', 156.88, '30'),
    ('tdf_lamivudina', 'Tenofovir DF + lamivudina 300/300 mg', 174.04, '30'),
    ('etravirina', 'Etravirina 200 mg', 208.36, '60'),
    ('darunavir_ritonavir_800', 'Darunavir + ritonavir 800/100 mg', 242.68, '30'),
    ('darunavir_ritonavir_600', 'Darunavir + ritonavir 600/100 mg', 259.84, '60'),
    ('dolutegravir', 'Dolutegravir 50 mg', 294.16, '30'),
    ('raltegravir', 'Raltegravir 400 mg', 311.32, '60'),
    ('tdf_lamivudina_dolutegravir', 'Tenofovir DF / lamivudina / dolutegravir 300/300/50 mg', 362.8, '30'),
    ('lamivudina_dolutegravir', 'Lamivudina + dolutegravir 300/50 mg', 379.96, '60'),
    ('abacavir_lamivudina_dolutegravir', 'Abacavir / lamivudina + dolutegravir 600/300/50 mg', 397.12, '60'),
    ('taf_emtricitabina_dolutegravir', 'Tenofovir alafenamida / emtricitabina / dolutegravir 25/200/50 mg', 414.28, '30'),
)


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold())
                   if not unicodedata.combining(c))


def search_medications(query):
    words = normalize(query).split()
    return [item for item in MEDICATIONS
            if all(word in normalize(item[1]) for word in words)]


FIELDS = []


def field(name, title, rect, kind='text'):
    FIELDS.append(dict(name=name, label=title, rect=rect, type=kind))


field('paciente_codigo', 'Código del paciente', (76, 15, 160, 28))
field('paciente_dni', 'DNI', (59, 31, 163, 44))
field('fecha_receta', 'Fecha', (73, 46, 151, 59))
field('tratamiento_inicio', 'Inicio', (376, 16, 387, 27), 'checkbox')
field('tratamiento_cambio', 'Cambio de tratamiento', (376, 32, 387, 43), 'checkbox')
field('tratamiento_continuacion', 'Continuación', (376, 47, 387, 58), 'checkbox')
field('excepcion_puco', 'Excepción al PUCO', (376, 63, 387, 74), 'checkbox')
for key, title, y, presentation in MEDICATIONS:
    field('med_' + key, title, (376, y + 3, 387, y + 14), 'checkbox')
for row in range(1, 5):
    y = 458 + (row - 1) * 18.5
    field(f'otro_{row}_medicamento', f'Otro medicamento {row}', (41, y, 258, y + 15))
    field(f'otro_{row}_dosis', 'Dosis diaria', (262, y, 350, y + 15))
    field(f'otro_{row}_dias', 'Días de tratamiento', (355, y, 409, y + 15))
SIGNATURE_RECT = (42, 533, 408, 581)
field('firma_medico', 'Firma y sello del médico', SIGNATURE_RECT, 'signature')

LABELS = {spec['name']: spec['label'] for spec in FIELDS}
MEDICATION_FIELDS = {'med_' + item[0] for item in MEDICATIONS}
OTHER_FIELDS = {f'otro_{row}_{part}' for row in range(1, 5)
                for part in ('medicamento', 'dosis', 'dias')}
COPY_OFFSET = 392.04
SECOND_PREFIX = 'segunda_'
REASONS = ('tratamiento_inicio', 'tratamiento_cambio', 'tratamiento_continuacion', 'excepcion_puco')
MONTH_OPTIONS = ('2', '4', '6', '8', '10', '12')
PATIENT_INPUTS = ('paciente_nombres', 'paciente_apellido', 'paciente_fecha_nacimiento',
                  'paciente_genero_f', 'paciente_genero_m')


def patient_code(names, surname, birth_date, sex):
    if not any((names.strip(), surname.strip(), birth_date.strip(), sex)):
        return ''
    first_name = normalize(names).strip().split()
    first_name = first_name[0] if first_name else ''
    surname = normalize(surname).strip()
    if sex not in ('M', 'F') or len(first_name) < 2 or len(surname) < 2 or not birth_date.strip():
        raise ValueError('Completá sexo, nombre, apellido y fecha de nacimiento para generar el código.')
    try:
        birthday = datetime.strptime(birth_date.strip(), '%d/%m/%Y')
    except ValueError:
        raise ValueError('Ingresá una fecha de nacimiento válida (DD/MM/AAAA).') from None
    return sex + first_name[:2].upper() + surname[:2].upper() + birthday.strftime('%d%m%Y')


def next_month(value, offset=1):
    if not str(value).strip():
        return ''
    try:
        original = datetime.strptime(str(value).strip(), '%d/%m/%Y').date()
        year, month = divmod(original.year * 12 + original.month - 1 + offset, 12)
        month += 1
        day = min(original.day, calendar.monthrange(year, month)[1])
        return original.replace(year=year, month=month, day=day).strftime('%d/%m/%Y')
    except (ValueError, OverflowError):
        raise ValueError('Ingresá una fecha válida en la primera receta (DD/MM/AAAA).') from None


def same_prescriptions(values):
    value = values.get('son_iguales', True)
    return value if isinstance(value, bool) else str(value).lower() in ('true', '1', 'si', 'sí')


def pdf_values(values):
    """Deriva la segunda receta sin sobrescribir su borrador independiente."""
    result = dict(values)
    if any(key in result for key in PATIENT_INPUTS):
        female, male = bool(result.get('paciente_genero_f')), bool(result.get('paciente_genero_m'))
        sex = 'F' if female and not male else 'M' if male and not female else ''
        result['paciente_codigo'] = patient_code(result.get('paciente_nombres', ''),
                                                 result.get('paciente_apellido', ''),
                                                 result.get('paciente_fecha_nacimiento', ''), sex)
        for key in PATIENT_INPUTS:
            result.pop(key, None)
    same = same_prescriptions(result)
    result.pop('son_iguales', None)
    result.pop('meses', None)
    for prefix in ('', SECOND_PREFIX):
        choice = result.pop(prefix + 'motivo', None)
        if choice is not None:
            if choice and choice not in REASONS:
                raise ValueError('Elegí un motivo válido para la receta.')
            for key in REASONS:
                result[prefix + key] = key == choice
        elif sum(bool(result.get(prefix + key)) for key in REASONS) > 1:
            raise ValueError('Elegí un solo motivo para cada receta.')
    for spec in FIELDS:
        key = spec['name']
        if key == 'firma_medico':
            continue
        if same or key in ('paciente_codigo', 'paciente_dni'):
            value = result.get(key, False if spec['type'] == 'checkbox' else '')
            result[SECOND_PREFIX + key] = next_month(value) if same and key == 'fecha_receta' else value
    if same:
        continue_treatment(result, SECOND_PREFIX)
    return result


def continue_treatment(values, prefix=''):
    if values.get(prefix + 'tratamiento_inicio') or values.get(prefix + 'tratamiento_cambio'):
        values[prefix + 'tratamiento_inicio'] = False
        values[prefix + 'tratamiento_cambio'] = False
        values[prefix + 'tratamiento_continuacion'] = True


def prescription_pages(values):
    months = str(values.get('meses') or '2')
    if months not in MONTH_OPTIONS:
        raise ValueError('Elegí 2, 4, 6, 8, 10 o 12 meses.')
    first = pdf_values(values)
    pages = [first]
    for page_number in range(1, int(months) // 2):
        page = dict(first)
        for prefix, extra in (('', 0), (SECOND_PREFIX, 1)):
            # Calcular desde la fecha original evita arrastrar el recorte de febrero.
            if same_prescriptions(values):
                page[prefix + 'fecha_receta'] = next_month(first.get('fecha_receta', ''), page_number * 2 + extra)
            else:
                page[prefix + 'fecha_receta'] = next_month(first.get(prefix + 'fecha_receta', ''), page_number * 2)
            continue_treatment(page, prefix)
        pages.append(page)
    return pages
