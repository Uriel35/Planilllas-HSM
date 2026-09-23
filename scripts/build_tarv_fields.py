"""Agrega campos a ambas copias sin alterar el recetario original."""

import fitz

from scripts.build_genxpert_fields import save_atomic
from app.forms.tarv_fields import FIELDS, COPY_OFFSET, SECOND_PREFIX

from app.paths import ORIGINALS_DIR, TEMPLATES_DIR


def build():
    with fitz.open(ORIGINALS_DIR / 'TARV_recetario.pdf') as doc:
        if len(doc) != 1:
            raise ValueError('Se esperaba un recetario TARV de una página.')
        page = doc[0]
        for offset in (0, COPY_OFFSET):
            for spec in FIELDS:
                widget = fitz.Widget()
                widget.field_name = (SECOND_PREFIX if offset else '') + spec['name']
                widget.field_label = spec['label']
                x0, y0, x1, y1 = spec['rect']
                widget.rect = fitz.Rect(x0 + offset, y0, x1 + offset, y1)
                widget.field_type = (fitz.PDF_WIDGET_TYPE_CHECKBOX if spec['type'] == 'checkbox'
                                     else fitz.PDF_WIDGET_TYPE_TEXT)
                widget.text_font = 'Helv'
                widget.text_fontsize = 9
                widget.text_color = (0, 0, 0)
                widget.border_width = 0
                annotation = page.add_widget(widget)
                if spec['type'] == 'signature':
                    doc.xref_set_key(annotation.xref, 'FT', '/Sig')
                    doc.xref_set_key(doc.pdf_catalog(), 'AcroForm/SigFlags', '3')
        save_atomic(doc, TEMPLATES_DIR / 'TARV_recetario_rellenable.pdf')


if __name__ == '__main__':
    build()
