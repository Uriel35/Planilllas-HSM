import json
import os
from pathlib import Path
import shutil
import tempfile

import fitz
from scripts.form_tools import add_fields


from app.paths import ORIGINALS_DIR, TEMPLATES_DIR, FIELDS_DIR


PDF_W = 595.275
PDF_H = 841.889
IMG_W = 1654
IMG_H = 2339
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


def add_text(name, rect, font_size=9, multiline=False):
    fields.append(
        {
            "type": "text",
            "name": name,
            "page": 0,
            "rect": rect,
            "font_size": font_size,
            "multiline": multiline,
        }
    )


def add_checkbox(name, rect, check_style="check"):
    fields.append(
        {
            "type": "checkbox",
            "name": name,
            "page": 0,
            "rect": rect,
            "check_style": check_style,
        }
    )


def add_copy(prefix, yoff):
    def r(x1, y1, x2, y2):
        return px_rect(x1, y1 + yoff, x2, y2 + yoff)

    def text(name, x1, y1, x2, y2, font_size=9, multiline=False):
        add_text(f"{prefix}_{name}", r(x1, y1, x2, y2), font_size, multiline)

    def cb(name, x1, y1, x2, y2, check_style="check"):
        add_checkbox(f"{prefix}_{name}", r(x1, y1, x2, y2), check_style)

    # Encabezado
    text("fecha", 1236, 106, 1582, 141, 9)

    # Datos del paciente
    text("apellido_y_nombre", 80, 272, 1138, 324, 10)
    text("historia_clinica", 1162, 272, 1582, 324, 10)
    cb("sexo_f", 94, 384, 107, 405)
    cb("sexo_m", 145, 384, 157, 405)
    text("edad", 164, 366, 230, 413, 10)
    text("fecha_nacimiento", 244, 366, 367, 413, 9)
    text("tipo_y_numero_documento", 390, 366, 768, 413, 9)
    text("obra_social_mutual", 792, 366, 1146, 413, 9)
    text("numero_afiliado", 1164, 366, 1582, 413, 9)
    text("domicilio", 80, 453, 1026, 501, 10)
    text("localidad", 1050, 453, 1582, 501, 10)

    # Diagnosticos y seguimiento
    text("servicio_seguimiento", 322, 560, 815, 584, 9)
    text("diagnostico_egreso", 1138, 560, 1584, 584, 9)
    text("diagnostico_principal", 314, 603, 1584, 640, 9)

    # Tipo de ingreso
    cb("ingreso_urgente_no_programado", 834, 693, 870, 729)
    cb("ingreso_programado", 1158, 693, 1194, 729)
    cb("ingreso_derivado", 1484, 693, 1521, 729)

    # Cama: nivel de cuidado requerido
    cb("cama_minimo", 86, 826, 113, 853)
    cb("cama_intermedio", 86, 895, 113, 922)
    cb("cama_intensivo", 86, 960, 113, 987)
    cb("cama_uci_ucim", 386, 948, 405, 971, "circle")
    cb("cama_uco", 486, 948, 505, 971, "circle")
    cb("cama_uacv", 386, 992, 405, 1015, "circle")
    cb("cama_s27", 486, 992, 505, 1015, "circle")

    # Caracteristica de la cama
    cb("aislamiento_si", 806, 824, 821, 849)
    cb("aislamiento_no", 806, 873, 821, 898)
    cb("aislamiento_respiratorio", 1021, 820, 1048, 847)
    cb("aislamiento_contacto", 1021, 849, 1048, 876)
    cb("aislamiento_neutropenico", 1021, 880, 1048, 907)
    cb("aspiracion_si", 806, 944, 821, 969)
    cb("aspiracion_no", 806, 992, 821, 1017)
    cb("oxigeno_si", 1048, 944, 1063, 969)
    cb("oxigeno_no", 1048, 992, 1063, 1017)

    # Tipo de alta
    cb("alta_hospitalaria_medica", 1547, 812, 1574, 839)
    cb("alta_hospitalaria_voluntaria", 1547, 849, 1574, 876)
    text("alta_derivacion", 1270, 884, 1580, 918, 9)
    cb("alta_defuncion", 1278, 962, 1305, 989)
    cb("intervencion_judicial_si", 1574, 944, 1589, 969)
    cb("intervencion_judicial_no", 1574, 992, 1589, 1017)

    # Firmas y sellos
    text("sellos_hospital", 1170, 1096, 1584, 1128, 9)


def build():
    fields.clear()
    add_copy("superior", 0)
    out = FIELDS_DIR / "orden_de_internacion_fields.json"
    out.write_text(json.dumps(fields, indent=2), encoding="utf-8")

    source = ORIGINALS_DIR / "orden_de_internacion.pdf"
    backup = ORIGINALS_DIR / "orden_de_internacion_original.pdf"
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():
        shutil.copy2(source, backup)
    with tempfile.TemporaryDirectory(dir=TEMPLATES_DIR) as temporary:
        blank = Path(temporary) / source.name
        fillable = Path(temporary) / "orden_de_internacion_rellenable.pdf"
        with fitz.open(backup) as doc:
            page = doc[0]
            # Eliminar también la línea divisoria, las imágenes y los trazos.
            page.add_redact_annot(fitz.Rect(0, 418, page.rect.width, page.rect.height))
            page.apply_redactions(images=2, graphics=2)
            doc.save(blank, garbage=4, deflate=True)
        add_fields(str(blank), str(out), str(fillable))
        os.replace(blank, source)
        os.replace(fillable, TEMPLATES_DIR / fillable.name)


if __name__ == "__main__":
    build()
    print(f"Orden de internación: una copia con {len(fields)} campos.")
