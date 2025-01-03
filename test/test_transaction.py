# -*- coding: utf-8 -*-
# pylint: disable=r0904, c0415, c0413, r0913, w0212
""" unittests for dkb_robo """
import sys
import os
from datetime import date
import unittest
import logging
import json
from unittest.mock import patch, Mock, MagicMock, mock_open
from bs4 import BeautifulSoup
from mechanicalsoup import LinkNotFoundError
import io
sys.path.insert(0, '.')
sys.path.insert(0, '..')
from dkb_robo.transaction import Transactions, AccountTransaction, CreditCardTransaction, DepotTransaction

def json_load(fname):
    """ simple json load """

    with open(fname, 'r', encoding='utf8') as myfile:
        data_dic = json.load(myfile)

    return data_dic


class TestTransactions(unittest.TestCase):
    """ Transactions test class """

    @patch("requests.Session")
    def setUp(self, mock_session):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.transaction = Transactions(client=mock_session)

    def test_001__fetch(self):
        """ test Transactions._fetch() returning error """
        self.transaction.client = Mock()
        self.transaction.client.get.return_value.status_code = 400
        self.transaction.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual({'data': [], 'included': []}, self.transaction._fetch('transaction_url'))
        self.assertIn('ERROR:dkb_robo.transaction:fetch transactions: http status code is not 200 but 400', lcm.output)

    def test_002__fetch(self):
        """ test _get_transaction_list() with wrong response"""
        self.transaction.client = Mock()
        self.transaction.client.get.return_value.status_code = 200
        self.transaction.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'data': [], 'included': []}, self.transaction._fetch('transaction_url'))

    def test_003__fetch(self):
        """ test _get_transaction_list() without pagination """
        self.transaction.client = Mock()
        self.transaction.client.get.return_value.status_code = 200
        self.transaction.client.get.return_value.json.return_value = {'data': [{'foo1': 'bar1'}, {'foo2': 'bar2'}]}
        self.assertEqual({'data': [{'foo1': 'bar1'}, {'foo2': 'bar2'}], 'included': []}, self.transaction._fetch('transaction_url'))

    def test_004__fetch(self):
        """ test _get_transaction_list()"""
        self.transaction.client = Mock()
        self.transaction.client.get.return_value.status_code = 200
        self.transaction.client.get.return_value.json.side_effect = [{'data': [{'foo1': 'bar1'}, {'foo2': 'bar2'}], 'links': {'next': 'next_url'}}, {'data': [{'foo3': 'bar3'}, {'foo4': 'bar4'}], 'links': {'foo': 'bar'}}]
        self.assertEqual({'data': [{'foo1': 'bar1'}, {'foo2': 'bar2'}, {'foo3': 'bar3'}, {'foo4': 'bar4'}], 'included': []}, self.transaction._fetch('transaction_url'))

    def test_005__fetch(self):
        """ test _get_transaction_list() with pagination """
        self.transaction.client = Mock()
        self.transaction.client.get.return_value.status_code = 200
        self.transaction.client.get.return_value.json.side_effect = [{'data': [{'foo1': 'bar1'}, {'foo2': 'bar2'}], 'links': {'next': 'next_url'}, 'included': ['1']}, {'data': [{'foo3': 'bar3'}, {'foo4': 'bar4'}], 'links': {'foo': 'bar'}, 'included': ['2']}]
        self.assertEqual({'data': [{'foo1': 'bar1'}, {'foo2': 'bar2'}, {'foo3': 'bar3'}, {'foo4': 'bar4'}], 'included': ['1', '2']}, self.transaction._fetch('transaction_url'))

    def test_006__filter(self):
        """ test _filter() with empty transaction list """
        transaction_list = []
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        self.assertFalse(self.transaction._filter(transaction_list, from_date, to_date, 'trtype'))

    def test_007__filter(self):
        """ test _filter() with a single transaction """
        transaction_list = [{'foo': 'bar', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo': 'bar', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.transaction._filter(transaction_list, from_date, to_date, 'trtype'))

    def test_008__filter(self):
        """ test _filter_transactions() with two transactions """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.transaction._filter(transaction_list, from_date, to_date, 'trtype'))

    def test_009__filter(self):
        """ test _filter_transactions() with two transactions but only one is in range """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-02-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.transaction._filter(transaction_list, from_date, to_date, 'trtype'))

    def test_010__filter(self):
        """ test _filter_transactions() with two transaction but only one is the right type """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype2', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.transaction._filter(transaction_list, from_date, to_date, 'trtype'))

    def test_011__filter(self):
        """ test _filter_transactions() with two transaction check for booked status """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'booked', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'pending', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'booked', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.transaction._filter(transaction_list, from_date, to_date, 'booked'))

    def test_012__filter(self):
        """ test _filter_transactions() with two transactions check for pending status """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'booked', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'pending', 'bookingDate': '2023-01-15'}}]
        from_date = '2023-01-01'
        to_date = '2023-01-31'
        result = [{'foo2': 'bar2', 'attributes': {'status': 'pending', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.transaction._filter(transaction_list, from_date, to_date, 'pending'))

    def test_013__filter(self):
        """ test _filter_transactions() with two transactions check for reserved status """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'booked', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'pending', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo2': 'bar2', 'attributes': {'status': 'pending', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.transaction._filter(transaction_list, from_date, to_date, 'reserved'))

    @patch('dkb_robo.transaction.DepotTransaction.format')
    @patch('dkb_robo.transaction.CreditCardTransaction.format')
    @patch('dkb_robo.transaction.AccountTransaction.format')
    @patch('dkb_robo.transaction.Transactions._filter')
    @patch('dkb_robo.transaction.Transactions._fetch')
    def test_014_get(self, mock_fetch, mock_filter, mock_aformat, mock_creditformat, mock_depotformat):
        "" " test get() for acount transactions """
        mock_aformat.return_value = 'mock_aformat'
        mock_creditformat.return_value = 'mock_creditformat'
        mock_depotformat.return_value = ['mock_depotformat']
        mock_filter.return_value = ['mock_filter']
        self.assertEqual(['mock_aformat'], self.transaction.get('transaction_url', 'account', 'from_date', 'to_date'))
        self.assertTrue(mock_fetch.called)
        self.assertTrue(mock_filter.called)
        self.assertTrue(mock_aformat.called)
        self.assertFalse(mock_creditformat.called)
        self.assertFalse(mock_depotformat.called)

    @patch('dkb_robo.transaction.DepotTransaction.format')
    @patch('dkb_robo.transaction.CreditCardTransaction.format')
    @patch('dkb_robo.transaction.AccountTransaction.format')
    @patch('dkb_robo.transaction.Transactions._filter')
    @patch('dkb_robo.transaction.Transactions._fetch')
    def test_015_get(self, mock_fetch, mock_filter, mock_aformat, mock_creditformat, mock_depotformat):
        "" " test get() for creaditcard transactions """
        mock_aformat.return_value = 'mock_aformat'
        mock_creditformat.return_value = 'mock_creditformat'
        mock_depotformat.return_value = ['mock_depotformat']
        mock_filter.return_value = ['mock_filter']
        self.assertEqual(['mock_creditformat'], self.transaction.get('transaction_url', 'creditcard', 'from_date', 'to_date'))
        self.assertTrue(mock_fetch.called)
        self.assertTrue(mock_filter.called)
        self.assertFalse(mock_aformat.called)
        self.assertTrue(mock_creditformat.called)
        self.assertFalse(mock_depotformat.called)

    @patch('dkb_robo.transaction.DepotTransaction.format')
    @patch('dkb_robo.transaction.CreditCardTransaction.format')
    @patch('dkb_robo.transaction.AccountTransaction.format')
    @patch('dkb_robo.transaction.Transactions._filter')
    @patch('dkb_robo.transaction.Transactions._fetch')
    def test_016_get(self, mock_fetch, mock_filter, mock_aformat, mock_creditformat, mock_depotformat):
        "" " test get() for creaditcard transactions """
        mock_aformat.return_value = 'mock_aformat'
        mock_creditformat.return_value = 'mock_creditformat'
        mock_depotformat.return_value = ['mock_depotformat']
        mock_filter.return_value = ['mock_filter']
        self.assertEqual(['mock_depotformat'], self.transaction.get('transaction_url', 'depot', 'from_date', 'to_date'))
        self.assertTrue(mock_fetch.called)
        self.assertFalse(mock_filter.called)
        self.assertFalse(mock_aformat.called)
        self.assertFalse(mock_creditformat.called)
        self.assertTrue(mock_depotformat.called)

    @patch('dkb_robo.transaction.DepotTransaction.format')
    @patch('dkb_robo.transaction.CreditCardTransaction.format')
    @patch('dkb_robo.transaction.AccountTransaction.format')
    @patch('dkb_robo.transaction.Transactions._filter')
    @patch('dkb_robo.transaction.Transactions._fetch')
    def test_017_get(self, mock_fetch, mock_filter, mock_aformat, mock_creditformat, mock_depotformat):
        "" " test get() for creaditcard transactions """
        mock_aformat.return_value = 'mock_aformat'
        mock_creditformat.return_value = 'mock_creditformat'
        mock_depotformat.return_value = ['mock_depotformat']
        mock_filter.return_value = ['mock_filter']
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.transaction.get('transaction_url', 'unknown', 'from_date', 'to_date'))
        self.assertEqual('transaction type unknown is not supported', str(err.exception))
        self.assertTrue(mock_fetch.called)
        self.assertFalse(mock_filter.called)
        self.assertFalse(mock_aformat.called)
        self.assertFalse(mock_creditformat.called)
        self.assertFalse(mock_depotformat.called)

class TestAccountTransaction(unittest.TestCase):
    """ AccountTransaction test class """

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.account_transaction = AccountTransaction()

    def test_001__debitorinfo(self):
        """ test _debitorinfo complete """
        transaction = {'attributes': {'debtor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}}}
        self.assertEqual({'peeraccount': 'iban', 'peerbic': 'bic', 'peerid': 'id', 'peer': 'name'}, self.account_transaction._debitorinfo(transaction))

    def test_002__debitorinfo(self):
        """ test _debitorinfo with intermediaryName and name """
        transaction = {'attributes': {'debtor': {'id': 'id', 'intermediaryName': 'intermediaryName', 'name': 'name', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}}}
        self.assertEqual({'peeraccount': 'iban', 'peerbic': 'bic', 'peerid': 'id', 'peer': 'intermediaryName'}, self.account_transaction._debitorinfo(transaction))

    def test_003__debitorinfo(self):
        """ test _debitorinfo no id field"""
        transaction = {'attributes': {'debtor': {'name': 'name', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}}}
        self.assertEqual({'peeraccount': 'iban', 'peerbic': 'bic', 'peerid': None, 'peer': 'name'}, self.account_transaction._debitorinfo(transaction))

    def test_004__debitorinfo(self):
        """ test _debitorinfo empty id field"""
        transaction = {'attributes': {'debtor': {'id': None, 'name': 'name', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}}}
        self.assertEqual({'peeraccount': 'iban', 'peerbic': 'bic', 'peerid': None, 'peer': 'name'}, self.account_transaction._debitorinfo(transaction))

    def test_005__creditorinfo(self):
        """ test _creditorinfo complete """
        transaction = {'attributes': {'creditor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}}}
        self.assertEqual({'peeraccount': 'iban', 'peerbic': 'bic', 'peerid': 'id', 'peer': 'name'}, self.account_transaction._creditorinfo(transaction))

    def test_006__creditorinfo(self):
        """ test _creditorinfo complete no id field """
        transaction = {'attributes': {'creditor': {'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}}}
        self.assertEqual({'peeraccount': 'iban', 'peerbic': 'bic', 'peerid': None, 'peer': 'name'}, self.account_transaction._creditorinfo(transaction))

    def test_007__creditorinfo(self):
        """ test _creditorinfo empty id field """
        transaction = {'attributes': {'creditor': {'id': None, 'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}}}
        self.assertEqual({'peeraccount': 'iban', 'peerbic': 'bic', 'peerid': None, 'peer': 'name'}, self.account_transaction._creditorinfo(transaction))

    def test_008__details(self):
        """ test _details() complete """
        transaction = {'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'mandateId':'mandateId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'creditor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}, 'amount': {'value': -1000, 'currencyCode': 'currencyCode'}}}
        result = {'amount': -1000.0, 'currencycode': 'currencyCode', 'date': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'mandateId': 'mandateId', 'postingtext': 'transactionType', 'reasonforpayment': 'description'}
        self.assertEqual(result, self.account_transaction._details(transaction))

    def test_009__details(self):
        """ test _details() no mandateid """
        transaction = {'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'creditor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}, 'amount': {'value': -1000, 'currencyCode': 'currencyCode'}}}
        result = {'amount': -1000.0, 'currencycode': 'currencyCode', 'date': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'mandateId': None, 'postingtext': 'transactionType', 'reasonforpayment': 'description'}
        self.assertEqual(result, self.account_transaction._details(transaction))

    def test_010__details(self):
        """ test _details() empty mandateid """
        transaction = {'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'mandateId': None, 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'creditor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}, 'amount': {'value': -1000, 'currencyCode': 'currencyCode'}}}
        result = {'amount': -1000.0, 'currencycode': 'currencyCode', 'date': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'mandateId': None, 'postingtext': 'transactionType', 'reasonforpayment': 'description'}
        self.assertEqual(result, self.account_transaction._details(transaction))

    def test_011__details(self):
        """ test _details() amount covertion error """
        transaction = {'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'mandateId':'mandateId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'creditor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}, 'amount': {'value': 'aa', 'currencyCode': 'currencyCode'}}}
        result = {'amount': None, 'currencycode': 'currencyCode', 'date': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'mandateId': 'mandateId', 'postingtext': 'transactionType', 'reasonforpayment': 'description'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(result, self.account_transaction._details(transaction))
        self.assertIn("ERROR:dkb_robo.transaction:amount conversion error: could not convert string to float: 'aa'", lcm.output)

    def test_012_format(self):
        """ test format() e2e for creditor transaction"""
        transaction = {'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'creditor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}, 'amount': {'value': -1000, 'currencyCode': 'currencyCode'}}}
        result = {'amount': -1000.0, 'currencycode': 'currencyCode', 'date': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'mandateId': None, 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'peeraccount': 'iban', 'peerbic': 'bic', 'peerid': 'id', 'peer': 'name', 'text': 'transactionType name description'}
        self.assertEqual(result, self.account_transaction.format(transaction))

    def test_013_format(self):
        """ test format() e2e for debitor transaction"""
        transaction = {'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'debtor': {'intermediaryName': 'intermediaryName', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}, 'amount': {'value': 1000, 'currencyCode': 'currencyCode'}}}
        result = {'amount': 1000.0, 'currencycode': 'currencyCode', 'date': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'mandateId': None, 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'peeraccount': 'iban', 'peerbic': 'bic', 'peerid': None, 'peer': 'intermediaryName', 'text': 'transactionType intermediaryName description'}
        self.assertEqual(result, self.account_transaction.format(transaction))

    def test_014_format(self):
        """ test format() empty list """
        transaction = {'foo': 'bar'}
        self.assertFalse(self.account_transaction.format(transaction))

class TestCreditCardTransaction(unittest.TestCase):
    """ AccountTransaction test class """

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.card_transaction = CreditCardTransaction()

    def test_001_format(self):
        """ test format() with empty transaction """
        transaction = {'foo': 'bar'}
        self.assertFalse(self.card_transaction.format(transaction))

    @patch('dkb_robo.transaction.CreditCardTransaction._details')
    def test_002_format(self, mock_det):
        """ test format() with empty transaction """
        transaction = {'attributes': {'foo': 'bar'}}
        mock_det.return_value = 'mock_det'
        self.assertEqual('mock_det', self.card_transaction.format(transaction))

    def test_003__details(self):
        """ test _details() with empty dictionary() """
        transaction_list = {}
        self.assertFalse(self.card_transaction._details(transaction_list))

    def test_004__details(self):
        """ test _details() complete """
        transaction_list = {'foo':'bar', 'attributes': {'description': 'description', 'bookingDate': '2023-01-01', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}
        result = {'amount': 1000.0, 'currencycode': 'CC', 'bdate': '2023-01-01', 'vdate': '2023-01-01', 'text': 'description'}
        self.assertEqual(result, self.card_transaction._details(transaction_list))

    def test_005__details(self):
        """ test _details() no description """
        transaction_list = {'foo':'bar', 'attributes': {'bookingDate': '2023-01-01', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}
        result = {'amount': 1000.0, 'currencycode': 'CC', 'bdate': '2023-01-01', 'vdate': '2023-01-01', 'text': None}
        self.assertEqual(result, self.card_transaction._details(transaction_list))

    def test_006__details(self):
        """ test _details() complete """
        transaction_list = {'foo':'bar', 'attributes': {'description': None, 'bookingDate': '2023-01-01', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}
        result = {'amount': 1000.0, 'currencycode': 'CC', 'bdate': '2023-01-01', 'vdate': '2023-01-01', 'text': None}
        self.assertEqual(result, self.card_transaction._details(transaction_list))

    def test_007__details(self):
        """ test _details() amount convertion error """
        transaction_list = {'foo':'bar', 'attributes': {'description': 'description', 'bookingDate': '2023-01-01', 'amount': {'value': 'aa', 'currencyCode': 'CC'}}}
        result = {'amount': None, 'currencycode': 'CC', 'bdate': '2023-01-01', 'vdate': '2023-01-01', 'text': 'description'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(result, self.card_transaction._details(transaction_list))
        self.assertIn("ERROR:dkb_robo.transaction:amount conversion error: could not convert string to float: 'aa'", lcm.output)

class TestDepotTransaction(unittest.TestCase):
    """ AccountTransaction test class """

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.depot_transaction = DepotTransaction()

    @patch('dkb_robo.transaction.DepotTransaction._quoteinformation')
    @patch('dkb_robo.transaction.DepotTransaction._instrumentinformation')
    def test_001__details(self, mock_ii, mock_qui):
        """ test _details() - add instrument information """
        mock_ii.return_value = {'mock_ii': 'mock_ii'}
        mock_qui.return_value = {'mock_qui': 'mock_qui'}
        included_list = [{'id': 'inid', 'attributes': {'identifiers': [{'identifier': 'isin', 'value': 'value'}, {'identifier': 'isin', 'value': 'value2'}], 'name': {'short': 'short'}}}]
        data_dic = {'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'inid'}}, 'quote': {'data': {'id': 'quoteid', 'value': 'value'}}}}
        result = {'shares': 1000, 'quantity': 1000.0, 'lastorderdate': '2020-01-01', 'price_euro': 1000, 'mock_ii': 'mock_ii', 'shares_unit': 'unit'}
        self.assertEqual(result, self.depot_transaction._details(data_dic, included_list))
        self.assertTrue(mock_ii.called)
        self.assertFalse(mock_qui.called)

    @patch('dkb_robo.transaction.DepotTransaction._quoteinformation')
    @patch('dkb_robo.transaction.DepotTransaction._instrumentinformation')
    def test_002__details(self, mock_ii, mock_qui):
        """ test _details()  add quote information """
        mock_ii.return_value = {'mock_ii': 'mock_ii'}
        mock_qui.return_value = {'mock_qui': 'mock_qui'}
        included_list = [{'id': 'quoteid', 'attributes': {'identifiers': [{'identifier': 'isin', 'value': 'value'}, {'identifier': 'isin', 'value': 'value2'}], 'name': {'short': 'short'}}}]
        data_dic = {'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'inid'}}, 'quote': {'data': {'id': 'quoteid', 'value': 'value'}}}}
        result = {'shares': 1000, 'quantity': 1000.0, 'lastorderdate': '2020-01-01', 'price_euro': 1000, 'mock_qui': 'mock_qui', 'shares_unit': 'unit'}
        self.assertEqual(result, self.depot_transaction._details(data_dic, included_list))
        self.assertFalse(mock_ii.called)
        self.assertTrue(mock_qui.called)

    @patch('dkb_robo.transaction.DepotTransaction._quoteinformation')
    @patch('dkb_robo.transaction.DepotTransaction._instrumentinformation')
    def test_003__details(self, mock_ii, mock_qui):
        """ test _details()  add instrument and quote information """
        mock_ii.return_value = {'mock_ii': 'mock_ii'}
        mock_qui.return_value = {'mock_qui': 'mock_qui'}
        included_list = [{'id': 'inid', 'attributes': {'identifiers': [{'identifier': 'isin', 'value': 'value'}, {'identifier': 'isin', 'value': 'value2'}], 'name': {'short': 'short'}}}]
        data_dic = {'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'inid'}}, 'quote': {'data': {'id': 'inid', 'value': 'value'}}}}
        result = {'shares': 1000, 'quantity': 1000.0, 'lastorderdate': '2020-01-01', 'price_euro': 1000, 'mock_qui': 'mock_qui', 'mock_ii': 'mock_ii', 'shares_unit': 'unit'}
        self.assertEqual(result, self.depot_transaction._details(data_dic, included_list))
        self.assertTrue(mock_ii.called)
        self.assertTrue(mock_qui.called)

    @patch('dkb_robo.transaction.DepotTransaction._quoteinformation')
    @patch('dkb_robo.transaction.DepotTransaction._instrumentinformation')
    def test_004__details(self, mock_ii, mock_qui):
        """ test _details() - quantity convertion error """
        mock_ii.return_value = {'mock_ii': 'mock_ii'}
        mock_qui.return_value = {'mock_qui': 'mock_qui'}
        included_list = [{'id': 'inid', 'attributes': {'identifiers': [{'identifier': 'isin', 'value': 'value'}, {'identifier': 'isin', 'value': 'value2'}], 'name': {'short': 'short'}}}]
        data_dic = {'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 'aa', 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'inid'}}, 'quote': {'data': {'id': 'quoteid', 'value': 'value'}}}}
        result = {'shares': 'aa', 'quantity': None, 'lastorderdate': '2020-01-01', 'price_euro': 1000, 'mock_ii': 'mock_ii', 'shares_unit': 'unit'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(result, self.depot_transaction._details(data_dic, included_list))
        self.assertIn("ERROR:dkb_robo.transaction:quantity conversion error: could not convert string to float: 'aa'", lcm.output)
        self.assertTrue(mock_ii.called)
        self.assertFalse(mock_qui.called)

    def test_005__instrumentinformation(self):
        """ test _instrumentinformation() complete """
        instrument = {'attributes': {'name': {'short': 'short'}, 'identifiers': [{'identifier': 'isin', 'value': 'value'}, {'identifier': 'isin', 'value': 'value2'}]}}
        self.assertEqual({'text': 'short', 'isin_wkn': 'value'}, self.depot_transaction._instrumentinformation(instrument))

    def test_006__instrumentinformation(self):
        """ test _instrumentinformation() no identifier """
        instrument = {'attributes': {'name': {'short': 'short'}}}
        self.assertEqual({'text': 'short'}, self.depot_transaction._instrumentinformation(instrument))

    def test_007_quoteinformation(self):
        """ test _quoteinformation() complete """
        quote = {'attributes': {'market': 'market', 'price': {'value': 1000, 'currencyCode': 'currencyCode'}}}
        self.assertEqual({'currencycode': 'currencyCode', 'market': 'market', 'price': 1000.0}, self.depot_transaction._quoteinformation(quote))

    def test_008_quoteinformation(self):
        """ test _quoteinformation() error value convert """
        quote = {'attributes': {'market': 'market', 'price': {'value': 'aaa', 'currencyCode': 'currencyCode'}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual({'currencycode': 'currencyCode', 'market': 'market', 'price': None}, self.depot_transaction._quoteinformation(quote))
        self.assertIn("ERROR:dkb_robo.transaction:price conversion error: could not convert string to float: 'aaa'", lcm.output)

    def test_009_format(self):
        """ test _format_brokerage_account() """
        included_list = []
        data_dic = [{'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id'}}, 'quote': {'data': {'id': 'id', 'value': 'value'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000}]
        self.assertEqual(result, self.depot_transaction.format(brokerage_dic))

    def test_010_format(self):
        """ test format() e2e """
        included_list = []
        data_dic = [
            {'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id'}}, 'quote': {'data': {'id': 'id', 'value': 'value'}}}},
            {'attributes': {'performance': {'currentValue': {'value': 2000}}, 'lastOrderDate': '2020-02-01', 'quantity': {'value': 2000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id2'}}, 'quote': {'data': {'id': 'id2', 'value': 'value2'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000}, {'shares': 2000, 'quantity': 2000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-02-01', 'price_euro': 2000}]
        self.assertEqual(result, self.depot_transaction.format(brokerage_dic))

    def test_011_format(self):
        """ test format() e2e """
        included_list = [{'id': 'inid', 'attributes': {'identifiers': [{'identifier': 'isin', 'value': 'value'}, {'identifier': 'isin', 'value': 'value2'}], 'name': {'short': 'short'}}}]
        data_dic = [{'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'inid'}}, 'quote': {'data': {'id': 'quoteid', 'value': 'value'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000, 'text': 'short', 'isin_wkn': 'value'}]
        self.assertEqual(result, self.depot_transaction.format(brokerage_dic))


if __name__ == '__main__':

    unittest.main()
