"""Genera una copia rellenable sin modificar la planilla original."""
import pymupdf as fitz
from app.forms.cisticercosis_fields import FIELDS

from app.paths import ORIGINALS_DIR, TEMPLATES_DIR


def build(destination=None):
    destination = destination or TEMPLATES_DIR / 'cisticercosis_planilla_rellenable.pdf'
    with fitz.open(ORIGINALS_DIR / 'cisticercosis_planilla.pdf') as doc:
        for spec in FIELDS:
            widget = fitz.Widget()
            widget.field_name = spec['name']
            widget.rect = fitz.Rect(spec['rect'])
            widget.field_type = (fitz.PDF_WIDGET_TYPE_CHECKBOX if spec['type'] == 'checkbox'
                                 else fitz.PDF_WIDGET_TYPE_TEXT)
            widget.field_flags = 4096 if spec['multiline'] else 0
            widget.text_font = 'Helv'
            widget.text_fontsize = 9
            doc[spec['page']].add_widget(widget)
        doc.save(destination, garbage=4, deflate=True)
    return destination


if __name__ == '__main__':
    print(build())
