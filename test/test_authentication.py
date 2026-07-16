# -*- coding: utf-8 -*-
# pylint: disable=r0904, c0415, c0413, r0913, w0212
"""unittests for dkb_robo"""

import sys
import os
import types
from datetime import date
import unittest
import logging
import json
from unittest.mock import patch, Mock, MagicMock, mock_open
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
            "INFO:dkb_robo.authentication:Using chip_tan for login", lcm.output
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
            "INFO:dkb_robo.authentication:Using chip_tan for login", lcm.output
        )
        self.assertEqual("chip_tan_qr", self.auth.mfa_method)

    def test_005_init(self):
        """test init()"""
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.auth.__init__(chip_tan="chip_tan_qr")
        self.assertIn(
            "INFO:dkb_robo.authentication:Using chip_tan for login", lcm.output
        )
        self.assertEqual("chip_tan_qr", self.auth.mfa_method)

    def test_006_init_session_backend_alias(self):
        """test session backend alias normalization"""
        self.auth.__init__(session_backend="curl_cffi")
        self.assertEqual("curl-cffi", self.auth.session_backend)

    def test_007_init_http1_only_default(self):
        """test http1_only defaults to False"""
        self.auth.__init__()
        self.assertFalse(self.auth.http1_only)

    def test_008_init_http1_only_enabled(self):
        """test http1_only can be enabled"""
        self.auth.__init__(http1_only=True)
        self.assertTrue(self.auth.http1_only)

    def test_009_init_invalid_session_backend(self):
        """test invalid session backend"""
        with self.assertRaises(Exception) as err:
            self.auth.__init__(session_backend="foo")
        self.assertEqual(
            "Unsupported session backend 'foo'. Use 'requests' or 'curl-cffi'.",
            str(err.exception),
        )

    def test_010__session_new_curl_backend(self):
        """test _session_new() using curl-cffi backend"""
        curl_client = Mock()
        curl_client.cookies = {}
        curl_requests = Mock()
        curl_requests.Session.return_value = curl_client
        curl_http_version = Mock()
        curl_http_version.V1_1 = "V1_1"
        curl_module = Mock()
        curl_module.requests = curl_requests
        curl_module.CurlHttpVersion = curl_http_version

        with patch.dict(sys.modules, {"curl_cffi": curl_module}):
            self.auth.__init__(session_backend="curl-cffi")
            client = self.auth._session_new()

        self.assertEqual(curl_client, client)
        self.assertTrue(curl_requests.Session.called)
        curl_requests.Session.assert_called_once_with(
            impersonate="chrome", default_headers=False
        )

    def test_011__session_new_curl_backend_http1(self):
        """test _session_new() forwards http_version when http1_only is enabled"""
        curl_client = Mock()
        curl_client.cookies = {}
        curl_requests = Mock()
        curl_requests.Session.return_value = curl_client
        curl_http_version = Mock()
        curl_http_version.V1_1 = "V1_1"
        curl_module = Mock()
        curl_module.requests = curl_requests
        curl_module.CurlHttpVersion = curl_http_version

        with patch.dict(sys.modules, {"curl_cffi": curl_module}):
            self.auth.__init__(session_backend="curl-cffi", http1_only=True)
            client = self.auth._session_new()

        self.assertEqual(curl_client, client)
        curl_requests.Session.assert_called_once_with(
            impersonate="chrome", default_headers=False, http_version="V1_1"
        )

    def test_012__session_new_curl_backend_debug_enabled(self):
        """test _session_new() forwards debug=True when logger debug mode is enabled"""
        curl_client = Mock()
        curl_client.cookies = {}
        curl_requests = Mock()
        curl_requests.Session.return_value = curl_client
        curl_http_version = Mock()
        curl_http_version.V1_1 = "V1_1"
        curl_module = Mock()
        curl_module.requests = curl_requests
        curl_module.CurlHttpVersion = curl_http_version

        with patch.dict(sys.modules, {"curl_cffi": curl_module}):
            with patch(
                "dkb_robo.authentication.logger.isEnabledFor", return_value=True
            ):
                self.auth.__init__(session_backend="curl-cffi")
                client = self.auth._session_new()

        self.assertEqual(curl_client, client)
        curl_requests.Session.assert_called_once_with(
            impersonate="chrome", default_headers=False, debug=True
        )

    @patch("requests.session")
    def test_013__session_new(self, mock_session):
        """test _session_new()"""
        self.auth.session_backend = "requests"
        mock_session.return_value.cookies = {}
        client = self.auth._session_new()
        self.assertEqual(mock_session.return_value, client)
        self.assertEqual(self.auth.headers, client.headers)

    @patch("requests.session")
    def test_014__session_new(self, mock_session):
        """test _session_new()"""
        mock_session.headers = {}
        self.auth.proxies = "proxies"
        client = self.auth._session_new()
        self.assertEqual("proxies", client.proxies)

    @patch("requests.session")
    def test_015__session_new(self, mock_session):
        """test _session_new()"""
        self.auth.session_backend = "requests"
        mock_session.return_value.headers = {}
        mock_session.return_value.cookies = {"__Host-xsrf": "foo"}
        client = self.auth._session_new()
        self.assertEqual("foo", client.headers["x-xsrf-token"])

    @patch("requests.session")
    def test_016__session_new_csrf_with_none_headers(self, mock_session):
        """test _session_new() initializes headers when csrf cookie exists and self.headers is None"""
        self.auth.session_backend = "requests"
        self.auth.headers = None
        mock_session.return_value.cookies = {"__Host-xsrf": "foo"}

        client = self.auth._session_new()

        self.assertEqual({"x-xsrf-token": "foo"}, self.auth.headers)
        self.assertEqual({"x-xsrf-token": "foo"}, client.headers)

    @patch("requests.session")
    def test_017__session_new_assigns_headers(self, mock_session):
        """test _session_new() assigns provided headers to client"""
        self.auth.session_backend = "requests"
        self.auth.headers = {"Accept": "application/json"}
        mock_session.return_value.cookies = {}

        client = self.auth._session_new()

        self.assertEqual(self.auth.headers, client.headers)

    def test_018__session_new_curl_backend_import_error(self):
        """test _session_new() raises DKBRoboError when curl-cffi import fails"""
        self.auth.session_backend = "curl-cffi"
        broken_module = types.ModuleType("curl_cffi")
        broken_module.requests = Mock()

        with patch.dict(sys.modules, {"curl_cffi": broken_module}):
            with self.assertRaises(Exception) as err:
                self.auth._session_new()

        self.assertEqual(
            "session_backend='curl-cffi' requires optional dependency 'curl-cffi'.",
            str(err.exception),
        )

    def test_019_init_xvfb(self):
        """test init() with xvfb=True"""
        self.auth.__init__(xvfb=True)
        self.assertTrue(self.auth.xvfb)

    def test_020_init_headless(self):
        """test init() with headless=True"""
        self.auth.__init__(headless=True)
        self.assertTrue(self.auth.headless)

    def test_021_token_get(self):
        """test _token_get() ok"""
        self.auth.dkb_user = "dkb_user"
        self.auth.dkb_password = "dkb_password"
        self.auth.client = Mock()
        self.auth.client.post.return_value.status_code = 200
        self.auth.client.post.return_value.json.return_value = {"foo": "bar"}
        self.auth._token_get()
        self.assertEqual({"foo": "bar"}, self.auth.token_dic)

    def test_022_token_get_xvfb(self):
        """test _token_get() ignores xvfb directly"""
        self.auth.dkb_user = "dkb_user"
        self.auth.dkb_password = "dkb_password"
        self.auth.xvfb = True
        self.auth.client = Mock()
        self.auth.client.post.return_value.status_code = 200
        self.auth.client.post.return_value.json.return_value = {"foo": "bar"}
        self.auth._token_get()
        self.assertEqual({"foo": "bar"}, self.auth.token_dic)

    def test_023_token_get_retries_once_on_csrf_403(self):
        """test _token_get() retries once after csrf-related 403"""
        self.auth.dkb_user = "dkb_user"
        self.auth.dkb_password = "dkb_password"
        self.auth.client = Mock()

        first_response = Mock()
        first_response.status_code = 403
        first_response.text = "csrf token invalid"

        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = {"access_token": "token"}

        self.auth.client.post.side_effect = [first_response, second_response]

        with self.assertLogs("dkb_robo", level="WARNING") as lcm:
            self.auth._token_get(captcha_token="captcha_token")

        self.assertEqual({"access_token": "token"}, self.auth.token_dic)
        self.assertEqual(2, self.auth.client.post.call_count)
        self.auth.client.get.assert_called_once_with(
            self.auth.base_url + "/login", timeout=self.auth.request_timeout
        )
        self.assertIn(
            "WARNING:dkb_robo.authentication:Authentication._token_get(): CSRF rejected, refreshing login page and retrying once",
            lcm.output,
        )

    def test_024_token_get_403_without_csrf_does_not_retry(self):
        """test _token_get() does not retry if 403 is not csrf-related"""
        self.auth.dkb_user = "dkb_user"
        self.auth.dkb_password = "dkb_password"
        self.auth.client = Mock()

        response = Mock()
        response.status_code = 403
        response.text = "forbidden"
        self.auth.client.post.return_value = response

        with self.assertRaises(Exception) as err:
            self.auth._token_get(captcha_token="captcha_token")

        self.assertEqual(
            "Login failed: 1st factor authentication failed. RC: 403",
            str(err.exception),
        )
        self.assertEqual(1, self.auth.client.post.call_count)
        self.auth.client.get.assert_not_called()

    def test_025_sync_csrf_header_uses_host_xsrf_cookie(self):
        """test _sync_csrf_header() prefers __Host-xsrf cookie"""
        self.auth.client = Mock()
        self.auth.client.cookies = {
            "__Host-xsrf": "host-token",
            "XSRF-TOKEN": "fallback-token",
        }
        self.auth.client.headers = {}

        self.auth._sync_csrf_header()

        self.assertEqual("host-token", self.auth.client.headers["x-xsrf-token"])

    def test_026_sync_csrf_header_uses_fallback_cookie(self):
        """test _sync_csrf_header() uses XSRF-TOKEN when __Host-xsrf is missing"""
        self.auth.client = Mock()
        self.auth.client.cookies = {"XSRF-TOKEN": "fallback-token"}
        self.auth.client.headers = {}

        self.auth._sync_csrf_header()

        self.assertEqual("fallback-token", self.auth.client.headers["x-xsrf-token"])

    def test_027_sync_csrf_header_no_token_no_change(self):
        """test _sync_csrf_header() does nothing when csrf cookie is missing"""
        self.auth.client = Mock()
        self.auth.client.cookies = {}
        self.auth.client.headers = {"existing": "header"}

        self.auth._sync_csrf_header()

        self.assertEqual({"existing": "header"}, self.auth.client.headers)

    def test_028_sync_csrf_header_cookies_error_no_change(self):
        """test _sync_csrf_header() ignores cookie access errors"""
        self.auth.client = Mock()
        self.auth.client.cookies = Mock()
        self.auth.client.cookies.get.side_effect = Exception("cookie failure")
        self.auth.client.headers = {"existing": "header"}

        self.auth._sync_csrf_header()

        self.assertEqual({"existing": "header"}, self.auth.client.headers)

    def test_029_sync_csrf_header_headers_fallback_assignment(self):
        """test _sync_csrf_header() falls back to replacing headers mapping"""
        self.auth.client = Mock()
        self.auth.client.cookies = {"__Host-xsrf": "host-token"}
        self.auth.client.headers = None

        self.auth._sync_csrf_header()

        self.assertEqual({"x-xsrf-token": "host-token"}, self.auth.client.headers)

    @patch("dkb_robo.portfolio.Overview.get")
    @patch("dkb_robo.authentication.Authentication._sync_csrf_header")
    @patch("dkb_robo.authentication.login_via_browser")
    @patch("dkb_robo.authentication.Authentication._session_new")
    def test_030_login_browser_applies_returned_headers(
        self,
        mock_session_new,
        mock_browser_login,
        mock_sync_csrf,
        mock_overview,
    ):
        """test login() browser flow syncs csrf after browser login"""
        self.auth.login_via_browser = True

        mock_client = Mock()
        mock_client.headers = {}
        mock_client.cookies = {}
        mock_session_new.return_value = mock_client
        mock_browser_login.return_value = (
            mock_client,
            {
                "headers": {
                    "User-Agent": "UA/1.0",
                    "X-XSRF-TOKEN": "token-from-browser",
                }
            },
        )
        mock_overview.return_value = {"accounts": []}

        self.auth.login()

        self.assertEqual(mock_client, self.auth.client)
        self.assertTrue(mock_sync_csrf.called)

    @patch("dkb_robo.authentication.get_dkb_redeem_token")
    def test_031_token_get(self, mock_captcha):
        """test _token_get() error"""
        mock_captcha.return_value = "captcha_token"
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

    @patch("dkb_robo.authentication.get_dkb_redeem_token")
    def test_032_rest_login_forwards_headless_and_xvfb(self, mock_captcha):
        """test _rest_login() forwards browser mode flags to captcha solver"""
        self.auth.headless = True
        self.auth.xvfb = True
        self.auth.headers = None
        self.auth.client = Mock()
        self.auth._sync_csrf_header = Mock()
        self.auth._device_data_send = Mock()
        self.auth._token_get = Mock()
        self.auth._mfa_get = Mock(return_value={})
        self.auth._mfa_select = Mock(return_value=0)
        self.auth._mfa_challenge = Mock(return_value=("challenge", "device"))
        self.auth._mfa_finalize = Mock(return_value=True)
        self.auth._token_update = Mock(
            side_effect=lambda: self.auth.token_dic.update({"token_factor_type": "2fa"})
        )
        self.auth.token_dic = {"mfa_id": "mfa-id", "access_token": "token"}
        mock_captcha.return_value = "captcha_token"

        with self.assertRaises(Exception) as err:
            self.auth._rest_login()

        self.assertEqual("Login failed: no 1fa access token.", str(err.exception))

        mock_captcha.assert_called_once_with(
            headless=True,
            xvfb=True,
            client=self.auth.client,
        )

    def test_033__mfa_get(self):
        """test _mfa_get()"""
        self.auth.token_dic = {"foo": "bar"}
        with self.assertRaises(Exception) as err:
            self.auth._mfa_get()
        self.assertEqual("Login failed: no 1fa access token.", str(err.exception))

    def test_034__mfa_get(self):
        """test _mfa_get()"""
        self.auth.token_dic = {"access_token": "bar", "mfa_id": "mfa_id"}
        self.auth.client = Mock()
        self.auth.client.get.return_value.status_code = 400
        with self.assertRaises(Exception) as err:
            self.auth._mfa_get()
        self.assertEqual(
            "Login failed: getting mfa_methods failed. RC: 400", str(err.exception)
        )

    def test_035__mfa_get(self):
        """test _mfa_get()"""
        self.auth.client = Mock()
        self.auth.client.get.return_value.status_code = 200
        self.auth.client.get.return_value.json.return_value = {"foo1": "bar1"}
        self.auth.token_dic = {"access_token": "bar", "mfa_id": "mfa_id"}
        self.assertEqual({"foo1": "bar1"}, self.auth._mfa_get())

    def test_036__mfa_sort(self):
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

    def test_037__mfa_sort(self):
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

    def test_038__mfa_sort(self):
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

    def test_039__mfa_select(self):
        """test _mfa_select()"""
        mfa_dic = {"foo": "bar"}
        self.auth.mfa_device = 1
        self.assertEqual(0, self.auth._mfa_select(mfa_dic))

    def test_040__mfa_select(self):
        """test _mfa_select()"""
        mfa_dic = {"foo": "bar"}
        self.auth.mfa_device = 2
        self.assertEqual(1, self.auth._mfa_select(mfa_dic))

    def test_041__mfa_select(self):
        """test _mfa_select()"""
        mfa_dic = {"foo": "bar"}
        self.assertEqual(0, self.auth._mfa_select(mfa_dic))

    def test_042__mfa_process_valid_selection(self):
        """test _mfa_process() accepts valid selection and marks completion"""
        device_num, deviceselection_completed = self.auth._mfa_process(
            device_num=0,
            device_list=[0, 1, 2],
            _tmp_device_num="2",
            deviceselection_completed=False,
        )
        self.assertEqual(1, device_num)
        self.assertTrue(deviceselection_completed)

    def test_043__mfa_process_out_of_range_selection(self):
        """test _mfa_process() rejects out-of-range input"""
        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            device_num, deviceselection_completed = self.auth._mfa_process(
                device_num=0,
                device_list=[0, 1],
                _tmp_device_num="5",
                deviceselection_completed=False,
            )
        self.assertEqual(0, device_num)
        self.assertFalse(deviceselection_completed)
        self.assertIn("Wrong input!", fake_out.getvalue())

    def test_044__mfa_process_non_numeric_selection(self):
        """test _mfa_process() rejects non-numeric input"""
        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            device_num, deviceselection_completed = self.auth._mfa_process(
                device_num=1,
                device_list=[0, 1],
                _tmp_device_num="abc",
                deviceselection_completed=False,
            )
        self.assertEqual(1, device_num)
        self.assertFalse(deviceselection_completed)
        self.assertIn("Invalid input!", fake_out.getvalue())

    @patch("builtins.input", return_value="1")
    def test_045__mfa_select(self, mock_input):
        """test _mfa_select() - multiple devices with interactive selection"""
        self.auth.mfa_device = 0
        mfa_dic = {
            "data": [
                {
                    "attributes": {
                        "deviceName": "device-1",
                        "enrolledAt": "2026-07-16T10:11:12.123Z",
                    }
                },
                {
                    "attributes": {
                        "deviceName": "device-2",
                        "enrolledAt": "2026-07-15T10:11:12.123Z",
                    }
                },
            ]
        }

        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            self.assertEqual(0, self.auth._mfa_select(mfa_dic))

        output = fake_out.getvalue()
        self.assertIn("#   device name", output)
        self.assertIn("enrollment date", output)
        self.assertIn("2026-07-16", output)
        self.assertNotIn("2026-07-16T10:11:12.123Z", output)
        mock_input.assert_called_once_with(":")

    @patch("builtins.input", return_value="1")
    def test_046__mfa_select(self, _mock_input):
        """test _mfa_select() - invalid mfa_device resets to 0 and allows interactive selection"""
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
            "WARNING:dkb_robo.authentication:User submitted mfa_device number is invalid. Ignoring...",
            lcm.output,
        )

    @patch("builtins.input", return_value="cancel")
    def test_041a__mfa_select_cancel(self, _mock_input):
        """test _mfa_select() allows user to cancel device selection"""
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }
        with self.assertRaises(Exception) as err:
            self.auth._mfa_select(mfa_dic)
        self.assertEqual(
            "Login canceled by user during MFA device selection",
            str(err.exception),
        )

    def test_041c__mfa_select_uses_injected_io_callbacks(self):
        """test _mfa_select() can use injected input/output callbacks"""
        outputs = []
        callback_auth = Authentication(
            input_callback=lambda _prompt: "1",
            output_callback=outputs.append,
        )
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }

        with patch("builtins.input", side_effect=AssertionError("builtins.input should not be called")):
            self.assertEqual(0, callback_auth._mfa_select(mfa_dic))

        self.assertTrue(any("Pick an authentication device" in line for line in outputs))

    @patch("builtins.input", return_value="x")
    def test_041b__mfa_select_max_attempts(self, _mock_input):
        """test _mfa_select() aborts after too many invalid attempts"""
        self.auth.mfa_selection_max_attempts = 2
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }
        with self.assertRaises(Exception) as err:
            self.auth._mfa_select(mfa_dic)
        self.assertEqual(
            "Login failed: maximum MFA device selection attempts exceeded",
            str(err.exception),
        )

    @patch("builtins.input", return_value="1")
    def test_047__mfa_select(self, _mock_input):
        """test _mfa_select() - multiple devices, default mfa_device: interactive selection"""
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }
        self.assertEqual(0, self.auth._mfa_select(mfa_dic))

    def test_048__mfa_select(self):
        """test _mfa_select() - multiple devices, mfa_device=2: selects second device"""
        self.auth.mfa_device = 2
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }
        self.assertEqual(1, self.auth._mfa_select(mfa_dic))

    @patch("builtins.input", return_value="1")
    def test_049__mfa_select(self, mock_input):
        """test _mfa_select() - multiple devices prompts for a selection"""
        mfa_dic = {
            "data": [
                {"attributes": {"deviceName": "device-1"}},
                {"attributes": {"deviceName": "device-2"}},
            ]
        }
        self.assertEqual(0, self.auth._mfa_select(mfa_dic))
        mock_input.assert_called_once_with(":")

    @patch("builtins.input", return_value="1")
    def test_050__mfa_select(self, mock_input):
        """test _mfa_select() - multiple devices without deviceName attribute still allow selection"""
        mfa_dic = {
            "data": [
                {"id": "dev1"},
                {"id": "dev2"},
            ]
        }
        self.assertEqual(0, self.auth._mfa_select(mfa_dic))
        mock_input.assert_called_once_with(":")

    @patch("builtins.input", return_value="1")
    def test_051__mfa_select_truncates_long_device_name(self, mock_input):
        """test _mfa_select() truncates long device names to fixed column width"""
        long_device_name = "very-long-device-name-abcdefghijklmnopqrstuvwxyz1234567890"
        expected_name = f"{long_device_name[:33]}..."
        mfa_dic = {
            "data": [
                {
                    "attributes": {
                        "deviceName": long_device_name,
                        "enrolledAt": "2026-07-16T10:11:12.123Z",
                    }
                },
                {"attributes": {"deviceName": "short-name"}},
            ]
        }

        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            self.assertEqual(0, self.auth._mfa_select(mfa_dic))

        output = fake_out.getvalue()
        self.assertIn(expected_name, output)
        self.assertNotIn(long_device_name, output)
        mock_input.assert_called_once_with(":")

    def test_051a__tan_print_uses_injected_io_callbacks(self):
        """test TANAuthentication._print() can use injected input/output callbacks"""
        outputs = []
        tan_auth = TANAuthentication(
            client=Mock(),
            input_callback=lambda _prompt: "123456",
            output_callback=outputs.append,
        )
        challenge_dic = {
            "data": {
                "attributes": {
                    "chipTan": {
                        "headline": "Please confirm",
                        "instructions": ["Step one", "Step two"],
                    }
                }
            }
        }

        with patch("builtins.input", side_effect=AssertionError("builtins.input should not be called")):
            self.assertEqual("123456", tan_auth._print(challenge_dic))

        self.assertTrue(any("Please confirm" in line for line in outputs))
        self.assertTrue(any("1. Step one" in line for line in outputs))

    @patch("requests.session")
    def test_052__mfa_challenge(self, mock_session):
        """test _mfa_challenge()"""
        mfa_dic = {}
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(({}, None), self.auth._mfa_challenge(mfa_dic, 1))
        self.assertIn(
            "ERROR:dkb_robo.authentication:mfa dictionary has an unexpected data structure",
            lcm.output,
        )

    @patch("requests.session")
    def test_053__mfa_challenge(self, mock_session):
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
    def test_054__mfa_challenge(self, mock_session):
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
    def test_055__mfa_challenge(self, mock_session):
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
    def test_056__mfa_finalize(self, mock_cid, mock_app, mock_ctm):
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
    def test_057__mfa_finalize(self, mock_cid, mock_app, mock_ctm):
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
    def test_058__mfa_finalize(self, mock_cid, mock_app, mock_ctm):
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
    def test_059__mfa_challenge_id(self, mock_session):
        """test _mfa_challenge_id()"""
        mfa_dic = {}
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.auth._mfa_challenge_id(mfa_dic))
        self.assertEqual(
            "Login failed: challenge response format is other than expected: {}",
            str(err.exception),
        )

    @patch("requests.session")
    def test_060__mfa_challenge_id(self, mock_session):
        """test _mfa_challenge_id()"""
        mfa_dic = {"data": {"id": "id", "type": "type"}}
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.auth._mfa_challenge_id(mfa_dic))
        self.assertEqual(
            "Login failed:: wrong challenge type: {'data': {'id': 'id', 'type': 'type'}}",
            str(err.exception),
        )

    @patch("requests.session")
    def test_061__mfa_challenge_id(self, mock_session):
        """test _mfa_challenge_id()"""
        mfa_dic = {"data": {"id": "id", "type": "mfa-challenge"}}
        self.assertEqual("id", self.auth._mfa_challenge_id(mfa_dic))

    def test_062__token_update(self):
        """test _token_update() ok"""
        self.auth.token_dic = {"mfa_id": "mfa_id", "access_token": "access_token"}
        self.auth.client = Mock()
        self.auth.client.post.return_value.status_code = 200
        self.auth.client.post.return_value.json.return_value = {"foo": "bar"}
        self.auth._token_update()
        self.assertEqual({"foo": "bar"}, self.auth.token_dic)

    def test_063__token_update(self):
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

    def test_064__device_data_send(self):
        """test _device_data_send() ok"""
        self.auth.token_dic = {"mfa_id": "mfa_id"}
        self.auth.client = Mock()
        self.auth.client.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        self.auth.client.post.return_value.status_code = 204

        self.auth._device_data_send()

        self.assertTrue(self.auth.client.post.called)
        self.assertEqual(
            "application/x-www-form-urlencoded",
            self.auth.client.headers["Content-Type"],
        )
        self.assertEqual(
            "application/json, text/plain, */*", self.auth.client.headers["Accept"]
        )

    def test_065__device_data_send(self):
        """test _device_data_send() nok"""
        self.auth.token_dic = {"mfa_id": "mfa_id"}
        self.auth.client = Mock()
        self.auth.client.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        self.auth.client.post.return_value.status_code = 400

        with self.assertRaises(Exception) as err:
            self.auth._device_data_send()

        self.assertEqual(
            "Login failed: sending web-device data failed. RC: 400",
            str(err.exception),
        )

    @patch("dkb_robo.authentication.get_valid_screen_resolution")
    def test_066__device_data_send_os_detection_and_payload(self, mock_resolution):
        """test _device_data_send() maps User-Agent to OS and forwards screen resolution"""
        mock_resolution.return_value = {"width": 1111, "height": 777}
        self.auth.token_dic = {"mfa_id": "mfa_id"}

        cases = [
            ("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Windows"),
            ("Mozilla/5.0 (X11; Linux x86_64)", "Linux"),
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "Mac OS"),
            ("SomeCustomAgent/1.0", "Unknown"),
        ]

        for user_agent, expected_os in cases:
            self.auth.client = Mock()
            self.auth.client.headers = {
                "User-Agent": user_agent,
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            self.auth.client.post.return_value.status_code = 204

            self.auth._device_data_send()

            mock_resolution.assert_called_with(expected_os)
            _args, kwargs = self.auth.client.post.call_args
            payload = json.loads(kwargs["data"])
            self.assertEqual(
                expected_os,
                payload["data"]["attributes"]["deviceInfo"]["os"],
            )
            self.assertEqual(
                {"width": 1111, "height": 777},
                payload["data"]["attributes"]["deviceInfo"]["screenResolution"],
            )

    @patch("dkb_robo.authentication.Authentication._device_data_send")
    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    @patch("dkb_robo.authentication.get_dkb_redeem_token")
    def test_067_login(
        self,
        _mock_captcha,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_sort,
        mock_device_data_send,
    ):
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
        self.assertTrue(mock_device_data_send.called)

    @patch("dkb_robo.authentication.Authentication._device_data_send")
    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    @patch("dkb_robo.authentication.get_dkb_redeem_token")
    def test_068_login(
        self,
        _mock_captcha,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_mfa,
        mock_sort,
        mock_device_data_send,
    ):
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
        self.assertTrue(mock_device_data_send.called)

    @patch("dkb_robo.authentication.Authentication._device_data_send")
    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    @patch("dkb_robo.authentication.get_dkb_redeem_token")
    def test_069_login(
        self,
        _mock_captcha,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_chall,
        mock_mfa,
        mock_sort,
        mock_device_data_send,
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
        self.assertTrue(mock_device_data_send.called)

    @patch("dkb_robo.authentication.Authentication._device_data_send")
    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._mfa_finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    @patch("dkb_robo.authentication.get_dkb_redeem_token")
    def test_070_login(
        self,
        _mock_captcha,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_chall,
        mock_2fa,
        mock_mfa,
        mock_sort,
        mock_device_data_send,
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
        self.assertTrue(mock_device_data_send.called)

    @patch("dkb_robo.authentication.Authentication._device_data_send")
    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._token_update")
    @patch("dkb_robo.authentication.Authentication._mfa_finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    @patch("dkb_robo.authentication.get_dkb_redeem_token")
    def test_071_login(
        self,
        _mock_captcha,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_chall,
        mock_2fa,
        mock_upd,
        mock_mfa,
        mock_sort,
        mock_device_data_send,
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
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)
        self.assertTrue(mock_device_data_send.called)

    @patch("dkb_robo.authentication.Authentication._device_data_send")
    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._token_update")
    @patch("dkb_robo.authentication.Authentication._mfa_finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    @patch("dkb_robo.authentication.get_dkb_redeem_token")
    def test_072_login(
        self,
        _mock_captcha,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_chall,
        mock_2fa,
        mock_upd,
        mock_mfa,
        mock_sort,
        mock_device_data_send,
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
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)
        self.assertTrue(mock_device_data_send.called)

    @patch("dkb_robo.authentication.Authentication._device_data_send")
    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._token_update")
    @patch("dkb_robo.authentication.Authentication._mfa_finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    @patch("dkb_robo.authentication.get_dkb_redeem_token")
    def test_073_login(
        self,
        _mock_captcha,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_chall,
        mock_2fa,
        mock_upd,
        mock_mfa,
        mock_sort,
        mock_device_data_send,
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
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_sort.called)
        self.assertTrue(mock_device_data_send.called)

    @patch("dkb_robo.authentication.Authentication._device_data_send")
    @patch("dkb_robo.authentication.Authentication._mfa_sort")
    @patch("dkb_robo.portfolio.Overview.get")
    @patch("dkb_robo.authentication.Authentication._mfa_select")
    @patch("dkb_robo.authentication.Authentication._token_update")
    @patch("dkb_robo.authentication.Authentication._mfa_finalize")
    @patch("dkb_robo.authentication.Authentication._mfa_challenge")
    @patch("dkb_robo.authentication.Authentication._mfa_get")
    @patch("dkb_robo.authentication.Authentication._token_get")
    @patch("dkb_robo.authentication.Authentication._session_new")
    @patch("dkb_robo.authentication.get_dkb_redeem_token")
    def test_074_login(
        self,
        _mock_captcha,
        mock_sess,
        mock_tok,
        mock_meth,
        mock_chall,
        mock_2fa,
        mock_upd,
        mock_mfa,
        mock_overview,
        mock_sort,
        mock_device_data_send,
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
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_overview.called)
        self.assertTrue(mock_device_data_send.called)

    def test_075_logout(self):
        """test logout"""
        self.assertFalse(self.auth.logout())

    def test_076_logout_closes_client_and_clears_reference(self):
        """test logout closes an active client and resets self.client"""
        client = Mock()
        self.auth.client = client

        self.auth.logout()

        client.close.assert_called_once()
        self.assertIsNone(self.auth.client)

    def test_077_logout_handles_close_exception_and_clears_reference(self):
        """test logout handles close() errors and still clears self.client"""
        failing_client = Mock()
        failing_client.close.side_effect = RuntimeError("close failed")
        self.auth.client = failing_client

        with self.assertLogs("dkb_robo", level="DEBUG") as lcm:
            self.auth.logout()

        self.assertIsNone(self.auth.client)
        self.assertTrue(
            any(
                "Authentication.logout(): closing client failed:" in line
                for line in lcm.output
            )
        )


class TestAPPAuthentication(unittest.TestCase):
    """test class"""

    @patch("requests.Session")
    def setUp(self, mock_session):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.appauth = APPAuthentication(client=mock_session)
        # self.maxDiff = None

    def test_078__check(self):
        """test _check_processing_status()"""
        polling_dic = {}
        with self.assertRaises(Exception) as err:
            self.assertEqual(False, self.appauth._check(polling_dic, 1))
        self.assertEqual(
            "Login failed: processing status format is other than expected",
            str(err.exception),
        )

    def test_079__check(self):
        """test _check_processing_status()"""
        polling_dic = {"data": {"attributes": {"verificationStatus": "foo"}}}
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(False, self.appauth._check(polling_dic, 1))
        self.assertIn(
            "INFO:dkb_robo.authentication:Unknown processing status: foo", lcm.output
        )

    def test_080__check(self):
        """test _check_processing_status()"""
        polling_dic = {"data": {"attributes": {"verificationStatus": "processed"}}}
        self.assertEqual(True, self.appauth._check(polling_dic, 1))

    def test_081__check(self):
        """test _check_processing_status()"""
        polling_dic = {"data": {"attributes": {"verificationStatus": "canceled"}}}
        with self.assertRaises(Exception) as err:
            self.assertEqual(True, self.appauth._check(polling_dic, 1))
        self.assertEqual("2fa canceled by user", str(err.exception))

    def test_082__check(self):
        """test _check_processing_status()"""
        polling_dic = {"data": {"attributes": {"verificationStatus": "processing"}}}
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(False, self.appauth._check(polling_dic, 1))
        self.assertIn(
            "INFO:dkb_robo.authentication:Status: processing. Waiting for confirmation",
            lcm.output,
        )

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_083__print(self, mock_stdout):
        """test _print_app_2fa_confirmation()"""
        self.appauth._print(None)
        self.assertIn(
            "check your banking app and confirm login...", mock_stdout.getvalue()
        )

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_084__print(self, mock_stdout):
        """test _print_app_2fa_confirmation()"""
        self.appauth._print("devicename")
        self.assertIn(
            'check your banking app on "devicename" and confirm login...',
            mock_stdout.getvalue(),
        )

    @patch("time.sleep", return_value=None)
    @patch("dkb_robo.authentication.APPAuthentication._check")
    @patch("dkb_robo.authentication.APPAuthentication._print")
    def test_085_finalize(self, mock_confirm, mock_status, _mock_sleep):
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
    def test_086_finalize(self, mock_confirm, mock_status, _mock_sleep):
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
    def test_087__print(self, mock_show):
        """test _print()"""
        challenge_dic = {}
        self.assertFalse(self.tanauth._print(challenge_dic))
        self.assertFalse(mock_show.called)

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    @patch("dkb_robo.authentication.TANAuthentication._image")
    @patch("builtins.input")
    def test_088__print(self, mock_input, mock_show, mock_stdout):
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
    def test_089__print(self, mock_input, mock_show, mock_stdout):
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
    def test_090__print(self, mock_open):
        """test _print()"""
        self.assertFalse(self.tanauth._image("cXJEYXRh"))
        self.assertTrue(mock_open.called)

    @patch("dkb_robo.authentication.TANAuthentication._print")
    def test_091_finalize(self, mock_ctan):
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
    def test_092_finalize(self, mock_ctan):
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
    def test_093_finalize(self, mock_ctan):
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
