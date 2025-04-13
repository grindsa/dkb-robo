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

sys.path.insert(0, ".")
sys.path.insert(0, "..")
from dkb_robo.authentication import Authentication, APPAuthentication, TANAuthentication


def json_load(fname):
    """simple json load"""

    with open(fname, "r", encoding="utf8") as myfile:
        data_dic = json.load(myfile)

    return data_dic


class TestAuthentication(unittest.TestCase):
    """test class"""

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger("dkb_robo")
        self.auth = Authentication()
        self.maxDiff = None

    def test_001_init(self):
        """test init()"""
        self.auth.__init__()
        self.assertEqual("seal_one", self.auth.mfa_method)

    def test_002_init(self):
        """test init()"""
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.auth.__init__(chip_tan=True)
        self.assertIn(
            "INFO:dkb_robo.authentication:Using to chip_tan to login", lcm.output
        )
        self.assertEqual("chip_tan_manual", self.auth.mfa_method)

    def test_003_init(self):
        """test init()"""
        self.auth.__init__(chip_tan=False)
        self.assertEqual("seal_one", self.auth.mfa_method)

    def test_004_init(self):
        """test init()"""
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.auth.__init__(chip_tan="qr")
        self.assertIn(
            "INFO:dkb_robo.authentication:Using to chip_tan to login", lcm.output
        )
        self.assertEqual("chip_tan_qr", self.auth.mfa_method)

    def test_005_init(self):
        """test init()"""
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.auth.__init__(chip_tan="chip_tan_qr")
        self.assertIn(
            "INFO:dkb_robo.authentication:Using to chip_tan to login", lcm.output
        )
        self.assertEqual("chip_tan_qr", self.auth.mfa_method)

    @patch("requests.session")
    def test_006__session_new(self, mock_session):
        """test _session_new()"""
        mock_session.headers = {}
        client = self.auth._session_new()
        exp_headers = {
            "Accept-Language": "en-US,en;q=0.5",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "DNT": "1",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "priority": "u=0",
            "sec-gpc": "1",
            "te": "trailers",
        }
        self.assertEqual(exp_headers, client.headers)

    @patch("requests.session")
    def test_007__session_new(self, mock_session):
        """test _session_new()"""
        mock_session.headers = {}
        self.auth.proxies = "proxies"
        client = self.auth._session_new()
        self.assertEqual("proxies", client.proxies)

    @patch("requests.session")
    def test_008__session_new(self, mock_session):
        """test _session_new()"""
        mock_session.headers = {}
        mock_session.get.return_value.status_code = 200
        mock_session.return_value.cookies = {"__Host-xsrf": "foo"}
        client = self.auth._session_new()
        exp_headers = {
            "Accept-Language": "en-US,en;q=0.5",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "DNT": "1",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "x-xsrf-token": "foo",
            "priority": "u=0",
            "sec-gpc": "1",
            "te": "trailers",
        }
        self.assertEqual(exp_headers, client.headers)

    def test_009_token_get(self):
        """test _token_get() ok"""
        self.auth.dkb_user = "dkb_user"
        self.auth.dkb_password = "dkb_password"
        self.auth.client = Mock()
        self.auth.client.post.return_value.status_code = 200
        self.auth.client.post.return_value.json.return_value = {"foo": "bar"}
        self.auth._token_get()
        self.assertEqual({"foo": "bar"}, self.auth.token_dic)

    def test_010_token_get(self):
        """test _token_get() ok"""
        self.auth.dkb_user = "dkb_user"
        self.auth.dkb_password = "dkb_password"
        self.auth.client = Mock()
        self.auth.client.post.return_value.status_code = 400
        self.auth.client.post.return_value.json.return_value = {"foo": "bar"}
        with self.assertRaises(Exception) as err:
            self.auth._token_get()
        self.assertEqual(
            "Login failed: 1st factor authentication failed. RC: 400",
            str(err.exception),
        )
        self.assertFalse(self.auth.token_dic)

    def test_011__mfa_get(self):
        """test _mfa_get()"""
        self.auth.token_dic = {"foo": "bar"}
        with self.assertRaises(Exception) as err:
            self.auth._mfa_get()
        self.assertEqual("Login failed: no 1fa access token.", str(err.exception))

    def test_012__mfa_get(self):
        """test _mfa_get()"""
        self.auth.token_dic = {"access_token": "bar", "mfa_id": "mfa_id"}
        self.auth.client = Mock()
        self.auth.client.get.return_value.status_code = 400
        with self.assertRaises(Exception) as err:
            self.auth._mfa_get()
        self.assertEqual(
            "Login failed: getting mfa_methods failed. RC: 400", str(err.exception)
        )

    def test_013__mfa_get(self):
        """test _mfa_get()"""
        self.auth.client = Mock()
        self.auth.client.get.return_value.status_code = 200
        self.auth.client.get.return_value.json.return_value = {"foo1": "bar1"}
        self.auth.token_dic = {"access_token": "bar", "mfa_id": "mfa_id"}
        self.assertEqual({"foo1": "bar1"}, self.auth._mfa_get())

    def test_014__mfa_sort(self):
        """test sort_mfa_devices()"""
        mfa_dic = {
            "data": [
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-01"}},
                {"attributes": {"preferredDevice": True, "enrolledAt": "2022-01-02"}},
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-03"}},
            ]
        }
        expected_result = {
            "data": [
                {"attributes": {"preferredDevice": True, "enrolledAt": "2022-01-02"}},
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-01"}},
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-03"}},
            ]
        }
        self.assertEqual(expected_result, self.auth._mfa_sort(mfa_dic))

    def test_015__mfa_sort(self):
        """test sort_mfa_devices()"""
        mfa_dic = {
            "data": [
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-03"}},
                {"attributes": {"preferredDevice": True, "enrolledAt": "2022-01-02"}},
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-01"}},
            ]
        }
        expected_result = {
            "data": [
                {"attributes": {"preferredDevice": True, "enrolledAt": "2022-01-02"}},
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-01"}},
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-03"}},
            ]
        }
        self.assertEqual(expected_result, self.auth._mfa_sort(mfa_dic))

    def test_016__mfa_sort(self):
        """test sort_mfa_devices()"""
        mfa_dic = {
            "data": [
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-03"}},
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-02"}},
                {"attributes": {"preferredDevice": True, "enrolledAt": "2022-01-04"}},
            ]
        }
        expected_result = {
            "data": [
                {"attributes": {"preferredDevice": True, "enrolledAt": "2022-01-04"}},
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-02"}},
                {"attributes": {"preferredDevice": False, "enrolledAt": "2022-01-03"}},
            ]
        }
        self.assertEqual(expected_result, self.auth._mfa_sort(mfa_dic))

    def test_017__mfa_select(self):
        """test _mfa_select()"""
        mfa_dic = {"foo": "bar"}
        self.auth.mfa_device = 1
        self.assertEqual(0, self.auth._mfa_select(mfa_dic))

    def test_018__mfa_select(self):
        """test _mfa_select()"""
        mfa_dic = {"foo": "bar"}
        self.auth.mfa_device = 2
        self.assertEqual(1, self.auth._mfa_select(mfa_dic))

    def test_019__mfa_select(self):
        """test _mfa_select()"""
        mfa_dic = {"foo": "bar"}
        self.assertEqual(0, self.auth._mfa_select(mfa_dic))

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input")
    def test_020__mfa_select(self, mock_input, mock_stdout):
        """test _mfa_select()"""
        mock_input.return_value = 1
        self.auth.mfa_device = 0
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }
        self.assertEqual(0, self.auth._mfa_select(mfa_dic))
        self.assertIn(
            "\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n",
            mock_stdout.getvalue(),
        )

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input")
    def test_021__mfa_select(self, mock_input, mock_stdout):
        """test _mfa_select()"""
        mock_input.return_value = 1
        self.auth.mfa_device = 4
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(0, self.auth._mfa_select(mfa_dic))
        self.assertIn(
            "WARNING:dkb_robo.authentication:User submitted mfa_device number is invalid. Ingoring...",
            lcm.output,
        )
        self.assertIn(
            "\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n",
            mock_stdout.getvalue(),
        )

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input")
    def test_022__mfa_select(self, mock_input, mock_stdout):
        """test _mfa_select()"""
        mock_input.return_value = 1
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }
        self.assertEqual(0, self.auth._mfa_select(mfa_dic))
        self.assertIn(
            "\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n",
            mock_stdout.getvalue(),
        )

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input")
    def test_023__mfa_select(self, mock_input, mock_stdout):
        """test _mfa_select()"""
        mock_input.return_value = 2
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }
        self.assertEqual(1, self.auth._mfa_select(mfa_dic))
        self.assertIn(
            "\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n",
            mock_stdout.getvalue(),
        )

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input")
    def test_024__mfa_select(self, mock_input, mock_stdout):
        """test _mfa_select()"""
        mock_input.side_effect = [4, 1]
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }
        self.assertEqual(0, self.auth._mfa_select(mfa_dic))
        self.assertIn(
            "\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n",
            mock_stdout.getvalue(),
        )
        self.assertIn("Wrong input!", mock_stdout.getvalue())

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input")
    def test_025__mfa_select(self, mock_input, mock_stdout):
        """test _mfa_select()"""
        mock_input.side_effect = ["a", 4, 1]
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }
        self.assertEqual(0, self.auth._mfa_select(mfa_dic))
        self.assertIn(
            "\nPick an authentication device from the below list:\n[1] - device-1\n[2] - device-2\n",
            mock_stdout.getvalue(),
        )
        self.assertIn("Invalid input!", mock_stdout.getvalue())
        self.assertIn("Wrong input!", mock_stdout.getvalue())

    @patch("requests.session")
    def test_026__mfa_challenge(self, mock_session):
        """test _mfa_challenge()"""
        mfa_dic = {}
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(({}, None), self.auth._mfa_challenge(mfa_dic, 1))
        self.assertIn(
            "ERROR:dkb_robo.authentication:mfa dictionary has an unexpected data structure",
            lcm.output,
        )

    @patch("requests.session")
    def test_027__mfa_challenge(self, mock_session):
        """test _mfa_challenge()"""
        self.auth.client = Mock()
        self.auth.client.headers = {}
        self.auth.client.post.return_value.status_code = 200
        self.auth.client.post.return_value.json.return_value = {
            "data": {"type": "mfa-challenge", "id": "id"}
        }
        self.auth.client.headers = {"foo": "bar"}
        self.auth.mfa_method = "seal_one"
        self.auth.token_dic = {"mfa_id": "mfa_id"}
        mfa_dic = {
            "data": {1: {"id": "id", "attributes": {"deviceName": "deviceName"}}}
        }
        self.assertEqual(
            ({"data": {"id": "id", "type": "mfa-challenge"}}, "deviceName"),
            self.auth._mfa_challenge(mfa_dic, 1),
        )

    @patch("requests.session")
    def test_028__mfa_challenge(self, mock_session):
        """test _mfa_challenge()"""
        self.auth.client = Mock()
        self.auth.client.headers = {}
        self.auth.client.post.return_value.status_code = 400
        self.auth.client.post.return_value.json.return_value = {
            "data": {"type": "mfa-challenge", "id": "id"}
        }
        self.auth.client.headers = {"foo": "bar"}
        self.auth.mfa_method = "seal_one"
        self.auth.token_dic = {"mfa_id": "mfa_id"}
        mfa_dic = {
            "data": {1: {"id": "id", "attributes": {"deviceName": "deviceName"}}}
        }
        with self.assertRaises(Exception) as err:
            self.assertEqual(
                ({"data": {"id": "id", "type": "mfa-challenge"}}, "deviceName"),
                self.auth._mfa_challenge(mfa_dic, 1),
            )
        self.assertEqual(
            "Login failed: post request to get the mfa challenges failed. RC: 400",
            str(err.exception),
        )

    @patch("requests.session")
    def test_029__mfa_challenge(self, mock_session):
        """test _mfa_challenge()"""
        self.auth.client = Mock()
        self.auth.client.headers = {}
        self.auth.client.post.return_value.status_code = 200
        self.auth.client.post.return_value.json.return_value = {
            "data": {"type": "mfa-challenge", "id": "id"}
        }
        self.auth.client.headers = {"foo": "bar"}
        self.auth.mfa_method = "seal_one"
        self.auth.token_dic = {"mfa_id": "mfa_id"}
        mfa_dic = {"data": {1: {"id": "id", "attributes": {"foo": "bar"}}}}
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(
                ({"data": {"id": "id", "type": "mfa-challenge"}}, None),
                self.auth._mfa_challenge(mfa_dic, 1),
            )
        self.assertIn(
            "ERROR:dkb_robo.authentication:unable to get mfa-deviceName for device_num: 1",
            lcm.output,
        )

    @patch("dkb_robo.authentication.TANAuthentication.finalize")
    @patch("dkb_robo.authentication.APPAuthentication.finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge_id")
    def test_030__mfa_finalize(self, mock_cid, mock_app, mock_ctm):
        """test _mfa_finalize()"""
        mock_cid.return_value = "cid"
        mock_app.return_value = "app"
        mock_ctm.return_value = "ctm"
        self.auth.mfa_method = "seal_one"
        self.assertEqual("app", self.auth._mfa_finalize("challenge_dic", "device_name"))
        self.assertTrue(mock_cid.called)
        self.assertTrue(mock_app.called)
        self.assertFalse(mock_ctm.called)

    @patch("dkb_robo.authentication.TANAuthentication.finalize")
    @patch("dkb_robo.authentication.APPAuthentication.finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge_id")
    def test_031__mfa_finalize(self, mock_cid, mock_app, mock_ctm):
        """test _mfa_finalize()"""
        mock_cid.return_value = "cid"
        mock_app.return_value = "app"
        mock_ctm.return_value = "ctm"
        self.auth.mfa_method = "chip_tan_manual"
        self.assertEqual("ctm", self.auth._mfa_finalize("challenge_dic", "device_name"))
        self.assertTrue(mock_cid.called)
        self.assertFalse(mock_app.called)
        self.assertTrue(mock_ctm.called)

    @patch("dkb_robo.authentication.TANAuthentication.finalize")
    @patch("dkb_robo.authentication.APPAuthentication.finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge_id")
    def test_032__mfa_finalize(self, mock_cid, mock_app, mock_ctm):
        """test _mfa_finalize()"""
        mock_cid.return_value = "cid"
        mock_app.return_value = "app"
        mock_ctm.return_value = "ctm"
        self.auth.mfa_method = "other_method"
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.auth._mfa_finalize("challenge_dic", "device_name"))
        self.assertEqual(
            "Login failed: unknown mfa method: other_method", str(err.exception)
        )
        self.assertTrue(mock_cid.called)
        self.assertFalse(mock_app.called)
        self.assertFalse(mock_ctm.called)

    @patch("requests.session")
    def test_033__mfa_challenge_id(self, mock_session):
        """test _mfa_challenge_id()"""
        mfa_dic = {}
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.auth._mfa_challenge_id(mfa_dic))
        self.assertEqual(
            "Login failed: challenge response format is other than expected: {}",
            str(err.exception),
        )

    @patch("requests.session")
    def test_034__mfa_challenge_id(self, mock_session):
        """test _mfa_challenge_id()"""
        mfa_dic = {"data": {"id": "id", "type": "type"}}
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.auth._mfa_challenge_id(mfa_dic))
        self.assertEqual(
            "Login failed:: wrong challenge type: {'data': {'id': 'id', 'type': 'type'}}",
            str(err.exception),
        )

    @patch("requests.session")
    def test_035__mfa_challenge_id(self, mock_session):
        """test _mfa_challenge_id()"""
        mfa_dic = {"data": {"id": "id", "type": "mfa-challenge"}}
        self.assertEqual("id", self.auth._mfa_challenge_id(mfa_dic))

    def test_036__token_update(self):
        """test _token_update() ok"""
        self.auth.token_dic = {"mfa_id": "mfa_id", "access_token": "access_token"}
        self.auth.client = Mock()
        self.auth.client.post.return_value.status_code = 200
        self.auth.client.post.return_value.json.return_value = {"foo": "bar"}
        self.auth._token_update()
        self.assertEqual({"foo": "bar"}, self.auth.token_dic)

    def test_037__token_update(self):
        """test _token_update() nok"""
        self.auth.token_dic = {"mfa_id": "mfa_id", "access_token": "access_token"}
        self.auth.client = Mock()
        self.auth.client.post.return_value.status_code = 400
        self.auth.client.post.return_value.json.return_value = {"foo": "bar"}
        with self.assertRaises(Exception) as err:
            self.auth._token_update()
        self.assertEqual(
            "Login failed: token update failed. RC: 400", str(err.exception)
        )
        self.assertEqual(
            {"mfa_id": "mfa_id", "access_token": "access_token"}, self.auth.token_dic
        )

    @patch("dkb_robo.legacy.Wrapper._new_instance")
    def test_037__sso_redirect(self, mock_instance):
        """test _sso_redirect() ok"""
        self.auth.client = Mock()
        self.auth.client.headers = {}
        self.auth.client.post.return_value.status_code = 200
        self.auth.client.post.return_value.text = "OK"
        self.auth._sso_redirect()
        self.assertTrue(mock_instance.called)

    @patch("dkb_robo.legacy.Wrapper._new_instance")
    def test_038__sso_redirect(self, mock_instance):
        """test _sso_redirect() nok"""
        self.auth.client = Mock()
        self.auth.client.headers = {}
        self.auth.client.post.return_value.status_code = 200
        self.auth.client.post.return_value.text = "NOK"
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.auth._sso_redirect()
        self.assertIn(
            "ERROR:dkb_robo.authentication:SSO redirect failed. RC: 200 text: NOK",
            lcm.output,
        )
        self.assertTrue(mock_instance.called)

    @patch("dkb_robo.legacy.Wrapper._new_instance")
    def test_039__sso_redirect(self, mock_instance):
        """test _sso_redirect() nok"""
        self.auth.client = Mock()
        self.auth.client.headers = {}
        self.auth.client.post.return_value.status_code = 400
        self.auth.client.post.return_value.text = "OK"
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.auth._sso_redirect()
        self.assertIn(
            "ERROR:dkb_robo.authentication:SSO redirect failed. RC: 400 text: OK",
            lcm.output,
        )
        self.assertTrue(mock_instance.called)

    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    def test_040_login(self, mock_sess, mock_tok, mock_meth, mock_sort):
        """test login()"""
        self.auth.token_dic = {"foo": "bar"}
        mock_meth.return_value = {"foo": "bar"}
        mock_sort.return_value = {"foo": "bar"}
        with self.assertRaises(Exception) as err:
            self.auth.login()
        self.assertEqual("Login failed: no 1fa access token.", str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)

    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    def test_041_login(self, mock_sess, mock_tok, mock_meth, mock_mfa, mock_sort):
        """test login()"""
        self.auth.token_dic = {"mfa_id": "mfa_id"}
        mock_meth.return_value = {"foo": "bar"}
        mock_sort.return_value = {"foo": "bar"}
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.auth.login()
        self.assertEqual("Login failed: no 1fa access token.", str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    def test_041_login(
        self, mock_sess, mock_tok, mock_meth, mock_chall, mock_mfa, mock_sort
    ):
        """test login()"""
        self.auth.token_dic = {"mfa_id": "mfa_id"}
        mock_meth.return_value = {"data": "bar"}
        mock_sort.return_value = {"data": "bar"}
        mock_chall.return_value = (None, None)
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.auth.login()
        self.assertEqual("Login failed: No challenge id.", str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._mfa_finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    def test_042_login(
        self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_mfa, mock_sort
    ):
        """test login()"""
        self.auth.token_dic = {"mfa_id": "mfa_id"}
        mock_meth.return_value = {"data": "bar"}
        mock_sort.return_value = {"data": "bar"}
        mock_chall.return_value = ("mfa_challenge_id", "deviceName")
        mock_2fa.return_value = False
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.auth.login()
        self.assertEqual("Login failed: mfa did not complete", str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._sso_redirect")
    @patch("dkb_robo.authentication.Authentication._token_update")
    @patch("dkb_robo.authentication.Authentication._mfa_finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    def test_043_login(
        self,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_chall,
        mock_2fa,
        mock_upd,
        mock_redir,
        mock_mfa,
        mock_sort,
    ):
        """test login()"""
        self.auth.token_dic = {"mfa_id": "mfa_id"}
        mock_meth.return_value = {"data": "bar"}
        mock_sort.return_value = {"data": "bar"}
        mock_chall.return_value = ("mfa_challenge_id", "deviceName")
        mock_2fa.return_value = True
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.auth.login()
        self.assertEqual("Login failed: mfa did not complete", str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertFalse(mock_redir.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._sso_redirect")
    @patch("dkb_robo.authentication.Authentication._token_update")
    @patch("dkb_robo.authentication.Authentication._mfa_finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    def test_044_login(
        self,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_chall,
        mock_2fa,
        mock_upd,
        mock_redir,
        mock_mfa,
        mock_sort,
    ):
        """test login()"""
        self.auth.token_dic = {"mfa_id": "mfa_id", "access_token": "access_token"}
        mock_meth.return_value = {"data": "bar"}
        mock_sort.return_value = {"data": "bar"}
        mock_chall.return_value = ("mfa_challenge_id", "deviceName")
        mock_2fa.return_value = True
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.auth.login()
        self.assertEqual(
            "Login failed: token_factor_type is missing", str(err.exception)
        )
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertFalse(mock_redir.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._sso_redirect")
    @patch("dkb_robo.authentication.Authentication._token_update")
    @patch("dkb_robo.authentication.Authentication._mfa_finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    def test_045_login(
        self,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_chall,
        mock_2fa,
        mock_upd,
        mock_redir,
        mock_mfa,
        mock_sort,
    ):
        """test login()"""
        self.auth.token_dic = {
            "mfa_id": "mfa_id",
            "access_token": "access_token",
            "token_factor_type": "token_factor_type",
        }
        mock_meth.return_value = {"data": "bar"}
        mock_sort.return_value = {"data": "bar"}
        mock_chall.return_value = ("mfa_challenge_id", "deviceName")
        mock_mfa.return_value = 0
        mock_2fa.return_value = True
        with self.assertRaises(Exception) as err:
            self.auth.login()
        self.assertEqual(
            "Login failed: 2nd factor authentication did not complete",
            str(err.exception),
        )
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertFalse(mock_redir.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)

    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.portfolio.Overview.get")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._sso_redirect")
    @patch("dkb_robo.authentication.Authentication._token_update")
    @patch("dkb_robo.authentication.Authentication._mfa_finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    def test_046_login(
        self,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_chall,
        mock_2fa,
        mock_upd,
        mock_redir,
        mock_mfa,
        mock_overview,
        mock_sort,
    ):
        """test login()"""
        self.auth.token_dic = {
            "mfa_id": "mfa_id",
            "access_token": "access_token",
            "token_factor_type": "2fa",
        }
        mock_meth.return_value = {"data": "bar"}
        mock_sort.return_value = {"data": "bar"}
        mock_chall.return_value = ("mfa_challenge_id", "deviceName")
        mock_mfa.return_value = 0
        mock_2fa.return_value = True
        self.auth.login()
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertTrue(mock_redir.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_overview.called)

    def test_147_logout(self):
        """test logout"""
        self.assertFalse(self.auth.logout())


class TestAPPAuthentication(unittest.TestCase):
    """test class"""

    @patch("requests.Session")
    def setUp(self, mock_session):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.appauth = APPAuthentication(client=mock_session)
        # self.maxDiff = None

    def test_001__check(self):
        """test _check_processing_status()"""
        polling_dic = {}
        with self.assertRaises(Exception) as err:
            self.assertEqual(False, self.appauth._check(polling_dic, 1))
        self.assertEqual(
            "Login failed: processing status format is other than expected",
            str(err.exception),
        )

    def test_002__check(self):
        """test _check_processing_status()"""
        polling_dic = {"data": {"attributes": {"verificationStatus": "foo"}}}
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(False, self.appauth._check(polling_dic, 1))
        self.assertIn(
            "INFO:dkb_robo.authentication:Unknown processing status: foo", lcm.output
        )

    def test_0003__check(self):
        """test _check_processing_status()"""
        polling_dic = {"data": {"attributes": {"verificationStatus": "processed"}}}
        self.assertEqual(True, self.appauth._check(polling_dic, 1))

    def test_004__check(self):
        """test _check_processing_status()"""
        polling_dic = {"data": {"attributes": {"verificationStatus": "canceled"}}}
        with self.assertRaises(Exception) as err:
            self.assertEqual(True, self.appauth._check(polling_dic, 1))
        self.assertEqual("2fa chanceled by user", str(err.exception))

    def test_005__check(self):
        """test _check_processing_status()"""
        polling_dic = {"data": {"attributes": {"verificationStatus": "processing"}}}
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(False, self.appauth._check(polling_dic, 1))
        self.assertIn(
            "INFO:dkb_robo.authentication:Status: processing. Waiting for confirmation",
            lcm.output,
        )

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_006__print(self, mock_stdout):
        """test _print_app_2fa_confirmation()"""
        self.appauth._print(None)
        self.assertIn(
            "check your banking app and confirm login...", mock_stdout.getvalue()
        )

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_007__print(self, mock_stdout):
        """test _print_app_2fa_confirmation()"""
        self.appauth._print("devicename")
        self.assertIn(
            'check your banking app on "devicename" and confirm login...',
            mock_stdout.getvalue(),
        )

    @patch("time.sleep", return_value=None)
    @patch("dkb_robo.authentication.APPAuthentication._check")
    @patch("dkb_robo.authentication.APPAuthentication._print")
    def test_008_finalize(self, mock_confirm, mock_status, _mock_sleep):
        """test _mfa_finalize()"""
        self.appauth.client = Mock()
        self.appauth.client.headers = {}
        self.appauth.client.get.return_value.status_code = 200
        self.appauth.client.get.return_value.json.side_effect = [
            {"foo1": "bar1"},
            {"data": {"attributes": {"verificationStatus": "bump"}}},
        ]
        mock_status.side_effects = [False, True]
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertTrue(
                self.appauth.finalize("challengeid", {"foo": "bar"}, "devicename")
            )
        self.assertIn(
            "ERROR:dkb_robo.authentication:error parsing polling response: {'foo1': 'bar1'}",
            lcm.output,
        )
        self.assertTrue(mock_confirm.called)

    @patch("time.sleep", return_value=None)
    @patch("dkb_robo.authentication.APPAuthentication._check")
    @patch("dkb_robo.authentication.APPAuthentication._print")
    def test_009_finalize(self, mock_confirm, mock_status, _mock_sleep):
        """test _mfa_finalize()"""
        self.appauth.client = Mock()
        self.appauth.client.headers = {}
        self.appauth.client.get.return_value.status_code = 400
        self.appauth.client.get.return_value.json.side_effect = [
            {"foo1": "bar1"},
            {"data": {"attributes": {"verificationStatus": "bump"}}},
        ]
        mock_status.return_value = False
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertFalse(
                self.appauth.finalize("challengeid", {"foo": "bar"}, "devicename")
            )
        self.assertIn(
            "ERROR:dkb_robo.authentication:Polling request failed. RC: 400", lcm.output
        )
        self.assertTrue(mock_confirm.called)


class TestTANAuthentication(unittest.TestCase):
    """test class"""

    @patch("requests.Session")
    def setUp(self, mock_session):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.tanauth = TANAuthentication(client=mock_session)
        # self.maxDiff = None

    @patch("dkb_robo.authentication.TANAuthentication._image")
    def test_001__print(self, mock_show):
        """test _print()"""
        challenge_dic = {}
        self.assertFalse(self.tanauth._print(challenge_dic))
        self.assertFalse(mock_show.called)

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    @patch("dkb_robo.authentication.TANAuthentication._image")
    @patch("builtins.input")
    def test_002__print(self, mock_input, mock_show, mock_stdout):
        """test _print()"""
        challenge_dic = {
            "data": {
                "attributes": {
                    "chipTan": {
                        "headline": "headline",
                        "instructions": ["in1", "in2", "in3"],
                    }
                }
            }
        }
        mock_input.return_value = 1234
        self.assertEqual(1234, self.tanauth._print(challenge_dic))
        self.assertIn(
            "headline\n\n1. in1\n\n2. in2\n\n3. in3\n\n", mock_stdout.getvalue()
        )
        self.assertFalse(mock_show.called)

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    @patch("dkb_robo.authentication.TANAuthentication._image")
    @patch("builtins.input")
    def test_003__print(self, mock_input, mock_show, mock_stdout):
        """test _print()"""
        challenge_dic = {
            "data": {
                "attributes": {
                    "chipTan": {
                        "qrData": "qrData",
                        "headline": "headline",
                        "instructions": ["in1", "in2", "in3"],
                    }
                }
            }
        }
        mock_input.return_value = 1234
        self.assertEqual(1234, self.tanauth._print(challenge_dic))
        self.assertIn(
            "headline\n\n1. in1\n\n2. in2\n\n3. in3\n\n", mock_stdout.getvalue()
        )
        self.assertTrue(mock_show.called)

    @patch("PIL.Image.open")
    def test_004__print(self, mock_open):
        """test _print()"""
        self.assertFalse(self.tanauth._image("cXJEYXRh"))
        self.assertTrue(mock_open.called)

    @patch("dkb_robo.authentication.TANAuthentication._print")
    def test_005_finalize(self, mock_ctan):
        """test finalize()"""
        mock_ctan.return_value = "ctan"
        self.tanauth.client = Mock()
        self.tanauth.client.headers = {}
        self.tanauth.client.post.return_value.status_code = 200
        self.tanauth.client.post.return_value.json.return_value = {
            "data": {"attributes": {"verificationStatus": "authorized"}}
        }
        challenge_dic = {"foo": "bar"}
        self.assertTrue(
            self.tanauth.finalize("challengeid", challenge_dic, "devicename")
        )
        self.assertTrue(mock_ctan.called)

    @patch("dkb_robo.authentication.TANAuthentication._print")
    def test_006_finalize(self, mock_ctan):
        """test finalize()"""
        mock_ctan.return_value = "ctan"
        self.tanauth.client = Mock()
        self.tanauth.client.headers = {}
        self.tanauth.client.post.return_value.status_code = 200
        self.tanauth.client.post.return_value.json.return_value = {
            "data": {"attributes": {"verificationStatus": "foo"}}
        }
        challenge_dic = {"foo": "bar"}
        self.assertFalse(
            self.tanauth.finalize("challengeid", challenge_dic, "devicename")
        )
        self.assertTrue(mock_ctan.called)

    @patch("dkb_robo.authentication.TANAuthentication._print")
    def test_007_finalize(self, mock_ctan):
        """test finalize()"""
        mock_ctan.return_value = "ctan"
        self.tanauth.client = Mock()
        self.tanauth.client.headers = {}
        self.tanauth.client.post.return_value.status_code = 400
        self.tanauth.client.post.return_value.json.return_value = {
            "data": {"attributes": {"verificationStatus": "foo"}}
        }
        self.tanauth.client.post.return_value.text = "bump"
        challenge_dic = {"foo": "bar"}
        with self.assertRaises(Exception) as err:
            self.assertFalse(
                self.tanauth.finalize("challengeid", challenge_dic, "devicename")
            )
        self.assertEqual(
            "Login failed: 2fa failed. RC: 400 text: bump", str(err.exception)
        )
        self.assertTrue(mock_ctan.called)


if __name__ == "__main__":

    unittest.main()
