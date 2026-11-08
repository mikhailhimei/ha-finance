import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('payroll',Path(__file__).parents[1]/'custom_components/ha_finance/payroll.py')
payroll=importlib.util.module_from_spec(spec)
spec.loader.exec_module(payroll)

class PayrollTests(unittest.TestCase):
    def setUp(self):
        self.worker={'income':10000000,'advance_day':25,'salary_day':10}

    def test_january_holidays_and_split(self):
        result=payroll.calculate(self.worker,2026,1)
        self.assertEqual(result['workdays'],15)
        self.assertEqual(result['first_workdays'],4)
        self.assertEqual(result['advance'],2666667)
        self.assertEqual(result['salary'],7333333)
        self.assertEqual(result['advance_date'],'2026-01-23')
        self.assertEqual(result['salary_date'],'2026-02-10')

    def test_transferred_working_saturday(self):
        self.assertIn('2025-11-01',payroll.WORKDAYS)
        self.assertNotIn('2025-11-03',payroll.WORKDAYS)
        self.assertIn('2027-02-20',payroll.WORKDAYS)
        self.assertNotIn('2026-01-09',payroll.WORKDAYS)

    def test_amounts_sum_exactly_and_february_clamps(self):
        result=payroll.calculate({**self.worker,'income':10000001,'advance_day':31},2026,2)
        self.assertEqual(result['advance']+result['salary'],10000001)
        self.assertEqual(result['advance_date'],'2026-02-27')

    def test_unsupported_calendar_is_explicit(self):
        for year,month in [(2028,1),(2026,13),(2027,12)]:
            with self.assertRaises(ValueError):payroll.calculate(self.worker,year,month)
