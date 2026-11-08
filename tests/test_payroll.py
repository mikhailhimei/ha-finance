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
        self.assertEqual(result['salary'],5000000)
        self.assertEqual(result['advance_date'],'2026-01-23')
        self.assertEqual(result['salary_date'],'2025-12-30')

    def test_transferred_working_saturday(self):
        self.assertIn('2025-11-01',payroll.WORKDAYS)
        self.assertNotIn('2025-11-03',payroll.WORKDAYS)
        self.assertIn('2027-02-20',payroll.WORKDAYS)
        self.assertNotIn('2026-01-09',payroll.WORKDAYS)

    def test_amounts_sum_exactly_and_february_clamps(self):
        result=payroll.calculate({**self.worker,'income':10000001,'advance_day':31},2026,2)
        previous=payroll.calculate({**self.worker,'income':10000001},2026,1)
        self.assertEqual(previous['advance']+result['salary'],10000001)
        self.assertEqual(result['advance_date'],'2026-02-27')

    def test_unsupported_calendar_is_explicit(self):
        for year,month in [(2028,1),(2026,13)]:
            with self.assertRaises(ValueError):payroll.calculate(self.worker,year,month)

    def test_december_payment_dates_and_periods(self):
        result=payroll.calculate({**self.worker,'advance_day':29,'salary_day':14},2026,12)
        self.assertEqual(result['salary_date'],'2026-12-14')
        self.assertEqual(result['advance_date'],'2026-12-29')
        self.assertEqual(result['salary_period'],'2026-11')
        self.assertEqual(result['advance_period'],'2026-12')
        self.assertEqual(result['salary'],5500000)
        self.assertEqual(result['advance'],5000000)
        self.assertEqual(payroll.calculate(self.worker,2027,12)['salary_period'],'2027-11')

    def test_migration_preserves_entered_days_once(self):
        data={'workers':[{'advance_day':14,'salary_day':29}]}
        self.assertTrue(payroll.migrate_worker_days(data))
        self.assertEqual(data['workers'][0],{'advance_day':29,'salary_day':14})
        self.assertFalse(payroll.migrate_worker_days(data))
        self.assertEqual(data['workers'][0]['salary_day'],14)

    def test_fixed_income_does_not_prorate(self):
        worker={'employment':'fixed','income':3000000,'fixed_day':14}
        result=payroll.calculate(worker,2026,11)
        self.assertEqual(result,{'kind':'fixed','payment':3000000,'payment_date':'2026-11-13'})
        self.assertEqual(payroll.calculate({**worker,'fixed_day':31},2026,2)['payment_date'],'2026-02-27')
        self.assertEqual(payroll.calculate({**worker,'fixed_day':10},2026,1)['payment_date'],'2025-12-30')
