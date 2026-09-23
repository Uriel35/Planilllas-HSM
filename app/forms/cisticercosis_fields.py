"""Campos de las dos páginas de la ficha de envío de muestras de parasitología.

Coordenadas sobre la referencia de 849 × 1200, convertidas a puntos PDF.
"""
import unicodedata

TEMPLATE = 'Cisticercosis — envío de muestras'
FIELDS = []
LABELS = {}
SECTIONS = {}
YES_NO_PAIRS = {}


def field(name, title, page, box, kind='text', multiline=False):
    FIELDS.append(dict(name=name, page=page, rect=[v * (595.32 / 849 if i % 2 == 0 else 841.92 / 1200)
                                                for i, v in enumerate(box)],
                       type=kind, multiline=multiline))
    LABELS[name] = title


def text(name, title, page, x, y, right, bottom=None):
    field(name, title, page, (x, y, right, bottom or y + 19), multiline=bottom is not None)


def check(name, title, page, x, y):
    field(name, title, page, (x, y, x + 20, y + 20), 'checkbox')


def pair(name, title, page, x, y, no_x):
    check(name + '_si', title, page, x, y)
    check(name + '_no', title + ': no', page, no_x, y)
    YES_NO_PAIRS[name + '_si'] = name + '_no'


SECTIONS['evento_cisticercosis'] = '1. Eventos sospechados'
for name, title, x, y in [('cisticercosis', 'Cisticercosis', 146, 150), ('hidatidosis', 'Hidatidosis', 255, 150),
                         ('toxoplasmosis_embarazo', 'Toxoplasmosis en embarazadas', 468, 150),
                         ('triquinosis', 'Triquinosis', 146, 177), ('toxocariosis', 'Toxocariosis', 255, 177),
                         ('toxoplasmosis_congenita', 'Toxoplasmosis congénita', 468, 177)]:
    check('evento_' + name, title, 0, x, y)
text('evento_otros', 'Otros eventos', 0, 548, 150, 790, 195)
SECTIONS['muestra_primera'] = '2. Material remitido'
for name, title, x, y in [('primera', 'Primera muestra', 71, 243), ('segunda', 'Segunda muestra', 71, 269),
                         ('tercera', 'Tercera muestra', 175, 243), ('recidiva', 'Recidiva', 175, 269)]:
    check('muestra_' + name, title, 0, x, y)
for name, title, x, y, tx, right in [('suero', 'Suero', 344, 255, 444, 562), ('lcr', 'LCR', 344, 282, 444, 562),
                                  ('quiste', 'Quiste', 573, 255, 672, 790), ('alimento', 'Alimento', 573, 282, 672, 790)]:
    check('muestra_' + name, title, 0, x, y)
    text('fecha_muestra_' + name, 'Fecha de toma: ' + title, 0, tx, y, right)
SECTIONS['paciente_dni'] = '3. Datos del paciente'
text('paciente_dni', 'DNI', 0, 112, 348, 254)
text('paciente_fecha_nacimiento', 'Fecha de nacimiento', 0, 369, 348, 487)
text('paciente_edad', 'Edad', 0, 539, 348, 617)
check('paciente_genero_m', 'Sexo: masculino', 0, 682, 348)
check('paciente_genero_f', 'Sexo: femenino', 0, 732, 348)
text('paciente_apellido_nombre', 'Apellido y nombres', 0, 182, 376, 788)
for prefix, title, x in [('nacimiento', 'Nacimiento', 120), ('residencia', 'Residencia', 474)]:
    for name, label, y in [('pais', 'país', 428), ('provincia', 'provincia', 455), ('localidad', 'localidad', 482)]:
        text(prefix + '_' + name, title + ': ' + label, 0, x, y, x + 233)
    for name, label, dx in [('urbana', 'urbana', 46), ('periurbana', 'periurbana', 130), ('rural', 'rural', 209)]:
        check(prefix + '_zona_' + name, title + ': zona ' + label, 0, x + dx - (11 if prefix == 'residencia' else 0), 508)
SECTIONS['fecha_consulta'] = '4. Datos clínicos'
text('fecha_consulta', 'Fecha de consulta', 0, 162, 574, 280)
check('ambulatorio', 'Ambulatorio', 0, 404, 573)
check('internado', 'Internado', 0, 493, 573)
pair('embarazo', 'Embarazo', 0, 667, 573, 713)
pair('sintomatologia', '¿Presenta sintomatología?', 0, 225, 600, 270)
text('fecha_internacion', 'Fecha de internación', 0, 444, 601, 562)
text('edad_gestacional', 'Edad gestacional', 0, 594, 626, 781)
text('fecha_inicio_sintomas', 'Fecha de inicio de síntomas', 0, 210, 627, 329)
SECTIONS['sintoma_fiebre'] = '5. Signos y síntomas'
for x, names in [(111, ['Fiebre', 'Diarrea', 'Náuseas', 'Vómitos']), (205, ['Mialgias', 'Exantema', 'Taquicardia', 'Sibilancias']),
                 (310, ['Conjuntivitis', 'Lesión ocular', 'Hidrocefalia', 'Cefalea']),
                 (419, ['Convulsiones', 'Epilepsia', 'Encefalitis']),
                 (543, ['Hepatomegalia', 'Edema palpebral', 'Esplenomegalia']),
                 (761, ['Hipertensión endocraneal', 'Síndromes neurológicos'])]:
    for i, title in enumerate(names):
        key = ''.join(c for c in unicodedata.normalize('NFD', title.lower()) if not unicodedata.combining(c)).replace(' ', '_')
        check('sintoma_' + key, title, 0, x, 679 + i * 26.5)
text('sintomas_otros', 'Otros signos y síntomas', 0, 379, 760, 782)
SECTIONS['antecedente_teniasis_si'] = '6. Antecedentes clínicos'
for i, name in enumerate(['teniasis', 'epilepsia', 'convulsiones']):
    y = 838 + i * 26.5
    pair('antecedente_' + name, 'Antecedente de ' + name, 0, 146, y, 170)
    check('antecedente_' + name + '_familiar', name.capitalize() + ': familiar', 0, 210, y)
    check('antecedente_' + name + '_personal', name.capitalize() + ': personal', 0, 250, y)
pair('inmunosupresion', 'Inmunosupresión', 0, 329, 838, 379)
text('inmunosupresion_causa', 'Causa de inmunosupresión', 0, 449, 812, 781, 858)
text('patologia_base', 'Patología de base', 0, 306, 897, 781)
SECTIONS['tratamiento_farmacologico_si'] = '7. Tratamiento'
pair('tratamiento_farmacologico', 'Tratamiento farmacológico', 0, 166, 951, 215)
text('fecha_tratamiento_farmacologico', 'Fecha del tratamiento farmacológico', 0, 280, 951, 399)
text('tratamiento_droga', 'Droga', 0, 446, 951, 536)
text('tratamiento_dosis', 'Dosis', 0, 584, 951, 662)
text('tratamiento_dias', 'Días', 0, 703, 951, 781)
pair('tratamiento_quirurgico', 'Tratamiento quirúrgico', 0, 166, 977, 215)
text('fecha_tratamiento_quirurgico', 'Fecha del tratamiento quirúrgico', 0, 280, 978, 399)
text('organo_afectado', 'Órgano afectado', 0, 504, 978, 781)
SECTIONS['serologia_1'] = '8. Laboratorio'
for i in range(2):
    for name, title, x, right in [('serologia', 'Serología', 62, 169), ('metodologia', 'Metodología', 181, 254),
                                  ('fecha_serologia', 'Fecha', 266, 383), ('resultado', 'Resultado', 395, 453)]:
        text(f'{name}_{i+1}', f'{title} {i+1}', 0, x, 1057 + i * 26, right)
for name, title, x, y, right in [('hto', 'Hto (%)', 504, 1030, 571), ('gb', 'GB (mm³)', 494, 1057, 557),
                               ('eosinofilos', 'Eosinófilos (%)', 530, 1083, 571), ('ldh', 'LDH (UI/L)', 624, 1030, 668),
                               ('asat', 'ASAT (UI/L)', 624, 1057, 668), ('cpk', 'CPK (UI/L)', 624, 1083, 668),
                               ('cd4', 'CD4', 732, 1030, 786), ('ige', 'IgE', 732, 1057, 786)]:
    text('laboratorio_' + name, title, 0, x, y, right)
SECTIONS['imagen_rmn'] = '9. Diagnóstico por imagen'
for name, title, x, y in [('rmn', 'RMN', 91, 163), ('ecografia', 'Ecografía', 176, 163), ('tac', 'TAC', 91, 189),
                         ('radiografia', 'Radiografía', 176, 189), ('unico', 'Quiste único', 275, 163),
                         ('multiple', 'Quistes múltiples', 365, 163), ('degenerado', 'Degenerado', 464, 163),
                         ('escolex_visible', 'Escólex visible', 549, 170), ('vesicular', 'Vesicular', 275, 189),
                         ('calcificado', 'Calcificado', 365, 189), ('complicado', 'Complicado', 464, 189)]:
    check('imagen_' + name, title, 1, x, y)
text('imagen_observaciones', 'Observaciones de imágenes', 1, 587, 170, 788, 402)
for i, (name, title) in enumerate([('neurologico_parenquimatoso', 'Neurológico parenquimatoso'),
                                  ('neurologico_extraparenquimatoso', 'Neurológico extraparenquimatoso'),
                                  ('pulmon', 'Pulmón'), ('higado', 'Hígado'), ('abdominal', 'Abdominal'), ('otras', 'Otras localizaciones')]):
    y = 250 + i * 26.5
    check('localizacion_' + name, title, 1, 61, y)
    text('cantidad_' + name, title + ': cantidad de quistes', 1, 296, y, 403)
    text('tamano_' + name, title + ': tamaño (mm)', 1, 410, y, 562)
text('localizacion_otras_detalle', 'Detalle de otras localizaciones', 1, 126, 382, 287)
# Un círculo marca el estadio sobre las alternativas impresas.
for i in range(4):
    check('estadio_higado_' + str(i + 1), 'Hígado: estadio ' + ['I', 'II', 'III', 'IV'][i], 1, 163 + i * 29, 348)
SECTIONS['ocupacion'] = '10. Datos epidemiológicos'
text('ocupacion', 'Ocupación', 1, 120, 449, 423)
pair('granja_huerta', '¿La vivienda cuenta con granja o huerta?', 1, 365, 474, 404)
check('destino_autoabastecimiento', 'Destino: autoabastecimiento', 1, 290, 508)
check('destino_comercializacion', 'Destino: comercialización', 1, 404, 508)
pair('cria_animales', '¿Cría animales?', 1, 365, 547, 404)
for name, x in [('perro', 146), ('gato', 205), ('cerdo', 265), ('oveja', 320)]:
    check('animal_' + name, name.capitalize(), 1, x, 574)
text('animal_otros', 'Otros animales', 1, 376, 575, 423)
pair('desparasitacion', '¿Implementa planes de desparasitación masiva?', 1, 365, 600, 404)
for name, title, y in [('consume_cerdo', '¿Consume carne de cerdo?', 448), ('consume_caza', '¿Consume carne de animales de caza?', 474),
                       ('faenas_domiciliarias', '¿Realiza faenas domiciliarias?', 501)]:
    pair(name, title, 1, 728, y, 767)
for name, title, y in [('exterior', 'Viaje al exterior', 574), ('interior', 'Viaje al interior', 600)]:
    check('viaje_' + name, title, 1, 494, y)
    text('viaje_' + name + '_lugar', title + ': lugar', 1, 575, y, 787)
SECTIONS['brote_si'] = '11. Completar ante sospecha de triquinosis'
pair('brote', '¿El caso está asociado a un brote?', 1, 250, 667, 290)
text('brote_localidad', 'Localidad del brote', 1, 162, 695, 304)
text('brote_consumidores', 'Personas que consumieron el alimento', 1, 221, 741, 304)
text('brote_sintomaticos', 'Casos sintomáticos', 1, 196, 794, 304)
text('brote_asintomaticos', 'Casos asintomáticos', 1, 196, 820, 304)
text('fecha_consumo', 'Fecha de consumo', 1, 327, 695, 442)
check('carne_cerdo', 'Carne: cerdo', 1, 404, 747)
check('carne_silvestre', 'Carne: fauna silvestre', 1, 404, 773)
text('carne_otra', 'Otra carne', 1, 327, 820, 439)
for name, title, y in [('comercial', 'Comercial', 693), ('ambulante', 'Venta ambulante', 720), ('familiar', 'Cría familiar', 747)]:
    check('origen_' + name, 'Origen: ' + title, 1, 549, y)
check('consumo_cocido', 'Consumo: cocido', 1, 633, 693)
check('consumo_fresco', 'Consumo: fresco', 1, 633, 720)
check('consumo_embutido', 'Consumo: embutido', 1, 762, 693)
text('consumo_otro', 'Otra forma de consumo', 1, 674, 748, 781)
pair('digestion_artificial', '¿Se realizó digestión artificial del alimento?', 1, 698, 794, 738)
pair('alimento_disponible', '¿Hay alimento disponible para análisis?', 1, 698, 820, 738)
SECTIONS['profesional_apellido_nombre'] = '12. Médico tratante y derivación'
text('profesional_apellido_nombre', 'Apellido y nombre del profesional', 1, 252, 893, 787)
text('institucion_solicitante', 'Institución solicitante', 1, 232, 926, 787)
text('profesional_telefono', 'Teléfono del profesional', 1, 117, 960, 234)
text('profesional_email', 'Email del profesional', 1, 282, 960, 787)
text('fecha_derivacion', 'Fecha de derivación', 1, 62, 1037, 248)
