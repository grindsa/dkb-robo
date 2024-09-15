# -*- coding: utf-8 -*-
# pylint: disable=r0904, c0415, c0413, r0913, w0212
""" unittests for dkb_robo """
import sys
import os
from datetime import date
import unittest
import logging
import json
from unittest.mock import patch, Mock, mock_open
from bs4 import BeautifulSoup
from mechanicalsoup import LinkNotFoundError
import io
sys.path.insert(0, '.')
sys.path.insert(0, '..')
from dkb_robo.api import Wrapper


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


def my_side_effect(*args):
    """ my sideeffect funtion """
    return [200, args[1], [args[4]]]


class TestDKBRobo(unittest.TestCase):
    """ test class """

    maxDiff = None

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')
        self.dkb = Wrapper(logger=self.logger)

    def test_001_get_accounts(self):
        """ test _get_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_accounts())

    def test_002_get_accounts(self):
        """ test _get_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_accounts())
        self.assertIn('ERROR:dkb_robo:api.Wrapper._get_accounts(): RC is not 200 but 400', lcm.output)

    def test_003_get_brokerage_accounts(self):
        """ test _get_brokerage_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_brokerage_accounts())

    def test_004_get_brokerage_accounts(self):
        """ test _get_brokerage_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_brokerage_accounts())
        self.assertIn('ERROR:dkb_robo:api.Wrapper._get_brokerage_accounts(): RC is not 200 but 400', lcm.output)

    def test_005_get_cards(self):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_cards())

    def test_006_get_cards(self):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_cards())
        self.assertIn('ERROR:dkb_robo:api.Wrapper._get_cards(): RC is not 200 but 400', lcm.output)

    def test_007_get_loans(self):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_loans())

    def test_008_get_loans(self):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_loans())
        self.assertIn('ERROR:dkb_robo:api.Wrapper._get_loans(): RC is not 200 but 400', lcm.output)

    @patch('dkb_robo.api.Wrapper._format_brokerage_account')
    @patch('dkb_robo.api.Wrapper._format_card_transactions')
    @patch('dkb_robo.api.Wrapper._format_account_transactions')
    @patch('dkb_robo.api.Wrapper._filter_transactions')
    def test_009_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        atype = 'account'
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb.get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertIn('ERROR:dkb_robo:api.Wrapper._get_transactions(): RC is not 200 but 400', lcm.output)
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.api.Wrapper._format_brokerage_account')
    @patch('dkb_robo.api.Wrapper._format_card_transactions')
    @patch('dkb_robo.api.Wrapper._format_account_transactions')
    @patch('dkb_robo.api.Wrapper._filter_transactions')
    def test_010_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {}
        atype = 'account'
        self.assertFalse(self.dkb.get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_atrans.called)

    @patch('dkb_robo.api.Wrapper._format_brokerage_account')
    @patch('dkb_robo.api.Wrapper._format_card_transactions')
    @patch('dkb_robo.api.Wrapper._format_account_transactions')
    @patch('dkb_robo.api.Wrapper._filter_transactions')
    def test_011_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        atype = 'account'
        self.assertFalse(self.dkb.get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.api.Wrapper._format_brokerage_account')
    @patch('dkb_robo.api.Wrapper._format_card_transactions')
    @patch('dkb_robo.api.Wrapper._format_account_transactions')
    @patch('dkb_robo.api.Wrapper._filter_transactions')
    def test_012_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'data': {'foo': 'bar'}}
        atype = 'account'
        mock_atrans.return_value = {'mock_foo': 'mock_bar'}
        self.assertEqual({'mock_foo': 'mock_bar'}, self.dkb.get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertTrue(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.api.Wrapper._format_brokerage_account')
    @patch('dkb_robo.api.Wrapper._format_card_transactions')
    @patch('dkb_robo.api.Wrapper._format_account_transactions')
    @patch('dkb_robo.api.Wrapper._filter_transactions')
    def test_013_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'data': {'foo': 'bar'}}
        atype = 'creditcard'
        mock_ctrans.return_value = {'mock_foo': 'mock_bar'}
        self.assertEqual({'mock_foo': 'mock_bar'}, self.dkb.get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertTrue(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.api.Wrapper._format_brokerage_account')
    @patch('dkb_robo.api.Wrapper._format_card_transactions')
    @patch('dkb_robo.api.Wrapper._format_account_transactions')
    @patch('dkb_robo.api.Wrapper._filter_transactions')
    def test_014_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'data': {'foo': 'bar'}}
        atype = 'depot'
        mock_btrans.return_value = {'mock_foo': 'mock_bar'}
        self.assertEqual({'mock_foo': 'mock_bar'}, self.dkb.get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertTrue(mock_btrans.called)

    def test_015_update_token(self):
        """ test _update_token() ok """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token'}
        self.dkb.client = Mock()
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        self.dkb._update_token()
        self.assertEqual({'foo': 'bar'}, self.dkb.token_dic)

    def test_016_update_token(self):
        """ test _update_token() nok """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token'}
        self.dkb.client = Mock()
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._update_token()
        self.assertEqual('Login failed: token update failed. RC: 400', str(err.exception))
        self.assertEqual({'mfa_id': 'mfa_id', 'access_token': 'access_token'}, self.dkb.token_dic)

    def test_017_get_token(self):
        """ test _get_token() ok """
        self.dkb.dkb_user = 'dkb_user'
        self.dkb.dkb_password = 'dkb_password'
        self.dkb.client = Mock()
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        self.dkb._get_token()
        self.assertEqual({'foo': 'bar'}, self.dkb.token_dic)

    def test_018_get_token(self):
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

    @patch('dkb_robo.legacy.Wrapper._new_instance')
    def test_019_do_sso_redirect(self, mock_instance):
        """ test _do_sso_redirect() ok """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.text = 'OK'
        self.dkb._do_sso_redirect()
        self.assertTrue(mock_instance.called)

    @patch('dkb_robo.legacy.Wrapper._new_instance')
    def test_020_do_sso_redirect(self, mock_instance):
        """ test _do_sso_redirect() nok """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.text = 'NOK'
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb._do_sso_redirect()
        self.assertIn('ERROR:dkb_robo:SSO redirect failed. RC: 200 text: NOK', lcm.output)
        self.assertTrue(mock_instance.called)

    @patch('dkb_robo.legacy.Wrapper._new_instance')
    def test_021_do_sso_redirect(self, mock_instance):
        """ test _do_sso_redirect() nok """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.text = 'OK'
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb._do_sso_redirect()
        self.assertIn('ERROR:dkb_robo:SSO redirect failed. RC: 400 text: OK', lcm.output)
        self.assertTrue(mock_instance.called)

    def test_022_get_mfa_methods(self):
        """ test _get_mfa_methods() """
        self.dkb.token_dic = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._get_mfa_methods()
        self.assertEqual('Login failed: no 1fa access token.', str(err.exception))

    def test_023_get_mfa_methods(self):
        """ test _get_mfa_methods() """
        self.dkb.token_dic = {'access_token': 'bar', 'mfa_id': 'mfa_id'}
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        with self.assertRaises(Exception) as err:
            self.dkb._get_mfa_methods()
        self.assertEqual('Login failed: getting mfa_methods failed. RC: 400', str(err.exception))

    def test_024_get_mfa_methods(self):
        """ test _get_mfa_methods() """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo1': 'bar1'}
        self.dkb.token_dic = {'access_token': 'bar', 'mfa_id': 'mfa_id'}
        self.assertEqual({'foo1': 'bar1'}, self.dkb._get_mfa_methods())

    def test_025_check_check_processing_status(self):
        """ test _check_processing_status() """
        polling_dic = {}
        with self.assertRaises(Exception) as err:
            self.assertEqual(False, self.dkb._check_processing_status(polling_dic, 1))
        self.assertEqual('Login failed: processing status format is other than expected', str(err.exception))

    def test_026_check_check_processing_status(self):
        """ test _check_processing_status() """
        polling_dic = {'data': {'attributes': {'verificationStatus': 'foo'}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(False, self.dkb._check_processing_status(polling_dic, 1))
        self.assertIn('INFO:dkb_robo:Unknown processing status: foo', lcm.output)

    def test_027_check_check_processing_status(self):
        """ test _check_processing_status() """
        polling_dic = {'data': {'attributes': {'verificationStatus': 'processed'}}}
        self.assertEqual(True, self.dkb._check_processing_status(polling_dic, 1))

    def test_028_check_check_processing_status(self):
        """ test _check_processing_status() """
        polling_dic = {'data': {'attributes': {'verificationStatus': 'canceled'}}}
        with self.assertRaises(Exception) as err:
            self.assertEqual(True, self.dkb._check_processing_status(polling_dic, 1))
        self.assertEqual('2fa chanceled by user', str(err.exception))

    def test_029_check_check_processing_status(self):
        """ test _check_processing_status() """
        polling_dic = {'data': {'attributes': {'verificationStatus': 'processing'}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(False, self.dkb._check_processing_status(polling_dic, 1))
        self.assertIn('INFO:dkb_robo:Status: processing. Waiting for confirmation', lcm.output)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_029_print_app_2fa_confirmation(self, mock_stdout):
        """ test _print_app_2fa_confirmation()"""
        self.dkb._print_app_2fa_confirmation(None)
        self.assertIn('check your banking app and confirm login...', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_030_print_app_2fa_confirmation(self, mock_stdout):
        """ test _print_app_2fa_confirmation()"""
        self.dkb._print_app_2fa_confirmation('devicename')
        self.assertIn('check your banking app on "devicename" and confirm login...', mock_stdout.getvalue())

    @patch('requests.session')
    def test_031_new_instance_new_session(self, mock_session):
        """ test _new_session() """
        mock_session.headers = {}
        client = self.dkb._new_session()
        exp_headers = {'Accept-Language': 'en-US,en;q=0.5', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'DNT': '1', 'Pragma': 'no-cache', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0', 'priority': 'u=0', 'sec-gpc': '1', 'te': 'trailers'}
        self.assertEqual(exp_headers, client.headers)

    @patch('requests.session')
    def test_032_new_instance_new_session(self, mock_session):
        """ test _new_session() """
        mock_session.headers = {}
        self.dkb.proxies = 'proxies'
        client = self.dkb._new_session()
        self.assertEqual('proxies', client.proxies)

    @patch('requests.session')
    def test_033_new_instance_new_session(self, mock_session):
        """ test _new_session() """
        mock_session.headers = {}
        mock_session.get.return_value.status_code = 200
        mock_session.return_value.cookies = {'__Host-xsrf': 'foo'}
        client = self.dkb._new_session()
        exp_headers = {'Accept-Language': 'en-US,en;q=0.5', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'DNT': '1', 'Pragma': 'no-cache', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0', 'x-xsrf-token': 'foo', 'priority': 'u=0', 'sec-gpc': '1', 'te': 'trailers'}
        self.assertEqual(exp_headers, client.headers)

    @patch('dkb_robo.api.Wrapper._sort_mfa_devices')
    @patch('dkb_robo.api.Wrapper._get_mfa_methods')
    @patch('dkb_robo.api.Wrapper._get_token')
    @patch('dkb_robo.api.Wrapper._new_session')
    def test_034_login(self, mock_sess, mock_tok, mock_meth, mock_sort):
        """ test login() """
        self.dkb.token_dic = {'foo': 'bar'}
        mock_meth.return_value = {'foo': 'bar'}
        mock_sort.return_value = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb.login()
        self.assertEqual('Login failed: no 1fa access token.', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)

    @patch('dkb_robo.api.Wrapper._sort_mfa_devices')
    @patch('dkb_robo.api.Wrapper._select_mfa_device')
    @patch('dkb_robo.api.Wrapper._get_mfa_methods')
    @patch('dkb_robo.api.Wrapper._get_token')
    @patch('dkb_robo.api.Wrapper._new_session')
    def test_035_login(self, mock_sess, mock_tok, mock_meth, mock_mfa, mock_sort):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'foo': 'bar'}
        mock_sort.return_value = {'foo': 'bar'}
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb.login()
        self.assertEqual('Login failed: no 1fa access token.', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch('dkb_robo.api.Wrapper._sort_mfa_devices')
    @patch('dkb_robo.api.Wrapper._select_mfa_device')
    @patch('dkb_robo.api.Wrapper._get_mfa_challenge_dic')
    @patch('dkb_robo.api.Wrapper._get_mfa_methods')
    @patch('dkb_robo.api.Wrapper._get_token')
    @patch('dkb_robo.api.Wrapper._new_session')
    def test_036_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_mfa, mock_sort):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'data': 'bar'}
        mock_sort.return_value = {'data': 'bar'}
        mock_chall.return_value = (None, None)
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb.login()
        self.assertEqual('Login failed: No challenge id.', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch('dkb_robo.api.Wrapper._sort_mfa_devices')
    @patch('dkb_robo.api.Wrapper._select_mfa_device')
    @patch('dkb_robo.api.Wrapper._complete_2fa')
    @patch('dkb_robo.api.Wrapper._get_mfa_challenge_dic')
    @patch('dkb_robo.api.Wrapper._get_mfa_methods')
    @patch('dkb_robo.api.Wrapper._get_token')
    @patch('dkb_robo.api.Wrapper._new_session')
    def test_037_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_mfa, mock_sort):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'data': 'bar'}
        mock_sort.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_2fa.return_value = False
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb.login()
        self.assertEqual('Login failed: mfa did not complete', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch('dkb_robo.api.Wrapper._sort_mfa_devices')
    @patch('dkb_robo.api.Wrapper._select_mfa_device')
    @patch('dkb_robo.api.Wrapper._do_sso_redirect')
    @patch('dkb_robo.api.Wrapper._update_token')
    @patch('dkb_robo.api.Wrapper._complete_2fa')
    @patch('dkb_robo.api.Wrapper._get_mfa_challenge_dic')
    @patch('dkb_robo.api.Wrapper._get_mfa_methods')
    @patch('dkb_robo.api.Wrapper._get_token')
    @patch('dkb_robo.api.Wrapper._new_session')
    def test_038_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_mfa, mock_sort):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'data': 'bar'}
        mock_sort.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_2fa.return_value = True
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb.login()
        self.assertEqual('Login failed: mfa did not complete', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertFalse(mock_redir.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch('dkb_robo.api.Wrapper._sort_mfa_devices')
    @patch('dkb_robo.api.Wrapper._select_mfa_device')
    @patch('dkb_robo.api.Wrapper._do_sso_redirect')
    @patch('dkb_robo.api.Wrapper._update_token')
    @patch('dkb_robo.api.Wrapper._complete_2fa')
    @patch('dkb_robo.api.Wrapper._get_mfa_challenge_dic')
    @patch('dkb_robo.api.Wrapper._get_mfa_methods')
    @patch('dkb_robo.api.Wrapper._get_token')
    @patch('dkb_robo.api.Wrapper._new_session')
    def test_039_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_mfa, mock_sort):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token'}
        mock_meth.return_value = {'data': 'bar'}
        mock_sort.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_2fa.return_value = True
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb.login()
        self.assertEqual('Login failed: token_factor_type is missing', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertFalse(mock_redir.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch('dkb_robo.api.Wrapper._sort_mfa_devices')
    @patch('dkb_robo.api.Wrapper._select_mfa_device')
    @patch('dkb_robo.api.Wrapper._do_sso_redirect')
    @patch('dkb_robo.api.Wrapper._update_token')
    @patch('dkb_robo.api.Wrapper._complete_2fa')
    @patch('dkb_robo.api.Wrapper._get_mfa_challenge_dic')
    @patch('dkb_robo.api.Wrapper._get_mfa_methods')
    @patch('dkb_robo.api.Wrapper._get_token')
    @patch('dkb_robo.api.Wrapper._new_session')
    def test_040_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_mfa, mock_sort):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token', 'token_factor_type': 'token_factor_type'}
        mock_meth.return_value = {'data': 'bar'}
        mock_sort.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_mfa.return_value = 0
        mock_2fa.return_value = True
        with self.assertRaises(Exception) as err:
            self.dkb.login()
        self.assertEqual('Login failed: 2nd factor authentication did not complete', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertFalse(mock_redir.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch('dkb_robo.api.Wrapper._sort_mfa_devices')
    @patch('dkb_robo.api.Wrapper._get_overview')
    @patch('dkb_robo.api.Wrapper._select_mfa_device')
    @patch('dkb_robo.api.Wrapper._do_sso_redirect')
    @patch('dkb_robo.api.Wrapper._update_token')
    @patch('dkb_robo.api.Wrapper._complete_2fa')
    @patch('dkb_robo.api.Wrapper._get_mfa_challenge_dic')
    @patch('dkb_robo.api.Wrapper._get_mfa_methods')
    @patch('dkb_robo.api.Wrapper._get_token')
    @patch('dkb_robo.api.Wrapper._new_session')
    def test_041_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_mfa, mock_overview, mock_sort):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token', 'token_factor_type': '2fa'}
        mock_meth.return_value = {'data': 'bar'}
        mock_sort.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_mfa.return_value = 0
        mock_2fa.return_value = True
        self.dkb.login()
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertTrue(mock_redir.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_overview.called)

    def test_042__select_mfa_device(self):
        """ test _select_mfa_device() """
        mfa_dic = {'foo': 'bar'}
        self.dkb.mfa_device = 1
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))

    def test_043__select_mfa_device(self):
        """ test _select_mfa_device() """
        mfa_dic = {'foo': 'bar'}
        self.dkb.mfa_device = 2
        self.assertEqual(1, self.dkb._select_mfa_device(mfa_dic))

    def test_044__select_mfa_device(self):
        """ test _select_mfa_device() """
        mfa_dic = {'foo': 'bar'}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_045__select_mfa_device(self, mock_input, mock_stdout):
        """ test _select_mfa_device() """
        mock_input.return_value=1
        self.dkb.mfa_device = 0
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_046__select_mfa_device(self, mock_input, mock_stdout):
        """ test _select_mfa_device() """
        mock_input.return_value=1
        self.dkb.mfa_device = 4
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn('WARNING:dkb_robo:User submitted mfa_device number is invalid. Ingoring...', lcm.output)
        self.assertIn("\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_047__select_mfa_device(self, mock_input, mock_stdout):
        """ test _select_mfa_device() """
        mock_input.return_value=1
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_048__select_mfa_device(self, mock_input, mock_stdout):
        """ test _select_mfa_device() """
        mock_input.return_value=2
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(1, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_049__select_mfa_device(self, mock_input, mock_stdout):
        """ test _select_mfa_device() """
        mock_input.side_effect = [4, 1]
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n", mock_stdout.getvalue())
        self.assertIn('Wrong input!', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_050__select_mfa_device(self, mock_input, mock_stdout):
        """ test _select_mfa_device() """
        mock_input.side_effect = ['a', 4, 1]
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n", mock_stdout.getvalue())
        self.assertIn('Invalid input!', mock_stdout.getvalue())
        self.assertIn('Wrong input!', mock_stdout.getvalue())

    @patch('dkb_robo.api.Wrapper._build_account_dic')
    @patch('dkb_robo.api.Wrapper._get_loans')
    @patch('dkb_robo.api.Wrapper._get_brokerage_accounts')
    @patch('dkb_robo.api.Wrapper._get_cards')
    @patch('dkb_robo.api.Wrapper._get_accounts')
    def test_051_get_overview(self, mock_acc, mock_cards, mock_br, mock_loans, mock_bac):
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

    @patch('dkb_robo.api.Wrapper._build_account_dic')
    @patch('dkb_robo.api.Wrapper._get_loans')
    @patch('dkb_robo.api.Wrapper._get_brokerage_accounts')
    @patch('dkb_robo.api.Wrapper._get_cards')
    @patch('dkb_robo.api.Wrapper._get_accounts')
    def test_052_get_overview(self, mock_acc, mock_cards, mock_br, mock_loans, mock_bac):
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

    def test_053__get_account_details(self):
        """ test _get_account_details() """
        account_dic = {}
        self.assertFalse(self.dkb._get_account_details('aid', account_dic))

    @patch('dkb_robo.utilities._convert_date_format')
    def test_054__get_account_details(self, mock_date):
        """ test _get_account_details() """
        account_dic = {'data': [{'id': 'aid', 'attributes': {'iban': 'iban', 'product': {'displayName': 'displayName'}, 'holderName': 'holdername', 'balance': {'value': 'value', 'currencyCode': 'currencycode'}, 'overdraftLimit': 'overdraftLimit', 'updatedAt': 'updatedat'}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'account', 'id': 'aid', 'iban': 'iban', 'account': 'iban', 'name': 'displayName', 'holdername': 'holdername', 'amount': 'value', 'currencycode': 'currencycode', 'date': 'updatedat', 'limit': 'overdraftLimit', 'transactions': 'https://banking.dkb.de/api/accounts/accounts/aid/transactions'}
        self.assertEqual(result, self.dkb._get_account_details('aid', account_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_055__get_account_details(self, mock_date):
        """ test _get_account_details() """
        account_dic = {'data': [{'id': 'aid', 'attributes': {'iban': 'iban', 'product': {'displayName': 'displayName'}, 'holderName': 'holdername', 'balance': {'value': 'value', 'currencyCode': 'currencycode'}, 'overdraftLimit': 'overdraftLimit', 'updatedAt': 'updatedat'}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'account', 'id': 'aid', 'iban': 'iban', 'account': 'iban', 'name': 'displayName', 'holdername': 'holdername', 'amount': 'value', 'currencycode': 'currencycode', 'date': 'updatedat', 'limit': 'overdraftLimit', 'transactions': 'https://banking.dkb.de/api/accounts/accounts/aid/transactions'}
        self.assertEqual(result, self.dkb._get_account_details('aid', account_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_056__get_account_details(self, mock_date):
        """ test _get_account_details() """
        account_dic = {'data': [{'id': 'aid1', 'attributes': {'iban': 'iban', 'product': {'displayName': 'displayName'}, 'holderName': 'holdername', 'balance': {'value': 'value', 'currencyCode': 'currencycode'}, 'overdraftLimit': 'overdraftLimit', 'updatedAt': 'updatedat'}}, {'id': 'aid', 'attributes': {'iban': 'iban2', 'product': {'displayName': 'displayName2'}, 'holderName': 'holdername2', 'balance': {'value': 'value2', 'currencyCode': 'currencycode2'}, 'overdraftLimit': 'overdraftLimit2', 'updatedAt': 'updatedat2'}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'account', 'id': 'aid', 'iban': 'iban2', 'account': 'iban2', 'name': 'displayName2', 'holdername': 'holdername2', 'amount': 'value2', 'currencycode': 'currencycode2', 'date': 'updatedat2', 'limit': 'overdraftLimit2', 'transactions': 'https://banking.dkb.de/api/accounts/accounts/aid/transactions'}
        self.assertEqual(result, self.dkb._get_account_details('aid', account_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_057__get_card_details(self, mock_date):
        """ test _get_card_details() """
        card_dic = {}
        self.assertFalse(self.dkb._get_card_details('cid', card_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_058__get_card_details(self, mock_date):
        """ test _get_card_details() """
        card_dic = {}
        self.assertFalse(self.dkb._get_card_details('cid', card_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_059__get_card_details(self, mock_date):
        """ test _get_card_details() """
        card_dic = {'data': [{'id': 'cid'}]}
        self.assertFalse(self.dkb._get_card_details('cid', card_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_060__get_card_details(self, mock_date):
        """ test _get_card_details() """
        card_dic = {'data': [{'id': 'cid', 'type': 'creditCard', 'attributes': {'product': {'displayName': 'displayname'}, 'holder': {'person': {'firstName': 'firstname', 'lastName': 'lastname'}}, 'maskedPan': 'maskedPan', 'status': 'status', 'limit': {'value': 'value'}, 'balance': {'date': 'date', 'value': '101', 'currencyCode': 'currencycode'}}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'creditcard', 'id': 'cid', 'maskedpan': 'maskedPan', 'name': 'displayname', 'status': 'status', 'account': 'maskedPan', 'amount': -101.0, 'currencycode': 'currencycode', 'date': 'date', 'limit': 'value', 'holdername': 'firstname lastname', 'transactions': 'https://banking.dkb.de/api/credit-card/cards/cid/transactions'}
        self.assertEqual(result, self.dkb._get_card_details('cid', card_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_061__get_card_details(self, mock_date):
        """ test _get_card_details() """
        card_dic = {'data': [{'id': 'cid', 'type': 'debitCard', 'attributes': {'product': {'displayName': 'displayname'}, 'holder': {'person': {'firstName': 'firstname', 'lastName': 'lastname'}}, 'maskedPan': 'maskedPan', 'limit': {'value': 'value'}, 'balance': {'date': 'date', 'value': '101', 'currencyCode': 'currencycode'}}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'debitcard', 'id': 'cid', 'maskedpan': 'maskedPan', 'name': 'displayname', 'account': 'maskedPan', 'amount': -101.0, 'currencycode': 'currencycode', 'date': 'date', 'limit': 'value', 'holdername': 'firstname lastname', 'transactions': None}
        self.assertEqual(result, self.dkb._get_card_details('cid', card_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_062__get_brokerage_details(self, mock_date):
        """ test _get_brokerage_details() """
        brok_dic = {}
        mock_date.return_value = 'mock_date'
        self.assertFalse(self.dkb._get_brokerage_details('bid', brok_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_063__get_brokerage_details(self, mock_date):
        """ test _get_brokerage_details() """
        brok_dic = {'data': []}
        mock_date.return_value = 'mock_date'
        self.assertFalse(self.dkb._get_brokerage_details('bid', brok_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_064__get_brokerage_details(self, mock_date):
        """ test _get_brokerage_details() """
        brok_dic = {'data': [{'id': 'bid'}]}
        mock_date.return_value = 'mock_date'
        self.assertFalse(self.dkb._get_brokerage_details('bid', brok_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_065__get_brokerage_details(self, mock_date):
        """ test _get_brokerage_details() """
        brok_dic = {'data': [{'id': 'bid', 'attributes': {'holderName': 'holdername', 'depositAccountId': 'depositaccountid', 'brokerageAccountPerformance': {'currentValue': {'currencyCode': 'currentcycode', 'value': 'value'} }}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'depot', 'id': 'bid', 'holdername': 'holdername', 'name': 'holdername', 'account': 'depositaccountid', 'currencycode': 'currentcycode', 'amount': 'value', 'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/bid/positions?include=instrument%2Cquote'}
        self.assertEqual(result, self.dkb._get_brokerage_details('bid', brok_dic))
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.utilities._convert_date_format')
    def test_066__get_brokerage_details(self, mock_date):
        """ test _get_brokerage_details() """
        brok_dic = {'data': [{'id': 'bid', 'attributes': {'holderName': 'holdername', 'depositAccountId': 'depositaccountid', 'brokerageAccountPerformance': {'currentValue': {'currencyCode': 'currentcycode', 'value': 'value'} }}}]}
        mock_date.return_value = 'mock_date'
        result = {'type': 'depot', 'id': 'bid', 'holdername': 'holdername', 'name': 'holdername', 'account': 'depositaccountid', 'currencycode': 'currentcycode', 'amount': 'value', 'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/bid/positions?include=instrument%2Cquote'}
        self.assertEqual(result, self.dkb._get_brokerage_details('bid', brok_dic))
        self.assertFalse(mock_date.called)

    def test_067__filter_transactions(self):
        """ test _filter_transactions() """
        transaction_list = []
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        self.assertFalse(self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_068__filter_transactions(self):
        """ test _filter_transactions() """
        transaction_list = [{'foo': 'bar', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo': 'bar', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_069__filter_transactions(self):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_070__filter_transactions(self):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-02-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_071__filter_transactions(self):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype2', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_072__filter_transactions(self):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype2', 'bookingDate': '2023-01-15'}}]
        from_date = '2023-01-01'
        to_date = '2023-01-31'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_073__filter_transactions(self):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'booked', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'pending', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'booked', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'booked'))

    def test_074__filter_transactions(self):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'booked', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'pending', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo2': 'bar2', 'attributes': {'status': 'pending', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'pending'))

    def test_075__filter_transactions(self):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'booked', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'pending', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo2': 'bar2', 'attributes': {'status': 'pending', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'reserved'))


    def test_076_format_card_transactions(self):
        """ _format_card_transactions() """
        transaction_list = []
        self.assertFalse(self.dkb._format_card_transactions(transaction_list))

    def test_077_format_card_transactions(self):
        """ _format_card_transactions() """
        transaction_list = [{'foo':'bar', 'attributes': {'description': 'description', 'bookingDate': '2023-01-01', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'CC', 'bdate': '2023-01-01', 'vdate': '2023-01-01', 'text': 'description'}]
        self.assertEqual(result, self.dkb._format_card_transactions(transaction_list))

    def test_078_format_card_transactions(self):
        """ _format_card_transactions() """
        transaction_list = [{'foo':'bar', 'attributes': {'bookingDate': '2023-01-01', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'CC', 'bdate': '2023-01-01', 'vdate': '2023-01-01'}]
        self.assertEqual(result, self.dkb._format_card_transactions(transaction_list))

    def test_079_format_card_transactions(self):
        """ _format_card_transactions() """
        transaction_list = [{'foo':'bar', 'attributes': {'description': 'description', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'CC', 'text': 'description'}]
        self.assertEqual(result, self.dkb._format_card_transactions(transaction_list))

    def test_080_format_brokerage_account(self):
        """ test _format_brokerage_account() """
        included_list = []
        data_dic = [{'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id'}}, 'quote': {'data': {'id': 'id', 'value': 'value'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_081_format_brokerage_account(self):
        """ test _format_brokerage_account() """
        included_list = []
        data_dic = [
            {'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id'}}, 'quote': {'data': {'id': 'id', 'value': 'value'}}}},
            {'attributes': {'performance': {'currentValue': {'value': 2000}}, 'lastOrderDate': '2020-02-01', 'quantity': {'value': 2000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id2'}}, 'quote': {'data': {'id': 'id2', 'value': 'value2'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000}, {'shares': 2000, 'quantity': 2000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-02-01', 'price_euro': 2000}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_082_format_brokerage_account(self):
        """ test _format_brokerage_account() """
        included_list = [{'id': 'inid', 'attributes': {'identifiers': [{'identifier': 'isin', 'value': 'value'}, {'identifier': 'isin', 'value': 'value2'}], 'name': {'short': 'short'}}}]
        data_dic = [{'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'inid'}}, 'quote': {'data': {'id': 'quoteid', 'value': 'value'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000, 'text': 'short', 'isin_wkn': 'value'}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_083_format_brokerage_account(self):
        """ test _format_brokerage_account() """
        included_list = [{'id': 'quoteid', 'attributes': {'market': 'market', 'price': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        data_dic = [{'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'inid'}}, 'quote': {'data': {'id': 'quoteid', 'value': 'value'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000, 'price': 1000.0, 'currencycode': 'currencyCode', 'market': 'market'}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_084_format_account_transactions(self):
        """ test _format_account_transactions() """
        transaction_list = [{'foo': 'bar'}]
        self.assertFalse(self.dkb._format_account_transactions(transaction_list))

    def test_085_format_account_transactions(self):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'debtor': {'name': 'name', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}, 'amount': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'peerid': '', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_086_format_account_transactions(self):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'debtor': {'intermediaryName': 'intermediaryName', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}, 'amount': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'intermediaryName', 'peerid': '', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType intermediaryName description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_087_format_account_transactions(self):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'debtor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}, 'amount': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'peerid': 'id', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_088_format_account_transactions(self):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'creditor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}, 'amount': {'value': -1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': -1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'peerid': 'id', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_089_format_account_transactions(self):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'mandateId': 'mandateId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'creditor': {'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}, 'amount': {'value': -1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': -1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'mandatereference': 'mandateId', 'peerid': '', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreference': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    @patch('dkb_robo.api.Wrapper._get_brokerage_details')
    @patch('dkb_robo.api.Wrapper._get_card_details')
    @patch('dkb_robo.api.Wrapper._get_account_details')
    def test_090_build_raw_account_dic(self, mock_acc, mock_card, mock_ba):
        """ teest _build_account_dic """
        portfolio_dic = {}
        self.assertFalse(self.dkb._build_raw_account_dic(portfolio_dic))
        self.assertFalse(mock_acc.called)
        self.assertFalse(mock_card.called)
        self.assertFalse(mock_ba.called)

    @patch('dkb_robo.api.Wrapper._get_brokerage_details')
    @patch('dkb_robo.api.Wrapper._get_card_details')
    @patch('dkb_robo.api.Wrapper._get_account_details')
    def test_091_build_raw_account_dic(self, mock_acc, mock_card, mock_ba):
        """ teest _build_account_dic """
        portfolio_dic = {'accounts': {'data': [{'id': 'id', 'type': 'brokerageAccount', 'foo': 'bar'}]} }
        mock_ba.return_value = 'mock_ba'
        result = {'id': 'mock_ba'}
        self.assertEqual(result, self.dkb._build_raw_account_dic(portfolio_dic))
        self.assertFalse(mock_acc.called)
        self.assertFalse(mock_card.called)
        self.assertTrue(mock_ba.called)

    @patch('dkb_robo.api.Wrapper._get_brokerage_details')
    @patch('dkb_robo.api.Wrapper._get_card_details')
    @patch('dkb_robo.api.Wrapper._get_account_details')
    def test_092_build_raw_account_dic(self, mock_acc, mock_card, mock_ba):
        """ teest _build_account_dic """
        portfolio_dic = {'cards': {'data': [{'id': 'id', 'type': 'fooCard', 'foo': 'bar'}]} }
        mock_card.return_value = 'mock_card'
        result = {'id': 'mock_card'}
        self.assertEqual(result, self.dkb._build_raw_account_dic(portfolio_dic))
        self.assertFalse(mock_acc.called)
        self.assertTrue(mock_card.called)
        self.assertFalse(mock_ba.called)

    @patch('dkb_robo.api.Wrapper._get_brokerage_details')
    @patch('dkb_robo.api.Wrapper._get_card_details')
    @patch('dkb_robo.api.Wrapper._get_account_details')
    def test_093_build_raw_account_dic(self, mock_acc, mock_card, mock_ba):
        """ teest _build_account_dic """
        portfolio_dic = {'accounts': {'data': [{'id': 'id', 'type': 'account', 'foo': 'bar'}]} }
        mock_acc.return_value = 'mock_acc'
        result = {'id': 'mock_acc'}
        self.assertEqual(result, self.dkb._build_raw_account_dic(portfolio_dic))
        self.assertTrue(mock_acc.called)
        self.assertFalse(mock_card.called)
        self.assertFalse(mock_ba.called)

    def test_094_build_product_display_settings_dic(self):
        """ _build_product_display_settings_dic() """
        data_ele = {'foo': 'bar'}
        self.assertFalse(self.dkb._build_product_display_settings_dic(data_ele))

    def test_095_build_product_display_settings_dic(self):
        """ _build_product_display_settings_dic() """
        data_ele = {'attributes': {'foo': 'bar'}}
        self.assertFalse(self.dkb._build_product_display_settings_dic(data_ele))

    def test_096_build_product_display_settings_dic(self):
        """ _build_product_display_settings_dic() """
        data_ele = {'attributes': {'productSettings': {'foo': 'bar'}}}

        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._build_product_display_settings_dic(data_ele))
        self.assertIn('ERROR:dkb_robo:api.Wrapper._build_product_display_settings_dic(): product_data is not of type dic', lcm.output)

    def test_097_build_product_display_settings_dic(self):
        """ _build_product_display_settings_dic() """
        data_ele = {'attributes': {'productSettings': {'product': {'uid': {'name': 'name'}}}}}
        self.assertEqual({'uid': 'name'}, self.dkb._build_product_display_settings_dic(data_ele))

    def test_098_build_product_display_settings_dic(self):
        """ _build_product_display_settings_dic() """
        data_ele = {'attributes': {'productSettings': {'product': {'uid': {'foo': 'bar'}}}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._build_product_display_settings_dic(data_ele))
        self.assertIn('ERROR:dkb_robo:api.Wrapper._build_product_display_settings_dic(): "name" key not found', lcm.output)

    def test_099_build_product_group_list(self):
        """ test _build_product_group_list() """
        data_ele = {}
        self.assertFalse(self.dkb._build_product_group_list(data_ele))

    def test_100_build_product_group_list(self):
        """ test _build_product_group_list() """
        data_ele = {'attributes': {'productGroups': {'foo': {'index': 0, 'name': 'foo', 'products': {'product1': {'uid1': {'index': 1}, 'uid2': {'index': 0}}}}}}}
        self.assertEqual([{'name': 'foo', 'product_list': {1: 'uid1', 0: 'uid2'}}], self.dkb._build_product_group_list(data_ele))

    def test_101_build_product_group_list(self):
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

    def test_102_build_product_group_list(self):
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


    def test_103_build_account_dic(self):
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

    def test_104_build_account_dic(self):
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

    @patch('dkb_robo.api.Wrapper._build_product_group_list')
    @patch('dkb_robo.api.Wrapper._build_product_display_settings_dic')
    @patch('dkb_robo.api.Wrapper._build_raw_account_dic')
    def test_105_build_account_dic(self, mock_raw, mock_dis, mock_grp):
        """ test build account dic """
        portfolio_dic = {}
        result = {}
        self.assertEqual(result, self.dkb._build_account_dic(portfolio_dic))
        self.assertTrue(mock_raw.called)
        self.assertFalse(mock_dis.called)
        self.assertFalse(mock_grp.called)

    @patch('dkb_robo.api.Wrapper._build_product_group_list')
    @patch('dkb_robo.api.Wrapper._build_product_display_settings_dic')
    @patch('dkb_robo.api.Wrapper._build_raw_account_dic')
    def test_106_build_account_dic(self, mock_raw, mock_dis, mock_grp):
        """ test build account dic """
        portfolio_dic = {'product_display': {'data': ['foo']}}
        result = {}
        self.assertEqual(result, self.dkb._build_account_dic(portfolio_dic))
        self.assertTrue(mock_raw.called)
        self.assertTrue(mock_dis.called)
        self.assertTrue(mock_grp.called)

    @patch('dkb_robo.api.Wrapper._build_product_group_list')
    @patch('dkb_robo.api.Wrapper._build_product_display_settings_dic')
    @patch('dkb_robo.api.Wrapper._build_raw_account_dic')
    def test_107_build_account_dic(self, mock_raw, mock_dis, mock_grp):
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

    @patch('dkb_robo.api.Wrapper._build_product_group_list')
    @patch('dkb_robo.api.Wrapper._build_product_display_settings_dic')
    @patch('dkb_robo.api.Wrapper._build_raw_account_dic')
    def test_108_build_account_dic(self, mock_raw, mock_dis, mock_grp):
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

    def test_109_get_credit_limits(self):
        """ teest _get_credit_limits() """
        self.dkb.account_dic = {0: {'limit': 1000, 'iban': 'iban'}, 1: {'limit': 2000, 'maskedpan': 'maskedpan'}}
        result_dic = {'iban': 1000, 'maskedpan': 2000}
        self.assertEqual(result_dic, self.dkb.get_credit_limits())

    def test_110_get_credit_limits(self):
        """ teest get_credit_limits() """
        self.dkb.account_dic = {'foo': 'bar'}
        self.assertFalse(self.dkb.get_credit_limits())

    @patch('dkb_robo.api.Wrapper._filter_standing_orders')
    def test_111___get_standing_orders(self, mock_filter):
        """ test _get_standing_orders() """
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb.get_standing_orders())
        self.assertEqual('get_standing_orders(): account-id is required', str(err.exception))
        self.assertFalse(mock_filter.called)

    @patch('dkb_robo.api.Wrapper._filter_standing_orders')
    def test_112___get_standing_orders(self, mock_filter):
        """ test _get_standing_orders() """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertFalse(self.dkb.get_standing_orders(uid='uid'))
        self.assertFalse(mock_filter.called)

    @patch('dkb_robo.api.Wrapper._filter_standing_orders')
    def test_113___get_standing_orders(self, mock_filter):
        """ test _get_standing_orders() """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        mock_filter.return_value = 'mock_filter'
        self.assertEqual('mock_filter', self.dkb.get_standing_orders(uid='uid'))
        self.assertTrue(mock_filter.called)

    def test_114__filter_standing_orders(self):
        """ test _filter_standing_orders() """
        full_list = {}
        self.assertFalse(self.dkb._filter_standing_orders(full_list))

    def test_115__filter_standing_orders(self):
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

    def test_116_add_cardlimit(self):
        """ test _add_cardlimit() """
        card = {'attributes': {'expiryDate': 'expiryDate', 'limit': {'value': 'value', 'foo': 'bar'}}}
        result = {'expirydate': 'expiryDate', 'limit': 'value'}
        self.assertEqual(result, self.dkb._add_cardlimit(card))

    def test_117_filter_standing_orders(self):
        """ e2e get_standing_orders() """
        so_list = json_load(self.dir_path + '/mocks/so.json')
        result = [{'amount': 100.0, 'currencycode': 'EUR', 'purpose': 'description1', 'recpipient': 'name1', 'creditoraccount': {'iban': 'iban1', 'bic': 'bic1'}, 'interval': {'from': '2022-01-01', 'until': '2025-12-01', 'frequency': 'monthly', 'holidayExecutionStrategy': 'following', 'nextExecutionAt': '2022-11-01'}}, {'amount': 200.0, 'currencycode': 'EUR', 'purpose': 'description2', 'recpipient': 'name2', 'creditoraccount': {'iban': 'iban2', 'bic': 'bic2'}, 'interval': {'from': '2022-02-01', 'until': '2025-12-02', 'frequency': 'monthly', 'holidayExecutionStrategy': 'following', 'nextExecutionAt': '2022-11-02'}}, {'amount': 300.0, 'currencycode': 'EUR', 'purpose': 'description3', 'recpipient': 'name3', 'creditoraccount': {'iban': 'iban3', 'bic': 'bic3'}, 'interval': {'from': '2022-03-01', 'until': '2025-03-01', 'frequency': 'monthly', 'holidayExecutionStrategy': 'following', 'nextExecutionAt': '2022-03-01'}}]
        self.assertEqual(result, self.dkb._filter_standing_orders(so_list))

    def test_118_logout(self):
        """ test logout """
        self.assertFalse(self.dkb.logout())

    def test_119__get_document_name(self):
        """ test _get_document_name() """
        self.assertEqual('foofoo', self.dkb._get_document_name('foofoo'))

    def test_120__get_document_name(self):
        """ test _get_document_name() """
        self.assertEqual('foo foo', self.dkb._get_document_name('foo foo'))

    def test_121__get_document_name(self):
        """ test _get_document_name() """
        self.assertEqual('foo foo', self.dkb._get_document_name('foo  foo'))

    def test_122__get_document_name(self):
        """ test _get_document_name() """
        self.assertEqual('foo foo', self.dkb._get_document_name('foo   foo'))

    def test_123__get_document_type(self):
        """ test _get_document_type() """
        self.assertEqual('foo', self.dkb._get_document_type('foo'))

    def test_124__get_document_type(self):
        """ test _get_document_type() """
        self.assertEqual('Kontoauszüge', self.dkb._get_document_type('bankAccountStatement'))

    def test_125__get_document_type(self):
        """ test _get_document_type() """
        self.assertEqual('Kreditkartenabrechnungen', self.dkb._get_document_type('creditCardStatement'))

    @patch('dkb_robo.api.Wrapper._get_document_name')
    def test_126__objectname_lookup(self, mock_doc):
        """ test _objectname_lookup() """
        document = {'attributes': {'metadata': {'subject': 'subject'}}}
        mock_doc.return_value = 'no cardid'
        self.assertEqual('no cardid', self.dkb._objectname_lookup(document))

    def test_127__objectname_lookup(self):
        """ test _objectname_lookup() """
        document = {'attributes': {'metadata': {'cardId': 'cardId', 'subject': 'subject'}}}
        self.dkb.account_dic = {0: {'id': 'cardId', 'foo': 'bar', 'account': 'account'}}
        self.assertEqual('subject account', self.dkb._objectname_lookup(document))

    def test_128__objectname_lookup(self):
        """ test _objectname_lookup() """
        document = {'attributes': {'metadata': {'cardId': 'cardId1', 'subject': 'subject'}, 'fileName': 'boo_foo_bar'}}
        self.dkb.account_dic = {0: {'id': 'cardId', 'foo': 'bar', 'account': 'account'}}
        self.assertEqual('subject foo', self.dkb._objectname_lookup(document))

    @patch('dkb_robo.legacy.Wrapper.get_exemption_order')
    def test_129_get_exemption_order(self, mock_exo):
        """ test get_exemption_order() """
        mock_exo.return_value = 'mock_exo'
        self.assertEqual('mock_exo', self.dkb.get_exemption_order())

    @patch('dkb_robo.api.Wrapper._filter_postbox')
    def test_130_scan_postbox(self, mock_filter):
        """ test scan_postbox() """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.side_effects = [400, 400]
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertFalse(self.dkb.scan_postbox('path', 'downloadall', 'archive', 'prepdate'))
        self.assertFalse(mock_filter.called)

    @patch('dkb_robo.api.Wrapper._filter_postbox')
    def test_131_scan_postbox(self, mock_filter):
        """ test scan_postbox() """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.side_effects = [400, 200]
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertFalse(self.dkb.scan_postbox('path', 'downloadall', 'archive', 'prepdate'))
        self.assertFalse(mock_filter.called)

    @patch('dkb_robo.api.Wrapper._filter_postbox')
    def test_132_scan_postbox(self, mock_filter):
        """ test scan_postbox() """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.side_effects = [200, 400]
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertFalse(self.dkb.scan_postbox('path', 'downloadall', 'archive', 'prepdate'))
        self.assertFalse(mock_filter.called)

    @patch('dkb_robo.api.Wrapper._filter_postbox')
    def test_133_scan_postbox(self, mock_filter):
        """ test scan_postbox() """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        mock_filter.return_value = 'mock_filter'
        self.assertEqual('mock_filter', self.dkb.scan_postbox('path', 'downloadall', 'archive', 'prepdate'))
        self.assertTrue(mock_filter.called)

    @patch('time.sleep')
    @patch('dkb_robo.api.Wrapper._download_document')
    @patch('dkb_robo.api.Wrapper._get_document_type')
    @patch('dkb_robo.api.Wrapper._objectname_lookup')
    def test_134__filter_postbox(self, mock_lookup, mock_type, mock_download, mock_sleep):
        """ _filter_postbox() """
        pb_dic = {'data': [{'id': 'id1', 'attributes': {'fileName': 'filename1', 'contentType': 'contentType1', 'metadata':{'statementDate': 'statementDate1'}}}, {'id': 'id2', 'attributes': {'fileName': 'filename2', 'contentType': 'contentType2', 'metadata':{'statementDate': 'statementDate2'}}}]}
        msg_dic = {'data': [{'id': 'id1', 'attributes': {'documentType': 'documentType1', 'read': False, 'archived': False}}, {'id': 'id2', 'attributes': {'documentType': 'documentType2', 'read': False, 'archived': False}}]}
        mock_lookup.side_effect = ['mock_lookup1', 'mock_lookup2']
        mock_type.return_value = 'mock_type'
        mock_download.return_value = 'mock_download'
        result = {'mock_type': {'documents': {'mock_lookup1': {'link': 'https://banking.dkb.de/api/documentstorage/documents/id1', 'fname': 'None/mock_type/filename1', 'date': 'statementDate1', 'rcode': 'unknown'}, 'mock_lookup2': {'link': 'https://banking.dkb.de/api/documentstorage/documents/id2', 'fname': 'None/mock_type/filename2', 'date': 'statementDate2', 'rcode': 'unknown'}}}}
        self.assertEqual(result, self.dkb._filter_postbox(msg_dic, pb_dic, path=None, download_all=False, prepend_date=False))
        self.assertTrue(mock_lookup.called)
        self.assertTrue(mock_type.called)
        self.assertFalse(mock_download.called)

    @patch('time.sleep')
    @patch('dkb_robo.api.Wrapper._download_document')
    @patch('dkb_robo.api.Wrapper._get_document_type')
    @patch('dkb_robo.api.Wrapper._objectname_lookup')
    def test_135__filter_postbox(self, mock_lookup, mock_type, mock_download, mock_sleep):
        """ _filter_postbox() """
        pb_dic = {'data': [{'id': 'id1', 'attributes': {'fileName': 'filename1', 'contentType': 'contentType1', 'metadata':{'statementDate': 'statementDate1'}}}, {'id': 'id2', 'attributes': {'fileName': 'filename2', 'contentType': 'contentType2', 'metadata':{'statementDate': 'statementDate2'}}}]}
        msg_dic = {'data': [{'id': 'id1', 'attributes': {'documentType': 'documentType1', 'read': False, 'archived': False}}, {'id': 'id2', 'attributes': {'documentType': 'documentType2', 'read': True, 'archived': False}}]}
        mock_lookup.side_effect = ['mock_lookup1', 'mock_lookup2']
        mock_type.return_value = 'mock_type'
        mock_download.return_value = 'mock_download'
        result = {'mock_type': {'documents': {'mock_lookup1': {'link': 'https://banking.dkb.de/api/documentstorage/documents/id1', 'fname': 'None/mock_type/filename1', 'date': 'statementDate1', 'rcode': 'unknown'}}}}
        self.assertEqual(result, self.dkb._filter_postbox(msg_dic, pb_dic, path=None, download_all=False, prepend_date=False))
        self.assertTrue(mock_lookup.called)
        self.assertTrue(mock_type.called)
        self.assertFalse(mock_download.called)

    @patch('time.sleep')
    @patch('dkb_robo.api.Wrapper._download_document')
    @patch('dkb_robo.api.Wrapper._get_document_type')
    @patch('dkb_robo.api.Wrapper._objectname_lookup')
    def test_136__filter_postbox(self, mock_lookup, mock_type, mock_download, mock_sleep):
        """ _filter_postbox() """
        pb_dic = {'data': [{'id': 'id1', 'attributes': {'fileName': 'filename1', 'contentType': 'contentType1', 'metadata':{'statementDate': 'statementDate1'}}}, {'id': 'id2', 'attributes': {'fileName': 'filename2', 'contentType': 'contentType2', 'metadata':{'statementDate': 'statementDate2'}}}]}
        msg_dic = {'data': [{'id': 'id1', 'attributes': {'documentType': 'documentType1', 'read': False, 'archived': False}}, {'id': 'id2', 'attributes': {'documentType': 'documentType2', 'read': True, 'archived': False}}]}
        mock_lookup.side_effect = ['mock_lookup1', 'mock_lookup2']
        mock_type.return_value = 'mock_type'
        mock_download.return_value = 'mock_download'
        result = {'mock_type': {'documents': {'mock_lookup1': {'link': 'https://banking.dkb.de/api/documentstorage/documents/id1', 'fname': 'None/mock_type/filename1', 'date': 'statementDate1', 'rcode': 'unknown'}, 'mock_lookup2': {'link': 'https://banking.dkb.de/api/documentstorage/documents/id2', 'fname': 'None/mock_type/filename2', 'date': 'statementDate2', 'rcode': 'unknown'}}}}
        self.assertEqual(result, self.dkb._filter_postbox(msg_dic, pb_dic, path=None, download_all=True, prepend_date=False))
        self.assertTrue(mock_lookup.called)
        self.assertTrue(mock_type.called)
        self.assertFalse(mock_download.called)

    @patch('time.sleep')
    @patch('dkb_robo.api.Wrapper._download_document')
    @patch('dkb_robo.api.Wrapper._get_document_type')
    @patch('dkb_robo.api.Wrapper._objectname_lookup')
    def test_137__filter_postbox(self, mock_lookup, mock_type, mock_download, mock_sleep):
        """ _filter_postbox() """
        pb_dic = {'data': [{'id': 'id1', 'attributes': {'fileName': 'filename1', 'contentType': 'contentType1', 'metadata':{'statementDate': 'statementDate1'}}}, {'id': 'id2', 'attributes': {'fileName': 'filename2', 'contentType': 'contentType2', 'metadata':{'statementDate': 'statementDate2'}}}]}
        msg_dic = {'data': [{'id': 'id1', 'attributes': {'documentType': 'documentType1', 'read': False, 'archived': False}}, {'id': 'id2', 'attributes': {'documentType': 'documentType2', 'read': True, 'archived': False}}]}
        mock_lookup.side_effect = ['mock_lookup1', 'mock_lookup2']
        mock_type.side_effect = ['mock_type1', 'mock_type2']
        mock_download.return_value = 'mock_download'
        result = {'mock_type1': {'documents': {'mock_lookup1': {'link': 'https://banking.dkb.de/api/documentstorage/documents/id1', 'fname': 'None/mock_type1/filename1', 'date': 'statementDate1', 'rcode': 'unknown'}}}, 'mock_type2': {'documents': {'mock_lookup2': {'link': 'https://banking.dkb.de/api/documentstorage/documents/id2', 'fname': 'None/mock_type2/filename2', 'date': 'statementDate2', 'rcode': 'unknown'}}}}
        self.assertEqual(result, self.dkb._filter_postbox(msg_dic, pb_dic, path=None, download_all=True, prepend_date=False))
        self.assertTrue(mock_lookup.called)
        self.assertTrue(mock_type.called)
        self.assertFalse(mock_download.called)

    @patch('time.sleep')
    @patch('dkb_robo.api.Wrapper._download_document')
    @patch('dkb_robo.api.Wrapper._get_document_type')
    @patch('dkb_robo.api.Wrapper._objectname_lookup')
    def test_138__filter_postbox(self, mock_lookup, mock_type, mock_download, mock_sleep):
        """ _filter_postbox() """
        pb_dic = {'data': [{'id': 'id1', 'attributes': {'fileName': 'filename1', 'contentType': 'contentType1', 'metadata':{'statementDate': 'statementDate1'}}}, {'id': 'id2', 'attributes': {'fileName': 'filename2', 'contentType': 'contentType2', 'metadata':{'statementDate': 'statementDate2'}}}]}
        msg_dic = {'data': [{'id': 'id1', 'attributes': {'documentType': 'documentType1', 'read': False, 'archived': False}}, {'id': 'id2', 'attributes': {'documentType': 'documentType2', 'read1': True, 'archived': False}}]}
        mock_lookup.side_effect = ['mock_lookup1', 'mock_lookup2']
        mock_type.side_effect = ['mock_type1', 'mock_type2']
        mock_download.return_value = 'mock_download'
        result = {'mock_type1': {'documents': {'mock_lookup1': {'link': 'https://banking.dkb.de/api/documentstorage/documents/id1', 'fname': 'None/mock_type1/filename1', 'date': 'statementDate1', 'rcode': 'unknown'}}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(result, self.dkb._filter_postbox(msg_dic, pb_dic, path=None, download_all=True, prepend_date=False))
        self.assertIn("ERROR:dkb_robo:api.Wrapper._filter_postbox(): document_dic incomplete: {'filename': 'filename2', 'contenttype': 'contentType2', 'date': 'statementDate2', 'name': 'mock_lookup2', 'document_type': 'mock_type2', 'archived': False, 'link': 'https://banking.dkb.de/api/documentstorage/documents/id2'}", lcm.output)
        self.assertTrue(mock_lookup.called)
        self.assertTrue(mock_type.called)
        self.assertFalse(mock_download.called)

    @patch('time.sleep')
    @patch('dkb_robo.api.Wrapper._download_document')
    @patch('dkb_robo.api.Wrapper._get_document_type')
    @patch('dkb_robo.api.Wrapper._objectname_lookup')
    def test_139__filter_postbox(self, mock_lookup, mock_type, mock_download, mock_sleep):
        """ _filter_postbox() """
        pb_dic = {'data': [{'id': 'id1', 'attributes': {'fileName': 'filename1', 'contentType': 'contentType1', 'metadata':{'statementDate': 'statementDate1'}}}, {'id': 'id2', 'attributes': {'fileName': 'filename2', 'contentType': 'contentType2', 'metadata':{'statementDate': 'statementDate2'}}}]}
        msg_dic = {'data': [{'id': 'id1', 'attributes': {'documentType': 'documentType1', 'read': False, 'archived': False}}, {'id': 'id2', 'attributes': {'documentType': 'documentType2', 'read': True, 'archived': False}}]}
        mock_lookup.side_effect = ['mock_lookup1', 'mock_lookup2']
        mock_type.return_value = 'mock_type'
        mock_download.return_value = 'mock_download'
        result = {'mock_type': {'documents': {'mock_lookup1': {'link': 'https://banking.dkb.de/api/documentstorage/documents/id1', 'fname': 'patch/mock_type/filename1', 'date': 'statementDate1', 'rcode': 'mock_download'}}}}
        self.assertEqual(result, self.dkb._filter_postbox(msg_dic, pb_dic, path='patch', download_all=False, prepend_date=False))
        self.assertTrue(mock_lookup.called)
        self.assertTrue(mock_type.called)
        self.assertTrue(mock_download.called)

    @patch('time.sleep')
    @patch('dkb_robo.api.Wrapper._download_document')
    @patch('dkb_robo.api.Wrapper._get_document_type')
    @patch('dkb_robo.api.Wrapper._objectname_lookup')
    def test_140__filter_postbox(self, mock_lookup, mock_type, mock_download, mock_sleep):
        """ _filter_postbox() """
        pb_dic = {'data': [{'id': 'id1', 'attributes': {'fileName': 'filename1', 'contentType': 'contentType1', 'metadata':{'statementDate': 'statementDate1'}}}, {'id': 'id2', 'attributes': {'fileName': 'filename1', 'contentType': 'contentType2', 'metadata':{'statementDate': 'statementDate2'}}}]}
        msg_dic = {'data': [{'id': 'id1', 'attributes': {'documentType': 'documentType1', 'read': False, 'archived': False}}, {'id': 'id2', 'attributes': {'documentType': 'documentType2', 'read': True, 'archived': False}}]}
        mock_lookup.side_effect = ['mock_lookup1', 'mock_lookup2']
        mock_type.return_value = 'mock_type'
        mock_download.return_value = 'mock_download'
        result = {'mock_type': {'documents': {'mock_lookup1': {'link': 'https://banking.dkb.de/api/documentstorage/documents/id1', 'fname': 'patch/mock_type/filename1', 'date': 'statementDate1', 'rcode': 'mock_download'}, 'mock_lookup2': {'link': 'https://banking.dkb.de/api/documentstorage/documents/id2', 'fname': 'patch/mock_type/statementDate2_filename1', 'date': 'statementDate2', 'rcode': 'mock_download'}}}}
        self.assertEqual(result, self.dkb._filter_postbox(msg_dic, pb_dic, path='patch', download_all=True, prepend_date=True))
        self.assertTrue(mock_lookup.called)
        self.assertTrue(mock_type.called)
        self.assertTrue(mock_download.called)

    @patch("builtins.open", create=True)
    @patch('time.sleep')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_141__download_document(self, mock_exists, mock_makedir, mock_sleep, mock_open):
        """ _get_document() """
        mock_exists.return_value = False
        self.dkb.client = Mock()
        self.dkb.client.headers = {'foo': 'bar'}
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        document = {'document_type': 'document_type', 'filename': 'filename', 'link': 'link', 'contenttype': 'contenttype', 'read': False}
        self.assertEqual(200, self.dkb._download_document('path', document))
        self.assertTrue(mock_makedir.called)
        self.assertTrue(self.dkb.client.patch.called)
        self.assertTrue(mock_open.called)

    @patch("builtins.open", create=True)
    @patch('time.sleep')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_142__download_document(self, mock_exists, mock_makedir, mock_sleep, mock_open):
        """ _get_document() """
        mock_exists.return_value = False
        self.dkb.client = Mock()
        self.dkb.client.headers = {'foo': 'bar'}
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        document = {'document_type': 'document_type', 'filename': 'filename', 'link': 'link', 'contenttype': 'contenttype', 'read': False}
        self.assertEqual(400, self.dkb._download_document('path', document))
        self.assertTrue(mock_makedir.called)
        self.assertFalse(self.dkb.client.patch.called)
        self.assertFalse(mock_open.called)

    @patch("builtins.open", create=True)
    @patch('time.sleep')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_143__download_document(self, mock_exists, mock_makedir, mock_sleep, mock_open):
        """ _get_document() """
        mock_exists.return_value = False
        self.dkb.client = Mock()
        self.dkb.client.headers = {'foo': 'bar'}
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        document = {'document_type': 'document_type', 'filename': 'filename', 'link': 'link', 'contenttype': 'application/pdf', 'read': False}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(200, self.dkb._download_document('path', document))
        self.assertIn('INFO:dkb_robo:api.Wrapper._download_document(): renaming filename', lcm.output)
        self.assertTrue(mock_makedir.called)
        self.assertTrue(self.dkb.client.patch.called)
        self.assertTrue(mock_open.called)

    def test_144_sort_mfa_devices(self):
        """ test sort_mfa_devices() """
        mfa_dic = {
            'data': [
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-01'}},
                {'attributes': {'preferredDevice': True, 'enrolledAt': '2022-01-02'}},
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-03'}}
            ]
        }
        expected_result = {
            'data': [
                {'attributes': {'preferredDevice': True, 'enrolledAt': '2022-01-02'}},
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-01'}},
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-03'}}
            ]
        }
        self.assertEqual(expected_result, self.dkb._sort_mfa_devices(mfa_dic))


    def test_145_sort_mfa_devices(self):
        """ test sort_mfa_devices() """
        mfa_dic = {
            'data': [
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-03'}},
                {'attributes': {'preferredDevice': True, 'enrolledAt': '2022-01-02'}},
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-01'}}
            ]
        }
        expected_result = {
            'data': [
                {'attributes': {'preferredDevice': True, 'enrolledAt': '2022-01-02'}},
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-01'}},
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-03'}}
            ]
        }
        self.assertEqual(expected_result, self.dkb._sort_mfa_devices(mfa_dic))


    def test_146_sort_mfa_devices(self):
        """ test sort_mfa_devices() """
        mfa_dic = {
            'data': [
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-03'}},
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-02'}},
                {'attributes': {'preferredDevice': True, 'enrolledAt': '2022-01-04'}}
            ]
        }
        expected_result = {
            'data': [
                {'attributes': {'preferredDevice': True, 'enrolledAt': '2022-01-04'}},
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-02'}},
                {'attributes': {'preferredDevice': False, 'enrolledAt': '2022-01-03'}}
            ]
        }
        self.assertEqual(expected_result, self.dkb._sort_mfa_devices(mfa_dic))

    def test_147__docdate_lookup(self):
        """ test _docdate_lookup() """
        input_dic = {'attributes': {'metadata': {'statementDate': 'statementDate'}}}
        self.assertEqual('statementDate', self.dkb._docdate_lookup(input_dic))

    def test_148__docdate_lookup(self):
        """ test _docdate_lookup() """
        input_dic = {'attributes': {'metadata': {'creationDate': 'creationDate'}}}
        self.assertEqual('creationDate', self.dkb._docdate_lookup(input_dic))

    def test_149__docdate_lookup(self):
        """ test _docdate_lookup() """
        input_dic = {'attributes': {'metadata': {'fooDate': 'creationDate'}}}
        self.assertEqual('unknown', self.dkb._docdate_lookup(input_dic))

    def test_150_get_transaction_list(self):
        """ test _get_transaction_list()"""
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual({'data': []}, self.dkb._get_transaction_list('transaction_url'))
        self.assertIn('ERROR:dkb_robo:api.Wrapper._get_transactions(): RC is not 200 but 400', lcm.output)

    def test_151_get_transaction_list(self):
        """ test _get_transaction_list()"""
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'data': []}, self.dkb._get_transaction_list('transaction_url'))

    def test_152_get_transaction_list(self):
        """ test _get_transaction_list()"""
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'data': [{'foo1': 'bar1'}, {'foo2': 'bar2'}]}
        self.assertEqual({'data': [{'foo1': 'bar1'}, {'foo2': 'bar2'}]}, self.dkb._get_transaction_list('transaction_url'))

    def test_153_get_transaction_list(self):
        """ test _get_transaction_list()"""
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.side_effect = [{'data': [{'foo1': 'bar1'}, {'foo2': 'bar2'}], 'links': {'next': 'next_url'}}, {'data': [{'foo3': 'bar3'}, {'foo4': 'bar4'}], 'links': {'foo': 'bar'}}]
        self.assertEqual({'data': [{'foo1': 'bar1'}, {'foo2': 'bar2'}, {'foo3': 'bar3'}, {'foo4': 'bar4'}]}, self.dkb._get_transaction_list('transaction_url'))

    def test_154_init(self):
        """ test init() """
        self.dkb.__init__()
        self.assertEqual('seal_one', self.dkb.mfa_method)

    def test_155_init(self):
        """ test init() """
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb.__init__(logger=self.logger, chip_tan=True)
        self.assertIn('INFO:dkb_robo:Using to chip_tan to login', lcm.output)
        self.assertEqual('chip_tan_manual', self.dkb.mfa_method)

    def test_156_init(self):
        """ test init() """
        self.dkb.__init__(logger=self.logger, chip_tan=False)
        self.assertEqual('seal_one', self.dkb.mfa_method)

    def test_157_init(self):
        """ test init() """
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb.__init__(logger=self.logger, chip_tan='qr')
        self.assertIn('INFO:dkb_robo:Using to chip_tan to login', lcm.output)
        self.assertEqual('chip_tan_qr', self.dkb.mfa_method)

    def test_158_init(self):
        """ test init() """
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb.__init__(logger=self.logger, chip_tan='chip_tan_qr')
        self.assertIn('INFO:dkb_robo:Using to chip_tan to login', lcm.output)
        self.assertEqual('chip_tan_qr', self.dkb.mfa_method)

    @patch('dkb_robo.api.Wrapper._complete_ctm_2fa')
    @patch('dkb_robo.api.Wrapper._complete_app_2fa')
    @patch('dkb_robo.api.Wrapper._get_challenge_id')
    def test_156_complete_2fa(self, mock_cid, mock_app, mock_ctm):
        """ test _complete_2fa() """
        mock_cid.return_value = 'cid'
        mock_app.return_value = 'app'
        mock_ctm.return_value = 'ctm'
        self.dkb.mfa_method = 'seal_one'
        self.assertEqual('app', self.dkb._complete_2fa('challenge_dic', 'device_name'))
        self.assertTrue(mock_cid.called)
        self.assertTrue(mock_app.called)
        self.assertFalse(mock_ctm.called)

    @patch('dkb_robo.api.Wrapper._complete_ctm_2fa')
    @patch('dkb_robo.api.Wrapper._complete_app_2fa')
    @patch('dkb_robo.api.Wrapper._get_challenge_id')
    def test_157_complete_2fa(self, mock_cid, mock_app, mock_ctm):
        """ test _complete_2fa() """
        mock_cid.return_value = 'cid'
        mock_app.return_value = 'app'
        mock_ctm.return_value = 'ctm'
        self.dkb.mfa_method = 'chip_tan_manual'
        self.assertEqual('ctm', self.dkb._complete_2fa('challenge_dic', 'device_name'))
        self.assertTrue(mock_cid.called)
        self.assertFalse(mock_app.called)
        self.assertTrue(mock_ctm.called)

    @patch('dkb_robo.api.Wrapper._complete_ctm_2fa')
    @patch('dkb_robo.api.Wrapper._complete_app_2fa')
    @patch('dkb_robo.api.Wrapper._get_challenge_id')
    def test_158_complete_2fa(self, mock_cid, mock_app, mock_ctm):
        """ test _complete_2fa() """
        mock_cid.return_value = 'cid'
        mock_app.return_value = 'app'
        mock_ctm.return_value = 'ctm'
        self.dkb.mfa_method = 'other_method'
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb._complete_2fa('challenge_dic', 'device_name'))
        self.assertEqual('Login failed: unknown 2fa method: other_method', str(err.exception))
        self.assertTrue(mock_cid.called)
        self.assertFalse(mock_app.called)
        self.assertFalse(mock_ctm.called)

    @patch('requests.session')
    def test_159_get_challenge_id(self, mock_session):
        """ test _get_challenge_id() """
        mfa_dic = {}
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb._get_challenge_id(mfa_dic))
        self.assertEqual('Login failed: challenge response format is other than expected: {}', str(err.exception))

    @patch('requests.session')
    def test_160_get_challenge_id(self, mock_session):
        """ test _get_challenge_id() """
        mfa_dic = {'data': {'id': 'id', 'type': 'type'}}
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb._get_challenge_id(mfa_dic))
        self.assertEqual("Login failed:: wrong challenge type: {'data': {'id': 'id', 'type': 'type'}}", str(err.exception))

    @patch('requests.session')
    def test_161_get_challenge_id(self, mock_session):
        """ test _get_challenge_id() """
        mfa_dic = {'data': {'id': 'id', 'type': 'mfa-challenge'}}
        self.assertEqual('id', self.dkb._get_challenge_id(mfa_dic))

    @patch('requests.session')
    def test_162_get_mfa_challenge_dic(self, mock_session):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(({}, None), self.dkb._get_mfa_challenge_dic(mfa_dic, 1))
        self.assertIn('ERROR:dkb_robo:api.Wrapper._get_mfa_challenge_dic(): mfa_dic has an unexpected data structure', lcm.output)

    @patch('requests.session')
    def test_163_get_mfa_challenge_dic(self, mock_session):
        """ test _get_mfa_challenge_id() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'data': {'type': 'mfa-challenge', 'id': 'id'}}
        self.dkb.client.headers = {'foo': 'bar'}
        self.dkb.mfa_method = 'seal_one'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mfa_dic = {'data': {1: {'id': 'id', 'attributes': {'deviceName': 'deviceName'}}}}
        self.assertEqual(({'data': {'id': 'id', 'type': 'mfa-challenge'}}, 'deviceName'), self.dkb._get_mfa_challenge_dic(mfa_dic, 1))

    @patch('requests.session')
    def test_164_get_mfa_challenge_dic(self, mock_session):
        """ test _get_mfa_challenge_id() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.json.return_value = {'data': {'type': 'mfa-challenge', 'id': 'id'}}
        self.dkb.client.headers = {'foo': 'bar'}
        self.dkb.mfa_method = 'seal_one'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mfa_dic = {'data': {1: {'id': 'id', 'attributes': {'deviceName': 'deviceName'}}}}
        with self.assertRaises(Exception) as err:
            self.assertEqual(({'data': {'id': 'id', 'type': 'mfa-challenge'}}, 'deviceName'), self.dkb._get_mfa_challenge_dic(mfa_dic, 1))
        self.assertEqual('Login failed: post request to get the mfa challenges failed. RC: 400', str(err.exception))

    @patch('requests.session')
    def test_165_get_mfa_challenge_dic(self, mock_session):
        """ test _get_mfa_challenge_id() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'data': {'type': 'mfa-challenge', 'id': 'id'}}
        self.dkb.client.headers = {'foo': 'bar'}
        self.dkb.mfa_method = 'seal_one'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mfa_dic = {'data': {1: {'id': 'id', 'attributes': {'foo': 'bar'}}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(({'data': {'id': 'id', 'type': 'mfa-challenge'}}, None), self.dkb._get_mfa_challenge_dic(mfa_dic, 1))
        self.assertIn('ERROR:dkb_robo:api.Wrapper._get_mfa_challenge_dic(): unable to get deviceName', lcm.output)

    @patch('time.sleep', return_value=None)
    @patch('dkb_robo.api.Wrapper._check_processing_status')
    @patch('dkb_robo.api.Wrapper._print_app_2fa_confirmation')
    def test_166__complete_app_2fa(self, mock_confirm, mock_status, _mock_sleep):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.side_effect = [{'foo1': 'bar1'}, {'data': {'attributes': {'verificationStatus': 'bump'}}}]
        mock_status.side_effects = [False, True]
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertTrue(self.dkb._complete_app_2fa('challengeid', 'devicename'))
        self.assertIn("ERROR:dkb_robo:api.Wrapper._complete_app_2fa(): error parsing polling response: {'foo1': 'bar1'}", lcm.output)
        self.assertTrue(mock_confirm.called)

    @patch('time.sleep', return_value=None)
    @patch('dkb_robo.api.Wrapper._check_processing_status')
    @patch('dkb_robo.api.Wrapper._print_app_2fa_confirmation')
    def test_167__complete_app_2fa(self, mock_confirm, mock_status, _mock_sleep):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.side_effect = [{'foo1': 'bar1'}, {'data': {'attributes': {'verificationStatus': 'bump'}}}]
        mock_status.return_value = False
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._complete_app_2fa('challengeid', 'devicename'))
        self.assertIn('ERROR:dkb_robo:api.Wrapper._complete_app_2fa(): polling request failed. RC: 400', lcm.output)
        self.assertTrue(mock_confirm.called)

    @patch('dkb_robo.api.Wrapper._print_ctan_instructions')
    def test_168_complete_ctm_2fa(self, mock_ctan):
        """ test _complete_ctm_2fa()"""
        mock_ctan.return_value = 'ctan'
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'data': {'attributes': {'verificationStatus': 'authorized'}}}
        challenge_dic = {'foo': 'bar'}
        self.assertTrue(self.dkb._complete_ctm_2fa('challengeid', challenge_dic))
        self.assertTrue(mock_ctan.called)

    @patch('dkb_robo.api.Wrapper._print_ctan_instructions')
    def test_169_complete_ctm_2fa(self, mock_ctan):
        """ test _complete_ctm_2fa()"""
        mock_ctan.return_value = 'ctan'
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'data': {'attributes': {'verificationStatus': 'foo'}}}
        challenge_dic = {'foo': 'bar'}
        self.assertFalse(self.dkb._complete_ctm_2fa('challengeid', challenge_dic))
        self.assertTrue(mock_ctan.called)

    @patch('dkb_robo.api.Wrapper._print_ctan_instructions')
    def test_170_complete_ctm_2fa(self, mock_ctan):
        """ test _complete_ctm_2fa()"""
        mock_ctan.return_value = 'ctan'
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.json.return_value = {'data': {'attributes': {'verificationStatus': 'foo'}}}
        self.dkb.client.post.return_value.text = 'bump'
        challenge_dic = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb._complete_ctm_2fa('challengeid', challenge_dic))
        self.assertEqual('Login failed: 2fa failed. RC: 400 text: bump', str(err.exception))
        self.assertTrue(mock_ctan.called)

    @patch('dkb_robo.api.Wrapper._show_image')
    def test_171__print_ctan_instructions(self, mock_show):
        """ test _print_ctan_instructions()"""
        challenge_dic = {}
        self.assertFalse(self.dkb._print_ctan_instructions(challenge_dic))
        self.assertFalse(mock_show.called)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('dkb_robo.api.Wrapper._show_image')
    @patch('builtins.input')
    def test_172__print_ctan_instructions(self, mock_input, mock_show, mock_stdout):
        """ test _print_ctan_instructions()"""
        challenge_dic = {'data': {'attributes': {'chipTan': {'headline': 'headline', 'instructions': ['in1', 'in2', 'in3']}}}}
        mock_input.return_value=1234
        self.assertEqual(1234, self.dkb._print_ctan_instructions(challenge_dic))
        self.assertIn("headline\n\n1. in1\n\n2. in2\n\n3. in3\n\n", mock_stdout.getvalue())
        self.assertFalse(mock_show.called)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('dkb_robo.api.Wrapper._show_image')
    @patch('builtins.input')
    def test_173__print_ctan_instructions(self, mock_input, mock_show, mock_stdout):
        """ test _print_ctan_instructions()"""
        challenge_dic = {'data': {'attributes': {'chipTan': {'qrData': 'qrData', 'headline': 'headline', 'instructions': ['in1', 'in2', 'in3']}}}}
        mock_input.return_value=1234
        self.assertEqual(1234, self.dkb._print_ctan_instructions(challenge_dic))
        self.assertIn("headline\n\n1. in1\n\n2. in2\n\n3. in3\n\n", mock_stdout.getvalue())
        self.assertTrue(mock_show.called)

    @patch("PIL.Image.open")
    def test_171__print_ctan_instructions(self, mock_open):
        """ test _print_ctan_instructions()"""
        self.assertFalse(self.dkb._show_image('cXJEYXRh'))
        self.assertTrue(mock_open.called)

if __name__ == '__main__':

    unittest.main()
