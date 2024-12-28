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
from dkb_robo.standingorder import StandingOrder

def json_load(fname):
    """ simple json load """

    with open(fname, 'r', encoding='utf8') as myfile:
        data_dic = json.load(myfile)

    return data_dic


class TestDKBRobo(unittest.TestCase):
    """ test class """

    @patch("requests.Session")
    def setUp(self, mock_session):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')
        self.dkb = StandingOrder(logger=self.logger, client=mock_session)

    @patch('dkb_robo.standingorder.StandingOrder._filter')
    def test_001_fetch(self, mock_filter):
        """ test StandingOrder.fetch() without uid """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}

        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb.fetch(None))
        self.assertEqual('account-id is required to fetch standing orders', str(err.exception))
        self.assertFalse(mock_filter.called)

    @patch('dkb_robo.standingorder.StandingOrder._filter')
    def test_002_fetch(self, mock_filter):
        """ test StandingOrder.fetch() with uid but http error """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertFalse(self.dkb.fetch(uid='uid'))
        self.assertFalse(mock_filter.called)

    @patch('dkb_robo.standingorder.StandingOrder._filter')
    def test_003_fetch(self, mock_filter):
        """ test StandingOrder.fetch() with uid no error """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        mock_filter.return_value = 'mock_filter'
        self.assertEqual('mock_filter', self.dkb.fetch(uid='uid'))
        self.assertTrue(mock_filter.called)

    def test_004__filter(self):
        """ test StandingOrder._filter() with empty list """
        full_list = {}
        self.assertFalse(self.dkb._filter(full_list))

    def test_005__filter(self):
        """ test StandingOrder._filter() with list """
        full_list = {
            "data": [
                {
                    "attributes": {
                        "description": "description",
                        "amount": {
                            "currencyCode": "EUR",
                            "value": "100.00"
                        },
                        "creditor": {
                            "name": "cardname",
                            "creditorAccount": {
                                "iban": "crediban",
                                "bic": "credbic"
                            }
                        },
                        "recurrence": {
                            "from": "2020-01-01",
                            "until": "2025-12-01",
                            "frequency": "monthly",
                            "nextExecutionAt": "2020-02-01"
                        }
                    }
                }]}
        result = [{'amount': 100.0, 'currencycode': 'EUR', 'purpose': 'description', 'recpipient': 'cardname', 'creditoraccount': {'iban': 'crediban', 'bic': 'credbic'}, 'interval': {'from': '2020-01-01', 'until': '2025-12-01', 'frequency': 'monthly', 'nextExecutionAt': '2020-02-01'}}]
        self.assertEqual(result, self.dkb._filter(full_list))

    def test_006__filter(self):
        """ test StandingOrder._filter() with list from file """
        so_list = json_load(self.dir_path + '/mocks/so.json')
        result = [{'amount': 100.0, 'currencycode': 'EUR', 'purpose': 'description1', 'recpipient': 'name1', 'creditoraccount': {'iban': 'iban1', 'bic': 'bic1'}, 'interval': {'from': '2022-01-01', 'until': '2025-12-01', 'frequency': 'monthly', 'holidayExecutionStrategy': 'following', 'nextExecutionAt': '2022-11-01'}}, {'amount': 200.0, 'currencycode': 'EUR', 'purpose': 'description2', 'recpipient': 'name2', 'creditoraccount': {'iban': 'iban2', 'bic': 'bic2'}, 'interval': {'from': '2022-02-01', 'until': '2025-12-02', 'frequency': 'monthly', 'holidayExecutionStrategy': 'following', 'nextExecutionAt': '2022-11-02'}}, {'amount': 300.0, 'currencycode': 'EUR', 'purpose': 'description3', 'recpipient': 'name3', 'creditoraccount': {'iban': 'iban3', 'bic': 'bic3'}, 'interval': {'from': '2022-03-01', 'until': '2025-03-01', 'frequency': 'monthly', 'holidayExecutionStrategy': 'following', 'nextExecutionAt': '2022-03-01'}}]
        self.assertEqual(result, self.dkb._filter(so_list))

    def test_007__filter(self):
        """ test StandingOrder._filter() with incomplete list """
        full_list = {
            "data": [
                {
                    "attributes": {
                        "description": "description",
                        "creditor": {
                            "name": "cardname",
                            "creditorAccount": {
                                "iban": "crediban",
                                "bic": "credbic"
                            }
                        },
                        "recurrence": {
                            "from": "2020-01-01",
                            "until": "2025-12-01",
                            "frequency": "monthly",
                            "nextExecutionAt": "2020-02-01"
                        }
                    }
                }]}
        result = [{'amount': 0.0, 'currencycode': None, 'purpose': 'description', 'recpipient': 'cardname', 'creditoraccount': {'iban': 'crediban', 'bic': 'credbic'}, 'interval': {'from': '2020-01-01', 'until': '2025-12-01', 'frequency': 'monthly', 'nextExecutionAt': '2020-02-01'}}]
        self.assertEqual(result, self.dkb._filter(full_list))

if __name__ == '__main__':

    unittest.main()