"""Campos de la solicitud VIH, medidos sobre una vista a escala 1,5."""
from app.forms.tarv_fields import PATIENT_INPUTS, patient_code

TEMPLATE = 'HIV — carga viral y CD4/CD8'
SERVICE_EMAILS = {
    'finalidad_diagnostico': 'resultadoshivsanmartin@gmail.com',
    'finalidad_seguimiento': 'seguimientohivhsm@gmail.com',
}


def apply_defaults(values):
    result = dict(values)
    for key, value in {'region_sanitaria': 'XI',
                       'establecimiento': 'Hospital San Martin de La Plata'}.items():
        if not str(result.get(key) or '').strip():
            result[key] = value
    result['servicio_correo'] = SERVICE_EMAILS.get(result.get('finalidad', ''), '')
    return result


FIELDS = []


def field(name, title, rect, kind='text', multiline=False):
    FIELDS.append(dict(name=name, label=title, rect=[v / 1.5 for v in rect],
                       type=kind, multiline=multiline))


field('region_sanitaria', 'Región sanitaria', (244, 219, 595, 239))
field('establecimiento', 'Establecimiento', (244, 239, 595, 259))
field('servicio_correo', 'Mail del servicio solicitante', (320, 259, 595, 279))
field('paciente_dni', 'Documento', (122, 365, 399, 391))
field('codigo_sexo', 'Código: sexo', (122, 439, 167, 465))
field('codigo_nombre', 'Código: nombre', (175, 439, 283, 465))
field('codigo_apellido', 'Código: apellido', (291, 439, 402, 465))
field('codigo_nacimiento', 'Código: nacimiento', (410, 439, 610, 465))
field('finalidad_diagnostico', 'Diagnóstico', (94, 590, 108, 604), 'checkbox')
field('finalidad_seguimiento', 'Seguimiento', (94, 613, 108, 627), 'checkbox')
field('gestante_si', 'Gestante: sí', (94, 713, 108, 727), 'checkbox')
field('gestante_no', 'Gestante: no', (94, 736, 108, 750), 'checkbox')
field('semanas_gestacion', 'Semanas de gestación', (342, 707, 488, 728))
field('carga_viral', 'Carga viral', (94, 817, 108, 831), 'checkbox')
field('cd4_cd8', 'Linfocitos T CD4/CD8', (94, 839, 108, 853), 'checkbox')
field('iua_carga_viral', 'IUA carga viral', (330, 813, 809, 833))
field('iua_cd4', 'IUA CD4', (330, 835, 809, 855))
field('numero_muestra', 'N.º de muestra (laboratorio)', (186, 932, 337, 953))
field('fecha_extraccion', 'Fecha de extracción (laboratorio)', (618, 932, 810, 953))
field('observaciones', 'Observaciones', (66, 991, 808, 1032), multiline=True)
field('fecha_solicitud', 'Fecha de solicitud', (192, 1081, 310, 1104))
field('firma_solicitante', 'Firma del profesional solicitante', (553, 1044, 798, 1105), 'signature')

LABELS = {spec['name']: spec['label'] for spec in FIELDS}
CODE_FIELDS = ('codigo_sexo', 'codigo_nombre', 'codigo_apellido', 'codigo_nacimiento')
IUA_FIELDS = {'carga_viral': 'iua_carga_viral', 'cd4_cd8': 'iua_cd4'}
GROUPS = {
    'finalidad': ('Determinación para', (('Diagnóstico', 'finalidad_diagnostico'),
                                       ('Seguimiento', 'finalidad_seguimiento'), ('Sin indicar', ''))),
    'gestante': ('Gestante', (('Sí', 'gestante_si'), ('No', 'gestante_no'), ('Sin indicar', ''))),
}


def pdf_values(values):
    result = apply_defaults(values)
    for key in IUA_FIELDS.values():
        value = str(result.get(key, '')).strip()
        if result.get('finalidad') == 'finalidad_seguimiento' and value:
            if not value.isascii() or not value.isdigit():
                raise ValueError(f'Ingresá solo números en {LABELS[key]}.')
            result[key] = f'{LABELS[key]}: {value}'
        else:
            result[key] = ''
    female, male = bool(result.get('paciente_genero_f')), bool(result.get('paciente_genero_m'))
    code = patient_code(result.get('paciente_nombres', ''), result.get('paciente_apellido', ''),
                        result.get('paciente_fecha_nacimiento', ''),
                        'F' if female and not male else 'M' if male and not female else '')
    for key, value in zip(CODE_FIELDS, (code[:1], code[1:3], code[3:5], code[5:])):
        result[key] = value
    for key in (*PATIENT_INPUTS, 'paciente_codigo'):
        result.pop(key, None)
    for group, (_, options) in GROUPS.items():
        choice = result.pop(group, '')
        if choice not in {key for _, key in options}:
            raise ValueError('Elegí una opción válida para ' + group + '.')
        for _, key in options:
            if key:
                result[key] = key == choice
    return result
