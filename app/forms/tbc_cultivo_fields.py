"""Campos sobre el escaneo original, medidos a escala 1,5."""

FIELDS = []


def field(name, title, rect, kind='text'):
    FIELDS.append(dict(name=name, label=title, rect=[v / 1.5 for v in rect],
                       type=kind))


field('paciente_apellido_nombre', 'Apellido y nombres', (233, 193, 678, 213))
field('historia_clinica_numero', 'Historia clínica N.º', (759, 193, 845, 213))
field('paciente_documento', 'Documento (tipo y número)', (177, 220, 321, 240))
field('paciente_fecha_nacimiento', 'Fecha de nacimiento', (498, 220, 596, 240))
field('paciente_edad', 'Edad', (656, 220, 687, 240))
field('paciente_genero_f', 'Sexo', (773, 222, 788, 238), 'checkbox')
field('paciente_genero_m', 'Sexo: masculino', (821, 222, 837, 238), 'checkbox')
field('paciente_nacionalidad', 'Nacionalidad', (185, 245, 334, 264))
field('paciente_domicilio', 'Domicilio', (425, 245, 840, 264))
field('paciente_localidad', 'Localidad', (163, 266, 334, 285))
field('paciente_departamento', 'Partido / departamento', (473, 266, 598, 285))
field('paciente_provincia', 'Provincia', (691, 266, 841, 285))
field('paciente_pais_anterior', 'País de residencia anterior', (286, 289, 600, 309))
field('paciente_telefono', 'Teléfono', (690, 289, 845, 309))
field('tratamiento_previo_si', 'Tratamiento previo para tuberculosis', (383, 318, 398, 333), 'checkbox')
field('tratamiento_previo_no', 'Tratamiento previo: no', (444, 318, 459, 333), 'checkbox')
field('servicio_derivante', 'Servicio que deriva la muestra', (309, 340, 669, 360))
field('fecha_solicitud', 'Fecha', (743, 340, 837, 360))
field('baciloscopia', 'Baciloscopía', (193, 396, 208, 411), 'checkbox')
field('baciloscopia_diagnostico', 'Para diagnóstico', (251, 426, 267, 442), 'checkbox')
field('muestra_primera', 'Primera muestra', (527, 426, 542, 442), 'checkbox')
field('muestra_segunda', 'Segunda muestra', (610, 426, 625, 442), 'checkbox')
field('muestra_otra', 'Otra muestra', (699, 426, 714, 442), 'checkbox')
field('muestra_otra_numero', 'Número de otra muestra', (659, 422, 690, 442))
field('baciloscopia_control', 'Para control de tratamiento', (325, 452, 340, 468), 'checkbox')
field('mes_tratamiento', 'Mes de tratamiento', (524, 451, 845, 471))
field('muestra_tipo', 'Muestra de', (207, 477, 416, 497))
field('resultado_baciloscopia', 'Resultado de la baciloscopía', (646, 477, 845, 497))
field('cultivo', 'Cultivo', (153, 508, 168, 522), 'checkbox')
field('cultivo_sintomatico_respiratorio', 'Sintomático respiratorio con dos o más baciloscopías de esputo negativas', (663, 537, 679, 553), 'checkbox')
field('cultivo_extrapulmonar', 'Enfermedad extrapulmonar', (327, 564, 342, 580), 'checkbox')
field('cultivo_otro', 'Otro motivo de cultivo', (164, 590, 179, 606), 'checkbox')
field('cultivo_otro_detalle', 'Describir otro motivo de cultivo', (273, 589, 845, 609))
field('cultivo_sensibilidad', 'Cultivo y prueba de sensibilidad', (337, 628, 352, 643), 'checkbox')
field('retratamiento', 'Retratamiento', (120, 662, 136, 678), 'checkbox')
field('retratamiento_abandono', 'Retratamiento: abandono', (310, 662, 325, 678), 'checkbox')
field('retratamiento_fracaso', 'Retratamiento: fracaso', (310, 689, 325, 705), 'checkbox')
field('retratamiento_recaida', 'Retratamiento: recaída', (310, 716, 325, 732), 'checkbox')
field('personal_salud', 'Personal de salud', (120, 742, 136, 758), 'checkbox')
field('privado_libertad', 'Privado de la libertad', (120, 769, 136, 785), 'checkbox')
field('contacto_tb_resistente', 'Contacto de paciente con TB resistente a las drogas', (120, 797, 136, 813), 'checkbox')
field('inmunocomprometido', 'Inmunocomprometido', (120, 824, 136, 840), 'checkbox')
field('diabetico', 'Diabético', (120, 850, 136, 866), 'checkbox')
field('nino', 'Niño', (120, 877, 136, 893), 'checkbox')
field('adiccion_alcohol_drogas', 'Adicto al alcohol y/o drogas (con baciloscopía positiva o dos negativas)', (120, 903, 136, 919), 'checkbox')
field('baciloscopia_positiva_segundo_mes', 'Baciloscopía de esputo positiva después del segundo mes de tratamiento', (120, 931, 136, 946), 'checkbox')
field('sensibilidad_otro', 'Otro motivo de prueba de sensibilidad', (120, 958, 136, 973), 'checkbox')
field('sensibilidad_otro_detalle', 'Describir otro motivo de sensibilidad', (182, 955, 554, 975))
field('solicitante_estudio', 'Solicitante del o los estudios', (333, 1014, 625, 1034))
field('firma_solicitante', 'Firma', (695, 979, 845, 1033), 'signature')
field('resumen_historia_clinica', 'Resumen de historia clinica', (81, 1101, 849, 1200), 'multiline')

LABELS = {item['name']: item['label'] for item in FIELDS}
SECTIONS = {
    'paciente_apellido_nombre': '1. Datos del paciente',
    'servicio_derivante': '2. Derivación de la muestra',
    'baciloscopia': '3. Baciloscopía',
    'cultivo': '4. Cultivo',
    'cultivo_sensibilidad': '5. Cultivo y prueba de sensibilidad',
    'solicitante_estudio': '6. Solicitante y firma',
    'resumen_historia_clinica': '7. Resumen de historia clinica',
}
YES_NO_PAIRS = {'tratamiento_previo_si': 'tratamiento_previo_no'}
