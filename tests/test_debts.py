from test_model import model
import unittest

class DebtTests(unittest.TestCase):
    def setUp(self):
        self.data={'deposits':[]}
        model.apply(self.data,'debt_create',{'name':'Кредит','principal':10000000,'remaining':6000000})
        self.debt=self.data['debts'][0]

    def test_payment_reduces_remaining_and_keeps_principal(self):
        model.apply(self.data,'debt_payment',{'debt_id':self.debt['id'],'amount':1000000,'date':'2026-11-08'})
        self.assertEqual(self.debt['remaining'],5000000)
        self.assertEqual(self.debt['principal'],10000000)
        self.assertEqual(self.debt['payments'][0]['amount'],1000000)
        model.apply(self.data,'debt_payment',{'debt_id':self.debt['id'],'amount':5000000,'date':'2026-11-08'})
        self.assertEqual(self.debt['remaining'],0)

    def test_reject_invalid_payment_and_initial_balance(self):
        for value in [0,-1,6000001]:
            with self.assertRaises(ValueError):model.apply(self.data,'debt_payment',{'debt_id':self.debt['id'],'amount':value,'date':'2026-11-08'})
        self.assertEqual(self.debt['remaining'],6000000)
        self.assertEqual(self.debt['payments'],[])
        with self.assertRaises(ValueError):model.apply(self.data,'debt_create',{'name':'Долг','principal':100,'remaining':101})
