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
from dkb_robo.exemptionorder import ExemptionOrder

def json_load(fname):
    """ simple json load """

    with open(fname, 'r', encoding='utf8') as myfile:
        data_dic = json.load(myfile)
    return data_dic


class TestExemptionOrder(unittest.TestCase):
    """ test class """

    @patch("requests.Session")
    def setUp(self, mock_session):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.exo = ExemptionOrder(client=mock_session)
        self.maxDiff = None

    @patch('dkb_robo.exemptionorder.ExemptionOrder._filter')
    def test_001_fetch(self, mock_filter):
        """ test ExemptionOrder.fetch() with uid but http error """
        self.exo.client = Mock()
        self.exo.client.get.return_value.status_code = 400
        self.exo.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.exo.fetch())
        self.assertEqual('fetch exemption orders: http status code is not 200 but 400', str(err.exception))
        self.assertFalse(mock_filter.called)

    @patch('dkb_robo.exemptionorder.ExemptionOrder._filter')
    def test_002_fetch(self, mock_filter):
        """ test ExemptionOrder.fetch() with uid no error """
        self.exo.client = Mock()
        self.exo.client.get.return_value.status_code = 200
        self.exo.client.get.return_value.json.return_value = {'foo': 'bar'}
        mock_filter.return_value = 'mock_filter'
        self.assertEqual('mock_filter', self.exo.fetch())
        self.assertTrue(mock_filter.called)

    def test_003__filter(self):
        """ test ExemptionOrder._filter() with empty list """
        full_list = {}
        self.assertFalse(self.exo._filter(full_list))

    def test_004__filter(self):
        """ test StandingOrder._filter() with list """
        full_list = {
            'data': {'attributes': {'exemptionCertificates': [],
                         'exemptionOrders': [{'exemptionAmount': {'currencyCode': 'EUR',
                                                                  'value': '2000.00'},
                                              'exemptionOrderType': 'joint',
                                              'partner': {'dateOfBirth': '1970-01-01',
                                                          'firstName': 'Jane',
                                                          'lastName': 'Doe',
                                                          'salutation': 'Frau',
                                                          'taxId': '1234567890'},
                                              'receivedAt': '2020-01-01',
                                              'remainingAmount': {'currencyCode': 'EUR',
                                                                  'value': '1699.55'},
                                              'utilizedAmount': {'currencyCode': 'EUR',
                                                                 'value': '300.50'},
                                              'validFrom': '2020-01-01',
                                              'validUntil': '9999-12-31'}]},
                    'id': 'xxxx',
                    'type': 'customerTaxExemptions'}}

        result = [{'amount': 2000.0, 'used': 300.5, 'currencycode': 'EUR', 'validfrom': '2020-01-01', 'validto': '9999-12-31', 'receivedat': '2020-01-01', 'type': 'joint', 'partner': {'dateofbirth': '1970-01-01', 'firstname': 'Jane', 'lastname': 'Doe', 'salutation': 'Frau', 'taxid': '1234567890'}}]
        self.assertEqual(result, self.exo._filter(full_list))


    def test_005__filter(self):
        """ test StandingOrder._filter() with incomplete list """
        full_list = {
            'data': {'attributes': {'exemptionCertificates': [],
                         'exemptionOrders': [{'exemptionAmount': {'currencyCode': 'EUR',
                                                                  'value': 'aa'},
                                              'exemptionOrderType': 'joint',
                                              'partner': {'dateOfBirth': '1970-01-01',
                                                          'firstName': 'Jane',
                                                          'lastName': 'Doe',
                                                          'salutation': 'Frau',
                                                          'taxId': '1234567890'},
                                              'receivedAt': '2020-01-01',
                                              'remainingAmount': {'currencyCode': 'EUR',
                                                                  'value': 'aa'},
                                              'utilizedAmount': {'currencyCode': 'EUR',
                                                                 'value': 'aa'},
                                              'validFrom': '2020-01-01',
                                              'validUntil': '9999-12-31'}]},
                    'id': 'xxxx',
                    'type': 'customerTaxExemptions'}}

        result = [{'amount': None, 'used': None, 'currencycode': 'EUR', 'validfrom': '2020-01-01', 'validto': '9999-12-31', 'receivedat': '2020-01-01', 'type': 'joint', 'partner': {'dateofbirth': '1970-01-01', 'firstname': 'Jane', 'lastname': 'Doe', 'salutation': 'Frau', 'taxid': '1234567890'}}]
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(result, self.exo._filter(full_list))
        self.assertIn("ERROR:dkb_robo.exemptionorder:amount conversion error: could not convert string to float: 'aa'", lcm.output)
        self.assertIn("ERROR:dkb_robo.exemptionorder:used conversion error: could not convert string to float: 'aa'", lcm.output)

if __name__ == '__main__':

    unittest.main()
