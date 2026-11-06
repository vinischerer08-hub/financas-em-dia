import os
import tempfile
import unittest
from app import app, init_db


class FinanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        app.config.update(TESTING=True, DATABASE=os.path.join(self.temp.name, 'test.db'))
        init_db()
        self.client = app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def add(self, **changes):
        data = {'description': 'Mercado', 'kind': 'despesa', 'category': 'Alimentação', 'amount': '12.35', 'transaction_date': '2026-11-05'}
        data.update(changes)
        return self.client.post('/transacoes', data=data, follow_redirects=True)

    def test_totals_filter_and_chart(self):
        self.add()
        self.add(description='Salário', kind='receita', category='Salário', amount='100.00')
        page = self.client.get('/?month=2026-11&category=Alimentação').get_data(as_text=True)
        self.assertIn('R$ 100,00', page)
        self.assertIn('R$ 12,35', page)
        self.assertIn('R$ 87,65', page)
        self.assertIn('Mercado', page)
        self.assertNotIn('>Salário</strong>', page)

    def test_edit_and_delete(self):
        self.add()
        response = self.client.post('/transacoes/1/editar', data={'description':'Padaria', 'kind':'despesa', 'category':'Alimentação', 'amount':'20.00', 'transaction_date':'2026-11-06'}, follow_redirects=True)
        self.assertIn('Padaria', response.get_data(as_text=True))
        response = self.client.post('/transacoes/1/excluir', data={'month':'2026-11'}, follow_redirects=True)
        self.assertNotIn('Padaria', response.get_data(as_text=True))
        self.assertIn('R$ 0,00', response.get_data(as_text=True))

    def test_invalid_values_are_rejected(self):
        for amount in ('-1', '0', '1.234', 'NaN', 'Infinity'):
            response = self.add(amount=amount)
            self.assertIn('valor positivo', response.get_data(as_text=True))
        self.assertNotIn('Mercado', self.client.get('/?month=2026-11').get_data(as_text=True))

    def test_unknown_transaction(self):
        self.assertEqual(self.client.get('/transacoes/999/editar').status_code, 404)


if __name__ == '__main__':
    unittest.main()
