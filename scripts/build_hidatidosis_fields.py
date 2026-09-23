from app.paths import FIELDS_DIR
import json


PDF_W = 595.0
PDF_H = 842.0
IMG_W = 1653
IMG_H = 2339
SX = PDF_W / IMG_W
SY = PDF_H / IMG_H


fields = []
TEXT_Y_SHIFT = -10
CHECK_X_SHIFT = -8
CHECK_Y_SHIFT = -10


def px_rect(x1, y1, x2, y2):
    return [
        round(x1 * SX, 2),
        round((IMG_H - y2) * SY, 2),
        round(x2 * SX, 2),
        round((IMG_H - y1) * SY, 2),
    ]


def add_text(name, page, x1, y1, x2, y2, font_size=9, multiline=False):
    fields.append(
        {
            "type": "text",
            "name": name,
            "page": page,
            "rect": px_rect(x1, y1 + TEXT_Y_SHIFT, x2, y2 + TEXT_Y_SHIFT),
            "font_size": font_size,
            "multiline": multiline,
        }
    )


def add_checkbox(name, page, x1, y1, x2, y2):
    fields.append(
        {
            "type": "checkbox",
            "name": name,
            "page": page,
            "rect": px_rect(
                x1 + CHECK_X_SHIFT,
                y1 + CHECK_Y_SHIFT,
                x2 + CHECK_X_SHIFT,
                y2 + CHECK_Y_SHIFT,
            ),
        }
    )


def build_page_1():
    p = 0

    # 1. Datos del declarante
    add_text("declarante_provincia", p, 262, 604, 590, 626)
    add_text("declarante_departamento", p, 772, 604, 1072, 626)
    add_text("declarante_localidad", p, 1215, 604, 1490, 626)
    add_text("fecha_notificacion", p, 1240, 648, 1492, 674)
    add_text("establecimiento_notificante", p, 456, 648, 878, 674)
    add_text("profesional_apellido_nombre", p, 532, 694, 1490, 720)
    add_text("declarante_telefono", p, 190, 735, 530, 760)
    add_text("declarante_fax", p, 640, 735, 932, 760)
    add_text("declarante_email", p, 1058, 735, 1490, 760)

    # 2. Identificacion del paciente
    add_text("paciente_apellido_nombres", p, 365, 885, 1492, 912)
    add_text("paciente_fecha_nacimiento", p, 382, 930, 640, 956)
    add_text("paciente_edad", p, 725, 930, 840, 956)
    add_checkbox("paciente_sexo_m", p, 962, 928, 986, 954)
    add_checkbox("paciente_sexo_f", p, 1042, 928, 1066, 954)
    add_text("paciente_dni", p, 1170, 930, 1492, 956)
    add_text("paciente_domicilio_actual", p, 335, 974, 970, 1000)
    add_text("paciente_telefono_propio_vecino", p, 1200, 974, 1492, 1000)
    add_text("referencia_ubicacion_domicilio", p, 550, 1018, 970, 1044)
    add_text("paciente_localidad", p, 1100, 1018, 1492, 1044)
    add_checkbox("paciente_urbano", p, 250, 1062, 274, 1088)
    add_checkbox("paciente_rural", p, 376, 1062, 400, 1088)
    add_text("paciente_departamento", p, 588, 1064, 924, 1090)
    add_text("paciente_provincia", p, 1048, 1064, 1492, 1090)

    # 3. Datos clinicos
    add_text("fecha_inicio_sintomas", p, 510, 1198, 770, 1224)
    add_text("fecha_consulta", p, 1245, 1198, 1492, 1224)
    add_text("fecha_internacion", p, 402, 1246, 652, 1272)
    add_checkbox("asintomatico", p, 318, 1286, 342, 1312)
    add_checkbox("vomica", p, 478, 1286, 502, 1312)
    add_checkbox("masa", p, 635, 1286, 659, 1312)
    add_checkbox("localizacion_hepatico", p, 560, 1330, 584, 1356)
    add_checkbox("localizacion_pulmonar", p, 745, 1330, 769, 1356)
    add_checkbox("localizacion_abdominal", p, 930, 1330, 954, 1356)
    add_text("localizacion_otros", p, 1048, 1334, 1492, 1360)
    add_checkbox("caracteristica_quiste_unico", p, 563, 1376, 587, 1402)
    add_checkbox("caracteristica_quiste_multiple", p, 850, 1376, 874, 1402)
    add_checkbox("caracteristica_quiste_calcificado", p, 1168, 1376, 1192, 1402)
    add_checkbox("caracteristica_quiste_complicado", p, 1490, 1376, 1514, 1402)
    add_text("diagnostico_imagenes_rx", p, 225, 1470, 1450, 1495)
    add_text("diagnostico_imagenes_ecografia", p, 300, 1514, 1450, 1539)
    add_text("diagnostico_imagenes_tac", p, 255, 1558, 1450, 1583)

    # 4. Datos epidemiologicos
    add_text("ocupacion_riesgo", p, 382, 1680, 650, 1706)
    add_checkbox("lugar_trabajo_urbana", p, 976, 1668, 1000, 1694)
    add_checkbox("lugar_trabajo_periurbano", p, 1175, 1668, 1199, 1694)
    add_checkbox("lugar_trabajo_rural", p, 1310, 1668, 1334, 1694)
    add_checkbox("lugar_trabajo_silvestre", p, 1488, 1668, 1512, 1694)
    add_checkbox("trabajo_vivio_zona_rural_si", p, 558, 1710, 582, 1736)
    add_checkbox("trabajo_vivio_zona_rural_no", p, 665, 1710, 689, 1736)
    add_checkbox("crio_animales_si", p, 927, 1752, 951, 1778)
    add_checkbox("crio_animales_no", p, 1032, 1752, 1056, 1778)
    add_checkbox("tiene_perros_si", p, 347, 1796, 371, 1822)
    add_checkbox("tiene_perros_no", p, 455, 1796, 479, 1822)
    add_checkbox("perro_parasitado_si", p, 927, 1796, 951, 1822)
    add_checkbox("perro_parasitado_no", p, 1034, 1796, 1058, 1822)
    add_checkbox("perro_tratado_si", p, 1390, 1796, 1414, 1822)
    add_checkbox("perro_tratado_no", p, 1492, 1796, 1516, 1822)
    add_text("fecha_ultima_desparasitacion", p, 485, 1842, 738, 1868)
    add_checkbox("alimenta_perros_visceras_crudas_si", p, 710, 1882, 734, 1908)
    add_checkbox("alimenta_perros_visceras_crudas_no", p, 820, 1882, 844, 1908)


def build_page_2():
    p = 1

    # 5. Examenes de laboratorio
    add_text("fecha_toma_muestra", p, 465, 368, 735, 394)
    add_text("material_remitido", p, 965, 368, 1492, 394)
    add_text("metodo_laboratorio", p, 205, 414, 895, 440)
    add_text("resultado_laboratorio", p, 1072, 414, 1492, 440)

    # 6. Acciones de control y prevencion
    add_checkbox("tratamiento_farmacologico_si", p, 488, 604, 512, 630)
    add_checkbox("tratamiento_farmacologico_no", p, 595, 604, 619, 630)
    add_checkbox("tratamiento_farmacologico_primera_vez", p, 885, 604, 909, 630)
    add_checkbox("tratamiento_farmacologico_ulterior", p, 1078, 604, 1102, 630)
    add_text("tratamiento_farmacologico_droga", p, 425, 650, 818, 676)
    add_text("tratamiento_farmacologico_dosis", p, 912, 650, 1172, 676)
    add_text("tratamiento_farmacologico_dias", p, 1302, 650, 1452, 676)
    add_checkbox("tratamiento_quirurgico_si", p, 488, 694, 512, 720)
    add_checkbox("tratamiento_quirurgico_no", p, 595, 694, 619, 720)
    add_checkbox("tratamiento_quirurgico_primera_vez", p, 885, 694, 909, 720)
    add_checkbox("tratamiento_quirurgico_recidiva", p, 1078, 694, 1102, 720)
    add_checkbox("control_serologico_ecografico_si", p, 918, 820, 942, 846)
    add_checkbox("control_serologico_ecografico_no", p, 1012, 820, 1036, 846)
    add_text("numero_controles_realizados", p, 1350, 830, 1450, 856)
    add_checkbox("educacion_promocion_salud_si", p, 918, 865, 942, 891)
    add_checkbox("educacion_promocion_salud_no", p, 1012, 865, 1036, 891)
    add_checkbox("desparasitacion_periodica_perros_si", p, 1358, 905, 1382, 931)
    add_checkbox("desparasitacion_periodica_perros_no", p, 1455, 905, 1479, 931)

    # 7. Evolucion y clasificacion del caso
    add_checkbox("paciente_hospitalizado_si", p, 488, 1068, 512, 1094)
    add_checkbox("paciente_hospitalizado_no", p, 595, 1068, 619, 1094)
    add_checkbox("paciente_hospitalizado_se_ignora", p, 790, 1068, 814, 1094)
    add_text("fecha_hospitalizacion", p, 1250, 1070, 1492, 1096)
    add_checkbox("alta_sin_secuelas", p, 368, 1112, 392, 1138)
    add_checkbox("alta_con_secuelas", p, 675, 1112, 699, 1138)
    add_checkbox("fallecido", p, 885, 1112, 909, 1138)
    add_text("fecha_fallecimiento_o_alta", p, 998, 1114, 1248, 1140)
    add_checkbox("desconocido", p, 1488, 1112, 1512, 1138)
    add_text("diagnostico_final", p, 345, 1158, 920, 1184)
    add_checkbox("laboratorio", p, 1162, 1156, 1186, 1182)
    add_checkbox("nexo_epidemiologico", p, 1488, 1156, 1512, 1182)

    add_text("fecha_final", p, 220, 1480, 485, 1508)


def build():
    build_page_1()
    build_page_2()


if __name__ == "__main__":
    build()
    out = FIELDS_DIR / "hidatidosis_fields.json"
    out.write_text(json.dumps(fields, indent=2), encoding="utf-8")
    print(f"wrote {out} with {len(fields)} fields")
