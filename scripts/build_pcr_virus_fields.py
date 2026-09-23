from app.paths import FIELDS_DIR
import json


PDF_W = 595.56
PDF_H = 842.04
IMG_W = 1241
IMG_H = 1755
SX = PDF_W / IMG_W
SY = PDF_H / IMG_H


fields = []


def px_rect(x1, y1, x2, y2):
    return [
        round(x1 * SX, 2),
        round((IMG_H - y2) * SY, 2),
        round(x2 * SX, 2),
        round((IMG_H - y1) * SY, 2),
    ]


def pt_rect(x1, y1, x2, y2):
    return [round(x1, 2), round(PDF_H - y2, 2), round(x2, 2), round(PDF_H - y1, 2)]


def add_text(name, page, rect, font_size=10, multiline=False):
    fields.append(
        {
            "type": "text",
            "name": name,
            "page": page,
            "rect": rect,
            "font_size": font_size,
            "multiline": multiline,
        }
    )


def add_checkbox(name, page, rect):
    fields.append({'type': 'checkbox', 'name': name, 'page': page, 'rect': rect})


def add_date(prefix, page, x, y, widths=(34, 34, 48), h=22, gap=14, font_size=10):
    total_w = sum(widths) + gap * (len(widths) - 1)
    add_text(prefix, page, px_rect(x, y, x + total_w, y + h), font_size=font_size)


def add_yes_no(prefix, page, yes_rect, no_rect):
    add_checkbox(f"{prefix}_si", page, yes_rect)
    add_checkbox(f"{prefix}_no", page, no_rect)


def build():
    fields.clear()
    # Page 1
    p = 0

    # Identificacion de la institucion
    add_text("establecimiento_notificador", p, px_rect(256, 351, 548, 373), 10)
    add_text("institucion_provincia", p, px_rect(608, 351, 803, 373), 10)
    add_text("institucion_departamento", p, px_rect(905, 351, 1134, 373), 10)
    add_date("fecha_notificacion", p, 245, 386, widths=(32, 32, 46), h=22, gap=14, font_size=10)
    add_text("notificador_apellido_nombre", p, px_rect(645, 386, 1168, 408), 10)
    add_text("institucion_telefono", p, px_rect(116, 419, 352, 441), 10)
    add_text("institucion_correo", p, px_rect(502, 419, 1167, 441), 10)

    # Identificacion del caso
    add_checkbox("tipo_documento_dni", p, pt_rect(119.45, 261.6, 130.75, 272.9))
    add_checkbox("tipo_documento_de", p, pt_rect(151.35, 261.6, 162.65, 272.9))
    add_checkbox("tipo_documento_ind", p, pt_rect(184.65, 261.6, 195.95, 272.9))
    add_text("numero_documento", p, px_rect(462, 540, 587, 562), 9)
    add_text("paciente_apellido_nombre", p, px_rect(712, 540, 1138, 562), 10)
    add_text("paciente_telefono", p, px_rect(108, 573, 322, 595), 10)
    add_date("fecha_nacimiento", p, 492, 573, widths=(33, 33, 42), h=22, gap=14, font_size=10)
    add_yes_no(
        "embarazada",
        p,
        pt_rect(367.25, 275.35, 378.55, 286.65),
        pt_rect(398.45, 275.35, 409.75, 286.65),
    )
    add_text("residencia_provincia", p, px_rect(300, 597, 500, 619), 10)
    add_text("residencia_departamento", p, px_rect(650, 597, 817, 619), 10)
    add_text("residencia_localidad", p, px_rect(918, 597, 1170, 619), 10)
    add_text("domicilio_calle", p, px_rect(266, 620, 430, 642), 10)
    add_text("domicilio_manzana", p, px_rect(431, 620, 642, 642), 10)
    add_text("domicilio_numero", p, px_rect(645, 620, 709, 642), 10)
    add_text("domicilio_piso", p, px_rect(738, 620, 812, 642), 10)
    add_text("domicilio_depto", p, px_rect(866, 620, 992, 642), 10)
    add_text("domicilio_codigo_postal", p, px_rect(1098, 620, 1171, 642), 10)

    # Informacion clinica
    add_date("fecha_primera_consulta", p, 257, 741, widths=(34, 34, 46), h=22, gap=14, font_size=10)
    add_date("fecha_inicio_sintomas", p, 692, 741, widths=(34, 34, 46), h=22, gap=14, font_size=10)

    symptom_boxes = {
        "fiebre_lt_38": (196, 775, 223, 799),
        "dolor_garganta": (383, 775, 409, 799),
        "tos": (576, 775, 602, 799),
        "dificultad_respiratoria": (790, 775, 816, 799),
        "cefalea": (995, 775, 1021, 799),
        "mialgias": (1155, 775, 1182, 799),
        "fiebre_ge_38": (196, 800, 223, 824),
        "vomitos": (383, 800, 409, 824),
        "rinitis_congestion_nasal": (576, 800, 602, 824),
        "anosmia_reciente_aparicion": (790, 800, 816, 824),
        "disgeusia_reciente_aparicion": (995, 800, 1021, 824),
        "diarrea": (1155, 800, 1182, 824),
        "astenia": (196, 826, 223, 849),
    }
    for name, rect in symptom_boxes.items():
        add_checkbox(name, p, px_rect(*rect))

    add_checkbox("caso_bronquiolitis", p, px_rect(171, 941, 199, 970))
    add_checkbox("caso_neumonia", p, px_rect(312, 941, 339, 970))
    add_checkbox("caso_irag", p, px_rect(430, 941, 456, 970))
    add_text("caso_otro", p, px_rect(628, 942, 812, 966), 10)

    add_yes_no(
        "comorbilidades_presenta",
        p,
        pt_rect(281.05, 487.8, 292.35, 499.1),
        pt_rect(310.25, 487.8, 321.55, 499.1),
    )

    comorb_boxes = {
        "asma": (160, 1060, 188, 1109),
        "dialisis_cronica": (381, 1060, 419, 1109),
        "insuficiencia_renal_cronica": (604, 1060, 642, 1109),
        "fumador": (836, 1060, 874, 1109),
        "tuberculosis": (1064, 1060, 1103, 1109),
        "bajo_peso_nacer": (160, 1110, 188, 1158),
        "embarazo_puerperio": (381, 1110, 419, 1158),
        "obesidad_imc_30_39_9": (604, 1110, 642, 1158),
        "insuficiencia_cardiaca": (836, 1110, 874, 1158),
        "obesidad_morbida_imc_gt_39_9": (1064, 1110, 1103, 1158),
        "bronquiolitis_previa": (160, 1159, 188, 1222),
        "hepatopatia_cronica": (381, 1159, 419, 1222),
        "inmunosupresion": (604, 1159, 642, 1222),
        "hipertension_arterial": (836, 1159, 874, 1222),
        "diabetes": (160, 1223, 188, 1287),
        "enfermedad_neurologica_cronica": (381, 1223, 419, 1287),
        "epoc": (604, 1223, 642, 1287),
        "neumonia_comunidad_previa": (836, 1223, 874, 1287),
        "dialisis_aguda": (160, 1288, 188, 1350),
        "enfermedad_oncologica": (381, 1288, 419, 1350),
        "ex_fumador": (604, 1288, 642, 1350),
        "prematuridad": (836, 1288, 874, 1350),
    }
    for name, rect in comorb_boxes.items():
        add_checkbox(name, p, px_rect(*rect))
    add_text("otras_comorbilidades", p, px_rect(878, 1160, 1102, 1349), 10, multiline=True)

    add_yes_no(
        "oseltamivir_administrado",
        p,
        pt_rect(188.05, 663.4, 199.35, 674.7),
        pt_rect(217.2, 663.4, 228.5, 674.7),
    )

    add_text("internado_estado", p, px_rect(112, 1437, 206, 1459), 10)
    add_date("internado_fecha", p, 262, 1437, widths=(34, 34, 46), h=22, gap=14, font_size=10)
    add_text("uti_estado", p, px_rect(452, 1437, 518, 1459), 10)
    add_text("uti_fecha", p, px_rect(572, 1437, 705, 1459), 10)
    add_text("arm_estado", p, px_rect(760, 1437, 853, 1459), 10)
    add_text("fallecido_estado", p, px_rect(112, 1461, 206, 1483), 10)
    add_date("fallecido_fecha", p, 262, 1461, widths=(34, 34, 46), h=22, gap=14, font_size=10)

    add_yes_no(
        "antecedente_viaje_14_dias",
        p,
        px_rect(378, 1546, 404, 1573),
        px_rect(446, 1546, 472, 1573),
    )
    add_date("viaje_fecha", p, 558, 1547, widths=(34, 34, 46), h=22, gap=14, font_size=10)
    add_text("viaje_lugar", p, px_rect(853, 1547, 1109, 1570), 10)

    add_yes_no(
        "vacunacion_covid_19",
        p,
        px_rect(242, 1579, 268, 1605),
        px_rect(307, 1579, 333, 1605),
    )
    add_date("vacunacion_covid_ultima_dosis", p, 488, 1578, widths=(34, 34, 46), h=22, gap=14, font_size=10)

    add_yes_no(
        "vacunacion_antigripal",
        p,
        px_rect(242, 1612, 268, 1638),
        px_rect(307, 1612, 333, 1638),
    )
    add_date("vacunacion_antigripal_ultima_dosis", p, 488, 1612, widths=(34, 34, 46), h=22, gap=14, font_size=10)

    # Page 2
    p = 1

    add_checkbox("muestra_hisopado_ag", p, pt_rect(166.55, 53.45, 177.85, 64.75))
    add_checkbox("muestra_hisopado_metodos_moleculares", p, pt_rect(373.85, 53.45, 385.15, 64.75))
    add_checkbox("muestra_hisopado_nasal", p, pt_rect(456.85, 53.45, 468.15, 64.75))
    add_checkbox("muestra_saliva", p, pt_rect(505.4, 53.45, 516.7, 64.75))
    add_text("muestra_otros", p, px_rect(99, 164, 502, 187), 10)
    add_date("fecha_toma_muestra", p, 731, 164, widths=(34, 34, 46), h=22, gap=14, font_size=10)

    add_checkbox("no_fue_posible_tomar_muestra", p, pt_rect(186.45, 91.7, 197.75, 103.0))
    add_text("no_toma_muestra_motivo", p, px_rect(551, 191, 1042, 214), 10)
    add_text("no_toma_muestra_detalle", p, px_rect(42, 216, 941, 247), 10, multiline=True)

    add_yes_no(
        "derivado_influenza_ovr",
        p,
        pt_rect(146.6, 119.5, 157.9, 130.8),
        pt_rect(175.75, 119.5, 187.05, 130.8),
    )
    add_date("fecha_derivacion", p, 551, 247, widths=(34, 34, 46), h=22, gap=14, font_size=10)
    add_text("establecimiento_deriva_muestra", p, px_rect(404, 273, 1165, 297), 10)

    classification_rows = [
        ("clasificacion_en_estudio", "clasificacion_influenza_a_positivo", 373, 406),
        ("clasificacion_vsr_positivo", "clasificacion_influenza_b_positivo", 408, 442),
        ("clasificacion_sars_cov2_test_ag", "clasificacion_sars_cov2_molecular_positivo", 444, 479),
        ("clasificacion_ovr_positivo", "clasificacion_codeteccion_virus_respiratorios", 480, 516),
        ("clasificacion_negativo_sars_cov2_ovr", "clasificacion_sars_cov2_molecular_negativo", 517, 552),
    ]
    for left_name, right_name, y1, y2 in classification_rows:
        add_checkbox(left_name, p, px_rect(585, y1, 621, y2))
        add_checkbox(right_name, p, px_rect(1145, y1, 1182, y2))

    add_text("firma_aclaracion_notificador", p, px_rect(118, 620, 700, 660), 11)


if __name__ == "__main__":
    build()
    out = FIELDS_DIR / "pcr_virus_fields.json"
    out.write_text(json.dumps(fields, indent=2), encoding="utf-8")
    print(f"wrote {out} with {len(fields)} fields")
