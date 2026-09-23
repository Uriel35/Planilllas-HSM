"""Órdenes independientes, paquetes y protección ante solicitudes demasiado largas."""
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call
from pathlib import Path

import pymupdf as fitz

import app.forms.samo_fields as samo
from app.application import TEMPLATES, apply_form_defaults, generate_pdf, read_fields
from app.services.patient_data import PatientSession
from app.services.professional_data import apply_professional
from app.ui.laboratory_picker import LaboratoryPicker, merge_studies
from app.services.session_storage import save_session, load_session
from app.forms.samo_form import SamoForm


class SamoTests(unittest.TestCase):
    def test_ppd_and_xray_preset(self):
        template = samo.PPD_TEMPLATE
        values = apply_form_defaults(template, {})
        self.assertEqual(values['cantidad_samo'], '2')
        self.assertEqual(values['solicitudes'], 'PPD')
        self.assertEqual(values['samo_2:solicitudes'], 'Rx de torax de frente y perfil')
        self.assertEqual(values['fecha_solicitud'], values['samo_2:fecha_solicitud'])
        values = apply_professional(template, values,
                                    {'surname': 'Uno', 'given_names': 'Dos', 'institution': 'Hospital'})
        self.assertEqual(values['establecimiento'], 'Hospital')
        self.assertEqual(values['samo_2:establecimiento'], 'Hospital')
        patient = PatientSession()
        patient.values = {'dni': '12345678', 'surname': 'Pérez', 'given_names': 'Ana'}
        restored = patient.apply(template, values)
        self.assertEqual(restored['paciente_dni'], '12345678')
        self.assertEqual(restored['paciente_apellido_nombre:surname'], 'Pérez')
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'ppd_rx.pdf'
            generate_pdf(TEMPLATES[template], output, values)
            with fitz.open(output) as doc:
                self.assertEqual(len(doc), 1)
                for index, expected in enumerate(('PPD', 'Rx de torax de frente y perfil')):
                    rect = fitz.Rect(samo.RECTS['solicitudes'][0])
                    offset = index * doc[0].rect.height / 2
                    rect += (0, offset, 0, offset)
                    self.assertEqual(' '.join(doc[0].get_text(clip=rect).split()), expected)
        values['solicitudes'] = ''
        values['samo_2:solicitudes'] = 'Otro estudio'
        self.assertEqual(apply_form_defaults(template, values), values)
        self.assertEqual(samo.order_count(apply_form_defaults(samo.TEMPLATE, {})), 1)

    def test_clear_all_studies(self):
        picker = SimpleNamespace(query=Mock(), value=Mock(), search=Mock(), app=Mock())
        LaboratoryPicker.clear_studies(picker)
        picker.query.set.assert_called_once_with('')
        picker.value.set.assert_called_once_with('')
        picker.app.persist_session.assert_called_once_with()

    def test_studies_in_two_columns_with_serologies_together(self):
        studies = ('Hemograma', 'Hepatograma', 'Urea', 'Creatinina')
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'columnas.pdf'
            for items in (studies, studies + samo.PACKAGES['Serología control de HIV']):
                generate_pdf(TEMPLATES[samo.TEMPLATE], output, {'solicitudes': '; '.join(items)})
                with fitz.open(output) as doc:
                    rect = fitz.Rect(samo.RECTS['solicitudes'][0])
                    middle = (rect.x0 + rect.x1) / 2
                    left = doc[0].get_text(clip=fitz.Rect(rect.x0, rect.y0, middle, rect.y1))
                    right = doc[0].get_text(clip=fitz.Rect(middle, rect.y0, rect.x1, rect.y1))
                    self.assertTrue(left.strip())
                    self.assertTrue(right.strip())
                    for study in studies:
                        self.assertIn(study, (left + right).splitlines())
                    self.assertNotIn(';', left + right)
                    if len(items) > len(studies):
                        self.assertNotIn('Serología', left)
                        self.assertIn('Serología: VDRL,', right)
                        for study in ('HSV-1', 'Chagas', 'EBV'):
                            self.assertIn(study, right)

    def test_shortcuts_select_samo_tabs_directly(self):
        tabs = Mock()
        tabs.tabs.return_value = ('samo1', 'samo2', 'samo3')
        tabs.index.side_effect = (0, 1, 2, 0)
        form = SimpleNamespace(tabs=tabs)
        for direction in (1, 1, 1, -1):
            self.assertEqual(SamoForm.change_tab(form, direction), 'break')
        self.assertEqual(tabs.select.call_args_list,
                         [call('samo2'), call('samo3'), call('samo1'), call('samo3')])
        self.assertEqual(tabs.focus_set.call_count, 4)
        tabs.event_generate.assert_not_called()

    def test_even_counts_fill_both_halves(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'pares.pdf'
            for count in (2, 4):
                with self.subTest(count=count):
                    values = {'cantidad_samo': str(count)}
                    values.update({samo.order_prefix(i) + 'solicitudes': f'Estudio {i + 1}'
                                   for i in range(count)})
                    generate_pdf(TEMPLATES[samo.TEMPLATE], output, values)
                    with fitz.open(output) as doc:
                        self.assertEqual(len(doc), count // 2)
                        for i in range(count):
                            page = doc[i // 2]
                            offset = page.rect.height / 2 if i % 2 else 0
                            rect = fitz.Rect(samo.RECTS['solicitudes'][0]) + (0, offset, 0, offset)
                            self.assertEqual(page.get_text(clip=rect).strip(), f'Estudio {i + 1}')
                            self.assertFalse(list(page.widgets()))

    def test_single_order_and_overflow(self):
        source = TEMPLATES[samo.TEMPLATE]
        original = source.read_bytes()
        self.assertEqual(len(read_fields(source)), len(samo.RECTS))
        values = dict(paciente_apellido_nombre='Pérez Ana', paciente_dni='12345678',
                      solicitudes='Hemograma; Hepatograma; Urea; Creatinina')
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'orden.pdf'
            generate_pdf(source, output, values)
            with fitz.open(output) as doc:
                self.assertEqual(len(doc), 1)
                self.assertFalse(list(doc[0].widgets()))
                bottom = doc[0].get_pixmap(clip=fitz.Rect(0, 421, 595, 841), colorspace=fitz.csGRAY)
                self.assertEqual(set(bottom.samples), {255})
                for key, value in values.items():
                    for rect in samo.RECTS[key]:
                        separator = '' if key in samo.NUMERIC_CELLS else ' '
                        expected = value.replace(';', '') if key == 'solicitudes' else value
                        self.assertEqual(separator.join(doc[0].get_text(clip=fitz.Rect(rect)).split()), expected)
            saved = output.read_bytes()
            with self.assertRaises(ValueError):
                generate_pdf(source, output, dict(values, solicitudes='Hemograma; ' * 500))
            self.assertEqual(output.read_bytes(), saved)
        self.assertEqual(source.read_bytes(), original)

    def test_independent_orders_and_session(self):
        values = {'cantidad_samo': '3', 'paciente_apellido_nombre': 'Paciente Uno',
                  'solicitudes': 'Hemograma', 'samo_2:paciente_apellido_nombre': 'Paciente Dos',
                  'samo_2:solicitudes': 'Urea', 'samo_3:paciente_apellido_nombre': 'Paciente Tres',
                  'samo_3:solicitudes': 'Creatinina'}
        with tempfile.TemporaryDirectory() as folder:
            session = Path(folder) / 'session.json'
            save_session(session, dict(version=1, patient={}, drafts={samo.TEMPLATE: values}, saved={}))
            restored = load_session(session)['drafts'][samo.TEMPLATE]
            self.assertEqual(restored, values)
            output = Path(folder) / 'ordenes.pdf'
            generate_pdf(TEMPLATES[samo.TEMPLATE], output, restored)
            with fitz.open(output) as doc:
                self.assertEqual(len(doc), 2)
                for index, (name, study) in enumerate(zip(('Paciente Uno', 'Paciente Uno', 'Paciente Uno'),
                                                        ('Hemograma', 'Urea', 'Creatinina'))):
                    page = doc[index // 2]
                    offset = page.rect.height / 2 if index % 2 else 0
                    for key, expected in (('paciente_apellido_nombre', name), ('solicitudes', study)):
                        rect = fitz.Rect(samo.RECTS[key][0]) + (0, offset, 0, offset)
                        self.assertEqual(page.get_text(clip=rect).strip(), expected)
                bottom = doc[1].get_pixmap(clip=fitz.Rect(0, doc[1].rect.height / 2, doc[1].rect.width,
                                                       doc[1].rect.height), colorspace=fitz.csGRAY)
                self.assertEqual(set(bottom.samples), {255})
            before = output.read_bytes()
            with self.assertRaises(ValueError):
                generate_pdf(TEMPLATES[samo.TEMPLATE], output, dict(values, **{'samo_3:solicitudes': 'Texto ' * 1000}))
            self.assertEqual(output.read_bytes(), before)

    def test_shared_patient_overrides_old_drafts(self):
        values = {'cantidad_samo': '3', 'solicitudes': 'Hemograma',
                  'samo_2:solicitudes': 'Urea', 'samo_3:solicitudes': 'Creatinina'}
        for key in samo.PATIENT_FIELDS:
            values[key] = key == 'paciente_genero_f' if key in samo.CHECKBOX_FIELDS else 'Dato común'
            values['samo_2:' + key] = 'Dato anterior'
        pages = samo.prescription_pages(values)
        for page in pages:
            for key in samo.PATIENT_FIELDS:
                self.assertEqual(page[key], values[key])
        self.assertEqual([page['solicitudes'] for page in pages], ['Hemograma', 'Urea', 'Creatinina'])
        values['paciente_domicilio'] = ''
        self.assertTrue(all(page['paciente_domicilio'] == '' for page in samo.prescription_pages(values)))

    def test_packages(self):
        self.assertEqual(samo.PACKAGES['Laboratorio general'], ('Hemograma', 'Hepatograma', 'Urea', 'Creatinina'))
        ets = samo.PACKAGES['Serología ETS']
        self.assertEqual(ets, ('Serología HIV', 'VDRL', 'HBV (AgS, Ac-S, Ac-core)', 'HCV'))
        hiv = samo.PACKAGES['Serología control de HIV']
        self.assertEqual(hiv, ('VDRL', 'HBV (AgS, Ac-S, Ac-core)', 'HCV',
                               'HSV-1', 'HSV-2', 'Chagas', 'Toxoplasmosis', 'CMV', 'VZV', 'EBV'))
        merged = merge_studies('Estudio propio; serologia hiv', ets)
        self.assertEqual(merged, 'Estudio propio; serologia hiv; VDRL; HBV (AgS, Ac-S, Ac-core); HCV')
        self.assertEqual(merge_studies(merged, ets), merged)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'paquete.pdf'
            generate_pdf(TEMPLATES[samo.TEMPLATE], output, {'solicitudes': merge_studies('', hiv)})
            with fitz.open(output) as doc:
                actual = ' '.join(doc[0].get_text(clip=fitz.Rect(samo.RECTS['solicitudes'][0])).split())
                self.assertEqual(actual, 'Serología: ' + ', '.join(hiv))

    def test_serology_heading_survives_removing_studies(self):
        studies = list(samo.PACKAGES['Serología control de HIV'])
        while studies:
            text = '; '.join(studies)
            page = samo.prescription_pages({'solicitudes': text})[0]
            self.assertEqual(page['solicitudes'], 'Serología: ' + ', '.join(studies))
            studies.pop(0)
        self.assertEqual(samo.format_studies('Hemograma'), 'Hemograma')
        self.assertEqual(samo.format_studies(''), '')
        self.assertEqual(samo.format_studies('Serología VDRL; HSV-1; Hemograma'),
                         'Hemograma\nSerología: VDRL, HSV-1')
        self.assertEqual(merge_studies('Serología VDRL; Serología HSV-1', ('VDRL', 'HSV-1')),
                         'Serología VDRL; Serología HSV-1')

    def test_digits_centered_and_new_fields(self):
        values = dict(paciente_edad='7', paciente_dni='12.345.678',
                      numero_afiliado='001234567890', consultorio_externo='12',
                      sala='3', cama='24', condicion='B', obra_social='Mutual de ejemplo',
                      paciente_genero_f=True)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'orden.pdf'
            generate_pdf(TEMPLATES[samo.TEMPLATE], output, values)
            with fitz.open(output) as doc:
                page = doc[0]
                for name, count in samo.NUMERIC_CELLS.items():
                    expected = samo.numeric_value(name, values[name])
                    for coords in samo.RECTS[name]:
                        rect = fitz.Rect(coords)
                        chars = [char for block in page.get_text('rawdict', clip=rect)['blocks']
                                 for line in block.get('lines', []) for span in line['spans']
                                 for char in span['chars'] if char['c'].isdigit()]
                        self.assertEqual(''.join(char['c'] for char in chars), expected)
                        offset = count - len(expected) if name == 'paciente_edad' else 0
                        for index, char in enumerate(chars, offset):
                            center = (char['bbox'][0] + char['bbox'][2]) / 2
                            self.assertAlmostEqual(center, rect.x0 + (index + .5) * rect.width / count, places=2)
                for name in ('consultorio_externo', 'sala', 'cama', 'condicion', 'obra_social'):
                    for rect in samo.RECTS[name]:
                        self.assertEqual(page.get_text(clip=fitz.Rect(rect)).strip(), values[name])
                for rect in samo.RECTS['paciente_genero_f']:
                    self.assertTrue(any(fitz.Rect(rect).contains(drawing['rect'])
                                        for drawing in page.get_drawings()))

    def test_invalid_numbers(self):
        for name, value in (('paciente_edad', '100'), ('paciente_dni', '123456789'),
                            ('numero_afiliado', '1234567890123'), ('numero_afiliado', '12A')):
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                samo.numeric_value(name, value)


if __name__ == '__main__':
    unittest.main()
