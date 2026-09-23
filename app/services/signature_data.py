"""Imágenes de firma y ubicaciones verificadas en las plantillas actuales."""
import base64
import binascii
import struct

import fitz
from app.forms.genxpert_fields import FIELDS as GENXPERT_FIELDS

MAX_PNG_BYTES = 2 * 1024 * 1024
SIGNATURE_AREAS = {
    'cisticercosis_planilla_rellenable.pdf': [(1, (423, 703, 544, 739))],
    'SAMO_rellenable.pdf': [(0, (153, 293, 312, 339))],
    'planilla_HIV_carga_viral_CD4_rellenable.pdf': [(0, (368.67, 696, 532, 736.67))],
    'TARV_recetario_rellenable.pdf': [
        (0, (42, 533, 408, 581)), (0, (434.04, 533, 800.04, 581)),
    ],
    'TBC_cultivo_rellenable.pdf': [(0, (463.33, 652.67, 563.33, 688.67))],
    'GenXpert_planilla_rellenable.pdf': [
        (spec['page'], tuple(spec['rect'])) for spec in GENXPERT_FIELDS
        if spec['name'] == 'firma_solicitante'
    ],
    'Hidatidosis ficha epidemiologica_rellenable.pdf': [(1, (296, 442, 542, 520))],
    'orden_de_internacion_rellenable.pdf': [
        (0, (111, 371, 365, 405)),
    ],
    'PCR_virus_respiratorios_planilla_rellenable.pdf': [(1, (57, 320, 390, 400))],
    'film_array_formulario_rellenable.pdf': [(0, (59, 721, 295, 776))],
}


def validate_png(data):
    if len(data) > MAX_PNG_BYTES:
        raise ValueError('La firma PNG debe ocupar como máximo 2 MB.')
    if len(data) < 24 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        raise ValueError('Seleccioná una imagen PNG válida.')
    width, height = struct.unpack('>II', data[16:24])
    if not width or not height or width * height > 16_000_000:
        raise ValueError('La firma debe tener entre 1 y 16 millones de píxeles.')
    try:
        fitz.Pixmap(data)
    except Exception as exc:
        raise ValueError('No se pudo leer la imagen PNG de la firma.') from exc
    return data


def encode_signature(data):
    return base64.b64encode(validate_png(data)).decode('ascii')


def decode_signature(encoded):
    if not encoded:
        return None
    if len(encoded) > ((MAX_PNG_BYTES + 2) // 3) * 4:
        raise ValueError('La firma PNG debe ocupar como máximo 2 MB.')
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError('La firma guardada no es válida.') from exc
    return validate_png(data)
