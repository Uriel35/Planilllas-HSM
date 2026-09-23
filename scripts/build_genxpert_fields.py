"""Crea GenXpert en una hoja, con el resumen clínico en lugar del pie institucional."""
from pathlib import Path
import os
import shutil
import tempfile

import fitz
from app.forms.genxpert_fields import FIELDS, FORM_Y_SCALE

from app.paths import ORIGINALS_DIR, TEMPLATES_DIR


def save_atomic(doc, path):
    fd, temporary = tempfile.mkstemp(suffix='.pdf', dir=path.parent)
    os.close(fd)
    try:
        doc.save(temporary, garbage=4, deflate=True)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def build():
    source = ORIGINALS_DIR / 'GenXpert_planilla.pdf'
    backup = ORIGINALS_DIR / 'GenXpert_planilla_original.pdf'
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():
        shutil.copy2(source, backup)
    # Partir siempre del respaldo evita compactar otra vez al regenerar.
    with fitz.open(backup) as original, fitz.open() as doc:
        first = original[0]
        first.add_redact_annot(fitz.Rect(0, 758, first.rect.width, first.rect.height))
        first.apply_redactions()
        page = doc.new_page(width=first.rect.width, height=first.rect.height)
        page.show_pdf_page(fitz.Rect(0, 0, first.rect.width, first.rect.height * FORM_Y_SCALE),
                           original, 0, keep_proportion=False)
        page.draw_rect(fitz.Rect(64, 680, 533, 780), color=(0.5, 0.5, 0.5), width=0.6)
        page.insert_textbox(fitz.Rect(68, 681, 529, 700),
                            'Resumen de historia clínica', fontname='hebo', fontsize=10,
                            align=fitz.TEXT_ALIGN_CENTER)
        save_atomic(doc, source)
        for spec in FIELDS:
            widget = fitz.Widget()
            widget.field_name = spec['name']
            widget.field_label = spec['label']
            widget.rect = fitz.Rect(spec['rect'])
            widget.field_type = {'text': fitz.PDF_WIDGET_TYPE_TEXT,
                                 'checkbox': fitz.PDF_WIDGET_TYPE_CHECKBOX,
                                 'signature': fitz.PDF_WIDGET_TYPE_TEXT}[spec['type']]
            widget.field_flags = 4096 if spec['multiline'] else 0
            widget.text_font = 'Helv'
            widget.text_fontsize = 9
            widget.text_color = (0, 0, 0)
            widget.border_width = 0
            page = doc[spec['page']]
            annotation = page.add_widget(widget)
            if spec['type'] == 'signature':
                # Evitar un fallo de add_widget(SIGNATURE) en la versión instalada.
                doc.xref_set_key(annotation.xref, 'FT', '/Sig')
                doc.xref_set_key(doc.pdf_catalog(), 'AcroForm/SigFlags', '3')
        save_atomic(doc, TEMPLATES_DIR / 'GenXpert_planilla_rellenable.pdf')


if __name__ == '__main__':
    build()
