"""Campos de GenXpert: coordenadas verificadas sobre la página de 612 × 792 pt."""

FIELDS = []
FORM_Y_SCALE = 0.88


def field(name, title, rect, kind='text', page=0, multiline=False):
    # Referencia visual a escala 1,5; convertir a puntos PDF (origen superior).
    FIELDS.append(dict(name=name, label=title, rect=[v / 1.5 for v in rect],
                       type=kind, page=page, multiline=multiline))


field('institucion', 'Institución', (171, 144, 739, 165))
field('profesional', 'Profesional', (171, 177, 739, 198))
field('servicio', 'Servicio', (157, 209, 739, 230))
field('institucion_direccion', 'Dirección postal de la institución', (207, 240, 739, 261))
field('institucion_telefono', 'Teléfono de la institución', (160, 271, 278, 292))
field('institucion_fax', 'Fax', (327, 271, 454, 292))
field('institucion_correo', 'Correo electrónico de la institución', (583, 271, 739, 292))
field('paciente_apellido_nombre', 'Apellido y nombres', (245, 351, 610, 372))
field('historia_clinica_numero', 'Historia clínica N.º', (721, 351, 795, 372))
field('paciente_documento', 'Documento (tipo y número)', (183, 381, 298, 402))
field('paciente_fecha_nacimiento', 'Fecha de nacimiento', (448, 381, 551, 402))
field('paciente_edad', 'Edad', (611, 381, 638, 402))
field('paciente_genero_f', 'Género: femenino', (730, 386, 744, 400), 'checkbox')
field('paciente_genero_m', 'Género: masculino', (779, 386, 793, 400), 'checkbox')
field('paciente_nacionalidad', 'Nacionalidad', (193, 409, 305, 430))
field('paciente_domicilio', 'Domicilio', (382, 409, 762, 430))
field('paciente_localidad', 'Localidad', (177, 436, 308, 457))
field('paciente_departamento', 'Partido / departamento', (430, 436, 556, 457))
field('paciente_provincia', 'Provincia', (645, 436, 795, 457))
field('paciente_pais_anterior', 'País de residencia anterior', (282, 462, 532, 483))
field('paciente_telefono', 'Teléfono del paciente', (606, 462, 743, 483))
field('muestra_esputo', 'Esputo', (213, 540, 227, 554), 'checkbox')
field('muestra_lavado_gastrico', 'Lavado gástrico', (454, 540, 468, 554), 'checkbox')
field('muestra_lcr', 'LCR', (640, 540, 654, 554), 'checkbox')
field('muestra_ganglio', 'Ganglio', (217, 580, 231, 594), 'checkbox')
field('muestra_otros_tejidos', 'Otros tejidos', (454, 580, 468, 594), 'checkbox')
field('muestra_otros_detalle', 'Indicar otros tejidos', (567, 575, 773, 596))
field('fecha_toma_muestra', 'Fecha de toma de muestra', (275, 610, 388, 631))
field('resultado_baciloscopia', 'Resultado de la baciloscopía', (285, 643, 457, 664))
field('cultivo_solicitado_si', 'Cultivo solicitado', (291, 683, 305, 697), 'checkbox')
field('cultivo_solicitado_no', 'Cultivo solicitado: no', (239, 683, 253, 697), 'checkbox')
field('laboratorio_cultivo', 'Laboratorio donde fue cultivada', (515, 679, 791, 700))
field('enfermedad_extrapulmonar', 'Enfermedad extrapulmonar', (110, 759, 124, 773), 'checkbox')
field('tratamiento_previo_si', 'Tratamiento previo para tuberculosis', (386, 795, 400, 809), 'checkbox')
field('tratamiento_previo_no', 'Tratamiento previo para tuberculosis: no', (349, 795, 363, 809), 'checkbox')
field('retratamiento_fracaso', 'Retratamiento: fracaso', (533, 821, 547, 835), 'checkbox')
field('retratamiento_recuperado', 'Retratamiento: recuperado a la pérdida de seguimiento', (533, 847, 547, 861), 'checkbox')
field('retratamiento_recaida', 'Retratamiento: recaída', (533, 868, 547, 882), 'checkbox')
field('fecha_fin_tratamiento', 'Fecha de finalización del último tratamiento', (665, 894, 766, 915))
field('contacto_tb_resistente', 'Contacto con paciente con TB resistente a rifampicina / multirresistente', (110, 940, 124, 954), 'checkbox')
field('huesped_especial', 'Huésped especial', (110, 966, 124, 980), 'checkbox')
field('nino', 'Niño', (288, 966, 302, 980), 'checkbox')
field('personal_salud', 'Personal de salud', (422, 966, 436, 980), 'checkbox')
field('contexto_encierro', 'Contexto de encierro', (616, 966, 630, 980), 'checkbox')
field('antecedente_otro', 'Otro antecedente', (148, 992, 162, 1006), 'checkbox')
field('antecedente_otro_detalle', 'Describir otro antecedente', (239, 988, 720, 1009))
field('fecha_solicitud', 'Fecha de solicitud', (141, 1094, 231, 1115))
field('solicitante_estudio', 'Solicitante del estudio', (426, 1094, 633, 1115))
field('firma_solicitante', 'Firma del solicitante', (682.5, 1041, 892.5, 1147.5), 'signature')
# Compactar la planilla para dejar el resumen al pie de la misma hoja.
for spec in FIELDS:
    spec['rect'][1] *= FORM_Y_SCALE
    spec['rect'][3] *= FORM_Y_SCALE

field('resumen_historia_clinica', 'Resumen de historia clínica', (102, 1050, 792, 1164),
      multiline=True)

LABELS = {item['name']: item['label'] for item in FIELDS}
SECTIONS = {
    'institucion': '1. Institución derivante',
    'paciente_apellido_nombre': '2. Datos del paciente',
    'muestra_esputo': '3. Muestra remitida',
    'enfermedad_extrapulmonar': '4. Antecedentes del paciente',
    'fecha_solicitud': '5. Solicitud y firma',
    'resumen_historia_clinica': '6. Resumen de historia clínica',
}
YES_NO_PAIRS = {'cultivo_solicitado_si': 'cultivo_solicitado_no',
                'tratamiento_previo_si': 'tratamiento_previo_no'}
