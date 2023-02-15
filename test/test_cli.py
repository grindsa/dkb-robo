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
import click
from click.testing import CliRunner

sys.path.insert(0, '.')
sys.path.insert(0, '..')
import logging


class Config():
    def __init__(self):
        self.FORMAT = None

    def __getitem__(self, key): # this allows getting an element (overrided method)
        return self.FORMAT(key)


class TestDKBRobo(unittest.TestCase):
    """ test class """

    maxDiff = None

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        from dkb_robo.cli import _load_format, _login, standing_orders, credit_limits, last_login, accounts, main, transactions
        self.logger = logging.getLogger('dkb_robo')
        self._load_format = _load_format
        self._login = _login
        self.standing_orders = standing_orders
        self.credit_limits = credit_limits
        self.last_login = last_login
        self.accounts = accounts
        self.main = main
        self.transactions = transactions

    def test_001_default(self):
        """ default test which always passes """
        self.assertEqual('foo', 'foo')


    def test_002__login(self):
        """ test login """
        cursor = MagicMock()
        cursor.__iter__.return_value = []
        self.assertTrue(self._login(cursor))

    def test_003__load_format(self):
        """ test _load_format() """
        oformat = 'pprint'
        self.assertIn('pprint', self._load_format(oformat).__code__.co_names)

    def test_004__load_format(self):
        """ test _load_format() """
        oformat = 'csv'
        self.assertIn('csv', self._load_format(oformat).__code__.co_names)

    def test_005__load_format(self):
        """ test _load_format() """
        oformat = 'table'
        self.assertIn('tabulate', self._load_format(oformat).__code__.co_names)

    def test_006__load_format(self):
        """ test _load_format() """
        oformat = 'json'
        self.assertIn('json', self._load_format(oformat).__code__.co_names)

    def test_007__load_format(self):
        """ test _load_format() """
        oformat = 'foo'
        with self.assertRaises(Exception) as err:
            self._load_format(oformat)
        self.assertEqual('Unknown format: foo', str(err.exception))

    @patch('click.echo')
    @patch('dkb_robo.cli._login')
    def test_008_standing_orders(self, mock_login, mock_click):
        """ test standing orders """
        obj = Config()
        obj.FORMAT = Mock()
        runner = CliRunner()
        self.assertEqual('<Result okay>', str(runner.invoke(self.standing_orders, obj=obj)))
        self.assertFalse(mock_click.called)

    @patch('click.echo')
    @patch('dkb_robo.cli._login')
    def test_009_standing_orders(self, mock_login, mock_click):
        """ standing orders """
        from dkb_robo import DKBRoboError
        mock_login.side_effect = DKBRoboError('Error during session confirmation')
        obj = Config()
        obj.FORMAT = 'foo'
        runner = CliRunner()
        self.assertIn('<Result okay>', str(runner.invoke(self.standing_orders, obj=obj)))
        self.assertTrue(mock_click.called)

    @patch('click.echo')
    @patch('dkb_robo.cli._login')
    def test_010_credit_limits(self, mock_login, mock_click):
        """ credit limits """
        obj = Config()
        obj.FORMAT = Mock()
        runner = CliRunner()
        self.assertEqual('<Result okay>', str(runner.invoke(self.credit_limits, obj=obj)))
        self.assertFalse(mock_click.called)

    @patch('click.echo')
    @patch('dkb_robo.cli._login')
    def test_011_credit_limits(self, mock_login, mock_click):
        """ credit limits """
        from dkb_robo import DKBRoboError
        mock_login.side_effect = DKBRoboError('Error during session confirmation')
        obj = Config()
        obj.FORMAT = 'foo'
        runner = CliRunner()
        self.assertIn('<Result okay>', str(runner.invoke(self.credit_limits, obj=obj)))
        self.assertTrue(mock_click.called)

    @patch('click.echo')
    @patch('dkb_robo.cli._login')
    def test_012_last_login(self, mock_login, mock_click):
        """ test last login """
        obj = Config()
        obj.FORMAT = Mock()
        runner = CliRunner()
        self.assertEqual('<Result okay>', str(runner.invoke(self.last_login, obj=obj)))
        self.assertFalse(mock_click.called)

    @patch('click.echo')
    @patch('dkb_robo.cli._login')
    def test_013_last_login(self, mock_login, mock_click):
        """ test last login """
        from dkb_robo import DKBRoboError
        mock_login.side_effect = DKBRoboError('Error during session confirmation')
        obj = Config()
        obj.FORMAT = 'foo'
        runner = CliRunner()
        self.assertIn('<Result okay>', str(runner.invoke(self.last_login, obj=obj)))
        self.assertTrue(mock_click.called)

    @patch('click.echo')
    @patch('dkb_robo.cli._login')
    def test_014_accounts(self, mock_login, mock_click):
        """ test accounts """
        obj = Config()
        obj.FORMAT = Mock()
        runner = CliRunner()
        self.assertEqual('<Result okay>', str(runner.invoke(self.accounts, obj=obj)))
        self.assertFalse(mock_click.called)

    @patch('click.echo')
    @patch('dkb_robo.cli._login')
    def test_015_accounts(self, mock_login, mock_click):
        """ test accounts """
        mock_login.return_value.__enter__.return_value.account_dic = {1: {'details': 'details', 'transactions': 'transactions'}, 2: {'details': 'details', 'transactions': 'transactions'}}
        obj = Config()
        obj.FORMAT = Mock()
        runner = CliRunner()
        self.assertEqual('<Result okay>', str(runner.invoke(self.accounts, obj=obj)))
        self.assertFalse(mock_click.called)

    @patch('click.echo')
    @patch('dkb_robo.cli._login')
    def test_016_accounts(self, mock_login, mock_click):
        """ test accounts """
        from dkb_robo import DKBRoboError
        mock_login.side_effect = DKBRoboError('Error during session confirmation')
        obj = Config()
        obj.FORMAT = 'foo'
        runner = CliRunner()
        self.assertIn('<Result okay>', str(runner.invoke(self.accounts, obj=obj)))
        self.assertTrue(mock_click.called)


    @patch('click.option')
    @patch('click.pass_context')
    def test_017_main(self, mock_pass, mock_option):
        """ test main """

        ctx = MagicMock()
        debug = 'debug'
        use_tan = 'use_tan'
        username = 'username'
        password = 'password'
        format = 'format'
        obj = Config()
        obj.FORMAT = 'foo'

        # self.assertEqual('foo', self.main(ctx, use_tan, username, password, format))
        runner = CliRunner()
        self.assertIn('<Result SystemExit(2)>', str(runner.invoke(self.accounts, [use_tan, username, password, format], obj=obj)))

    #@patch('dkb_robo.cli._load_format')
    #@patch('click.core')
    #def test_017_main(self, mock_click, mock_format):
    #    """ test main """
    #    # ctx = MagicMock()
    #    debug = 'debug'
    #    use_tan = 'use_tan'
    #    username = 'username'
    #    password = 'password'
    #    format = 'format'
    #    obj = Config()
    #    obj.FORMAT = 'foo'
    #    runner = CliRunner()
    #    self.assertIn('<Result SystemExit(2)>', str(runner.invoke(self.accounts, [debug, use_tan, username, password, format], obj=obj)))
    #    # self.assertTrue(self.main(ctx, debug, use_tan, username, password))
    #    self.assertTrue(mock_format.called)

    #@patch('dkb_robo.cli._load_format')
    #@patch('dkb_robo.cli._login')
    #def test_017_main(self, mock_login, mock_load):
    #    """ test accounts """
    #    obj = Config()
    #    obj.FORMAT = 'foo'
    #    runner = CliRunner()
    #    self.assertIn('<Result okay>', str(runner.invoke(self.maine, obj=obj, username='username', )))
    #    # self.assertTrue(mock_load.called)

    #@patch('click.echo')
    #@patch('dkb_robo.cli._login')
    #def test_017_transactions(self, mock_login, mock_click):
    #    """ credit limits """
    #    name = ['name']
    #    account = None
    #    transaction_type = 'booked'
    #    date_from = 'date_from'
    #    date_to = 'date_to'

    #    runner = CliRunner()
    #    result = runner.invoke(self.transactions, ['ctx', name, account, transaction_type, date_from, date_to])

    #    print(result.exception)
        # assert isinstance(result.exception, ValueError)
        #result = self.transactions(name, account, transaction_type, date_from, date_to)
        # print(result)

        #self.assertTrue(mock_click.called)


if __name__ == '__main__':

    unittest.main()