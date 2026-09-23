"""Código compartido y exportación de la solicitud VIH."""
import tempfile
import unittest
from pathlib import Path

import fitz

import app.forms.hiv_fields as hiv
import app.forms.tarv_fields as tarv
from app.application import generate_pdf, read_fields, TEMPLATES
from app.services.patient_data import PatientSession


class HivTests(unittest.TestCase):
    def test_iua_followup_only(self):
        draft = dict(finalidad='finalidad_seguimiento', iua_carga_viral='0012345678', iua_cd4='87654321')
        result = hiv.pdf_values(draft)
        self.assertEqual(result['iua_carga_viral'], 'IUA carga viral: 0012345678')
        self.assertEqual(result['iua_cd4'], 'IUA CD4: 87654321')
        self.assertEqual(draft['iua_carga_viral'], '0012345678')
        diagnostic = hiv.pdf_values(dict(draft, finalidad='finalidad_diagnostico'))
        self.assertEqual(diagnostic['iua_carga_viral'], '')
        self.assertEqual(diagnostic['iua_cd4'], '')
        with self.assertRaises(ValueError):
            hiv.pdf_values(dict(draft, iua_cd4='123ABC'))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'iua.pdf'
            generate_pdf(TEMPLATES[hiv.TEMPLATE], path, draft)
            with fitz.open(path) as doc:
                for key in hiv.IUA_FIELDS.values():
                    spec = next(spec for spec in hiv.FIELDS if spec['name'] == key)
                    self.assertEqual(doc[0].get_text(clip=fitz.Rect(spec['rect'])).strip(), result[key])

    def test_institution_defaults_and_email(self):
        defaults = hiv.apply_defaults({})
        self.assertEqual(defaults['region_sanitaria'], 'XI')
        self.assertEqual(defaults['establecimiento'], 'Hospital San Martin de La Plata')
        self.assertEqual(defaults['servicio_correo'], '')
        for purpose, email in hiv.SERVICE_EMAILS.items():
            values = hiv.pdf_values(dict(finalidad=purpose, servicio_correo='anterior@example.org'))
            self.assertEqual(values['servicio_correo'], email)
            self.assertTrue(values[purpose])
        self.assertEqual(hiv.apply_defaults(dict(establecimiento='Otro hospital'))['establecimiento'],
                         'Otro hospital')

    def test_shared_code(self):
        values = dict(paciente_nombres='María Elena', paciente_apellido='Gómez',
                      paciente_fecha_nacimiento='29/02/2000', paciente_genero_f=True,
                      paciente_genero_m=False, paciente_dni='12345678')
        session = PatientSession()
        session.update(tarv.TEMPLATE, values, {})
        draft = session.apply(hiv.TEMPLATE, {})
        output = hiv.pdf_values(draft)
        self.assertEqual([output[key] for key in hiv.CODE_FIELDS], ['F', 'MA', 'GO', '29022000'])
        self.assertEqual(output['paciente_dni'], '12345678')
        session.update(hiv.TEMPLATE, dict(draft, paciente_nombres='Ana'), draft)
        self.assertEqual(session.apply(tarv.TEMPLATE, {})['paciente_nombres'], 'Ana')
        with self.assertRaises(ValueError):
            hiv.pdf_values(dict(values, paciente_fecha_nacimiento='29/02/2001'))

    def test_export(self):
        source = TEMPLATES[hiv.TEMPLATE]
        self.assertEqual(len(read_fields(source)), len(hiv.FIELDS))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'prueba.pdf'
            generate_pdf(source, path, dict(paciente_nombres='Juan', paciente_apellido='Pérez',
                         paciente_fecha_nacimiento='03/07/1985', paciente_genero_m=True,
                         finalidad='finalidad_diagnostico', gestante='gestante_no',
                         carga_viral=True, cd4_cd8=True))
            with fitz.open(path) as doc:
                self.assertEqual(len(doc), 1)
                self.assertFalse(list(doc[0].widgets()))
                for name, expected in zip(hiv.CODE_FIELDS, ('M', 'JU', 'PE', '03071985')):
                    spec = next(spec for spec in hiv.FIELDS if spec['name'] == name)
                    self.assertEqual(doc[0].get_text(clip=fitz.Rect(spec['rect'])).strip(), expected)
            with fitz.open(source) as doc:
                for widget in doc[0].widgets():
                    self.assertTrue(doc[0].rect.contains(widget.rect))
        result = hiv.pdf_values(dict(finalidad='finalidad_seguimiento', gestante='gestante_no'))
        self.assertTrue(result['finalidad_seguimiento'])
        self.assertFalse(result['finalidad_diagnostico'])
        self.assertTrue(result['gestante_no'])
        self.assertFalse(result['gestante_si'])


if __name__ == '__main__':
    unittest.main()
