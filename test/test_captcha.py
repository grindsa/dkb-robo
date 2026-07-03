# -*- coding: utf-8 -*-
# pylint: disable=r0904, c0415, c0413, w0212
"""unittests for dkb_robo.captcha"""

import sys
import unittest
import logging
from unittest.mock import patch, MagicMock

sys.path.insert(0, ".")
sys.path.insert(0, "..")
from dkb_robo.captcha import (
    _apply_browser_headers,
    _click_frc_checkbox,
    _dismiss_cookie_banner,
    _poll_frc_token,
    _transfer_browser_state_to_client,
    get_dkb_redeem_token,
    login_via_browser,
)


class TestApplyBrowserHeaders(unittest.TestCase):
    """tests for _apply_browser_headers()"""

    def test_001_invalid_headers_payload_is_ignored(self):
        """_apply_browser_headers() ignores invalid headers payload"""
        mock_sb = MagicMock()

        class BadHeaders:
            """mapping-like object that fails on items()"""

            def items(self):
                raise Exception("broken mapping")

        _apply_browser_headers(mock_sb, headers=BadHeaders())

        self.assertFalse(mock_sb.driver.execute_cdp_cmd.called)

    def test_002_cdp_exception_is_swallowed(self):
        """_apply_browser_headers() swallows CDP exceptions"""
        mock_sb = MagicMock()
        mock_sb.driver.execute_cdp_cmd.side_effect = Exception("cdp failure")

        _apply_browser_headers(
            mock_sb,
            headers={
                "User-Agent": "UA/1.0",
                "Accept-Language": "de-DE",
            },
        )


class TestDismissCookieBanner(unittest.TestCase):
    """tests for _dismiss_cookie_banner()"""

    def test_003_swallows_exceptions_when_banner_not_clickable(self):
        """_dismiss_cookie_banner() ignores failures of deny/accept clicks"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.side_effect = [Exception("deny"), Exception("accept")]

        _dismiss_cookie_banner(mock_sb)
        self.assertEqual(2, mock_sb.cdp.evaluate.call_count)

    def test_004_accept_path_runs_when_deny_fails(self):
        """_dismiss_cookie_banner() falls back to accept path"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.side_effect = [Exception("deny"), None]

        _dismiss_cookie_banner(mock_sb)
        self.assertEqual(2, mock_sb.cdp.evaluate.call_count)


class TestClickFrcCheckbox(unittest.TestCase):
    """tests for _click_frc_checkbox()"""

    def setUp(self):
        self._sleep_patcher = patch("dkb_robo.captcha.time.sleep", return_value=None)
        self._sleep_patcher.start()

    def tearDown(self):
        self._sleep_patcher.stop()

    def test_005_returns_false_when_find_element_keeps_failing(self):
        """_click_frc_checkbox() returns False after repeated exceptions"""
        mock_sb = MagicMock()
        mock_sb.cdp.find_element.side_effect = Exception("not ready")

        result = _click_frc_checkbox(mock_sb, attempts=3)
        self.assertFalse(result)
        self.assertEqual(3, mock_sb.cdp.find_element.call_count)


class TestTransferBrowserStateToClient(unittest.TestCase):
    """tests for _transfer_browser_state_to_client()"""

    def test_006_handles_cookie_transfer_exception(self):
        """_transfer_browser_state_to_client() continues when cookie transfer fails"""
        mock_sb = MagicMock()
        mock_sb.get_cookies.side_effect = Exception("cookie fail")
        mock_sb.cdp.evaluate.return_value = "UA/1.0"

        mock_client = MagicMock()
        mock_client.headers = {}

        _transfer_browser_state_to_client(mock_sb, mock_client)
        self.assertEqual("UA/1.0", mock_client.headers["User-Agent"])

    def test_007_handles_user_agent_exception(self):
        """_transfer_browser_state_to_client() ignores UA evaluation errors"""
        mock_sb = MagicMock()
        mock_sb.get_cookies.return_value = [{"name": "foo", "value": "bar"}]
        mock_sb.cdp.evaluate.side_effect = Exception("ua fail")

        mock_client = MagicMock()
        mock_client.headers = {}

        _transfer_browser_state_to_client(mock_sb, mock_client)

        mock_client.cookies.set.assert_called_once_with("foo", "bar")
        self.assertNotIn("User-Agent", mock_client.headers)


class TestLoginViaBrowser(unittest.TestCase):
    """tests for login_via_browser()"""

    def setUp(self):
        self._sleep_patcher = patch("dkb_robo.captcha.time.sleep", return_value=None)
        self._sleep_patcher.start()

    def tearDown(self):
        self._sleep_patcher.stop()

    @patch("dkb_robo.captcha.SB")
    def test_008_ignores_optional_step_exceptions(self, mock_sb):
        """login_via_browser() ignores optional UI step exceptions"""
        sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = sb_instance

        def click_side_effect(selector):
            if selector == 'input[id="seal_one"]':
                raise Exception("radio not found")
            if (
                selector
                == 'button[type="submit"] span._sui-button__inner__text_4101u_278'
            ):
                raise Exception("weiter not found")
            return None

        sb_instance.click.side_effect = click_side_effect
        sb_instance.get_cookies.return_value = [{"name": "foo", "value": "bar"}]
        sb_instance.cdp.evaluate.side_effect = [
            Exception("cookie banner lookup fail"),
            "UA/1.0",
            Exception("xsrf fail"),
        ]

        mock_client = MagicMock()
        mock_client.cookies = MagicMock()
        mock_client.headers = {}

        login_via_browser(
            "user",
            "password",
            timeout=1,
            client=mock_client,
        )

        mock_client.cookies.set.assert_called_once_with("foo", "bar")
        self.assertEqual("UA/1.0", mock_client.headers["User-Agent"])

    @patch("dkb_robo.captcha.SB")
    def test_009_covers_cookie_and_checkbox_retry_paths(self, mock_sb):
        """login_via_browser() covers cookie banner deny and captcha retry exception path"""
        sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = sb_instance

        widget = MagicMock()
        sb_instance.cdp.find_element.side_effect = [Exception("not ready"), widget]
        sb_instance.get_cookies.return_value = [{"name": "foo", "value": "bar"}]
        sb_instance.cdp.evaluate.side_effect = [
            True,
            None,
            "UA/1.0",
            "xsrf-token",
        ]

        mock_client = MagicMock()
        mock_client.cookies = MagicMock()
        mock_client.headers = {}

        login_via_browser(
            "user",
            "password",
            timeout=2,
            client=mock_client,
        )

        widget.scroll_into_view.assert_called_once()
        widget.mouse_click.assert_called_once()
        mock_client.cookies.set.assert_called_once_with("foo", "bar")
        self.assertEqual("UA/1.0", mock_client.headers["User-Agent"])
        self.assertEqual("xsrf-token", mock_client.headers["x-xsrf-token"])


class TestPollFrcToken(unittest.TestCase):
    """tests for _poll_frc_token()"""

    def setUp(self):
        # Avoid real delays from polling loops in _poll_frc_token.
        self._sleep_patcher = patch("dkb_robo.captcha.time.sleep", return_value=None)
        self._sleep_patcher.start()

    def tearDown(self):
        self._sleep_patcher.stop()

    def test_010_returns_token_when_available(self):
        """_poll_frc_token() returns token when input has value >400 chars"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = "x" * 401

        result = _poll_frc_token(mock_sb, timeout=5)
        self.assertEqual("x" * 401, result)

    def test_011_returns_false_on_timeout(self):
        """_poll_frc_token() returns False when no token arrives within timeout"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = ".UNFINISHED"

        result = _poll_frc_token(mock_sb, timeout=0)
        self.assertFalse(result)

    def test_012_returns_false_when_value_too_short(self):
        """_poll_frc_token() returns False when value is a placeholder (<= 400 chars)"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = ".ACTIVATED"

        result = _poll_frc_token(mock_sb, timeout=0)
        self.assertFalse(result)

    def test_013_returns_false_when_evaluate_raises(self):
        """_poll_frc_token() returns False when cdp.evaluate raises an exception"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.side_effect = Exception("js error")

        result = _poll_frc_token(mock_sb, timeout=1)
        self.assertFalse(result)

    def test_014_returns_false_when_value_is_none(self):
        """_poll_frc_token() returns False when evaluate returns None"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = None

        result = _poll_frc_token(mock_sb, timeout=0)
        self.assertFalse(result)

    def test_015_retries_until_token_ready(self):
        """_poll_frc_token() retries and returns token once it becomes available"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.side_effect = [".UNFINISHED", ".UNFINISHED", "x" * 401]

        result = _poll_frc_token(mock_sb, timeout=5)
        self.assertEqual("x" * 401, result)
        self.assertEqual(3, mock_sb.cdp.evaluate.call_count)


class TestGetDkbRedeemToken(unittest.TestCase):
    """tests for get_dkb_redeem_token()"""

    def setUp(self):
        # Avoid real delays from checkbox/poll helper sleeps in captcha flow.
        self._sleep_patcher = patch("dkb_robo.captcha.time.sleep", return_value=None)
        self._sleep_patcher.start()

    def tearDown(self):
        self._sleep_patcher.stop()

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_016_returns_token(self, mock_sb, mock_poll):
        """get_dkb_redeem_token() returns token from _poll_frc_token"""
        mock_poll.return_value = "captcha-token-xyz"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        result = get_dkb_redeem_token()
        self.assertEqual("captcha-token-xyz", result)

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_017_returns_false_on_timeout(self, mock_sb, mock_poll):
        """get_dkb_redeem_token() returns False when no token obtained"""
        mock_poll.return_value = False
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        result = get_dkb_redeem_token()
        self.assertFalse(result)

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_018_sb_called_with_uc_true(self, mock_sb, mock_poll):
        """get_dkb_redeem_token() calls SB with uc=True"""
        mock_poll.return_value = "token"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        get_dkb_redeem_token()
        mock_sb.assert_called_once_with(
            uc=True, locale="de", headless=False, xvfb=False
        )

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_019_headless_param_forwarded(self, mock_sb, mock_poll):
        """get_dkb_redeem_token(headless=True) passes headless=True to SB"""
        mock_poll.return_value = "token"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        get_dkb_redeem_token(headless=True)
        _, kwargs = mock_sb.call_args
        self.assertTrue(kwargs["headless"])

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_020_xvfb_param_forwarded(self, mock_sb, mock_poll):
        """get_dkb_redeem_token(xvfb=True) passes xvfb=True to SB"""
        mock_poll.return_value = "token"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        get_dkb_redeem_token(xvfb=True)
        _, kwargs = mock_sb.call_args
        self.assertTrue(kwargs["xvfb"])

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_021_opens_dkb_login(self, mock_sb, mock_poll):
        """get_dkb_redeem_token() opens the DKB login URL"""
        mock_poll.return_value = "token"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        get_dkb_redeem_token()
        mock_sb_instance.open.assert_called_once_with("https://banking.dkb.de/login")

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_022_applies_headers_via_cdp(self, mock_sb, mock_poll):
        """get_dkb_redeem_token(headers=...) applies UA and extra headers via CDP"""
        mock_poll.return_value = "token"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        get_dkb_redeem_token(
            headers={
                "User-Agent": "TestAgent/1.0",
                "Accept-Language": "de-DE",
                "Connection": "keep-alive",
            }
        )

        mock_sb_instance.driver.execute_cdp_cmd.assert_any_call("Network.enable", {})
        mock_sb_instance.driver.execute_cdp_cmd.assert_any_call(
            "Network.setUserAgentOverride", {"userAgent": "TestAgent/1.0"}
        )
        mock_sb_instance.driver.execute_cdp_cmd.assert_any_call(
            "Network.setExtraHTTPHeaders", {"headers": {"Accept-Language": "de-DE"}}
        )

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_023_transfers_browser_state_to_client(self, mock_sb, mock_poll):
        """get_dkb_redeem_token(client=...) copies cookies and UA to the provided client"""
        mock_poll.return_value = "token"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance
        mock_sb_instance.get_cookies.return_value = [{"name": "foo", "value": "bar"}]
        mock_sb_instance.cdp.evaluate.return_value = "UA/1.0"

        mock_client = MagicMock()
        mock_client.headers = {}

        get_dkb_redeem_token(client=mock_client)

        mock_client.cookies.set.assert_called_once_with("foo", "bar")
        self.assertEqual("UA/1.0", mock_client.headers["User-Agent"])


if __name__ == "__main__":
    unittest.main()
