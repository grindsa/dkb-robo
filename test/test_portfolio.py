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
from dkb_robo.portfolio import ProductGroup, Account, Card, Depot, Overview

def json_load(fname):
    """ simple json load """

    with open(fname, 'r', encoding='utf8') as myfile:
        data_dic = json.load(myfile)

    return data_dic


class TestProductGroup(unittest.TestCase):
    """ test class """

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')
        self.productgroup = ProductGroup(logger=self.logger)

    def test_001__uid2names(self):
        """ test uid2names one item"""
        data_ele = {'attributes': {'productSettings': {'product': {'uid': {'name': 'name'}}}}}
        self.assertEqual({'uid': 'name'}, self.productgroup._uid2names(data_ele))

    def test_002__uid2names(self):
        """ test uid2names two items """
        data_ele = {'attributes': {'productSettings': {'product1': {'uid1': {'name': 'name1'}}, 'product2': {'uid2': {'name': 'name2'}}}}}
        self.assertEqual({'uid1': 'name1', 'uid2': 'name2'}, self.productgroup._uid2names(data_ele))

    def test_003__uid2names(self):
        """ test uid2names malformed input """
        data_ele = {'attributes': {'foo': 'bar'}}
        self.assertFalse({}, self.productgroup._uid2names(data_ele))

    def test_004__uid2names(self):
        """ test uid2names malformed input """
        data_ele = {'attributes': {'productSettings': {'foo': 'bar'}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse({}, self.productgroup._uid2names(data_ele))
        self.assertIn('WARNING:dkb_robo:uid2name mapping failed. product data are not in dictionary format', lcm.output)

    def test_005__uid2names(self):
        """ test uid2names malformed input """
        data_ele = {'foo': 'bar'}
        self.assertFalse({}, self.productgroup._uid2names(data_ele))

    def test_006__group(self):
        """ test _group() malformed input """
        data_ele = {}
        self.assertFalse(self.productgroup._group(data_ele))

    def test_007__group(self):
        """ test _group() """
        data_ele = {'attributes': {'productGroups': {'foo': {'index': 0, 'name': 'foo', 'products': {'product1': {'uid1': {'index': 1}, 'uid2': {'index': 0}}}}}}}
        self.assertEqual([{'name': 'foo', 'product_list': {1: 'uid1', 0: 'uid2'}}], self.productgroup._group(data_ele))

    def test_008__group(self):
        """ test _group() """
        data_ele = {'attributes':
                    {'productGroups':
                                   {'foo': {'index': 0,
                                            'name': 'foo',
                                            'products': {
                                                'product1': {'uid1': {'index': 1}, 'uid2': {'index': 2}},
                                                'product2': {'uid3': {'index': 0}, 'uid4': {'index': 3}}
                                                }}}}}
        self.assertEqual([{'name': 'foo', 'product_list': {0: 'uid3', 1: 'uid1', 2: 'uid2', 3: 'uid4'}}], self.productgroup._group(data_ele))

    def test_009__group(self):
        """ test _group() """
        data_ele = {'attributes':
                        {'productGroups':
                            {'foo': {'index': 1, 'name': 'foo',
                                    'products': {
                                        'product1': {'uid1': {'index': 1}, 'uid2': {'index': 2}},
                                        'product2': {'uid3': {'index': 0}, 'uid4': {'index': 3}}
                                    }},
                            'bar': {'index': 0, 'name': 'bar',
                                    'products': {
                                        'product1': {'uid4': {'index': 1}, 'uid5': {'index': 2}},
                                        'product2': {'uid6': {'index': 0}, 'uid7': {'index': 3}}
                                    }}

                                    }}}
        result = [{'name': 'bar', 'product_list': {1: 'uid4', 2: 'uid5', 0: 'uid6', 3: 'uid7'}}, {'name': 'foo', 'product_list': {1: 'uid1', 2: 'uid2', 0: 'uid3', 3: 'uid4'}}]
        self.assertEqual(result, self.productgroup._group(data_ele))

    @patch('dkb_robo.portfolio.ProductGroup._group')
    @patch('dkb_robo.portfolio.ProductGroup._uid2names')
    def test_010_map(self, mock_uid2names, mock_group):
        """ test map() """
        data = {'data': {'foo': 'bar'}}
        mock_uid2names.return_value = 'mock_uid2names'
        mock_group.return_value = 'mock_group'
        self.assertEqual(('mock_uid2names', 'mock_group'), self.productgroup.map(data))
        self.assertTrue(mock_uid2names.called)
        self.assertTrue(mock_group.called)


class TestOverview(unittest.TestCase):
    """ test class """

    @patch('requests.Session')
    def setUp(self, mock_session):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')
        self.overview = Overview(logger=self.logger,  client=mock_session)
        # self.maxDiff = None

    def test_011__fetch(self):
        """ test _fetch() """
        self.overview.client = Mock()
        self.overview.client.get.return_value.status_code = 200
        self.overview.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.overview._fetch('url'))
        self.assertTrue(self.overview.client.get.called)

    def test_012__fetch(self):
        """ test _fetch() """
        self.overview.client = Mock()
        self.overview.client.get.return_value.status_code = 400
        self.overview.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.overview._fetch('url'))
        self.assertIn('ERROR:dkb_robo:fetch url: RC is not 200 but 400', lcm.output)
        self.assertTrue(self.overview.client.get.called)

    @patch('dkb_robo.portfolio.Overview._sort')
    @patch('dkb_robo.portfolio.Overview._fetch')
    def test_013_get(self, mock_fetch, mock_sort):
        """ test get() """
        mock_fetch.return_value = {'data': 'data'}
        mock_sort.return_value = 'mock_sort'
        self.assertEqual('mock_sort', self.overview.get())
        self.assertTrue(mock_fetch.called)
        self.assertTrue(mock_sort.called)

    @patch('dkb_robo.portfolio.Overview._sort')
    @patch('dkb_robo.portfolio.Overview._fetch')
    def test_014_get(self, mock_fetch, mock_sort):
        """ test get() """
        mock_fetch.return_value = None
        mock_sort.return_value = 'mock_sort'
        self.assertEqual('mock_sort', self.overview.get())
        self.assertTrue(mock_fetch.called)
        self.assertTrue(mock_sort.called)

    @patch('dkb_robo.portfolio.Depot.get')
    @patch('dkb_robo.portfolio.Card.get')
    @patch('dkb_robo.portfolio.Account.get')
    def test_015__itemize(self, mock_account, mock_card, mock_depot):
        """ test _itemize() """
        mock_account.side_effect = ['account1', 'account2']
        data_dic = {
            'accounts': {'data': [{'id': 'id1', 'type': 'type1'}, {'id': 'id2', 'type': 'type2'}]}
        }
        self.assertEqual({'id1': 'account1', 'id2': 'account2'}, self.overview._itemize(data_dic))
        self.assertTrue(mock_account.called)
        self.assertFalse(mock_card.called)
        self.assertFalse(mock_depot.called)

    @patch('dkb_robo.portfolio.Depot.get')
    @patch('dkb_robo.portfolio.Card.get')
    @patch('dkb_robo.portfolio.Account.get')
    def test_016__itemize(self, mock_account, mock_card, mock_depot):
        """ test _itemize() """
        mock_account.side_effect = ['account1', 'account2']
        mock_card.side_effect = ['card1', 'card2']
        data_dic = {
            'accounts': {'data': [{'id': 'id1', 'type': 'type1'}, {'id': 'id2', 'type': 'type2'}]},
            'cards': {'data': [{'id': 'id3', 'type': 'type3'}, {'id': 'id4', 'type': 'type4'}]},
        }
        self.assertEqual({'id1': 'account1', 'id2': 'account2', 'id3': 'card1', 'id4': 'card2'}, self.overview._itemize(data_dic))
        self.assertTrue(mock_account.called)
        self.assertTrue(mock_card.called)
        self.assertFalse(mock_depot.called)

    @patch('dkb_robo.portfolio.Depot.get')
    @patch('dkb_robo.portfolio.Card.get')
    @patch('dkb_robo.portfolio.Account.get')
    def test_017__itemize(self, mock_account, mock_card, mock_depot):
        """ test _itemize() """
        mock_account.side_effect = ['account1', 'account2']
        mock_card.side_effect = ['card1', 'card2']
        mock_depot.side_effect = ['depot1', 'depot2']
        data_dic = {
            'accounts': {'data': [{'id': 'id1', 'type': 'type1'}, {'id': 'id2', 'type': 'type2'}]},
            'cards': {'data': [{'id': 'id3', 'type': 'type3'}, {'id': 'id4', 'type': 'type4'}]},
            'depots': {'data': [{'id': 'id5', 'type': 'type5'}, {'id': 'id6', 'type': 'type6'}]},
        }
        self.assertEqual({'id1': 'account1', 'id2': 'account2', 'id3': 'card1', 'id4': 'card2', 'id5': 'depot1', 'id6': 'depot2'}, self.overview._itemize(data_dic))
        self.assertTrue(mock_account.called)
        self.assertTrue(mock_card.called)
        self.assertTrue(mock_depot.called)

    def test_018__sort(self):
        """ test _sort() """
        data = {
            'accounts': json_load(self.dir_path + '/mocks/accounts.json'),
            'cards': json_load(self.dir_path + '/mocks/cards.json'),
            'depots': json_load(self.dir_path + '/mocks/brokerage.json'),
            'product_display': json_load(self.dir_path + '/mocks/pd.json')}
        result = {0: {'account': '987654321',
                        'amount': 1234.56,
                        'currencycode': 'EUR',
                        'holdername': 'HolderName1',
                        'id': 'baccountid1',
                        'name': 'pdsettings brokeraage baccountid1',
                        'productgroup': 'productGroup name 1',
                        'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/baccountid1/positions?include=instrument%2Cquote',
                        'type': 'depot'},
                    1: {'account': 'AccountIBAN3',
                        'amount': -1000.22,
                        'currencycode': 'EUR',
                        'date': '2020-03-01',
                        'holdername': 'Account HolderName 3',
                        'iban': 'AccountIBAN3',
                        'id': 'accountid3',
                        'limit': 2500.00,
                        'name': 'pdsettings accoutname accountid3',
                        'productgroup': 'productGroup name 1',
                        'transactions': 'https://banking.dkb.de/api/accounts/accounts/accountid3/transactions',
                        'type': 'account'},
                    2: {'account': 'maskedPan1',
                        'amount': -1234.56,
                        'currencycode': 'EUR',
                        'date': '2020-01-03',
                        'expirydate': '2020-01-02',
                        'holdername': 'holderfirstName holderlastName',
                        'id': 'cardid1',
                        'limit': 1000.00,
                        'maskedpan': 'maskedPan1',
                        'name': 'pdsettings cardname cardid1',
                        'productgroup': 'productGroup name 1',
                        'status': {'category': 'active', 'limitationsFor': []},
                        'transactions': 'https://banking.dkb.de/api/credit-card/cards/cardid1/transactions',
                        'type': 'creditcard'},
                    3: {'account': 'maskedPan2',
                        'amount': 12345.67,
                        'currencycode': 'EUR',
                        'date': '2020-02-07',
                        'holdername': 'holderfirstName2 holderlastName2',
                        'expirydate': '2020-02-02',
                        'id': 'cardid2',
                        'limit': 0.00,
                        'maskedpan': 'maskedPan2',
                        'name': 'displayName2',
                        'productgroup': 'productGroup name 1',
                        'status': {'category': 'active', 'limitationsFor': []},
                        'transactions': 'https://banking.dkb.de/api/credit-card/cards/cardid2/transactions',
                        'type': 'creditcard'},
                    4: {'account': 'AccountIBAN2',
                        'amount': 1284.56,
                        'currencycode': 'EUR',
                        'date': '2020-02-01',
                        'holdername': 'Account HolderName 2',
                        'iban': 'AccountIBAN2',
                        'id': 'accountid2',
                        'limit': 0.00,
                        'name': 'pdsettings accoutname accountid2',
                        'productgroup': 'productGroup name 2',
                        'transactions': 'https://banking.dkb.de/api/accounts/accounts/accountid2/transactions',
                        'type': 'account'},
                    5: {'account': 'AccountIBAN1',
                        'amount': 12345.67,
                        'currencycode': 'EUR',
                        'date': '2020-01-01',
                        'holdername': 'Account HolderName 1',
                        'iban': 'AccountIBAN1',
                        'id': 'accountid1',
                        'limit': 1000.00,
                        'name': 'Account DisplayName 1',
                        'productgroup': None,
                        'transactions': 'https://banking.dkb.de/api/accounts/accounts/accountid1/transactions',
                        'type': 'account'},
                    6: {'account': 'maskedPan3',
                        'holdername': 'holderfirstName3 holderlastName3',
                        'id': 'cardid3',
                        'expirydate': '2020-04-04',
                        'maskedpan': 'maskedPan3',
                        'name': 'Visa Debitkarte',
                        'productgroup': None,
                        'status': {'category': 'blocked',
                                    'final': True,
                                    'reason': 'cancellation-of-product-by-customer',
                                    'since': '2020-03-01'},
                        'transactions': None,
                        'type': 'debitcard'},
                    7: {'account': 'maskedPan4',
                        'holdername': 'holderfirstName4 holderlastName4',
                        'id': 'cardid4',
                        'expirydate': '2020-04-03',
                        'maskedpan': 'maskedPan4',
                        'name': 'Visa Debitkarte',
                        'productgroup': None,
                        'status': {'category': 'active'},
                        'transactions': None,
                        'type': 'debitcard'}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(result, self.overview._sort(data))
        self.assertIn("ERROR:dkb_robo:limit conversion error: float() argument must be a string or a real number, not 'NoneType'", lcm.output)

    def test_019__sort(self):
        """ test _sort() """

        data = {
            'accounts': json_load(self.dir_path + '/mocks/accounts.json'),
            'cards': json_load(self.dir_path + '/mocks/cards.json'),
            'depots': json_load(self.dir_path + '/mocks/brokerage.json'),
            'product_display': json_load(self.dir_path + '/mocks/pd.json')}

        # empty display dic
        data['product_display']['data'][0]['attributes']['productGroups'] = {}

        result = {0: {'account': 'AccountIBAN1',
                        'amount': 12345.67,
                        'currencycode': 'EUR',
                        'date': '2020-01-01',
                        'holdername': 'Account HolderName 1',
                        'iban': 'AccountIBAN1',
                        'id': 'accountid1',
                        'limit': 1000.00,
                        'name': 'Account DisplayName 1',
                        'productgroup': None,
                        'transactions': 'https://banking.dkb.de/api/accounts/accounts/accountid1/transactions',
                        'type': 'account'},
                    1: {'account': 'AccountIBAN2',
                        'amount': 1284.56,
                        'currencycode': 'EUR',
                        'date': '2020-02-01',
                        'holdername': 'Account HolderName 2',
                        'iban': 'AccountIBAN2',
                        'id': 'accountid2',
                        'limit': 0.00,
                        'name': 'Account DisplayName 2',
                        'productgroup': None,
                        'transactions': 'https://banking.dkb.de/api/accounts/accounts/accountid2/transactions',
                        'type': 'account'},
                    2: {'account': 'AccountIBAN3',
                        'amount': -1000.22,
                        'currencycode': 'EUR',
                        'date': '2020-03-01',
                        'holdername': 'Account HolderName 3',
                        'iban': 'AccountIBAN3',
                        'id': 'accountid3',
                        'limit': 2500.00,
                        'name': 'Account DisplayName 3',
                        'productgroup': None,
                        'transactions': 'https://banking.dkb.de/api/accounts/accounts/accountid3/transactions',
                        'type': 'account'},
                    3: {'account': 'maskedPan1',
                        'amount': -1234.56,
                        'currencycode': 'EUR',
                        'date': '2020-01-03',
                        'holdername': 'holderfirstName holderlastName',
                        'id': 'cardid1',
                        'limit': 1000.00,
                        'maskedpan': 'maskedPan1',
                        'name': 'displayName1',
                        'productgroup': None,
                        'expirydate': '2020-01-02',
                        'status': {'category': 'active', 'limitationsFor': []},
                        'transactions': 'https://banking.dkb.de/api/credit-card/cards/cardid1/transactions',
                        'type': 'creditcard'},
                    4: {'account': 'maskedPan2',
                        'amount': 12345.67,
                        'currencycode': 'EUR',
                        'date': '2020-02-07',
                        'holdername': 'holderfirstName2 holderlastName2',
                        'id': 'cardid2',
                        'limit': 0.00,
                        'maskedpan': 'maskedPan2',
                        'name': 'displayName2',
                        'productgroup': None,
                        'expirydate': '2020-02-02',
                        'status': {'category': 'active', 'limitationsFor': []},
                        'transactions': 'https://banking.dkb.de/api/credit-card/cards/cardid2/transactions',
                        'type': 'creditcard'},
                    5: {'account': 'maskedPan3',
                        'holdername': 'holderfirstName3 holderlastName3',
                        'id': 'cardid3',
                        'maskedpan': 'maskedPan3',
                        'name': 'Visa Debitkarte',
                        'productgroup': None,
                        'expirydate': '2020-04-04',
                        'status': {'category': 'blocked',
                                    'final': True,
                                    'reason': 'cancellation-of-product-by-customer',
                                    'since': '2020-03-01'},
                        'transactions': None,
                        'type': 'debitcard'},
                    6: {'account': 'maskedPan4',
                        'holdername': 'holderfirstName4 holderlastName4',
                        'id': 'cardid4',
                        'maskedpan': 'maskedPan4',
                        'name': 'Visa Debitkarte',
                        'productgroup': None,
                        'status': {'category': 'active'},
                        'transactions': None,
                        'expirydate': '2020-04-03',
                        'type': 'debitcard'},
                    7: {'account': '987654321',
                        'amount': 1234.56,
                        'currencycode': 'EUR',
                        'holdername': 'HolderName1',
                        'id': 'baccountid1',
                        'name': 'HolderName1',
                        'productgroup': None,
                        'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/baccountid1/positions?include=instrument%2Cquote',
                        'type': 'depot'}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(result, self.overview._sort(data))
        self.assertIn("ERROR:dkb_robo:limit conversion error: float() argument must be a string or a real number, not 'NoneType'", lcm.output)

class TestAccount(unittest.TestCase):
    """ test class """

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')
        self.account = Account(logger=self.logger)

    def test_020__balance(self):
        """ test _balance() """
        account = {'attributes': {'balance': {'currencyCode': 'EUR', 'value': '100.45'}}}
        self.assertEqual({'amount': 100.45, 'currencycode': 'EUR'}, self.account._balance(account))

    def test_021__balance(self):
        """ test _balance() """
        account = {'attributes': {'balance': {'currencyCode': 'EUR', 'value': 100.45}}}
        self.assertEqual({'amount': 100.45, 'currencycode': 'EUR'}, self.account._balance(account))

    def test_022__balance(self):
        """ test _balance() """
        account = {'attributes': {'balance': {'currencyCode': 'EUR', 'value': 'aa'}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual({'amount': None, 'currencycode': 'EUR'}, self.account._balance(account))
        self.assertIn("ERROR:dkb_robo:amount conversion error: could not convert string to float: 'aa'", lcm.output)

    def test_023__details(self):
        """ test _details() """
        account = {'attributes': {'iban': 'iban', 'bic': 'bic', 'accountNumber': 'accountNumber', 'bankCode': 'bankCode', 'accountType': 'accountType', 'balance': 'balance'}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual({'type': 'account', 'name': None, 'id': 'aid', 'transactions': 'https://banking.dkb.de/api/accounts/accounts/aid/transactions', 'date': None, 'iban': 'iban', 'account': 'iban', 'holdername': None, 'limit': None}, self.account._details(account, 'aid'))
        self.assertIn("ERROR:dkb_robo:limit conversion error: float() argument must be a string or a real number, not 'NoneType'", lcm.output)

    @patch('dkb_robo.portfolio.Account._balance')
    @patch('dkb_robo.portfolio.Account._details')
    def test_024_get(self, mock_details, mock_balance):
        """ test get() ok """
        mock_details.return_value = {'mock_details': 'mock_details'}
        mock_balance.return_value = {'mock_balance': 'mock_balance'}
        data_dic = {'data': [{'attributes': {'foo': 'bar'}, 'id': 'aid'}]}
        self.assertEqual({'mock_balance': 'mock_balance', 'mock_details': 'mock_details'}, self.account.get('aid', data_dic))
        self.assertTrue(mock_details.called)
        self.assertTrue(mock_balance.called)

    @patch('dkb_robo.portfolio.Account._balance')
    @patch('dkb_robo.portfolio.Account._details')
    def test_025_get(self, mock_details, mock_balance):
        """ test get() wrong aid"""
        mock_details.return_value = {'mock_details': 'mock_details'}
        mock_balance.return_value = {'mock_balance': 'mock_balance'}
        data_dic = {'data': [{'attributes': {'foo': 'bar'}, 'id': 'aid'}]}
        self.assertFalse(self.account.get('aid1', data_dic))
        self.assertFalse(mock_details.called)
        self.assertFalse(mock_balance.called)

    @patch('dkb_robo.portfolio.Account._balance')
    @patch('dkb_robo.portfolio.Account._details')
    def test_026_get(self, mock_details, mock_balance):
        """ test get() wrong aid"""
        mock_details.return_value = {'mock_details': 'mock_details'}
        mock_balance.return_value = {'mock_balance': 'mock_balance'}
        data_dic = {'data1': [{'attributes': {'foo': 'bar'}, 'id': 'aid'}]}
        self.assertFalse(self.account.get('aid1', data_dic))
        self.assertFalse(mock_details.called)
        self.assertFalse(mock_balance.called)

class TestCard(unittest.TestCase):
    """ test class """

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')
        self.card = Card(logger=self.logger)

    def test_027__balance(self):
        """ test _balance() """
        account = {'attributes': {'balance': {'currencyCode': 'EUR', 'value': '100.45', 'date': 'date'}}}
        self.assertEqual({'amount': -100.45, 'currencycode': 'EUR', 'date': 'date'}, self.card._balance(account))

    def test_028__balance(self):
        """ test _balance() """
        account = {'attributes': {'balance': {'currencyCode': 'EUR', 'value': 100.45, 'date': 'date'}}}
        self.assertEqual({'amount': -100.45, 'currencycode': 'EUR', 'date': 'date'}, self.card._balance(account))

    def test_029__balance(self):
        """ test _balance() """
        account = {'attributes': {'balance': {'currencyCode': 'EUR', 'value': 'aa', 'date': 'date'}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual({'amount': None, 'currencycode': 'EUR', 'date': 'date'}, self.card._balance(account))
        self.assertIn("ERROR:dkb_robo:amount conversion error: could not convert string to float: 'aa'", lcm.output)

    def test_030__details(self):
        """ test _details() """
        account = {'type': 'type', 'attributes': {'limit': {'value': '1000'}, 'maskedpan': 'maskedpan', 'status': 'status', 'expirydate': 'expirydate', 'product': {'displayName': 'displayName'}, 'holder': {'person': {'firstName': 'firstName', 'lastName': 'lastName'}}}}
        result = {'id': 'cid', 'type': 'type', 'maskedpan': None, 'account': None, 'status': 'status', 'name': 'displayName', 'expirydate': None, 'holdername': 'firstName lastName', 'transactions': 'https://banking.dkb.de/api/credit-card/cards/cid/transactions', 'limit': 1000}
        self.assertEqual(result, self.card._details(account, 'cid'))

    def test_031__details(self):
        """ test _details() """
        account = {'type': 'type', 'attributes': {'limit': {'value': '100'}, 'maskedpan': 'maskedpan', 'status': 'status', 'expirydate': 'expirydate', 'product': {'displayName': 'displayName'}, 'holder': {'person': {'firstName': 'firstName'}}}}
        result = {'id': 'cid', 'type': 'type', 'maskedpan': None, 'account': None, 'status': 'status', 'name': 'displayName', 'expirydate': None, 'holdername': 'firstName ', 'transactions': 'https://banking.dkb.de/api/credit-card/cards/cid/transactions', 'limit': 100.0}
        self.assertEqual(result, self.card._details(account, 'cid'))

    def test_032__details(self):
        """ test _details() """
        account = {'type': 'debitCard', 'attributes': {'limit': {'value': 'aa'}, 'maskedpan': 'maskedpan', 'status': 'status', 'expirydate': 'expirydate', 'product': {'displayName': 'displayName'}}}
        result = {'id': 'cid', 'type': 'debitcard', 'maskedpan': None, 'account': None, 'status': 'status', 'name': 'displayName', 'expirydate': None, 'holdername': ' ', 'transactions': None}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(result, self.card._details(account, 'cid'))
        self.assertIn("ERROR:dkb_robo:limit conversion error: could not convert string to float: 'aa'", lcm.output)

    @patch('dkb_robo.portfolio.Card._balance')
    @patch('dkb_robo.portfolio.Card._details')
    def test_033_get(self, mock_details, mock_balance):
        """ test get() ok """
        mock_details.return_value = {'mock_details': 'mock_details'}
        mock_balance.return_value = {'mock_balance': 'mock_balance'}
        data_dic = {'data': [{'attributes': {'foo': 'bar'}, 'id': 'aid'}]}
        self.assertEqual({'mock_balance': 'mock_balance', 'mock_details': 'mock_details'}, self.card.get('aid', data_dic))
        self.assertTrue(mock_details.called)
        self.assertTrue(mock_balance.called)

    @patch('dkb_robo.portfolio.Card._balance')
    @patch('dkb_robo.portfolio.Card._details')
    def test_034_get(self, mock_details, mock_balance):
        """ test get() wrong aid"""
        mock_details.return_value = {'mock_details': 'mock_details'}
        mock_balance.return_value = {'mock_balance': 'mock_balance'}
        data_dic = {'data': [{'attributes': {'foo': 'bar'}, 'id': 'aid'}]}
        self.assertFalse(self.card.get('aid1', data_dic))
        self.assertFalse(mock_details.called)
        self.assertFalse(mock_balance.called)

    @patch('dkb_robo.portfolio.Card._balance')
    @patch('dkb_robo.portfolio.Card._details')
    def test_035_get(self, mock_details, mock_balance):
        """ test get() wrong aid"""
        mock_details.return_value = {'mock_details': 'mock_details'}
        mock_balance.return_value = {'mock_balance': 'mock_balance'}
        data_dic = {'data1': [{'attributes': {'foo': 'bar'}, 'id': 'aid'}]}
        self.assertFalse(self.card.get('aid1', data_dic))
        self.assertFalse(mock_details.called)
        self.assertFalse(mock_balance.called)


class TestDepot(unittest.TestCase):
    """ test class """

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')
        self.depot = Depot(logger=self.logger)

    def test_036__balance(self):
        """ test _balance() """
        account = {'attributes': {'brokerageAccountPerformance': {'currentValue': {'currencyCode': 'EUR', 'value': '100.45'}}}}
        self.assertEqual({'amount': 100.45, 'currencycode': 'EUR'}, self.depot._balance(account))

    def test_037__balance(self):
        """ test _balance() """
        account = {'attributes': {'brokerageAccountPerformance': {'currentValue': {'currencyCode': 'EUR', 'value': 100.45}}}}
        self.assertEqual({'amount': 100.45, 'currencycode': 'EUR'}, self.depot._balance(account))

    def test_038__balance(self):
        """ test _balance() """
        account = {'attributes': {'brokerageAccountPerformance': {'currentValue': {'currencyCode': 'EUR', 'value': 'aa'}}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual({'amount': None, 'currencycode': 'EUR'}, self.depot._balance(account))
        self.assertIn("ERROR:dkb_robo:amount conversion error: could not convert string to float: 'aa'", lcm.output)

    def test_039__details(self):
        """ test _details() """
        account = {'attributes': {'holderName': 'holderName', 'depositAccountId': 'depositAccountId'}}
        result = {'type': 'depot', 'id': 'did', 'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/did/positions?include=instrument%2Cquote', 'holdername': 'holderName', 'account': 'depositAccountId', 'name': 'holderName'}
        self.assertEqual(result, self.depot._details(account, 'did'))

    @patch('dkb_robo.portfolio.Depot._balance')
    @patch('dkb_robo.portfolio.Depot._details')
    def test_040_get(self, mock_details, mock_balance):
        """ test get() ok """
        mock_details.return_value = {'mock_details': 'mock_details'}
        mock_balance.return_value = {'mock_balance': 'mock_balance'}
        data_dic = {'data': [{'attributes': {'foo': 'bar'}, 'id': 'aid'}]}
        self.assertEqual({'mock_balance': 'mock_balance', 'mock_details': 'mock_details'}, self.depot.get('aid', data_dic))
        self.assertTrue(mock_details.called)
        self.assertTrue(mock_balance.called)

    @patch('dkb_robo.portfolio.Depot._balance')
    @patch('dkb_robo.portfolio.Depot._details')
    def test_041_get(self, mock_details, mock_balance):
        """ test get() wrong aid"""
        mock_details.return_value = {'mock_details': 'mock_details'}
        mock_balance.return_value = {'mock_balance': 'mock_balance'}
        data_dic = {'data': [{'attributes': {'foo': 'bar'}, 'id': 'aid'}]}
        self.assertFalse(self.depot.get('aid1', data_dic))
        self.assertFalse(mock_details.called)
        self.assertFalse(mock_balance.called)

    @patch('dkb_robo.portfolio.Depot._balance')
    @patch('dkb_robo.portfolio.Depot._details')
    def test_042_get(self, mock_details, mock_balance):
        """ test get() wrong aid"""
        mock_details.return_value = {'mock_details': 'mock_details'}
        mock_balance.return_value = {'mock_balance': 'mock_balance'}
        data_dic = {'data1': [{'attributes': {'foo': 'bar'}, 'id': 'aid'}]}
        self.assertFalse(self.depot.get('aid1', data_dic))
        self.assertFalse(mock_details.called)
        self.assertFalse(mock_balance.called)


if __name__ == '__main__':

    unittest.main()
