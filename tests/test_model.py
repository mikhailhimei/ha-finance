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

    def test_delete_paid_expense_preserves_spending(self):
        e=self.expense(True)
        model.apply(self.data,'expense_delete',{'deposit_id':self.id,'expense_id':e['id']})
        self.assertEqual(model.totals(self.deposit), {'principal':5300000,'actual':0,'expected':0,'balance':5300000,'available':5300000})
        self.assertEqual(self.deposit['expenses'],[])
        with self.assertRaises(ValueError):
            model.apply(self.data,'expense_delete',{'deposit_id':self.id,'expense_id':e['id']})
        self.assertEqual(model.totals(self.deposit)['balance'],5300000)

    def test_delete_expense_paid_from_income_with_other_plans(self):
        self.deposit['principal']=0
        model.apply(self.data,'expense_save',{'deposit_id':self.id,'kind':'income','name':'Доход','amount':10000000,'date':'2026-11-08','paid':True})
        self.expense(True)
        paid=self.deposit['expenses'][-1]
        self.expense(False)
        before=model.totals(self.deposit)
        model.apply(self.data,'expense_delete',{'deposit_id':self.id,'expense_id':paid['id']})
        after=model.totals(self.deposit)
        self.assertEqual(after['principal'],5300000)
        self.assertEqual(after['balance'],before['balance'])
        self.assertEqual(after['available'],before['available'])
        self.assertEqual(after['expected'],before['expected'])

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

class WorkerTests(unittest.TestCase):
    def test_create_and_update_preserve_deposits(self):
        data={"deposits": []}
        payload={"name":"Иван", "income":10000000, "employment":"TK", "advance_day":25, "salary_day":10}
        model.apply(data,"worker_save",payload)
        self.assertEqual(data["workers"][0]["income"],10000000)
        model.apply(data,"worker_save",{**payload,"worker_id":data["workers"][0]["id"],"income":12000000})
        self.assertEqual(len(data["workers"]),1)
        self.assertEqual(data["workers"][0]["income"],12000000)
        self.assertEqual(data["deposits"],[])

    def test_fixed_income_and_type_switch(self):
        data={'deposits':[]}
        payload={'name':'Аренда','income':3000000,'employment':'fixed','fixed_day':10}
        model.apply(data,'worker_save',payload)
        worker=data['workers'][0]
        self.assertEqual(worker['fixed_day'],10)
        self.assertNotIn('salary_day',worker)
        model.apply(data,'worker_save',{**payload,'worker_id':worker['id'],'employment':'TK','advance_day':29,'salary_day':14})
        self.assertNotIn('fixed_day',worker)
        self.assertEqual(worker['salary_day'],14)
        with self.assertRaises(ValueError):model.apply(data,'worker_save',{**payload,'fixed_day':32})

    def test_worker_delete(self):
        data={'deposits':[], 'workers':[{'id':'one'},{'id':'two'}]}
        model.apply(data,'worker_delete',{'worker_id':'one'})
        self.assertEqual(data['workers'],[{'id':'two'}])
        with self.assertRaises(ValueError):model.apply(data,'worker_delete',{'worker_id':'missing'})

    def test_invalid_days_and_type(self):
        payload={"name":"Иван", "income":100, "employment":"TK", "advance_day":25, "salary_day":10}
        for values in [{"advance_day":0},{"salary_day":32},{"salary_day":1.5},{"advance_day":True},{"employment":"other"}]:
            with self.assertRaises(ValueError):model.apply({"deposits":[]},"worker_save",{**payload,**values})

if __name__=='__main__':unittest.main()
