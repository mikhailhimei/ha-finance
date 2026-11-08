from copy import deepcopy
from test_model import model
from test_payroll import payroll
import unittest

class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.data={'deposits':[]}
        self.rule=deepcopy(payroll.export_calendar(2030))
        self.rule['confirmed']=True
        self.rule['days_off'].append('2030-06-14')
        self.rule['days_off'].remove('2030-06-22')
        self.rule['working_days'].append('2030-06-22')

    def test_import_changes_payment_dates_and_salary_split(self):
        model.apply(self.data,'calendar_import',{'calendar':self.rule})
        overrides=self.data['calendar_overrides']
        fixed=payroll.calculate({'employment':'fixed','income':10000,'fixed_day':14},2030,6,overrides)
        self.assertEqual(fixed['payment_date'],'2030-06-13')
        self.assertFalse(fixed['calendar_provisional'])
        worker={'income':10000000,'salary_day':14,'advance_day':29}
        base=payroll.calculate(worker,2030,6)
        custom=payroll.calculate(worker,2030,6,overrides)
        self.assertLess(custom['advance'],base['advance'])
        self.assertIn('2030-06-22',payroll.workdays_for_year(2030,overrides))
        self.assertNotIn('2030-06-14',payroll.workdays_for_year(2030,overrides))
        self.assertEqual(payroll.export_calendar(2030,overrides)['confirmed'],True)
        model.apply(self.data,'calendar_reset',{'year':2030})
        self.assertTrue(payroll.calculate(worker,2030,6,self.data['calendar_overrides'])['calendar_provisional'])

    def test_validation_and_atomic_import(self):
        invalid=[{**self.rule,'year':2101},{**self.rule,'days_off':['2031-01-01']},{**self.rule,'days_off':[]},{**self.rule,'working_days':['2030-01-01']},{**self.rule,'days_off':self.rule['days_off']+['2030-06-14']},{**self.rule,'confirmed':'true'}]
        for rule in invalid:
            with self.assertRaises(ValueError):model.apply(self.data,'calendar_import',{'calendar':rule})
        self.assertNotIn('calendar_overrides',self.data)

    def test_export_roundtrip_preserves_calendar(self):
        for year in (2026,2027,2030):
            original=payroll.export_calendar(year)
            model.apply(self.data,'calendar_import',{'calendar':original})
            self.assertEqual(payroll.workdays_for_year(year),payroll.workdays_for_year(year,self.data['calendar_overrides']))
