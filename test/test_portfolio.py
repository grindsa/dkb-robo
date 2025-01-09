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
from dkb_robo.portfolio import ProductGroup, AccountItem, CardItem, DepotItem, Overview

def json_load(fname):
    """ simple json load """

    with open(fname, 'r', encoding='utf8') as myfile:
        data_dic = json.load(myfile)

    return data_dic


class TestProductGroup(unittest.TestCase):
    """ test class """

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.productgroup = ProductGroup()

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
        self.assertIn('WARNING:dkb_robo.portfolio:uid2name mapping failed. product data are not in dictionary format', lcm.output)

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
        self.overview = Overview(client=mock_session)
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
        self.assertIn('ERROR:dkb_robo.portfolio:fetch url: RC is not 200 but 400', lcm.output)
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

    @patch('dkb_robo.portfolio.AccountItem', autospec=True)
    @patch('dkb_robo.portfolio.CardItem', autospec=True)
    @patch('dkb_robo.portfolio.DepotItem', autospec=True)
    def test_015_itemize(self, mock_depot, mock_card, mock_account):
        portfolio_dic = {
            'accounts': {'data': [{'id': 'acc1', 'attributes': {'amount': 100}}]},
            'cards': {'data': [{'id': 'card1', 'attributes': {'limit': 500}}]},
            'depots': {'data': [{'id': 'depot1', 'attributes': {'value': 1000}}]}
        }

        mock_account.return_value.format.return_value = 'formatted_account'
        mock_card.return_value.format.return_value = 'formatted_card'
        mock_depot.return_value.format.return_value = 'formatted_depot'

        result = self.overview._itemize(portfolio_dic)

        self.assertEqual(result, {
            'acc1': 'formatted_account',
            'card1': 'formatted_card',
            'depot1': 'formatted_depot'
        })

    @patch('dkb_robo.portfolio.AccountItem', autospec=True)
    @patch('dkb_robo.portfolio.CardItem', autospec=True)
    @patch('dkb_robo.portfolio.DepotItem', autospec=True)
    def test_016_itemize(self, mock_depot, mock_card, mock_account):
        portfolio_dic = {
            'accounts': {'data': [{'id': 'acc1', 'attributes': {'amount': 100}}]},
            'cards': {'data': [{'id': 'card1', 'attributes': {'limit': 500}}]},
            'depots': {'data': [{'id': 'depot1', 'attributes': {'value': 1000}}]}
        }

        mock_account.return_value = 'unprocessed_account'
        mock_card.return_value = 'unprocessed_card'
        mock_depot.return_value = 'unprocessed_depot'
        self.overview.unprocessed = True
        result = self.overview._itemize(portfolio_dic)

        self.assertEqual(result, {
            'acc1': 'unprocessed_account',
            'card1': 'unprocessed_card',
            'depot1': 'unprocessed_depot'
        })

    @patch('dkb_robo.portfolio.ProductGroup', autospec=True)
    @patch('dkb_robo.portfolio.Overview._itemize', autospec=True)
    @patch('dkb_robo.portfolio.Overview._add_remaining', autospec=True)
    def test_017_sort(self, mock_add, mock_itemize, mock_pgrp):
        portfolio_dic = {
            'product_display': {'data': [{'id': 'display1'}]},
            'accounts': {'data': [{'id': 'acc1', 'attributes': {'amount': 100}}]},
            'cards': {'data': [{'id': 'card1', 'attributes': {'limit': 500}}]},
            'depots': {'data': [{'id': 'depot1', 'attributes': {'value': 1000}}]}
        }

        mock_itemize.return_value = {
            'acc1': {'amount': 100},
            'card1': {'limit': 500},
            'depot1': {'value': 1000}
        }

        mock_product_group = MagicMock()
        mock_product_group.map.return_value = ({'acc1': 'Account'}, [{'name': 'Group1', 'product_list': {'acc1': 'acc1'}}])
        mock_pgrp.return_value = mock_product_group

        mock_add.return_value = {
            0: {'amount': 100, 'productgroup': 'Group1'}
        }

        result = self.overview._sort(portfolio_dic)

        self.assertEqual(result, {
            0: {'amount': 100, 'productgroup': 'Group1'}
        })

    @patch('dkb_robo.portfolio.ProductGroup', autospec=True)
    @patch('dkb_robo.portfolio.Overview._itemize', autospec=True)
    @patch('dkb_robo.portfolio.Overview._add_remaining', autospec=True)
    def test_018_sort(self, mock_add, mock_itemize, mock_pgrp):
        portfolio_dic = {
            'product_display': {'data': [{'id': 'display1'}]},
            'accounts': {'data': [{'id': 'acc1', 'attributes': {'amount': 100}}]},
            'cards': {'data': [{'id': 'card1', 'attributes': {'limit': 500}}]},
            'depots': {'data': [{'id': 'depot1', 'attributes': {'value': 1000}}]}
        }

        mock_itemize.return_value = {
            'acc1': {'amount': 100},
            'card1': {'limit': 500},
            'depot1': {'value': 1000}
        }

        mock_product_group = MagicMock()
        mock_product_group.map.return_value = ({'acc1': 'Account'}, [{'name': 'Group1', 'product_list': {'acc1': 'acc1'}}])
        mock_pgrp.return_value = mock_product_group

        mock_add.return_value = {
            0: {'amount': 100, 'productgroup': 'Group1'}
        }

        self.overview.unprocessed = True
        result = self.overview._sort(portfolio_dic)

        self.assertEqual(result, {
            0: {'amount': 100, 'productgroup': 'Group1'}
        })


if __name__ == '__main__':

    unittest.main()
