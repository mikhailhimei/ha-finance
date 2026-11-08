from test_model import model
from test_payroll import payroll
import unittest

class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.data={'deposits':[],'workers':[{'id':'w','employment':'TK','name':'Миша','income':17400000,'salary_day':14,'advance_day':29},{'id':'f','employment':'fixed','name':'Аренда','income':3000000,'fixed_day':8}]}
        model.apply(self.data,'budget_create',{'month':'2026-11'})
        self.budget=self.data['budgets'][0]
        self.payload={'budget_id':self.budget['id'],'name':'Здоровье','amount':1100000,'comment':'Стоматолог','month':'2026-11','payment_id':'w:salary'}

    def test_schedule_includes_salary_advance_and_fixed(self):
        payments=payroll.budget_schedule(self.data['workers'],2026,11)
        self.assertEqual(len(payments),3)
        self.assertEqual([p['id'] for p in payments],['f:fixed','w:salary','w:advance'])
        self.assertEqual(payments[0]['date'],'2026-11-06')
        self.assertEqual(payments[0]['amount'],3000000)

    def test_expense_create_update_delete_preserves_income(self):
        original=self.data['workers'][0]['income']
        model.apply(self.data,'budget_expense_save',self.payload)
        expense=self.budget['expenses'][0]
        self.assertEqual(expense['comment'],'Стоматолог')
        model.apply(self.data,'budget_expense_save',{**self.payload,'expense_id':expense['id'],'amount':1200000})
        self.assertEqual(len(self.budget['expenses']),1)
        self.assertEqual(expense['amount'],1200000)
        self.assertEqual(self.data['workers'][0]['income'],original)
        model.apply(self.data,'budget_expense_delete',{'budget_id':self.budget['id'],'expense_id':expense['id']})
        self.assertEqual(self.budget['expenses'],[])

    def test_month_title_and_migration_preserve_all_expenses(self):
        self.assertEqual(self.budget['name'],'Ноябрь 2026')
        data={'budgets':[{'id':'old','name':'Дом','expenses':[{'id':'a','month':'2026-10'},{'id':'b','month':'2026-11'}]}]}
        self.assertTrue(model.migrate_budget_months(data,'2026-12'))
        self.assertEqual(len(data['budgets']),2)
        self.assertEqual(data['budgets'][0]['id'],'old')
        self.assertEqual(data['budgets'][1]['name'],'Ноябрь 2026')
        self.assertEqual([e['id'] for b in data['budgets'] for e in b['expenses']],['a','b'])
        self.assertFalse(model.migrate_budget_months(data,'2026-12'))
        with self.assertRaises(ValueError):model.apply(self.data,'budget_expense_save',{**self.payload,'month':'2026-12'})

    def test_delete_whole_budget_preserves_other_data(self):
        model.apply(self.data,'budget_expense_save',self.payload)
        model.apply(self.data,'budget_create',{'month':'2026-12'})
        model.apply(self.data,'budget_delete',{'budget_id':self.budget['id']})
        self.assertEqual(len(self.data['budgets']),1)
        self.assertEqual(self.data['budgets'][0]['month'],'2026-12')
        self.assertEqual(len(self.data['workers']),2)
        with self.assertRaises(ValueError):model.apply(self.data,'budget_delete',{'budget_id':'missing'})

    def test_validation(self):
        for change in [{'amount':-1},{'month':'2026-13'},{'payment_id':'missing'},{'comment':'x'*1001}]:
            with self.assertRaises(ValueError):model.apply(self.data,'budget_expense_save',{**self.payload,**change})
        self.assertEqual(self.budget['expenses'],[])
