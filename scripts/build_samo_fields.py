"""Crea una copia rellenable sin modificar SAMO.pdf."""

import pymupdf as fitz

from scripts.build_genxpert_fields import save_atomic
from app.forms.samo_fields import LABELS, RECTS, CHECKBOX_FIELDS

from app.paths import ORIGINALS_DIR, TEMPLATES_DIR


def build():
    with fitz.open(ORIGINALS_DIR / 'SAMO.pdf') as original, fitz.open() as doc:
        if len(original) != 1:
            raise ValueError('Se esperaba una hoja SAMO con dos órdenes.')
        page = doc.new_page(width=original[0].rect.width, height=original[0].rect.height)
        # Importar únicamente la orden superior: la inferior no se imprime.
        clip = fitz.Rect(0, 0, original[0].rect.width, 420)
        page.show_pdf_page(clip, original, 0, clip=clip)
        for name, rects in RECTS.items():
            for rect in rects:
                widget = fitz.Widget()
                widget.field_name = name
                widget.field_label = LABELS[name]
                widget.field_type = (fitz.PDF_WIDGET_TYPE_CHECKBOX if name in CHECKBOX_FIELDS
                                     else fitz.PDF_WIDGET_TYPE_TEXT)
                widget.rect = fitz.Rect(rect)
                widget.field_flags = 4096 if name == 'solicitudes' else 0
                widget.text_font = 'Helv'
                widget.text_fontsize = 9
                widget.text_color = (0, 0, 0)
                widget.border_width = 0
                doc[0].add_widget(widget)
        save_atomic(doc, TEMPLATES_DIR / 'SAMO_rellenable.pdf')


if __name__ == '__main__':
    build()
