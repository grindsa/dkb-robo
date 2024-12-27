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
    def test_030_print_app_2fa_confirmation(self, mock_stdout):
        """ test _print_app_2fa_confirmation()"""
        self.dkb._print_app_2fa_confirmation(None)
        self.assertIn('check your banking app and confirm login...', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_031_print_app_2fa_confirmation(self, mock_stdout):
        """ test _print_app_2fa_confirmation()"""
        self.dkb._print_app_2fa_confirmation('devicename')
        self.assertIn('check your banking app on "devicename" and confirm login...', mock_stdout.getvalue())

    @patch('requests.session')
    def test_032_new_instance_new_session(self, mock_session):
        """ test _new_session() """
        mock_session.headers = {}
        client = self.dkb._new_session()
        exp_headers = {'Accept-Language': 'en-US,en;q=0.5', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'DNT': '1', 'Pragma': 'no-cache', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0', 'priority': 'u=0', 'sec-gpc': '1', 'te': 'trailers'}
        self.assertEqual(exp_headers, client.headers)

    @patch('requests.session')
    def test_033_new_instance_new_session(self, mock_session):
        """ test _new_session() """
        mock_session.headers = {}
        self.dkb.proxies = 'proxies'
        client = self.dkb._new_session()
        self.assertEqual('proxies', client.proxies)

    @patch('requests.session')
    def test_034_new_instance_new_session(self, mock_session):
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
    def test_035_login(self, mock_sess, mock_tok, mock_meth, mock_sort):
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
    def test_036_login(self, mock_sess, mock_tok, mock_meth, mock_mfa, mock_sort):
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
    def test_037_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_mfa, mock_sort):
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
    def test_038_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_mfa, mock_sort):
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
    def test_039_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_mfa, mock_sort):
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
    def test_040_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_mfa, mock_sort):
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
    def test_041_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_mfa, mock_sort):
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
    def test_042_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_mfa, mock_overview, mock_sort):
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
        self.assertFalse(mock_overview.called)

    def test_043__select_mfa_device(self):
        """ test _select_mfa_device() """
        mfa_dic = {'foo': 'bar'}
        self.dkb.mfa_device = 1
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))

    def test_044__select_mfa_device(self):
        """ test _select_mfa_device() """
        mfa_dic = {'foo': 'bar'}
        self.dkb.mfa_device = 2
        self.assertEqual(1, self.dkb._select_mfa_device(mfa_dic))

    def test_045__select_mfa_device(self):
        """ test _select_mfa_device() """
        mfa_dic = {'foo': 'bar'}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_046__select_mfa_device(self, mock_input, mock_stdout):
        """ test _select_mfa_device() """
        mock_input.return_value=1
        self.dkb.mfa_device = 0
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_047__select_mfa_device(self, mock_input, mock_stdout):
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
    def test_048__select_mfa_device(self, mock_input, mock_stdout):
        """ test _select_mfa_device() """
        mock_input.return_value=1
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_049__select_mfa_device(self, mock_input, mock_stdout):
        """ test _select_mfa_device() """
        mock_input.return_value=2
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(1, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_050__select_mfa_device(self, mock_input, mock_stdout):
        """ test _select_mfa_device() """
        mock_input.side_effect = [4, 1]
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n", mock_stdout.getvalue())
        self.assertIn('Wrong input!', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_051__select_mfa_device(self, mock_input, mock_stdout):
        """ test _select_mfa_device() """
        mock_input.side_effect = ['a', 4, 1]
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n", mock_stdout.getvalue())
        self.assertIn('Invalid input!', mock_stdout.getvalue())
        self.assertIn('Wrong input!', mock_stdout.getvalue())

    def test_110_get_credit_limits(self):
        """ teest _get_credit_limits() """
        self.dkb.account_dic = {0: {'limit': 1000, 'iban': 'iban'}, 1: {'limit': 2000, 'maskedpan': 'maskedpan'}}
        result_dic = {'iban': 1000, 'maskedpan': 2000}
        self.assertEqual(result_dic, self.dkb.get_credit_limits())

    def test_111_get_credit_limits(self):
        """ teest get_credit_limits() """
        self.dkb.account_dic = {'foo': 'bar'}
        self.assertFalse(self.dkb.get_credit_limits())

    def test_119_logout(self):
        """ test logout """
        self.assertFalse(self.dkb.logout())

    @patch('dkb_robo.legacy.Wrapper.get_exemption_order')
    def test_130_get_exemption_order(self, mock_exo):
        """ test get_exemption_order() """
        mock_exo.return_value = 'mock_exo'
        self.assertEqual('mock_exo', self.dkb.get_exemption_order())

    def test_145_sort_mfa_devices(self):
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


    def test_146_sort_mfa_devices(self):
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


    def test_147_sort_mfa_devices(self):
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

    def test_156_init(self):
        """ test init() """
        self.dkb.__init__()
        self.assertEqual('seal_one', self.dkb.mfa_method)

    def test_157_init(self):
        """ test init() """
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb.__init__(logger=self.logger, chip_tan=True)
        self.assertIn('INFO:dkb_robo:Using to chip_tan to login', lcm.output)
        self.assertEqual('chip_tan_manual', self.dkb.mfa_method)

    def test_158_init(self):
        """ test init() """
        self.dkb.__init__(logger=self.logger, chip_tan=False)
        self.assertEqual('seal_one', self.dkb.mfa_method)

    def test_159_init(self):
        """ test init() """
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb.__init__(logger=self.logger, chip_tan='qr')
        self.assertIn('INFO:dkb_robo:Using to chip_tan to login', lcm.output)
        self.assertEqual('chip_tan_qr', self.dkb.mfa_method)

    def test_160_init(self):
        """ test init() """
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb.__init__(logger=self.logger, chip_tan='chip_tan_qr')
        self.assertIn('INFO:dkb_robo:Using to chip_tan to login', lcm.output)
        self.assertEqual('chip_tan_qr', self.dkb.mfa_method)

    @patch('dkb_robo.api.Wrapper._complete_ctm_2fa')
    @patch('dkb_robo.api.Wrapper._complete_app_2fa')
    @patch('dkb_robo.api.Wrapper._get_challenge_id')
    def test_161_complete_2fa(self, mock_cid, mock_app, mock_ctm):
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
    def test_162_complete_2fa(self, mock_cid, mock_app, mock_ctm):
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
    def test_163_complete_2fa(self, mock_cid, mock_app, mock_ctm):
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
    def test_164_get_challenge_id(self, mock_session):
        """ test _get_challenge_id() """
        mfa_dic = {}
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb._get_challenge_id(mfa_dic))
        self.assertEqual('Login failed: challenge response format is other than expected: {}', str(err.exception))

    @patch('requests.session')
    def test_165_get_challenge_id(self, mock_session):
        """ test _get_challenge_id() """
        mfa_dic = {'data': {'id': 'id', 'type': 'type'}}
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb._get_challenge_id(mfa_dic))
        self.assertEqual("Login failed:: wrong challenge type: {'data': {'id': 'id', 'type': 'type'}}", str(err.exception))

    @patch('requests.session')
    def test_166_get_challenge_id(self, mock_session):
        """ test _get_challenge_id() """
        mfa_dic = {'data': {'id': 'id', 'type': 'mfa-challenge'}}
        self.assertEqual('id', self.dkb._get_challenge_id(mfa_dic))

    @patch('requests.session')
    def test_167_get_mfa_challenge_dic(self, mock_session):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(({}, None), self.dkb._get_mfa_challenge_dic(mfa_dic, 1))
        self.assertIn('ERROR:dkb_robo:api.Wrapper._get_mfa_challenge_dic(): mfa_dic has an unexpected data structure', lcm.output)

    @patch('requests.session')
    def test_168_get_mfa_challenge_dic(self, mock_session):
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
    def test_169_get_mfa_challenge_dic(self, mock_session):
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
    def test_170_get_mfa_challenge_dic(self, mock_session):
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
    def test_171__complete_app_2fa(self, mock_confirm, mock_status, _mock_sleep):
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
    def test_172__complete_app_2fa(self, mock_confirm, mock_status, _mock_sleep):
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
    def test_173_complete_ctm_2fa(self, mock_ctan):
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
    def test_174_complete_ctm_2fa(self, mock_ctan):
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
    def test_175_complete_ctm_2fa(self, mock_ctan):
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
    def test_176__print_ctan_instructions(self, mock_show):
        """ test _print_ctan_instructions()"""
        challenge_dic = {}
        self.assertFalse(self.dkb._print_ctan_instructions(challenge_dic))
        self.assertFalse(mock_show.called)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('dkb_robo.api.Wrapper._show_image')
    @patch('builtins.input')
    def test_177__print_ctan_instructions(self, mock_input, mock_show, mock_stdout):
        """ test _print_ctan_instructions()"""
        challenge_dic = {'data': {'attributes': {'chipTan': {'headline': 'headline', 'instructions': ['in1', 'in2', 'in3']}}}}
        mock_input.return_value=1234
        self.assertEqual(1234, self.dkb._print_ctan_instructions(challenge_dic))
        self.assertIn("headline\n\n1. in1\n\n2. in2\n\n3. in3\n\n", mock_stdout.getvalue())
        self.assertFalse(mock_show.called)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('dkb_robo.api.Wrapper._show_image')
    @patch('builtins.input')
    def test_178__print_ctan_instructions(self, mock_input, mock_show, mock_stdout):
        """ test _print_ctan_instructions()"""
        challenge_dic = {'data': {'attributes': {'chipTan': {'qrData': 'qrData', 'headline': 'headline', 'instructions': ['in1', 'in2', 'in3']}}}}
        mock_input.return_value=1234
        self.assertEqual(1234, self.dkb._print_ctan_instructions(challenge_dic))
        self.assertIn("headline\n\n1. in1\n\n2. in2\n\n3. in3\n\n", mock_stdout.getvalue())
        self.assertTrue(mock_show.called)

    @patch("PIL.Image.open")
    def test_179__print_ctan_instructions(self, mock_open):
        """ test _print_ctan_instructions()"""
        self.assertFalse(self.dkb._show_image('cXJEYXRh'))
        self.assertTrue(mock_open.called)

if __name__ == '__main__':

    unittest.main()
