"""Verifica la plantilla, la exportación y los datos compartidos."""
import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz
import app.forms.cisticercosis_fields as c
from app.application import TEMPLATES, generate_pdf, read_fields
from app.services.patient_data import PatientSession
from app.services.professional_data import apply_professional


class CisticercosisTests(unittest.TestCase):
    def test_fields_and_export(self):
        fields = read_fields(TEMPLATES[c.TEMPLATE])
        self.assertEqual(len(fields), len(c.FIELDS))
        self.assertEqual(len({s['name'] for s in c.FIELDS}), len(c.FIELDS))
        values = {s['name']: s['type'] == 'checkbox' or ('12/09/2026' if 'fecha' in s['name'] else 'Dato')
                  for s in c.FIELDS}
        values['paciente_apellido_nombre'] = 'Pérez Ana'
        values['brote_localidad'] = 'La Plata'
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / 'salida.pdf'
            generate_pdf(TEMPLATES[c.TEMPLATE], destination, values)
            with fitz.open(destination) as doc:
                self.assertEqual(len(doc), 2)
                for page in doc:
                    self.assertFalse(list(page.widgets()))
                self.assertIn('Pérez Ana', doc[0].get_text())
                spec = next(s for s in c.FIELDS if s['name'] == 'brote_localidad')
                self.assertIn('La Plata', doc[1].get_text(clip=fitz.Rect(spec['rect'])))
            with fitz.open(TEMPLATES[c.TEMPLATE]) as doc:
                for spec in c.FIELDS:
                    self.assertTrue(doc[spec['page']].rect.contains(fitz.Rect(spec['rect'])))
                self.assertEqual(sum(len(list(p.widgets())) for p in doc), len(c.FIELDS))

    def test_shared_data(self):
        session = PatientSession()
        session.update(c.TEMPLATE, {'paciente_dni': '12345678', 'paciente_apellido_nombre:surname': 'Pérez',
                                    'paciente_apellido_nombre:given_names': 'Ana'}, {})
        toxo = session.apply('Toxoplasmosis — planilla', {})
        self.assertEqual(toxo['DNI'], '12345678')
        self.assertEqual(toxo['Apellido'], 'Pérez')
        result = apply_professional(c.TEMPLATE, {}, dict(surname='García', given_names='Juan', email='medico@example.org'))
        self.assertEqual(result['profesional_apellido_nombre'], 'García Juan')
        self.assertEqual(result['profesional_email'], 'medico@example.org')
