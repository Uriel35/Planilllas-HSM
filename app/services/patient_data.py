"""Equivalencias explícitas de datos del paciente entre plantillas."""
import app.forms.samo_fields as samo
PATIENT_FIELDS = {
    'Cisticercosis — envío de muestras': {
        'paciente_dni': 'dni', 'paciente_fecha_nacimiento': 'birth_date',
        'paciente_edad': 'age', 'paciente_genero_f': 'female', 'paciente_genero_m': 'male',
        'residencia_provincia': 'province', 'residencia_localidad': 'city',
    },
    'SAMO — órdenes de laboratorio': {
        'paciente_dni': 'dni', 'paciente_edad': 'age', 'paciente_domicilio': 'address',
        'paciente_genero_f': 'female', 'paciente_genero_m': 'male',
    },
    'HIV — carga viral y CD4/CD8': {
        'paciente_dni': 'dni', 'paciente_nombres': 'given_names',
        'paciente_apellido': 'surname', 'paciente_fecha_nacimiento': 'birth_date',
        'paciente_genero_f': 'female', 'paciente_genero_m': 'male',
    },
    'TARV — recetario': {
        'paciente_dni': 'dni', 'paciente_nombres': 'given_names',
        'paciente_apellido': 'surname', 'paciente_fecha_nacimiento': 'birth_date',
        'paciente_genero_f': 'female', 'paciente_genero_m': 'male',
    },
    'TBC — cultivo': {
        'paciente_fecha_nacimiento': 'birth_date', 'paciente_edad': 'age',
        'paciente_domicilio': 'address', 'paciente_localidad': 'city',
        'paciente_departamento': 'department', 'paciente_provincia': 'province',
        'paciente_telefono': 'phone', 'paciente_genero_f': 'female', 'paciente_genero_m': 'male',
    },
    'GenXpert': {
        'paciente_fecha_nacimiento': 'birth_date', 'paciente_edad': 'age',
        'paciente_domicilio': 'address', 'paciente_localidad': 'city',
        'paciente_departamento': 'department', 'paciente_provincia': 'province',
        'paciente_telefono': 'phone', 'paciente_genero_f': 'female', 'paciente_genero_m': 'male',
    },
    'Hidatidosis — ficha epidemiológica': {
        'paciente_dni': 'dni', 'paciente_fecha_nacimiento': 'birth_date',
        'paciente_edad': 'age', 'paciente_domicilio_actual': 'address',
        'paciente_localidad': 'city', 'paciente_departamento': 'department',
        'paciente_provincia': 'province',
        'paciente_sexo_m': 'male', 'paciente_sexo_f': 'female',
    },
    'Toxoplasmosis — planilla': {
        'Apellido': 'surname', 'Nombre': 'given_names', 'DNI': 'dni',
        'Fecha de Nacimiento': 'birth_date', 'Edad': 'age',
        'Localidad': 'city', 'Pcia': 'province', 'TelCelular': 'phone',
        'Dirección de email': 'email',
    },
    'PCR de virus': {
        'fecha_nacimiento': 'birth_date', 'paciente_telefono': 'phone',
        'residencia_provincia': 'province', 'residencia_departamento': 'department',
        'residencia_localidad': 'city',
    },
    'Orden de internación': {
        f'{part}_{field}': shared
        for part in ('superior',)
        for field, shared in {
            'edad': 'age', 'fecha_nacimiento': 'birth_date',
            'domicilio': 'address', 'localidad': 'city',
            'sexo_m': 'male', 'sexo_f': 'female',
        }.items()
    },
}
FULL_NAME_FIELDS = {
    'Cisticercosis — envío de muestras': {'paciente_apellido_nombre'},
    'SAMO — órdenes de laboratorio': {'paciente_apellido_nombre'},
    'TBC — cultivo': {'paciente_apellido_nombre'},
    'GenXpert': {'paciente_apellido_nombre'},
    'Hidatidosis — ficha epidemiológica': {'paciente_apellido_nombres'},
    'PCR de virus': {'paciente_apellido_nombre'},
    'Orden de internación': {'superior_apellido_y_nombre'},
}


PATIENT_FIELDS[samo.PPD_TEMPLATE] = PATIENT_FIELDS[samo.TEMPLATE].copy()
FULL_NAME_FIELDS[samo.PPD_TEMPLATE] = FULL_NAME_FIELDS[samo.TEMPLATE].copy()


class PatientSession:
    def __init__(self):
        self.values = {}

    def update(self, template, current, original):
        # Solo propagar cambios reales, incluso vacíos y False. Así un borrador
        # anterior no vuelve a introducir información que ya fue corregida.
        for field, shared in PATIENT_FIELDS.get(template, {}).items():
            if field in current and current[field] != original.get(field):
                self.values[shared] = current[field]
        for field in FULL_NAME_FIELDS.get(template, set()):
            for part in ('surname', 'given_names'):
                key = f'{field}:{part}'
                if key in current and current[key] != original.get(key):
                    self.values[part] = current[key]

    def apply(self, template, draft):
        result = dict(draft)
        for field, shared in PATIENT_FIELDS.get(template, {}).items():
            if shared in self.values:
                result[field] = self.values[shared]
        for field in FULL_NAME_FIELDS.get(template, set()):
            for part in ('surname', 'given_names'):
                result[f'{field}:{part}'] = self.values.get(part, '')
        return result

    def clear(self):
        self.values.clear()
