"""Verificaciones sin pantalla de selección, borradores y exportación TARV."""
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import Mock

import fitz

from app.application import TEMPLATES, generate_pdf, read_fields
from app.ui.medication_picker import MedicationPicker
from app.services.session_storage import load_session, save_session
from app.services.patient_data import PatientSession
from app.forms.tarv_fields import patient_code
from app.forms.tarv_fields import (FIELDS, MEDICATIONS, MEDICATION_FIELDS, TEMPLATE, search_medications,
                         next_month, pdf_values, prescription_pages, REASONS)


class TarvTests(unittest.TestCase):
    def test_patient_code_and_shared_data(self):
        self.assertEqual(patient_code('Juan Carlos', 'Pérez', '03/07/1985', 'M'), 'MJUPE03071985')
        self.assertEqual(patient_code(' María Elena ', ' Gómez ', '29/02/2000', 'F'), 'FMAGO29022000')
        self.assertEqual(patient_code('', '', '', ''), '')
        for args in [('Ana', 'Pérez', '31/02/2000', 'F'), ('Ana', '', '01/01/2000', 'F')]:
            with self.assertRaises(ValueError):
                patient_code(*args)
        draft = dict(paciente_nombres='Juan Carlos', paciente_apellido='Pérez',
                     paciente_fecha_nacimiento='03/07/1985', paciente_genero_m=True, paciente_genero_f=False)
        session = PatientSession()
        session.update(TEMPLATE, draft, {})
        other = session.apply('Toxoplasmosis — planilla', {})
        self.assertEqual(other['Nombre'], 'Juan Carlos')
        self.assertEqual(other['Apellido'], 'Pérez')
        self.assertEqual(other['Fecha de Nacimiento'], '03/07/1985')
        self.assertTrue(session.apply('GenXpert', {})['paciente_genero_m'])
        pages = prescription_pages(dict(draft, meses='4'))
        for page in pages:
            self.assertEqual(page['paciente_codigo'], 'MJUPE03071985')
            self.assertEqual(page['segunda_paciente_codigo'], 'MJUPE03071985')
            self.assertNotIn('paciente_nombres', page)
        session.update(TEMPLATE, dict(draft, paciente_nombres=''), draft)
        self.assertEqual(session.apply('Toxoplasmosis — planilla', {})['Nombre'], '')

    def test_reason_transitions_and_months(self):
        for reason in REASONS:
            pages = prescription_pages(dict(motivo=reason, fecha_receta='31/01/2028', meses='6'))
            expected = reason if reason == 'excepcion_puco' else 'tratamiento_continuacion'
            self.assertTrue(pages[0][reason])
            self.assertTrue(pages[0]['segunda_' + expected])
            self.assertTrue(pages[1][expected])
            self.assertEqual(pages[0]['segunda_fecha_receta'], '29/02/2028')
            self.assertEqual(pages[1]['fecha_receta'], '31/03/2028')
            self.assertEqual(pages[1]['segunda_fecha_receta'], '30/04/2028')
            for page in pages:
                for prefix in ('', 'segunda_'):
                    self.assertEqual(sum(bool(page.get(prefix + key)) for key in REASONS), 1)
        independent = prescription_pages(dict(son_iguales=False, meses='4', motivo='tratamiento_inicio',
                                              segunda_motivo='excepcion_puco', fecha_receta='31/01/2028',
                                              segunda_fecha_receta='15/02/2028', segunda_med_dolutegravir=True))
        self.assertEqual(independent[1]['segunda_fecha_receta'], '15/04/2028')
        self.assertTrue(independent[1]['segunda_excepcion_puco'])
        self.assertTrue(independent[1]['segunda_med_dolutegravir'])
        with self.assertRaises(ValueError):
            prescription_pages(dict(meses='3'))
        with self.assertRaises(ValueError):
            pdf_values(dict(tratamiento_inicio=True, excepcion_puco=True))

    def test_multi_page_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'recetas.pdf'
            for months in (2, 4, 6, 8, 10, 12):
                generate_pdf(TEMPLATES[TEMPLATE], path, dict(meses=str(months), fecha_receta='31/01/2028',
                                                            motivo='tratamiento_inicio', paciente_dni='12345678'))
                with fitz.open(path) as doc:
                    self.assertEqual(len(doc), months // 2)
                    for index, page in enumerate(doc):
                        self.assertIn(next_month('31/01/2028', index * 2), page.get_text())
                        self.assertIn(next_month('31/01/2028', index * 2 + 1), page.get_text())
                        self.assertEqual(page.get_text().count('12345678'), 2)
                        self.assertFalse(list(page.widgets()))

    def test_calendar_month(self):
        for original, expected in [('31/01/2026', '28/02/2026'), ('31/01/2028', '29/02/2028'),
                                   ('31/12/2026', '31/01/2027'), ('31/03/2026', '30/04/2026'), ('', '')]:
            self.assertEqual(next_month(original), expected)
        with self.assertRaises(ValueError):
            next_month('31/02/2026')

    def test_same_and_independent_prescriptions(self):
        draft = dict(son_iguales=True, fecha_receta='31/01/2026', med_lamivudina_300=True,
                     segunda_fecha_receta='15/03/2026', segunda_med_lamivudina_300=False,
                     segunda_med_dolutegravir=True, otro_1_dosis='Prueba',
                     segunda_otro_1_dosis='Otra dosis', paciente_dni='12345678')
        same = pdf_values(draft)
        self.assertEqual(same['segunda_fecha_receta'], '28/02/2026')
        self.assertTrue(same['segunda_med_lamivudina_300'])
        self.assertFalse(same['segunda_med_dolutegravir'])
        self.assertEqual(same['segunda_otro_1_dosis'], 'Prueba')
        self.assertEqual(draft['segunda_fecha_receta'], '15/03/2026')
        different = pdf_values(dict(draft, son_iguales=False))
        self.assertEqual(different['segunda_fecha_receta'], '15/03/2026')
        self.assertFalse(different['segunda_med_lamivudina_300'])
        self.assertTrue(different['segunda_med_dolutegravir'])
        self.assertEqual(different['segunda_otro_1_dosis'], 'Otra dosis')
        self.assertEqual(different['segunda_paciente_dni'], '12345678')
        self.assertNotIn('son_iguales', different)

    def test_search(self):
        self.assertEqual(search_medications('DARUNAVIR 800')[0][0], 'darunavir_ritonavir_800')
        self.assertEqual(len(search_medications('DOLUTÉGRAVIR')), 5)
        self.assertEqual(search_medications('inexistente'), [])

    def test_replace_remove_and_duplicate(self):
        interpreter = tk.Tcl()
        picker = MedicationPicker.__new__(MedicationPicker)
        picker.controls = {key: tk.BooleanVar(interpreter, False) for key in MEDICATION_FIELDS}
        picker.on_change = Mock()
        picker.cancel = Mock()
        picker.filter = Mock()
        picker.add_button = Mock()
        state = dict(key='', matches=[MEDICATIONS[0]], results=Mock(), frame=Mock())
        state['results'].curselection.return_value = ()
        picker.rows = [state]
        picker.choose(state)
        self.assertTrue(picker.controls['med_lamivudina_300'].get())
        state['matches'] = [MEDICATIONS[1]]
        picker.choose(state)
        self.assertFalse(picker.controls['med_lamivudina_300'].get())
        self.assertTrue(picker.controls['med_abacavir_lamivudina'].get())
        duplicate = dict(key='', matches=[MEDICATIONS[1]], results=Mock())
        duplicate['results'].curselection.return_value = ()
        picker.rows.append(duplicate)
        picker.choose(duplicate)
        self.assertEqual(duplicate['key'], '')
        picker.remove(state)
        self.assertFalse(any(control.get() for control in picker.controls.values()))

    def test_export_and_draft(self):
        template = TEMPLATES[TEMPLATE]
        self.assertEqual(len(read_fields(template)), len(FIELDS) * 2)
        values = {key: True for key in MEDICATION_FIELDS}
        values.update(paciente_dni='12345678', paciente_codigo='PRUEBA', fecha_receta='16/09/2026')
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            data = dict(version=1, patient={}, drafts={TEMPLATE: values}, saved={}, current=TEMPLATE)
            save_session(directory / 'session.json', data)
            self.assertEqual(load_session(directory / 'session.json'), data)
            generate_pdf(template, directory / 'empty.pdf', {})
            generate_pdf(template, directory / 'filled.pdf', values)
            with fitz.open(template) as doc:
                self.assertEqual(len(list(doc[0].widgets())), len(FIELDS) * 2)
                for widget in doc[0].widgets():
                    self.assertTrue(doc[0].rect.contains(widget.rect))
            with fitz.open(directory / 'filled.pdf') as filled, fitz.open(directory / 'empty.pdf') as empty:
                self.assertEqual(filled[0].get_text().count('12345678'), 2)
                self.assertIn('16/10/2026', filled[0].get_text())
                self.assertEqual(filled[0].get_text().count('Firma y sello'), 2)
                self.assertFalse(list(filled[0].widgets()))
                self.assertEqual(len(filled[0].get_drawings()) - len(empty[0].get_drawings()),
                                 2 * len(MEDICATIONS) + 2)  # X y fondos de fecha.


if __name__ == '__main__':
    unittest.main()
