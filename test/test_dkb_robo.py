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


@patch('dkb_robo.DKBRobo.dkb_br')
class TestDKBRobo(unittest.TestCase):
    """ test class """

    maxDiff = None

    def setUp(self):
        self.dkb = DKBRobo()
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')


    @patch('dkb_robo.DKBRobo._legacy_login')
    @patch('dkb_robo.DKBRobo._login')
    def test_043__enter(self, mock_login, mock_legacy_login, mock_browser):
        """ test enter """
        self.dkb.legacy_login = True
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy_login.called)
        self.assertFalse(mock_login.called)

    @patch('dkb_robo.DKBRobo._legacy_login')
    @patch('dkb_robo.DKBRobo._login')
    def test_044__enter(self, mock_login, mock_legacy_login, _unused):
        """ test enter """
        self.dkb.dkb_br = None
        self.dkb.legacy_login = True
        self.assertTrue(self.dkb.__enter__())
        self.assertTrue(mock_legacy_login.called)
        self.assertFalse(mock_login.called)

    @patch('dkb_robo.DKBRobo._legacy_login')
    @patch('dkb_robo.DKBRobo._login')
    def test_045__enter(self, mock_login, mock_legacy_login, _unused):
        """ test enter """
        self.dkb.client = None
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy_login.called)
        self.assertTrue(mock_login.called)

    @patch('dkb_robo.DKBRobo._legacy_login')
    @patch('dkb_robo.DKBRobo._login')
    def test_046__enter(self, mock_login, mock_legacy_login, _unused):
        """ test enter """
        self.dkb.client = 'foo'
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy_login.called)
        self.assertFalse(mock_login.called)

    @patch('dkb_robo.DKBRobo._legacy_login')
    @patch('dkb_robo.DKBRobo._login')
    def test_047__enter(self, mock_login, mock_legacy_login, _unused):
        """ test enter """
        self.dkb.dkb_br = None
        self.dkb.legacy_login = False
        self.dkb.tan_insert = True
        self.assertTrue(self.dkb.__enter__())
        self.assertTrue(mock_legacy_login.called)
        self.assertFalse(mock_login.called)

    @patch('dkb_robo.DKBRobo._logout')
    def test_048__exit(self, mock_logout, _ununsed):
        """ test enter """
        self.assertFalse(self.dkb.__exit__())
        self.assertTrue(mock_logout.called)



    def test_088_get_accounts(self, _unused):
        """ test _get_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_accounts())

    def test_089_get_accounts(self, _unused):
        """ test _get_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_accounts())
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_accounts(): RC is not 200 but 400', lcm.output)

    def test_090_get_brokerage_accounts(self, _unused):
        """ test _get_brokerage_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_brokerage_accounts())

    def test_091_get_brokerage_accounts(self, _unused):
        """ test _get_brokerage_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_brokerage_accounts())
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_brokerage_accounts(): RC is not 200 but 400', lcm.output)

    def test_092_get_cards(self, _unused):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_cards())

    def test_093_get_cards(self, _unused):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_cards())
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_cards(): RC is not 200 but 400', lcm.output)

    def test_094_get_loans(self, _unused):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_loans())

    def test_095_get_loans(self, _unused):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_loans())
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_loans(): RC is not 200 but 400', lcm.output)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_096_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        atype = 'account'
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_transactions(): RC is not 200 but 400', lcm.output)
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_097_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans_unused, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {}
        atype = 'account'
        self.assertFalse(self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_atrans.called)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_098_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        atype = 'account'
        self.assertFalse(self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_099_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'data': {'foo': 'bar'}}
        atype = 'account'
        mock_atrans.return_value = {'mock_foo': 'mock_bar'}
        self.assertEqual({'mock_foo': 'mock_bar'}, self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertTrue(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_100_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'data': {'foo': 'bar'}}
        atype = 'creditcard'
        mock_ctrans.return_value = {'mock_foo': 'mock_bar'}
        self.assertEqual({'mock_foo': 'mock_bar'}, self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertTrue(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_101_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'data': {'foo': 'bar'}}
        atype = 'depot'
        mock_btrans.return_value = {'mock_foo': 'mock_bar'}
        self.assertEqual({'mock_foo': 'mock_bar'}, self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertTrue(mock_btrans.called)

    def test_102_update_token(self, _unused):
        """ test _update_token() ok """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token'}
        self.dkb.client = Mock()
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        self.dkb._update_token()
        self.assertEqual({'foo': 'bar'}, self.dkb.token_dic)

    def test_103_update_token(self, _unused):
        """ test _update_token() nok """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token'}
        self.dkb.client = Mock()
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._update_token()
        self.assertEqual('Login failed: token update failed. RC: 400', str(err.exception))
        self.assertEqual({'mfa_id': 'mfa_id', 'access_token': 'access_token'}, self.dkb.token_dic)

    def test_104_get_token(self, _unused):
        """ test _get_token() ok """
        self.dkb.dkb_user = 'dkb_user'
        self.dkb.dkb_password = 'dkb_password'
        self.dkb.client = Mock()
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        self.dkb._get_token()
        self.assertEqual({'foo': 'bar'}, self.dkb.token_dic)

    def test_105_get_token(self, _unused):
        """ test _get_token() ok """
        self.dkb.dkb_user = 'dkb_user'
        self.dkb.dkb_password = 'dkb_password'
        self.dkb.client = Mock()
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._get_token()
        self.assertEqual('Login failed: 1st factor authentication failed. RC: 400', str(err.exception))
        self.assertFalse(self.dkb.token_dic)

    @patch('dkb_robo.DKBRobo._new_instance')
    def test_106_do_sso_redirect(self, mock_instance, _unused):
        """ test _do_sso_redirect() ok """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.text = 'OK'
        self.dkb._do_sso_redirect()
        self.assertTrue(mock_instance.called)

    @patch('dkb_robo.DKBRobo._new_instance')
    def test_107_do_sso_redirect(self, mock_instance, _unused):
        """ test _do_sso_redirect() nok """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.text = 'NOK'
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb._do_sso_redirect()
        self.assertIn('ERROR:dkb_robo:SSO redirect failed. RC: 200 text: NOK', lcm.output)
        self.assertTrue(mock_instance.called)

    @patch('dkb_robo.DKBRobo._new_instance')
    def test_108_do_sso_redirect(self, mock_instance, _unused):
        """ test _do_sso_redirect() nok """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.text = 'OK'
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb._do_sso_redirect()
        self.assertIn('ERROR:dkb_robo:SSO redirect failed. RC: 400 text: OK', lcm.output)
        self.assertTrue(mock_instance.called)

    def test_109_get_mfa_methods(self, _unused):
        """ test _get_mfa_methods() """
        self.dkb.token_dic = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._get_mfa_methods()
        self.assertEqual('Login failed: no 1fa access token.', str(err.exception))

    def test_110_get_mfa_methods(self, _unused):
        """ test _get_mfa_methods() """
        self.dkb.token_dic = {'access_token': 'bar'}
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        with self.assertRaises(Exception) as err:
            self.dkb._get_mfa_methods()
        self.assertEqual('Login failed: getting mfa_methods failed. RC: 400', str(err.exception))

    def test_111_get_mfa_methods(self, _unused):
        """ test _get_mfa_methods() """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo1': 'bar1'}
        self.dkb.token_dic = {'access_token': 'bar'}
        self.assertEqual({'foo1': 'bar1'}, self.dkb._get_mfa_methods())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('time.sleep', return_value=None)
    def test_112__complete_2fa(self, _mock_sleep, mock_stdout, _unused):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 400
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._complete_2fa('challengeid', 'devicename'))
        self.assertIn('ERROR:dkb_robo:DKBRobo._complete_2fa(): polling request failed. RC: 400', lcm.output)
        self.assertIn('check your banking app on "devicename" and confirm login...', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('time.sleep', return_value=None)
    def test_113__complete_2fa(self, _mock_sleep, mock_stdout, _unused):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 400
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._complete_2fa('challengeid', None))
        self.assertIn('ERROR:dkb_robo:DKBRobo._complete_2fa(): polling request failed. RC: 400', lcm.output)
        self.assertIn('check your banking app and confirm login...', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('time.sleep', return_value=None)
    def test_114__complete_2fa(self, _mock_sleep, mock_stdout, _unused):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo1': 'bar1'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._complete_2fa('challengeid', 'devicename'))
        self.assertIn("ERROR:dkb_robo:DKBRobo._complete_2fa(): error parsing polling response: {'foo1': 'bar1'}", lcm.output)
        self.assertIn('check your banking app on "devicename" and confirm login...', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('time.sleep', return_value=None)
    def test_115__complete_2fa(self, _mock_sleep, mock_stdout, _unused):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.side_effect = [{'foo1': 'bar1'}, {'data': {'attributes': {'verificationStatus': 'processed'}}}]
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertTrue(self.dkb._complete_2fa('challengeid', 'devicename'))
        self.assertIn("ERROR:dkb_robo:DKBRobo._complete_2fa(): error parsing polling response: {'foo1': 'bar1'}", lcm.output)
        self.assertIn('check your banking app on "devicename" and confirm login...', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('time.sleep', return_value=None)
    def test_116__complete_2fa(self, _mock_sleep, mock_stdout, _unused):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.side_effect = [{'foo1': 'bar1'}, {'data': {'attributes': {'verificationStatus': 'canceled'}}}]
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            with self.assertRaises(Exception) as err:
                self.assertTrue(self.dkb._complete_2fa('challengeid', 'devicename'))
        self.assertEqual('2fa chanceled by user', str(err.exception))
        self.assertIn("ERROR:dkb_robo:DKBRobo._complete_2fa(): error parsing polling response: {'foo1': 'bar1'}", lcm.output)

    @patch('requests.session')
    def test_117_new_instance_new_session(self, mock_session, _unused):
        """ test _new_session() """
        mock_session.headers = {}
        client = self.dkb._new_session()
        exp_headers = {'Accept-Language': 'en-US,en;q=0.5', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'DNT': '1', 'Pragma': 'no-cache', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0'}
        self.assertEqual(exp_headers, client.headers)

    @patch('requests.session')
    def test_118_new_instance_new_session(self, mock_session, _unused):
        """ test _new_session() """
        mock_session.headers = {}
        self.dkb.proxies = 'proxies'
        client = self.dkb._new_session()
        self.assertEqual('proxies', client.proxies)

    @patch('requests.session')
    def test_119_new_instance_new_session(self, mock_session, _unused):
        """ test _new_session() """
        mock_session.headers = {}
        mock_session.get.return_value.status_code = 200
        mock_session.return_value.cookies = {'__Host-xsrf': 'foo'}
        client = self.dkb._new_session()
        exp_headers = {'Accept-Language': 'en-US,en;q=0.5', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'DNT': '1', 'Pragma': 'no-cache', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0', 'x-xsrf-token': 'foo'}
        self.assertEqual(exp_headers, client.headers)

    @patch('requests.session')
    def test_120_get_mfa_challenge_id(self, mock_session, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual((None, None), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_mfa_challenge_id(): mfa_dic has an unexpected data structure', lcm.output)

    @patch('requests.session')
    def test_121_get_mfa_challenge_id(self, mock_session, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual((None, None), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_mfa_challenge_id(): mfa_dic has an unexpected data structure', lcm.output)

    def test_122_get_mfa_challenge_id(self, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'data': [{'id': 'id', 'attributes': {'deviceName': 'deviceName', 'foo': 'bar'}}]}
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'data': {'type': 'mfa-challenge', 'id': 'id'}}
        self.dkb.mfa_method = 'mfa_method'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        self.assertEqual(('id', 'deviceName'), self.dkb._get_mfa_challenge_id(mfa_dic))

    def test_123_get_mfa_challenge_id(self, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'data': [{'id': 'id', 'attributes': {'foo': 'bar'}}]}
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'data': {'type': 'mfa-challenge', 'id': 'id'}}
        self.dkb.mfa_method = 'mfa_method'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('id', None), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_mfa_challenge_id(): unable to get deviceName', lcm.output)

    def test_124_get_mfa_challenge_id(self, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'data': [{'id': 'id', 'attributes': {'deviceName': 'deviceName', 'foo': 'bar'}}]}
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.json.return_value = {'data': {'type': 'mfa-challenge', 'id': 'id'}}
        self.dkb.mfa_method = 'mfa_method'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        with self.assertRaises(Exception) as err:
            self.assertEqual(('id', 'deviceName'), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertEqual('Login failed: post request to get the mfa challenges failed. RC: 400', str(err.exception))

    def test_125_get_mfa_challenge_id(self, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'data': [{'id': 'id', 'attributes': {'deviceName': 'deviceName', 'foo': 'bar'}}]}
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'data': {'type': 'unknown', 'id': 'id'}}
        self.dkb.mfa_method = 'mfa_method'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        with self.assertRaises(Exception) as err:
            self.assertEqual(('id', 'deviceName'), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertEqual("Login failed:: wrong challenge type: {'data': {'type': 'unknown', 'id': 'id'}}", str(err.exception))

    def test_126_get_mfa_challenge_id(self, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'data': [{'id': 'id', 'attributes': {'deviceName': 'deviceName', 'foo': 'bar'}}]}
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        self.dkb.mfa_method = 'mfa_method'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        with self.assertRaises(Exception) as err:
            self.assertEqual(('id', 'deviceName'), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertEqual("Login failed: challenge response format is other than expected: {'foo': 'bar'}", str(err.exception))

    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_127_login(self, mock_sess, mock_tok, mock_meth,_ununsed):
        """ test login() """
        self.dkb.token_dic = {'foo': 'bar'}
        mock_meth.return_value = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: no 1fa access token.', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_128_login(self, mock_sess, mock_tok, mock_meth, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'foo': 'bar'}
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: no 1fa access token.', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_129_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = (None, None)
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: No challenge id.', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._complete_2fa')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_130_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_2fa.return_value = False
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: mfa did not complete', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._do_sso_redirect')
    @patch('dkb_robo.DKBRobo._update_token')
    @patch('dkb_robo.DKBRobo._complete_2fa')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_131_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_gf, mock_po, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_2fa.return_value = True
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: mfa did not complete', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertFalse(mock_redir.called)
        self.assertFalse(mock_gf.called)
        self.assertFalse(mock_po.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._do_sso_redirect')
    @patch('dkb_robo.DKBRobo._update_token')
    @patch('dkb_robo.DKBRobo._complete_2fa')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_132_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_gf, mock_po, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_2fa.return_value = True
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: token_factor_type is missing', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertFalse(mock_redir.called)
        self.assertFalse(mock_gf.called)
        self.assertFalse(mock_po.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._do_sso_redirect')
    @patch('dkb_robo.DKBRobo._update_token')
    @patch('dkb_robo.DKBRobo._complete_2fa')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_133_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_gf, mock_po, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token', 'token_factor_type': 'token_factor_type'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_mfa.return_value = 0
        mock_2fa.return_value = True
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: 2nd factor authentication did not complete', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertFalse(mock_redir.called)
        self.assertFalse(mock_gf.called)
        self.assertFalse(mock_po.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._get_overview')
    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._do_sso_redirect')
    @patch('dkb_robo.DKBRobo._update_token')
    @patch('dkb_robo.DKBRobo._complete_2fa')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_134_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_mfa, mock_overview, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token', 'token_factor_type': '2fa'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_mfa.return_value = 0
        mock_2fa.return_value = True
        self.dkb._login()
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertTrue(mock_redir.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_overview.called)

    def test_135__select_mfa_device(self, _unused):
        """ test _select_mfa_device() """
        mfa_dic = {'foo': 'bar'}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_136__select_mfa_device(self, mock_input, mock_stdout, _unused):
        """ test _select_mfa_device() """
        mock_input.return_value=0
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[0] - device-1\n[1] - device-2\n", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_137__select_mfa_device(self, mock_input, mock_stdout, _unused):
        """ test _select_mfa_device() """
        mock_input.return_value=1
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(1, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[0] - device-1\n[1] - device-2\n", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_138__select_mfa_device(self, mock_input, mock_stdout, _unused):
        """ test _select_mfa_device() """
        mock_input.side_effect = [3, 0]
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[0] - device-1\n[1] - device-2\n", mock_stdout.getvalue())
        self.assertIn('Wrong input!', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_139__select_mfa_device(self, mock_input, mock_stdout, _unused):
        """ test _select_mfa_device() """
        mock_input.side_effect = ['a', 3, 0]
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[0] - device-1\n[1] - device-2\n", mock_stdout.getvalue())
        self.assertIn('Invalid input!', mock_stdout.getvalue())
        self.assertIn('Wrong input!', mock_stdout.getvalue())

    @patch('dkb_robo.DKBRobo._build_account_dic')
    @patch('dkb_robo.DKBRobo._get_loans')
    @patch('dkb_robo.DKBRobo._get_brokerage_accounts')
    @patch('dkb_robo.DKBRobo._get_cards')
    @patch('dkb_robo.DKBRobo._get_accounts')
    def test_140_get_overview(self, mock_acc, mock_cards, mock_br, mock_loans, mock_bac, _unused):
        """ test _get_overview() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.dkb._get_overview()
        self.assertTrue(mock_acc.called)
        self.assertTrue(mock_cards.called)
        self.assertTrue(mock_br.called)
        self.assertTrue(mock_loans.called)
        self.assertTrue(mock_bac.called)

    @patch('dkb_robo.DKBRobo._build_account_dic')
    @patch('dkb_robo.DKBRobo._get_loans')
    @patch('dkb_robo.DKBRobo._get_brokerage_accounts')
    @patch('dkb_robo.DKBRobo._get_cards')
    @patch('dkb_robo.DKBRobo._get_accounts')
    def test_141_get_overview(self, mock_acc, mock_cards, mock_br, mock_loans, mock_bac, _unused):
        """ test _get_overview() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.dkb._get_overview()
        self.assertFalse(mock_acc.called)
        self.assertFalse(mock_cards.called)
        self.assertFalse(mock_br.called)
        self.assertFalse(mock_loans.called)
        self.assertTrue(mock_bac.called)

    def test_142__get_account_details(self, _unused):
        """ test _get_account_details() """
        account_dic = {}
        self.assertFalse(self.dkb._get_account_details('aid', account_dic))

    @patch('dkb_robo.utilities._convert_date_format')
    def test_143__get_account_details(self, mock_date, _unused):
        """ test _get_account_details() """
        account_dic = {'data': [{'id': 'aid', 'attributes': {'iban': 'iban', 'product': {'displayName': 'displayName'}, 'holderName': 'holdername', 'balance': {'value': 'value', 'currencyCode': 'currencycode'}, 'overdraftLimit': 'overdraftLimit', 'updatedAt': 'updatedat'}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'account', 'id': 'aid', 'iban': 'iban', 'account': 'iban', 'name': 'displayName', 'holdername': 'holdername', 'amount': 'value', 'currencycode': 'currencycode', 'date': 'updatedat', 'limit': 'overdraftLimit', 'transactions': 'https://banking.dkb.de/api/accounts/accounts/aid/transactions'}
        self.assertEqual(result, self.dkb._get_account_details('aid', account_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_144__get_account_details(self, mock_date, _unused):
        """ test _get_account_details() """
        account_dic = {'data': [{'id': 'aid', 'attributes': {'iban': 'iban', 'product': {'displayName': 'displayName'}, 'holderName': 'holdername', 'balance': {'value': 'value', 'currencyCode': 'currencycode'}, 'overdraftLimit': 'overdraftLimit', 'updatedAt': 'updatedat'}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'account', 'id': 'aid', 'iban': 'iban', 'account': 'iban', 'name': 'displayName', 'holdername': 'holdername', 'amount': 'value', 'currencycode': 'currencycode', 'date': 'updatedat', 'limit': 'overdraftLimit', 'transactions': 'https://banking.dkb.de/api/accounts/accounts/aid/transactions'}
        self.assertEqual(result, self.dkb._get_account_details('aid', account_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_145__get_account_details(self, mock_date, _unused):
        """ test _get_account_details() """
        account_dic = {'data': [{'id': 'aid1', 'attributes': {'iban': 'iban', 'product': {'displayName': 'displayName'}, 'holderName': 'holdername', 'balance': {'value': 'value', 'currencyCode': 'currencycode'}, 'overdraftLimit': 'overdraftLimit', 'updatedAt': 'updatedat'}}, {'id': 'aid', 'attributes': {'iban': 'iban2', 'product': {'displayName': 'displayName2'}, 'holderName': 'holdername2', 'balance': {'value': 'value2', 'currencyCode': 'currencycode2'}, 'overdraftLimit': 'overdraftLimit2', 'updatedAt': 'updatedat2'}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'account', 'id': 'aid', 'iban': 'iban2', 'account': 'iban2', 'name': 'displayName2', 'holdername': 'holdername2', 'amount': 'value2', 'currencycode': 'currencycode2', 'date': 'updatedat2', 'limit': 'overdraftLimit2', 'transactions': 'https://banking.dkb.de/api/accounts/accounts/aid/transactions'}
        self.assertEqual(result, self.dkb._get_account_details('aid', account_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_146__get_card_details(self, mock_date, _unused):
        """ test _get_card_details() """
        card_dic = {}
        self.assertFalse(self.dkb._get_card_details('cid', card_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_147__get_card_details(self, mock_date, _unused):
        """ test _get_card_details() """
        card_dic = {}
        self.assertFalse(self.dkb._get_card_details('cid', card_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_148__get_card_details(self, mock_date, _unused):
        """ test _get_card_details() """
        card_dic = {'data': [{'id': 'cid'}]}
        self.assertFalse(self.dkb._get_card_details('cid', card_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_149__get_card_details(self, mock_date, _unused):
        """ test _get_card_details() """
        card_dic = {'data': [{'id': 'cid', 'type': 'creditCard', 'attributes': {'product': {'displayName': 'displayname'}, 'holder': {'person': {'firstName': 'firstname', 'lastName': 'lastname'}}, 'maskedPan': 'maskedPan', 'status': 'status', 'limit': {'value': 'value'}, 'balance': {'date': 'date', 'value': '101', 'currencyCode': 'currencycode'}}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'creditcard', 'id': 'cid', 'maskedpan': 'maskedPan', 'name': 'displayname', 'status': 'status', 'account': 'maskedPan', 'amount': -101.0, 'currencycode': 'currencycode', 'date': 'date', 'limit': 'value', 'holdername': 'firstname lastname', 'transactions': 'https://banking.dkb.de/api/credit-card/cards/cid/transactions'}
        self.assertEqual(result, self.dkb._get_card_details('cid', card_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_150__get_card_details(self, mock_date, _unused):
        """ test _get_card_details() """
        card_dic = {'data': [{'id': 'cid', 'type': 'debitCard', 'attributes': {'product': {'displayName': 'displayname'}, 'holder': {'person': {'firstName': 'firstname', 'lastName': 'lastname'}}, 'maskedPan': 'maskedPan', 'limit': {'value': 'value'}, 'balance': {'date': 'date', 'value': '101', 'currencyCode': 'currencycode'}}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'debitcard', 'id': 'cid', 'maskedpan': 'maskedPan', 'name': 'displayname', 'account': 'maskedPan', 'amount': -101.0, 'currencycode': 'currencycode', 'date': 'date', 'limit': 'value', 'holdername': 'firstname lastname', 'transactions': None}
        self.assertEqual(result, self.dkb._get_card_details('cid', card_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_151__get_brokerage_details(self, mock_date, _unused):
        """ test _get_brokerage_details() """
        brok_dic = {}
        mock_date.return_value = 'mock_date'
        self.assertFalse(self.dkb._get_brokerage_details('bid', brok_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_152__get_brokerage_details(self, mock_date, _unused):
        """ test _get_brokerage_details() """
        brok_dic = {'data': []}
        mock_date.return_value = 'mock_date'
        self.assertFalse(self.dkb._get_brokerage_details('bid', brok_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_153__get_brokerage_details(self, mock_date, _unused):
        """ test _get_brokerage_details() """
        brok_dic = {'data': [{'id': 'bid'}]}
        mock_date.return_value = 'mock_date'
        self.assertFalse(self.dkb._get_brokerage_details('bid', brok_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_154__get_brokerage_details(self, mock_date, _unused):
        """ test _get_brokerage_details() """
        brok_dic = {'data': [{'id': 'bid', 'attributes': {'holderName': 'holdername', 'depositAccountId': 'depositaccountid', 'brokerageAccountPerformance': {'currentValue': {'currencyCode': 'currentcycode', 'value': 'value'} }}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'depot', 'id': 'bid', 'holdername': 'holdername', 'name': 'holdername', 'account': 'depositaccountid', 'currencycode': 'currentcycode', 'amount': 'value', 'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/bid/positions?include=instrument%2Cquote'}
        self.assertEqual(result, self.dkb._get_brokerage_details('bid', brok_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_155__get_brokerage_details(self, mock_date, _unused):
        """ test _get_brokerage_details() """
        brok_dic = {'data': [{'id': 'bid', 'attributes': {'holderName': 'holdername', 'depositAccountId': 'depositaccountid', 'brokerageAccountPerformance': {'currentValue': {'currencyCode': 'currentcycode', 'value': 'value'} }}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'depot', 'id': 'bid', 'holdername': 'holdername', 'name': 'holdername', 'account': 'depositaccountid', 'currencycode': 'currentcycode', 'amount': 'value', 'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/bid/positions?include=instrument%2Cquote'}
        self.assertEqual(result, self.dkb._get_brokerage_details('bid', brok_dic))
        self.assertFalse(mock_date.called)

    def test_156__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = []
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        self.assertFalse(self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_157__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = [{'foo': 'bar', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo': 'bar', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_158__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_159__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-02-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_160__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype2', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_161__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype2', 'bookingDate': '2023-01-15'}}]
        from_date = '2023-01-01'
        to_date = '2023-01-31'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_162_format_card_transactions(self, _unused):
        """ _format_card_transactions() """
        transaction_list = []
        self.assertFalse(self.dkb._format_card_transactions(transaction_list))

    def test_163_format_card_transactions(self, _unused):
        """ _format_card_transactions() """
        transaction_list = [{'foo':'bar', 'attributes': {'description': 'description', 'bookingDate': '2023-01-01', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'CC', 'bdate': '2023-01-01', 'vdate': '2023-01-01', 'text': 'description'}]
        self.assertEqual(result, self.dkb._format_card_transactions(transaction_list))

    def test_164_format_card_transactions(self, _unused):
        """ _format_card_transactions() """
        transaction_list = [{'foo':'bar', 'attributes': {'bookingDate': '2023-01-01', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'CC', 'bdate': '2023-01-01', 'vdate': '2023-01-01'}]
        self.assertEqual(result, self.dkb._format_card_transactions(transaction_list))

    def test_165_format_card_transactions(self, _unused):
        """ _format_card_transactions() """
        transaction_list = [{'foo':'bar', 'attributes': {'description': 'description', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'CC', 'text': 'description'}]
        self.assertEqual(result, self.dkb._format_card_transactions(transaction_list))

    def test_166_format_brokerage_account(self, _unused):
        """ test _format_brokerage_account() """
        included_list = []
        data_dic = [{'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id'}}, 'quote': {'data': {'id': 'id', 'value': 'value'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_167_format_brokerage_account(self, _unused):
        """ test _format_brokerage_account() """
        included_list = []
        data_dic = [
            {'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id'}}, 'quote': {'data': {'id': 'id', 'value': 'value'}}}},
            {'attributes': {'performance': {'currentValue': {'value': 2000}}, 'lastOrderDate': '2020-02-01', 'quantity': {'value': 2000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id2'}}, 'quote': {'data': {'id': 'id2', 'value': 'value2'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000}, {'shares': 2000, 'quantity': 2000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-02-01', 'price_euro': 2000}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_168_format_brokerage_account(self, _unused):
        """ test _format_brokerage_account() """
        included_list = [{'id': 'inid', 'attributes': {'identifiers': [{'identifier': 'isin', 'value': 'value'}, {'identifier': 'isin', 'value': 'value2'}], 'name': {'short': 'short'}}}]
        data_dic = [{'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'inid'}}, 'quote': {'data': {'id': 'quoteid', 'value': 'value'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000, 'text': 'short', 'isin_wkn': 'value'}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_169_format_brokerage_account(self, _unused):
        """ test _format_brokerage_account() """
        included_list = [{'id': 'quoteid', 'attributes': {'market': 'market', 'price': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        data_dic = [{'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'inid'}}, 'quote': {'data': {'id': 'quoteid', 'value': 'value'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000, 'price': 1000.0, 'currencycode': 'currencyCode', 'market': 'market'}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_170_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'foo': 'bar'}]
        self.assertFalse(self.dkb._format_account_transactions(transaction_list))

    def test_171_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'debtor': {'name': 'name', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}, 'amount': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'peerid': '', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_172_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'debtor': {'intermediaryName': 'intermediaryName', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}, 'amount': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'intermediaryName', 'peerid': '', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType intermediaryName description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_173_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'debtor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}, 'amount': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'peerid': 'id', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_174_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'creditor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}, 'amount': {'value': -1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': -1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'peerid': 'id', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_175_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'mandateId': 'mandateId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'creditor': {'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}, 'amount': {'value': -1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': -1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'mandatereference': 'mandateId', 'peerid': '', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    @patch('dkb_robo.dkb_robo.validate_dates')
    @patch('dkb_robo.DKBRobo._get_transactions')
    @patch('dkb_robo.DKBRobo._legacy_get_transactions')
    def test_176_get_transactions(self, mock_legacy, mock_new, mock_date, _unused):
        """ test get_transactions() """
        mock_new.return_value = 'foo'
        mock_date.return_value = ('from', 'to')
        self.assertEqual('foo', self.dkb.get_transactions('url', 'atype', 'from', 'to', 'btype'))
        self.assertTrue(mock_new.called)
        self.assertFalse(mock_legacy.called)

    @patch('dkb_robo.dkb_robo.validate_dates')
    @patch('dkb_robo.DKBRobo._get_transactions')
    @patch('dkb_robo.DKBRobo._legacy_get_transactions')
    def test_177_get_transactions(self, mock_legacy, mock_new, mock_date, _unused):
        """ test get_transactions() """
        mock_legacy.return_value = 'foo_legacy'
        mock_date.return_value = ('from', 'to')
        self.dkb.legacy_login = True
        self.assertEqual('foo_legacy', self.dkb.get_transactions('url', 'atype', 'from', 'to', 'btype'))
        self.assertFalse(mock_new.called)
        self.assertTrue(mock_legacy.called)

    @patch('dkb_robo.dkb_robo.validate_dates')
    @patch('dkb_robo.DKBRobo._get_transactions')
    @patch('dkb_robo.DKBRobo._legacy_get_transactions')
    def test_178_get_transactions(self, mock_legacy, mock_new, mock_date, _unused):
        """ test get_transactions() """
        mock_new.return_value = 'foo'
        mock_date.return_value = ('from', 'to')
        self.dkb.legacy_login = False
        self.assertEqual('foo', self.dkb.get_transactions('url', 'atype', 'from', 'to', 'btype'))
        self.assertTrue(mock_new.called)
        self.assertFalse(mock_legacy.called)

    @patch('dkb_robo.DKBRobo._get_brokerage_details')
    @patch('dkb_robo.DKBRobo._get_card_details')
    @patch('dkb_robo.DKBRobo._get_account_details')
    def test_179_build_raw_account_dic(self, mock_acc, mock_card, mock_ba, _ununsed):
        """ teest _build_account_dic """
        portfolio_dic = {}
        self.assertFalse(self.dkb._build_raw_account_dic(portfolio_dic))
        self.assertFalse(mock_acc.called)
        self.assertFalse(mock_card.called)
        self.assertFalse(mock_ba.called)

    @patch('dkb_robo.DKBRobo._get_brokerage_details')
    @patch('dkb_robo.DKBRobo._get_card_details')
    @patch('dkb_robo.DKBRobo._get_account_details')
    def test_180_build_raw_account_dic(self, mock_acc, mock_card, mock_ba, _ununsed):
        """ teest _build_account_dic """
        portfolio_dic = {'accounts': {'data': [{'id': 'id', 'type': 'brokerageAccount', 'foo': 'bar'}]} }
        mock_ba.return_value = 'mock_ba'
        result = {'id': 'mock_ba'}
        self.assertEqual(result, self.dkb._build_raw_account_dic(portfolio_dic))
        self.assertFalse(mock_acc.called)
        self.assertFalse(mock_card.called)
        self.assertTrue(mock_ba.called)

    @patch('dkb_robo.DKBRobo._get_brokerage_details')
    @patch('dkb_robo.DKBRobo._get_card_details')
    @patch('dkb_robo.DKBRobo._get_account_details')
    def test_181_build_raw_account_dic(self, mock_acc, mock_card, mock_ba, _ununsed):
        """ teest _build_account_dic """
        portfolio_dic = {'cards': {'data': [{'id': 'id', 'type': 'fooCard', 'foo': 'bar'}]} }
        mock_card.return_value = 'mock_card'
        result = {'id': 'mock_card'}
        self.assertEqual(result, self.dkb._build_raw_account_dic(portfolio_dic))
        self.assertFalse(mock_acc.called)
        self.assertTrue(mock_card.called)
        self.assertFalse(mock_ba.called)

    @patch('dkb_robo.DKBRobo._get_brokerage_details')
    @patch('dkb_robo.DKBRobo._get_card_details')
    @patch('dkb_robo.DKBRobo._get_account_details')
    def test_182_build_raw_account_dic(self, mock_acc, mock_card, mock_ba, _ununsed):
        """ teest _build_account_dic """
        portfolio_dic = {'accounts': {'data': [{'id': 'id', 'type': 'account', 'foo': 'bar'}]} }
        mock_acc.return_value = 'mock_acc'
        result = {'id': 'mock_acc'}
        self.assertEqual(result, self.dkb._build_raw_account_dic(portfolio_dic))
        self.assertTrue(mock_acc.called)
        self.assertFalse(mock_card.called)
        self.assertFalse(mock_ba.called)

    def test_183_build_product_display_settings_dic(self, _unused):
        """ _build_product_display_settings_dic() """
        data_ele = {'foo': 'bar'}
        self.assertFalse(self.dkb._build_product_display_settings_dic(data_ele))

    def test_184_build_product_display_settings_dic(self, _unused):
        """ _build_product_display_settings_dic() """
        data_ele = {'attributes': {'foo': 'bar'}}
        self.assertFalse(self.dkb._build_product_display_settings_dic(data_ele))

    def test_185_build_product_display_settings_dic(self, _unused):
        """ _build_product_display_settings_dic() """
        data_ele = {'attributes': {'productSettings': {'foo': 'bar'}}}

        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._build_product_display_settings_dic(data_ele))
        self.assertIn('ERROR:dkb_robo:DKBRobo._build_product_display_settings_dic(): product_data is not of type dic', lcm.output)

    def test_186_build_product_display_settings_dic(self, _unused):
        """ _build_product_display_settings_dic() """
        data_ele = {'attributes': {'productSettings': {'product': {'uid': {'name': 'name'}}}}}
        self.assertEqual({'uid': 'name'}, self.dkb._build_product_display_settings_dic(data_ele))

    def test_187_build_product_display_settings_dic(self, _unused):
        """ _build_product_display_settings_dic() """
        data_ele = {'attributes': {'productSettings': {'product': {'uid': {'foo': 'bar'}}}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._build_product_display_settings_dic(data_ele))
        self.assertIn('ERROR:dkb_robo:DKBRobo._build_product_display_settings_dic(): "name" key not found', lcm.output)

    def test_188_build_product_group_list(self, _unused):
        """ test _build_product_group_list() """
        data_ele = {}
        self.assertFalse(self.dkb._build_product_group_list(data_ele))

    def test_189_build_product_group_list(self, _unused):
        """ test _build_product_group_list() """
        data_ele = {'attributes': {'productGroups': {'foo': {'index': 0, 'name': 'foo', 'products': {'product1': {'uid1': {'index': 1}, 'uid2': {'index': 0}}}}}}}
        self.assertEqual([{'name': 'foo', 'product_list': {1: 'uid1', 0: 'uid2'}}], self.dkb._build_product_group_list(data_ele))

    def test_190_build_product_group_list(self, _unused):
        """ test _build_product_group_list() """
        data_ele = {'attributes':
                    {'productGroups':
                                   {'foo': {'index': 0,
                                            'name': 'foo',
                                            'products': {
                                                'product1': {'uid1': {'index': 1}, 'uid2': {'index': 2}},
                                                'product2': {'uid3': {'index': 0}, 'uid4': {'index': 3}}
                                                }}}}}


        self.assertEqual([{'name': 'foo', 'product_list': {0: 'uid3', 1: 'uid1', 2: 'uid2', 3: 'uid4'}}], self.dkb._build_product_group_list(data_ele))

    def test_191_build_product_group_list(self, _unused):
        """ test _build_product_group_list() """
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
        self.assertEqual(result, self.dkb._build_product_group_list(data_ele))


    def test_192_build_account_dic(self, _unused):
        """ e22 build account dic """

        portfolio_dic = {
            'accounts': json_load(self.dir_path + '/mocks/accounts.json'),
            'cards': json_load(self.dir_path + '/mocks/cards.json'),
            'brokerage_accounts': json_load(self.dir_path + '/mocks/brokerage.json'),
            'product_display': json_load(self.dir_path + '/mocks/pd.json')}
        result = {0: {'account': '987654321',
                        'amount': '1234.56',
                        'currencycode': 'EUR',
                        'holdername': 'HolderName1',
                        'id': 'baccountid1',
                        'name': 'pdsettings brokeraage baccountid1',
                        'productgroup': 'productGroup name 1',
                        'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/baccountid1/positions?include=instrument%2Cquote',
                        'type': 'depot'},
                    1: {'account': 'AccountIBAN3',
                        'amount': '-1000.22',
                        'currencycode': 'EUR',
                        'date': '2020-03-01',
                        'holdername': 'Account HolderName 3',
                        'iban': 'AccountIBAN3',
                        'id': 'accountid3',
                        'limit': '2500.00',
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
                        'limit': '1000.00',
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
                        'limit': '0.00',
                        'maskedpan': 'maskedPan2',
                        'name': 'displayName2',
                        'productgroup': 'productGroup name 1',
                        'status': {'category': 'active', 'limitationsFor': []},
                        'transactions': 'https://banking.dkb.de/api/credit-card/cards/cardid2/transactions',
                        'type': 'creditcard'},
                    4: {'account': 'AccountIBAN2',
                        'amount': '1284.56',
                        'currencycode': 'EUR',
                        'date': '2020-02-01',
                        'holdername': 'Account HolderName 2',
                        'iban': 'AccountIBAN2',
                        'id': 'accountid2',
                        'limit': '0.00',
                        'name': 'pdsettings accoutname accountid2',
                        'productgroup': 'productGroup name 2',
                        'transactions': 'https://banking.dkb.de/api/accounts/accounts/accountid2/transactions',
                        'type': 'account'},
                    5: {'account': 'AccountIBAN1',
                        'amount': '12345.67',
                        'currencycode': 'EUR',
                        'date': '2020-01-01',
                        'holdername': 'Account HolderName 1',
                        'iban': 'AccountIBAN1',
                        'id': 'accountid1',
                        'limit': '1000.00',
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

        self.assertEqual(result, self.dkb._build_account_dic(portfolio_dic))

    def test_193_build_account_dic(self, _unused):
        """ e22 build account dic """

        portfolio_dic = {
            'accounts': json_load(self.dir_path + '/mocks/accounts.json'),
            'cards': json_load(self.dir_path + '/mocks/cards.json'),
            'brokerage_accounts': json_load(self.dir_path + '/mocks/brokerage.json'),
            'product_display': json_load(self.dir_path + '/mocks/pd.json')}

        # empty display dic
        portfolio_dic['product_display']['data'][0]['attributes']['productGroups'] = {}

        result = {0: {'account': 'AccountIBAN1',
                        'amount': '12345.67',
                        'currencycode': 'EUR',
                        'date': '2020-01-01',
                        'holdername': 'Account HolderName 1',
                        'iban': 'AccountIBAN1',
                        'id': 'accountid1',
                        'limit': '1000.00',
                        'name': 'Account DisplayName 1',
                        'productgroup': None,
                        'transactions': 'https://banking.dkb.de/api/accounts/accounts/accountid1/transactions',
                        'type': 'account'},
                    1: {'account': 'AccountIBAN2',
                        'amount': '1284.56',
                        'currencycode': 'EUR',
                        'date': '2020-02-01',
                        'holdername': 'Account HolderName 2',
                        'iban': 'AccountIBAN2',
                        'id': 'accountid2',
                        'limit': '0.00',
                        'name': 'Account DisplayName 2',
                        'productgroup': None,
                        'transactions': 'https://banking.dkb.de/api/accounts/accounts/accountid2/transactions',
                        'type': 'account'},
                    2: {'account': 'AccountIBAN3',
                        'amount': '-1000.22',
                        'currencycode': 'EUR',
                        'date': '2020-03-01',
                        'holdername': 'Account HolderName 3',
                        'iban': 'AccountIBAN3',
                        'id': 'accountid3',
                        'limit': '2500.00',
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
                        'limit': '1000.00',
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
                        'limit': '0.00',
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
                        'amount': '1234.56',
                        'currencycode': 'EUR',
                        'holdername': 'HolderName1',
                        'id': 'baccountid1',
                        'name': 'HolderName1',
                        'productgroup': None,
                        'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/baccountid1/positions?include=instrument%2Cquote',
                        'type': 'depot'}}

        self.assertEqual(result, self.dkb._build_account_dic(portfolio_dic))

    @patch('dkb_robo.DKBRobo._build_product_group_list')
    @patch('dkb_robo.DKBRobo._build_product_display_settings_dic')
    @patch('dkb_robo.DKBRobo._build_raw_account_dic')
    def test_194_build_account_dic(self, mock_raw, mock_dis, mock_grp, _unused):
        """ test build account dic """
        portfolio_dic = {}
        result = {}
        self.assertEqual(result, self.dkb._build_account_dic(portfolio_dic))
        self.assertTrue(mock_raw.called)
        self.assertFalse(mock_dis.called)
        self.assertFalse(mock_grp.called)

    @patch('dkb_robo.DKBRobo._build_product_group_list')
    @patch('dkb_robo.DKBRobo._build_product_display_settings_dic')
    @patch('dkb_robo.DKBRobo._build_raw_account_dic')
    def test_195_build_account_dic(self, mock_raw, mock_dis, mock_grp, _unused):
        """ test build account dic """
        portfolio_dic = {'product_display': {'data': ['foo']}}
        result = {}
        self.assertEqual(result, self.dkb._build_account_dic(portfolio_dic))
        self.assertTrue(mock_raw.called)
        self.assertTrue(mock_dis.called)
        self.assertTrue(mock_grp.called)

    @patch('dkb_robo.DKBRobo._build_product_group_list')
    @patch('dkb_robo.DKBRobo._build_product_display_settings_dic')
    @patch('dkb_robo.DKBRobo._build_raw_account_dic')
    def test_196_build_account_dic(self, mock_raw, mock_dis, mock_grp, _unused):
        """ test build account dic """
        portfolio_dic = {'product_display': {'data': ['foo']}}
        mock_raw.return_value = {'dic_id1': {'foo': 'bar1'}, 'dic_id2': {'foo': 'bar2'}, 'dic_id3': {'foo': 'bar3'}, 'dic_id4': {'foo': 'bar4'}, 'dic_id5': {'foo': 'bar5'}}
        mock_dis.return_value = {}
        mock_grp.return_value = [{'name': 'mylist1', 'product_list': {0: 'dic_id1', 2: 'dic_id4', 1: 'dic_list5'}}, {'name': 'mylist2', 'product_list': {0: 'dic_id2', 1: 'dic_id3'}}]
        result = {0: {'foo': 'bar1', 'productgroup': 'mylist1'}, 1: {'foo': 'bar4', 'productgroup': 'mylist1'}, 2: {'foo': 'bar2', 'productgroup': 'mylist2'}, 3: {'foo': 'bar3', 'productgroup': 'mylist2'}, 4: {'foo': 'bar5', 'productgroup': None}}
        self.assertEqual(result, self.dkb._build_account_dic(portfolio_dic))
        self.assertTrue(mock_raw.called)
        self.assertTrue(mock_dis.called)
        self.assertTrue(mock_grp.called)

    @patch('dkb_robo.DKBRobo._build_product_group_list')
    @patch('dkb_robo.DKBRobo._build_product_display_settings_dic')
    @patch('dkb_robo.DKBRobo._build_raw_account_dic')
    def test_197_build_account_dic(self, mock_raw, mock_dis, mock_grp, _unused):
        """ test build account dic """
        portfolio_dic = {'product_display': {'data': ['foo']}}
        mock_raw.return_value = {'dic_id1': {'foo': 'bar1'}, 'dic_id2': {'foo': 'bar2'}, 'dic_id3': {'foo': 'bar3'}, 'dic_id4': {'foo': 'bar4'}, 'dic_id5': {'foo': 'bar5'}}
        mock_dis.return_value = {'dic_id2': 'changed_name2', 'dic_id4': 'changed_name4'}
        mock_grp.return_value = [{'name': 'mylist1', 'product_list': {0: 'dic_id1', 2: 'dic_id4', 1: 'dic_list5'}}, {'name': 'mylist2', 'product_list': {0: 'dic_id2', 1: 'dic_id3'}}]
        result = {0: {'foo': 'bar1', 'productgroup': 'mylist1'}, 1: {'foo': 'bar4', 'productgroup': 'mylist1', 'name': 'changed_name4'}, 2: {'foo': 'bar2', 'productgroup': 'mylist2', 'name': 'changed_name2'}, 3: {'foo': 'bar3', 'productgroup': 'mylist2'}, 4: {'foo': 'bar5', 'productgroup': None}}
        self.assertEqual(result, self.dkb._build_account_dic(portfolio_dic))
        self.assertTrue(mock_raw.called)
        self.assertTrue(mock_dis.called)
        self.assertTrue(mock_grp.called)

    @patch('dkb_robo.DKBRobo._get_credit_limits')
    @patch('dkb_robo.DKBRobo._legacy_get_credit_limits')
    def test_198_get_credit_limits(self, mock_lcr, mock_cr, _unused):
        """ test get_credit_limits()"""
        mock_cr.return_value = 'mock_cr'
        mock_lcr.return_value = 'mock_lcr'
        self.assertEqual('mock_cr', self.dkb.get_credit_limits())
        self.assertTrue(mock_cr.called)
        self.assertFalse(mock_lcr.called)

    @patch('dkb_robo.DKBRobo._get_credit_limits')
    @patch('dkb_robo.DKBRobo._legacy_get_credit_limits')
    def test_199_get_credit_limits(self, mock_lcr, mock_cr, _unused):
        """ test get_credit_limits()"""
        mock_cr.return_value = 'mock_cr'
        mock_lcr.return_value = 'mock_lcr'
        self.dkb.legacy_login = True
        self.assertEqual('mock_lcr', self.dkb.get_credit_limits())
        self.assertFalse(mock_cr.called)
        self.assertTrue(mock_lcr.called)


    @patch('dkb_robo.DKBRobo._get_standing_orders')
    @patch('dkb_robo.DKBRobo._legacy_get_standing_orders')
    def test_200_get_standing_orders(self, mock_lso, mock_so, _unused):
        """ test get_standing_orders()"""
        mock_so.return_value = 'mock_cr'
        mock_lso.return_value = 'mock_lcr'
        self.assertEqual('mock_cr', self.dkb.get_standing_orders())
        self.assertTrue(mock_so.called)
        self.assertFalse(mock_lso.called)

    @patch('dkb_robo.DKBRobo._get_standing_orders')
    @patch('dkb_robo.DKBRobo._legacy_get_standing_orders')
    def test_201_get_standing_orders(self, mock_lso, mock_so, _unused):
        """ test get_standing_orders()"""
        mock_so.return_value = 'mock_cr'
        mock_lso.return_value = 'mock_lcr'
        self.dkb.legacy_login = True
        self.assertEqual('mock_lcr', self.dkb.get_standing_orders())
        self.assertFalse(mock_so.called)
        self.assertTrue(mock_lso.called)

    def test_202__get_credit_limits(self, _unused):
        """ teest _get_credit_limits() """
        account_dic = {0: {'limit': 1000, 'iban': 'iban'}, 1: {'limit': 2000, 'maskedpan': 'maskedpan'}}
        result_dic = {'iban': 1000, 'maskedpan': 2000}
        self.assertEqual(result_dic, self.dkb._get_credit_limits(account_dic))

    def test_203__get_credit_limits(self, _unused):
        """ teest _get_credit_limits() """
        account_dic = {'foo': 'bar'}
        self.assertFalse(self.dkb._get_credit_limits(account_dic))

    @patch('dkb_robo.DKBRobo._filter_standing_orders')
    def test_204___get_standing_orders(self, mock_filter, _unused):
        """ test _get_standing_orders() """
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb._get_standing_orders())
        self.assertEqual('get_standing_orders(): account-id is required', str(err.exception))
        self.assertFalse(mock_filter.called)

    @patch('dkb_robo.DKBRobo._filter_standing_orders')
    def test_205___get_standing_orders(self, mock_filter, _unused):
        """ test _get_standing_orders() """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertFalse(self.dkb._get_standing_orders(uid='uid'))
        self.assertFalse(mock_filter.called)

    @patch('dkb_robo.DKBRobo._filter_standing_orders')
    def test_206___get_standing_orders(self, mock_filter, _unused):
        """ test _get_standing_orders() """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        mock_filter.return_value = 'mock_filter'
        self.assertEqual('mock_filter', self.dkb._get_standing_orders(uid='uid'))
        self.assertTrue(mock_filter.called)

    def test_207__filter_standing_orders(self, _unused):
        """ test _filter_standing_orders() """
        full_list = {}
        self.assertFalse(self.dkb._filter_standing_orders(full_list))

    def test_208__filter_standing_orders(self, _unused):
        """ test _filter_standing_orders() """
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
        self.assertEqual(result, self.dkb._filter_standing_orders(full_list))

    def test_209_add_cardlimit(self, _unused):
        """ test _add_cardlimit() """
        card = {'attributes': {'expiryDate': 'expiryDate', 'limit': {'value': 'value', 'foo': 'bar'}}}
        result = {'expirydate': 'expiryDate', 'limit': 'value'}
        self.assertEqual(result, self.dkb._add_cardlimit(card))

    def test_210_filter_standing_orders(self, _unused):
        """ e2e get_standing_orders() """
        so_list = json_load(self.dir_path + '/mocks/so.json')
        result = [{'amount': 100.0, 'currencycode': 'EUR', 'purpose': 'description1', 'recpipient': 'name1', 'creditoraccount': {'iban': 'iban1', 'bic': 'bic1'}, 'interval': {'from': '2022-01-01', 'until': '2025-12-01', 'frequency': 'monthly', 'holidayExecutionStrategy': 'following', 'nextExecutionAt': '2022-11-01'}}, {'amount': 200.0, 'currencycode': 'EUR', 'purpose': 'description2', 'recpipient': 'name2', 'creditoraccount': {'iban': 'iban2', 'bic': 'bic2'}, 'interval': {'from': '2022-02-01', 'until': '2025-12-02', 'frequency': 'monthly', 'holidayExecutionStrategy': 'following', 'nextExecutionAt': '2022-11-02'}}, {'amount': 300.0, 'currencycode': 'EUR', 'purpose': 'description3', 'recpipient': 'name3', 'creditoraccount': {'iban': 'iban3', 'bic': 'bic3'}, 'interval': {'from': '2022-03-01', 'until': '2025-03-01', 'frequency': 'monthly', 'holidayExecutionStrategy': 'following', 'nextExecutionAt': '2022-03-01'}}]
        self.assertEqual(result, self.dkb._filter_standing_orders(so_list))


if __name__ == '__main__':

    unittest.main()
