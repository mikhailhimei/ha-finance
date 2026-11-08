import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('model', Path(__file__).parents[1] / 'custom_components/ha_finance/model.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)

class FinanceTests(unittest.TestCase):
    def setUp(self):
        self.data = {'deposits': []}
        model.apply(self.data, 'create', {'name': 'Дом', 'principal': 10000000})
        self.deposit = self.data['deposits'][0]
        self.id = self.deposit['id']

    def expense(self, paid=False):
        model.apply(self.data, 'expense_save', {'deposit_id':self.id, 'name':'Ипотека', 'amount':4700000, 'date':'2026-11-08', 'paid':paid})
        return self.deposit['expenses'][0]

    def test_planned_paid_and_unpaid(self):
        e = self.expense()
        self.assertEqual(model.totals(self.deposit), {'principal':10000000,'actual':0,'expected':4700000,'balance':10000000,'available':5300000})
        for paid, balance in [(True,5300000),(True,5300000),(False,10000000)]:
            model.apply(self.data,'expense_paid',{'deposit_id':self.id,'expense_id':e['id'],'paid':paid})
            self.assertEqual(model.totals(self.deposit)['balance'],balance)

    def test_topup_and_principal_edit_preserve_expenses(self):
        self.expense(True)
        model.apply(self.data,'top_up',{'deposit_id':self.id,'amount':1000000})
        self.assertEqual(model.totals(self.deposit)['balance'],6300000)
        model.apply(self.data,'update',{'deposit_id':self.id,'name':'Дом','principal':12000000})
        self.assertEqual(model.totals(self.deposit)['balance'],7300000)

    def test_due_once_and_catchup(self):
        self.expense()
        self.assertEqual(model.due_events(self.data,'2026-11-07'),[])
        events=model.due_events(self.data,'2026-11-09')
        self.assertEqual(events[0]['amount'],47000)
        self.assertEqual(events[0]['expense_name'],'Ипотека')
        self.assertEqual(model.due_events(self.data,'2026-11-10'),[])

    def test_paid_does_not_notify(self):
        self.expense(True)
        self.assertEqual(model.due_events(self.data,'2026-11-08'),[])

    def test_reschedule_notifies_again(self):
        e=self.expense()
        model.due_events(self.data,'2026-11-08')
        model.apply(self.data,'expense_save',{'deposit_id':self.id,'expense_id':e['id'],'name':e['name'],'amount':e['amount'],'date':'2026-11-10','paid':False})
        self.assertEqual(model.due_events(self.data,'2026-11-09'),[])
        self.assertEqual(len(model.due_events(self.data,'2026-11-10')),1)

    def test_validation(self):
        for value in [-1,True,1.5,10**15]:
            with self.assertRaises(ValueError):model.amount(value)
        with self.assertRaises(ValueError):model.label(' ')

    def test_delete_paid_expense_restores_balance(self):
        e=self.expense(True)
        model.apply(self.data,'expense_delete',{'deposit_id':self.id,'expense_id':e['id']})
        self.assertEqual(model.totals(self.deposit)['balance'],10000000)

class IncomeTests(unittest.TestCase):
    setUp = FinanceTests.setUp
    expense = FinanceTests.expense
    def test_income_lifecycle_and_delete(self):
        self.expense(True)
        model.apply(self.data,'expense_save',{'deposit_id':self.id,'name':'Зарплата','amount':2000000,'date':'2026-11-08','paid':False,'kind':'income'})
        income=self.deposit['expenses'][-1]
        self.assertEqual(model.totals(self.deposit)['principal'],10000000)
        self.assertEqual(model.totals(self.deposit)['expected'],0)
        model.apply(self.data,'expense_paid',{'deposit_id':self.id,'expense_id':income['id'],'paid':True})
        self.assertEqual(model.totals(self.deposit)['principal'],12000000)
        self.assertEqual(model.totals(self.deposit)['balance'],7300000)
        model.apply(self.data,'expense_paid',{'deposit_id':self.id,'expense_id':income['id'],'paid':False})
        self.assertEqual(model.totals(self.deposit)['balance'],5300000)
        model.apply(self.data,'expense_paid',{'deposit_id':self.id,'expense_id':income['id'],'paid':True})
        model.apply(self.data,'expense_delete',{'deposit_id':self.id,'expense_id':income['id']})
        self.assertEqual(model.totals(self.deposit)['principal'],10000000)
        self.assertEqual(model.totals(self.deposit)['balance'],5300000)

    def test_income_does_not_fire_expense_reminder(self):
        model.apply(self.data,'expense_save',{'deposit_id':self.id,'name':'Доход','amount':100,'date':'2026-11-08','paid':False,'kind':'income'})
        self.assertEqual(model.due_events(self.data,'2026-11-09'),[])

if __name__=='__main__':unittest.main()
