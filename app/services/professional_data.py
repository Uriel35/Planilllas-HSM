"""Perfiles locales y equivalencias explícitas de datos profesionales."""
import json
from pathlib import Path
from app.services.signature_data import decode_signature
import app.forms.samo_fields as samo

PROFILE_FIELDS = {
    'surname': 'Apellido(s) *', 'given_names': 'Nombre(s) *',
    'registration': 'Matrícula', 'specialty': 'Especialidad',
    'phone': 'Celular profesional', 'email': 'Email profesional',
    'institution': 'Establecimiento', 'province': 'Provincia del establecimiento',
    'department': 'Departamento del establecimiento',
    'city': 'Localidad del establecimiento',
    'institution_phone': 'Teléfono del establecimiento',
    'institution_email': 'Email del establecimiento',
}
PROFESSIONAL_FIELDS = {
    'Cisticercosis — envío de muestras': {
        'profesional_apellido_nombre': 'full_name', 'institucion_solicitante': 'institution',
        'profesional_telefono': 'phone', 'profesional_email': 'email',
    },
    'SAMO — órdenes de laboratorio': {'establecimiento': 'institution'},
    'TBC — cultivo': {'solicitante_estudio': 'full_name'},
    'GenXpert': {
        'institucion': 'institution', 'profesional': 'full_name',
        'solicitante_estudio': 'full_name', 'institucion_telefono': 'institution_phone',
        'institucion_correo': 'institution_email',
    },
    'Hidatidosis — ficha epidemiológica': {
        'profesional_apellido_nombre': 'full_name',
        'establecimiento_notificante': 'institution',
        'declarante_provincia': 'province', 'declarante_departamento': 'department',
        'declarante_localidad': 'city', 'declarante_telefono': 'phone',
        'declarante_email': 'email',
    },
    'Toxoplasmosis — planilla': {
        'Apellido Medico': 'surname', 'Nombre Medico': 'given_names',
        'Celular Medico': 'phone', 'E  MAIL CELULAR': 'email',
        'ESTABLECIMIENTO': 'institution',
    },
    'PCR de virus': {
        'notificador_apellido_nombre': 'full_name',
        'establecimiento_notificador': 'institution',
        'institucion_provincia': 'province', 'institucion_departamento': 'department',
        'institucion_telefono': 'institution_phone', 'institucion_correo': 'institution_email',
    },
}


PROFESSIONAL_FIELDS[samo.PPD_TEMPLATE] = PROFESSIONAL_FIELDS[samo.TEMPLATE].copy()


def validate_profile(profile):
    if not isinstance(profile, dict) or any(not isinstance(v, str) for v in profile.values()):
        raise ValueError('El perfil profesional contiene datos inválidos.')
    result = {key: profile.get(key, '').strip() for key in PROFILE_FIELDS}
    result['signature_png'] = profile.get('signature_png', '')
    decode_signature(result['signature_png'])
    if not result['surname'] or not result['given_names']:
        raise ValueError('Completá apellido y nombre del profesional.')
    return result


def load_profiles(path):
    path = Path(path)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('profiles'), dict):
        raise ValueError('El archivo de profesionales no tiene un formato compatible.')
    return {key: validate_profile(value) for key, value in data['profiles'].items()}


def apply_professional(template, draft, profile, replace=False):
    result = dict(draft)
    values = dict(profile, full_name=f"{profile['surname']} {profile['given_names']}")
    for field, source in PROFESSIONAL_FIELDS.get(template, {}).items():
        if replace or field not in result:
            result[field] = values.get(source, '')
    if template in samo.TEMPLATES:
        from app.forms.samo_fields import order_count, order_prefix
        count_values = draft if 'cantidad_samo' in draft else {'cantidad_samo': '2' if template == samo.PPD_TEMPLATE else '1'}
        for index in range(1, order_count(count_values)):
            key = order_prefix(index) + 'establecimiento'
            if replace or key not in result:
                result[key] = values.get('institution', '')
    return result
