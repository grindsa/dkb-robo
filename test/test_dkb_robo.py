#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" unittests for dkb_robo """
import sys
import os
import unittest
from unittest.mock import patch, MagicMock, Mock, mock_open
from bs4 import BeautifulSoup
from mechanicalsoup import LinkNotFoundError
from datetime import date
import io
import json

sys.path.insert(0, '.')
sys.path.insert(0, '..')
from dkb_robo import DKBRobo
import logging


def json_load(fname):
    """ simple json load """

    with open(fname, 'r', encoding='utf8') as myfile:
        data_dic = json.load(myfile)

    return data_dic

def read_file(fname):
    """ read file into string """
    with open(fname, "rb") as myfile:
        data = myfile.read()

    return data

def cnt_list(value):
    """ customized function return just the number if entries in input list """
    return len(value)

def my_side_effect(*args, **kwargs):
    """ my sideeffect funtion """
    return [200, args[1], [args[4]]]


class TestDKBRobo(unittest.TestCase):
    """ test class """

    maxDiff = None

    def setUp(self):
        self.dkb = DKBRobo()
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')

    @patch('dkb_robo.api.Wrapper.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_001__enter(self, mock_legacy, mock_api):
        """ test enter """
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)

    @patch('dkb_robo.api.Wrapper.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_002__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.legacy_login = False
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)

    @patch('dkb_robo.api.Wrapper.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_003__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.legacy_login = True
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        with self.assertRaises(Exception) as err:
            self.dkb.__enter__()
        self.assertEqual('Legacy Login got deprecated. Please do not use this option anymore', str(err.exception))
        self.assertFalse(mock_legacy.called)
        self.assertFalse(mock_api.called)

    @patch('dkb_robo.api.Wrapper.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_004__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.tan_insert = True
        # self.dkb.wrapper = Mock()
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb.__enter__()
        self.assertIn("INFO:dkb_robo:tan_insert is a legacy login option and will be disabled soon. Please use chip_tan instead", lcm.output)
        self.assertTrue(self.dkb.chip_tan)
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)

    @patch('dkb_robo.api.Wrapper.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_005__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.mfa_device = 1
        # self.dkb.wrapper = Mock()
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)
        self.assertEqual(1, self.dkb.mfa_device)

    @patch('dkb_robo.api.Wrapper.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_006__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.mfa_device = 2
        # self.dkb.wrapper = Mock()
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)
        self.assertEqual(2, self.dkb.mfa_device)

    @patch('dkb_robo.api.Wrapper.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_007__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.mfa_device = 'm'
        # self.dkb.wrapper = Mock()
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)
        self.assertEqual(1, self.dkb.mfa_device)

    def test_008__exit(self):
        """ test enter """
        self.dkb.wrapper = Mock()
        self.dkb.wrapper.logout = Mock()
        self.assertFalse(self.dkb.__exit__())
        self.assertTrue(self.dkb.wrapper.logout.called)

    @patch('dkb_robo.dkb_robo.validate_dates')
    def test_009_get_transactions(self, mock_date):
        """ test get_transactions() """
        self.dkb.legacy_login = True
        mock_date.return_value = ('from', 'to')
        self.dkb.wrapper = Mock()
        self.dkb.wrapper.get_transactions.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb.get_transactions('url', 'atype', 'from', 'to', 'btype'))

    @patch('dkb_robo.dkb_robo.validate_dates')
    def test_010_get_transactions(self, mock_date):
        """ test get_transactions() """
        self.dkb.legacy_login = False
        mock_date.return_value = ('from', 'to')
        self.dkb.wrapper = Mock()
        self.dkb.wrapper.get_transactions.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb.get_transactions('url', 'atype', 'from', 'to', 'btype'))

    def test_011_get_points(self):
        """ test get_exemption_order()"""
        self.dkb.wrapper = Mock()
        with self.assertRaises(Exception) as err:
            self.dkb.get_points()
        self.assertEqual('Method not supported...', str(err.exception))

    def test_012_get_exemption_order(self):
        """ test get_exemption_order()"""
        self.dkb.wrapper = Mock()
        self.dkb.wrapper.get_exemption_order.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb.get_exemption_order())

    def test_013_get_credit_limits(self):
        """ test get_credit_limits()"""
        self.dkb.wrapper = Mock()
        self.dkb.wrapper.get_credit_limits.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb.get_credit_limits())

    def test_014_get_standing_orders(self):
        """ test get_standing_orders()"""
        self.dkb.wrapper = Mock()
        self.dkb.wrapper.get_standing_orders.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb.get_standing_orders())

    def test_015_scan_postbox(self):
        """ test get_standing_orders()"""
        self.dkb.wrapper = Mock()
        self.dkb.wrapper.scan_postbox.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb.scan_postbox())

if __name__ == '__main__':

    unittest.main()
