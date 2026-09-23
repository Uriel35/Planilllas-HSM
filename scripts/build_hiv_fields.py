"""Genera la planilla VIH rellenable sin modificar el documento original."""

import fitz

from scripts.build_genxpert_fields import save_atomic
from app.forms.hiv_fields import FIELDS

from app.paths import ORIGINALS_DIR, TEMPLATES_DIR


def build():
    with fitz.open(ORIGINALS_DIR / 'planilla_HIV_carga_viral_CD4.pdf') as doc:
        if len(doc) != 1:
            raise ValueError('Se esperaba una planilla VIH de una página.')
        page = doc[0]
        for spec in FIELDS:
            widget = fitz.Widget()
            widget.field_name = spec['name']
            widget.field_label = spec['label']
            widget.rect = fitz.Rect(spec['rect'])
            widget.field_type = (fitz.PDF_WIDGET_TYPE_CHECKBOX if spec['type'] == 'checkbox'
                                 else fitz.PDF_WIDGET_TYPE_TEXT)
            widget.field_flags = 4096 if spec['multiline'] else 0
            widget.text_font = 'Helv'
            widget.text_fontsize = 9
            widget.text_color = (0, 0, 0)
            widget.border_width = 0
            annotation = page.add_widget(widget)
            if spec['type'] == 'signature':
                doc.xref_set_key(annotation.xref, 'FT', '/Sig')
                doc.xref_set_key(doc.pdf_catalog(), 'AcroForm/SigFlags', '3')
        save_atomic(doc, TEMPLATES_DIR / 'planilla_HIV_carga_viral_CD4_rellenable.pdf')


if __name__ == '__main__':
    build()
