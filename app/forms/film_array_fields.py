"""Correspondencias verificadas contra los rótulos y posiciones del PDF de Film Array.

Las claves originales se conservan para mantener los borradores compatibles.
El orden de este diccionario define el recorrido del formulario.
"""

LABELS = {
    'text_37yucz': 'Fecha',
    'text_1obcu': 'Apellido y nombre',
    'text_2gmhq': 'DNI',
    'text_3rfbn': 'Fecha de nacimiento',
    'text_4sctv': 'Edad',
    'text_5ebzr': 'Sala / cama',
    'text_6pnla': 'Fecha de ingreso',
    'text_7buei': 'Diagnóstico de ingreso',
    'text_8ebez': 'Tratamiento antibiótico 1',
    'text_9wiya': 'Inicio 1',
    'text_10ilqz': 'Suspensión 1',
    'text_11whjh': 'Tratamiento antibiótico 2',
    'text_12twns': 'Inicio 2',
    'text_13xgkk': 'Suspensión 2',
    'text_14niru': 'Tratamiento antibiótico 3',
    'text_15gajc': 'Inicio 3',
    'text_16btag': 'Suspensión 3',
    'text_18l': 'Tratamiento inmunosupresor',
    'text_17lbrl': 'Tratamiento inmunosupresor: no',
    'text_19airg': 'Cuáles',
    'text_20ieby': 'Panel BCID 2',
    'text_23xglf': 'Panel meningitis / encefalitis',
    'text_21jjgy': 'Panel neumonía',
    'text_24ynfg': 'Panel respiratorio',
    'text_22blbk': 'Panel gastrointestinal',
    'text_25ubku': 'Hemocultivo',
    'text_28hspr': 'Mini BAL',
    'text_31ljsv': 'LCR',
    'text_26rnbl': 'Retrocultivo',
    'text_29hmk': 'Esputo',
    'text_32buzw': 'Hisopado nasofaríngeo',
    'text_27vigi': 'BAL',
    'text_30uqjh': 'Materia fecal',
    'text_33eace': 'Otros',
    'text_34yohr': 'Fecha de toma de muestra',
    'text_35cibq': 'Hora de toma de muestra',
    'textarea_36iqsg': 'Criterio de solicitud',
    'firma_profesional_solicitante': 'Profesional solicitante (firma y sello)',
}

YES_NO_PAIRS = {'text_18l': 'text_17lbrl'}
CHECKBOX_FIELDS = {
    'text_17lbrl', 'text_18l',
    'text_20ieby', 'text_23xglf', 'text_21jjgy', 'text_24ynfg', 'text_22blbk',
    'text_25ubku', 'text_28hspr', 'text_31ljsv', 'text_26rnbl', 'text_29hmk',
    'text_32buzw', 'text_27vigi', 'text_30uqjh', 'text_33eace',
}
ANTIBIOTIC_ROWS = (
    ('text_8ebez', 'text_9wiya', 'text_10ilqz'),
    ('text_11whjh', 'text_12twns', 'text_13xgkk'),
    ('text_14niru', 'text_15gajc', 'text_16btag'),
)
ANTIBIOTIC_FIELDS = {key for row in ANTIBIOTIC_ROWS for key in row}
SECTIONS = {
    'text_37yucz': '1. Datos del paciente e ingreso',
    'text_18l': '3. Tratamiento inmunosupresor',
    'text_20ieby': '4. Panel de Film Array solicitado',
    'text_25ubku': '5. Tipo de muestra',
    'text_34yohr': '6. Toma de muestra y criterio de solicitud',
    'firma_profesional_solicitante': '7. Profesional solicitante',
}
