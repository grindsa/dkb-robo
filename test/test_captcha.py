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
    _UcDebugPortGuard,
    _apply_browser_headers,
    _click_frc_checkbox,
    _click_frc_with_screen_coords,
    _cookie_banner_button_rects,
    _cookie_banner_visible,
    _dismiss_cookie_banner,
    _frc_click_started,
    _frc_iframe_rect,
    _frc_token_value,
    _gui_click_cookie_button,
    _is_active_frc_token,
    _poll_frc_token,
    _remove_cookie_banner_host,
    _shadow_dom_dismiss_cookies,
    _transfer_browser_state_to_client,
    _uc_ui_dismiss_cookies,
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

    def setUp(self):
        self._sleep_patcher = patch("dkb_robo.captcha.time.sleep", return_value=None)
        self._sleep_patcher.start()

    def tearDown(self):
        self._sleep_patcher.stop()

    @patch("dkb_robo.captcha._remove_cookie_banner_host", return_value=True)
    @patch("dkb_robo.captcha._cookie_banner_visible", side_effect=[True, True, True])
    def test_003_swallows_exceptions_when_banner_not_clickable(
        self, _mock_visible, mock_remove
    ):
        """_dismiss_cookie_banner() keeps going when UC_UI/deny/accept clicks fail"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.side_effect = Exception("boom")

        # Final remove path still clears the banner for this attempt.
        result = _dismiss_cookie_banner(mock_sb, timeout=1)
        self.assertTrue(result)
        self.assertTrue(mock_remove.called)

    @patch("dkb_robo.captcha._remove_cookie_banner_host", return_value=True)
    @patch(
        "dkb_robo.captcha._cookie_banner_visible",
        side_effect=[True, False],
    )
    @patch("dkb_robo.captcha._uc_ui_dismiss_cookies", return_value=True)
    def test_004b_uc_ui_path_dismisses_banner(
        self, mock_uc, _mock_visible, mock_remove
    ):
        """_dismiss_cookie_banner() prefers UC_UI.denyAllConsents()+closeCMP()"""
        mock_sb = MagicMock()

        result = _dismiss_cookie_banner(mock_sb, timeout=1)
        self.assertTrue(result)
        self.assertTrue(mock_uc.called)
        self.assertTrue(mock_remove.called)


class TestClickFrcCheckbox(unittest.TestCase):
    """tests for _click_frc_checkbox()"""

    def setUp(self):
        self._sleep_patcher = patch("dkb_robo.captcha.time.sleep", return_value=None)
        self._sleep_patcher.start()

    def tearDown(self):
        self._sleep_patcher.stop()

    @patch("dkb_robo.captcha._cookie_banner_visible", return_value=False)
    @patch("dkb_robo.captcha._frc_iframe_rect", return_value=None)
    def test_005_returns_false_when_iframe_never_appears(
        self, _mock_rect, _mock_visible
    ):
        """_click_frc_checkbox() returns False when the FRC iframe is missing"""
        mock_sb = MagicMock()

        result = _click_frc_checkbox(mock_sb, attempts=3)
        self.assertFalse(result)

    @patch("dkb_robo.captcha._frc_token_value", side_effect=[".UNACTIVATED", "x" * 401])
    @patch("dkb_robo.captcha._cookie_banner_visible", return_value=False)
    @patch(
        "dkb_robo.captcha._frc_iframe_rect",
        return_value={"x": 100, "y": 200, "w": 400, "h": 70},
    )
    @patch(
        "dkb_robo.captcha._click_frc_with_screen_coords",
        return_value="gui_click_captcha",
    )
    def test_005b_uses_screen_click_when_widget_present(
        self, mock_screen_click, _mock_rect, _mock_visible, _mock_token
    ):
        """_click_frc_checkbox() prefers a screen-aware OS-level captcha click"""
        mock_sb = MagicMock()

        result = _click_frc_checkbox(mock_sb, attempts=1)
        self.assertTrue(result)
        self.assertTrue(mock_screen_click.called)


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

    @patch("dkb_robo.captcha._click_frc_checkbox", return_value=True)
    @patch("dkb_robo.captcha._dismiss_cookie_banner", return_value=False)
    @patch("dkb_robo.captcha.SB")
    def test_008_ignores_optional_step_exceptions(
        self, mock_sb, _mock_dismiss, _mock_click_frc
    ):
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

    @patch("dkb_robo.captcha._click_frc_checkbox", return_value=True)
    @patch("dkb_robo.captcha._dismiss_cookie_banner", return_value=True)
    @patch("dkb_robo.captcha.SB")
    def test_009_covers_cookie_and_checkbox_helpers(
        self, mock_sb, mock_dismiss, mock_click_frc
    ):
        """login_via_browser() calls cookie/captcha helpers then builds a session"""
        sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = sb_instance

        sb_instance.get_cookies.return_value = [{"name": "foo", "value": "bar"}]
        sb_instance.cdp.evaluate.side_effect = [
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

        mock_dismiss.assert_called()
        mock_click_frc.assert_called()
        mock_client.cookies.set.assert_called_once_with("foo", "bar")
        self.assertEqual("UA/1.0", mock_client.headers["User-Agent"])
        self.assertEqual("xsrf-token", mock_client.headers["x-xsrf-token"])

    @patch("dkb_robo.captcha._click_frc_checkbox", return_value=True)
    @patch("dkb_robo.captcha._dismiss_cookie_banner", return_value=True)
    @patch("dkb_robo.captcha.SB")
    def test_009a_initializes_client_headers_when_missing(
        self, mock_sb, _mock_dismiss, _mock_click_frc
    ):
        """login_via_browser() initializes client.headers when it is None"""
        sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = sb_instance

        sb_instance.get_cookies.return_value = [{"name": "foo", "value": "bar"}]
        sb_instance.cdp.evaluate.return_value = "UA/1.0"

        mock_client = MagicMock()
        mock_client.cookies = MagicMock()
        mock_client.headers = None

        login_via_browser(
            "user",
            "password",
            timeout=1,
            client=mock_client,
        )

        self.assertIsInstance(mock_client.headers, dict)
        self.assertIn("User-Agent", mock_client.headers)
        mock_client.cookies.set.assert_called_once_with("foo", "bar")


class TestIsActiveFrcToken(unittest.TestCase):
    """tests for _is_active_frc_token()"""

    def test_009b_rejects_placeholders_and_short_values(self):
        """_is_active_frc_token() rejects .UNACTIVATED and short values"""
        self.assertFalse(_is_active_frc_token(None))
        self.assertFalse(_is_active_frc_token(""))
        self.assertFalse(_is_active_frc_token(".UNACTIVATED"))
        self.assertFalse(_is_active_frc_token(".UNFINISHED"))
        self.assertFalse(_is_active_frc_token("x" * 100))
        self.assertTrue(_is_active_frc_token("x" * 401))


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
        self._dismiss_patcher = patch(
            "dkb_robo.captcha._dismiss_cookie_banner", return_value=True
        )
        self._dismiss_patcher.start()
        self._click_patcher = patch(
            "dkb_robo.captcha._click_frc_checkbox", return_value=True
        )
        self._click_patcher.start()

    def tearDown(self):
        self._sleep_patcher.stop()
        self._dismiss_patcher.stop()
        self._click_patcher.stop()

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


class TestUcDebugPortGuard(unittest.TestCase):
    """tests for _UcDebugPortGuard"""

    def test_024_blocks_9222_probe_and_restores_get(self):
        """_UcDebugPortGuard fakes a busy 9222 probe then restores Session.get"""
        import requests

        original_get = requests.Session.get
        session = requests.Session()
        passthrough = MagicMock(return_value="passthrough")

        with _UcDebugPortGuard() as guard:
            probe = session.get("http://127.0.0.1:9222/json/version")
            self.assertEqual(200, probe.status_code)
            saved_original = guard.original_get
            guard.original_get = passthrough
            self.assertEqual("passthrough", session.get("http://example.com/other"))
            passthrough.assert_called()
            guard.original_get = saved_original

        self.assertIs(original_get, requests.Session.get)


class TestCookieBannerHelpers(unittest.TestCase):
    """direct coverage for cookie-banner helper functions"""

    def test_025_cookie_banner_button_rects_non_list(self):
        """_cookie_banner_button_rects() returns [] when evaluate is non-list"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = {"unexpected": True}
        self.assertEqual([], _cookie_banner_button_rects(mock_sb))

    def test_026_cookie_banner_button_rects_filters_non_dicts(self):
        """_cookie_banner_button_rects() keeps only dict entries"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = [
            {"text": "Ablehnen", "className": "deny", "x": 1, "y": 2, "w": 3, "h": 4},
            "skip",
        ]
        result = _cookie_banner_button_rects(mock_sb)
        self.assertEqual(1, len(result))
        self.assertEqual("Ablehnen", result[0]["text"])

    def test_027_cookie_banner_button_rects_exception(self):
        """_cookie_banner_button_rects() returns [] on evaluate errors"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.side_effect = Exception("boom")
        self.assertEqual([], _cookie_banner_button_rects(mock_sb))

    def test_028_cookie_banner_visible(self):
        """_cookie_banner_visible() mirrors button-rect presence"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = [
            {"text": "x", "className": "", "x": 0, "y": 0, "w": 1, "h": 1}
        ]
        self.assertTrue(_cookie_banner_visible(mock_sb))
        mock_sb.cdp.evaluate.return_value = []
        self.assertFalse(_cookie_banner_visible(mock_sb))

    def test_029_remove_cookie_banner_host_success_and_error(self):
        """_remove_cookie_banner_host() returns True/False based on evaluate"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = True
        self.assertTrue(_remove_cookie_banner_host(mock_sb))
        mock_sb.cdp.evaluate.side_effect = Exception("boom")
        self.assertFalse(_remove_cookie_banner_host(mock_sb))

    def test_030_uc_ui_dismiss_cookies_success(self):
        """_uc_ui_dismiss_cookies() returns evaluate result as bool"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = True
        self.assertTrue(_uc_ui_dismiss_cookies(mock_sb))
        mock_sb.cdp.evaluate.return_value = False
        self.assertFalse(_uc_ui_dismiss_cookies(mock_sb))

    def test_031_gui_click_cookie_button_prefers_deny(self):
        """_gui_click_cookie_button() prefers Ablehnen/deny then gui-clicks"""
        mock_sb = MagicMock()
        mock_sb.bring_active_window_to_front.side_effect = Exception("focus fail")
        with patch(
            "dkb_robo.captcha._cookie_banner_button_rects",
            return_value=[
                {
                    "text": "Alles akzeptieren",
                    "className": "accept",
                    "x": 10,
                    "y": 20,
                    "w": 100,
                    "h": 40,
                },
                {
                    "text": "Ablehnen",
                    "className": "uc-deny-button",
                    "x": 5,
                    "y": 6,
                    "w": 10,
                    "h": 20,
                },
            ],
        ):
            self.assertTrue(_gui_click_cookie_button(mock_sb))
        mock_sb.cdp.gui_click_x_y.assert_called_once_with(10.0, 16.0)
        mock_sb.bring_active_window_to_front.assert_called()

    def test_032_gui_click_cookie_button_falls_back_and_handles_errors(self):
        """_gui_click_cookie_button() uses first button and swallows click errors"""
        mock_sb = MagicMock()
        del mock_sb.bring_active_window_to_front
        mock_sb.cdp.gui_click_x_y.side_effect = Exception("click fail")
        with patch(
            "dkb_robo.captcha._cookie_banner_button_rects",
            return_value=[
                {
                    "text": "OK",
                    "className": "",
                    "x": 0,
                    "y": 0,
                    "w": 10,
                    "h": 10,
                }
            ],
        ):
            self.assertFalse(_gui_click_cookie_button(mock_sb))

    def test_033_gui_click_cookie_button_no_buttons(self):
        """_gui_click_cookie_button() returns False when no buttons"""
        with patch("dkb_robo.captcha._cookie_banner_button_rects", return_value=[]):
            self.assertFalse(_gui_click_cookie_button(MagicMock()))

    def test_034_shadow_dom_dismiss_deny_then_accept(self):
        """_shadow_dom_dismiss_cookies() tries deny then accept"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.side_effect = [None]
        self.assertTrue(_shadow_dom_dismiss_cookies(mock_sb))

        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.side_effect = [Exception("no deny"), None]
        self.assertTrue(_shadow_dom_dismiss_cookies(mock_sb))

        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.side_effect = [
            Exception("no deny"),
            Exception("no accept"),
        ]
        self.assertFalse(_shadow_dom_dismiss_cookies(mock_sb))


class TestDismissCookieBannerPaths(unittest.TestCase):
    """path coverage for _dismiss_cookie_banner()"""

    def setUp(self):
        self._sleep_patcher = patch("dkb_robo.captcha.time.sleep", return_value=None)
        self._sleep_patcher.start()

    def tearDown(self):
        self._sleep_patcher.stop()

    @patch("dkb_robo.captcha._remove_cookie_banner_host", return_value=True)
    @patch("dkb_robo.captcha._cookie_banner_visible", return_value=False)
    def test_035_not_visible_removes_host(self, _mock_visible, mock_remove):
        """_dismiss_cookie_banner() removes host when banner already gone"""
        self.assertTrue(_dismiss_cookie_banner(MagicMock(), timeout=1))
        self.assertTrue(mock_remove.called)

    @patch("dkb_robo.captcha._remove_cookie_banner_host", return_value=True)
    @patch(
        "dkb_robo.captcha._cookie_banner_visible",
        side_effect=[True, False],
    )
    @patch("dkb_robo.captcha._gui_click_cookie_button", return_value=True)
    @patch("dkb_robo.captcha._uc_ui_dismiss_cookies", return_value=False)
    def test_036_gui_path(self, _mock_uc, mock_gui, _mock_visible, mock_remove):
        """_dismiss_cookie_banner() succeeds via GUI click path"""
        self.assertTrue(_dismiss_cookie_banner(MagicMock(), timeout=1))
        self.assertTrue(mock_gui.called)
        self.assertTrue(mock_remove.called)

    @patch("dkb_robo.captcha._remove_cookie_banner_host", return_value=True)
    @patch(
        "dkb_robo.captcha._cookie_banner_visible",
        side_effect=[True, False],
    )
    @patch("dkb_robo.captcha._shadow_dom_dismiss_cookies", return_value=True)
    @patch("dkb_robo.captcha._gui_click_cookie_button", return_value=False)
    @patch("dkb_robo.captcha._uc_ui_dismiss_cookies", return_value=False)
    def test_037_shadow_path(
        self, _mock_uc, _mock_gui, mock_shadow, _mock_visible, mock_remove
    ):
        """_dismiss_cookie_banner() succeeds via shadow DOM path"""
        self.assertTrue(_dismiss_cookie_banner(MagicMock(), timeout=1))
        self.assertTrue(mock_shadow.called)
        self.assertTrue(mock_remove.called)

    @patch("dkb_robo.captcha._remove_cookie_banner_host", return_value=False)
    @patch("dkb_robo.captcha._cookie_banner_visible", return_value=True)
    @patch("dkb_robo.captcha._shadow_dom_dismiss_cookies", return_value=False)
    @patch("dkb_robo.captcha._gui_click_cookie_button", return_value=False)
    @patch("dkb_robo.captcha._uc_ui_dismiss_cookies", return_value=False)
    def test_038_timeout_returns_false(self, _a, _b, _c, _d, _e):
        """_dismiss_cookie_banner() returns False after timeout"""
        self.assertFalse(_dismiss_cookie_banner(MagicMock(), timeout=1))


class TestFrcHelpers(unittest.TestCase):
    """coverage for FRC helper functions"""

    def test_039_frc_iframe_rect_success_and_errors(self):
        """_frc_iframe_rect() returns evaluate payload or None"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = {"x": 1, "y": 2, "w": 3, "h": 4}
        self.assertEqual({"x": 1, "y": 2, "w": 3, "h": 4}, _frc_iframe_rect(mock_sb))
        mock_sb.cdp.evaluate.side_effect = Exception("boom")
        self.assertIsNone(_frc_iframe_rect(mock_sb))

    def test_040_frc_token_value_success_and_errors(self):
        """_frc_token_value() returns evaluate payload or None"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = ".UNACTIVATED"
        self.assertEqual(".UNACTIVATED", _frc_token_value(mock_sb))
        mock_sb.cdp.evaluate.side_effect = Exception("boom")
        self.assertIsNone(_frc_token_value(mock_sb))

    def test_041_frc_click_started(self):
        """_frc_click_started() rejects empty/.UNACTIVATED, accepts others"""
        self.assertFalse(_frc_click_started(None))
        self.assertFalse(_frc_click_started(""))
        self.assertFalse(_frc_click_started(".UNACTIVATED"))
        self.assertTrue(_frc_click_started(".UNFINISHED"))
        self.assertTrue(_frc_click_started("token"))

    def test_042_click_frc_with_screen_coords_gui_click_captcha(self):
        """prefers cdp.gui_click_captcha when available"""
        mock_sb = MagicMock()
        mock_sb.cdp.gui_click_captcha = MagicMock()
        self.assertEqual("gui_click_captcha", _click_frc_with_screen_coords(mock_sb))
        mock_sb.cdp.gui_click_captcha.assert_called_once()

    def test_043_click_frc_with_screen_coords_uc_gui(self):
        """falls back to sb.uc_gui_click_captcha"""
        mock_sb = MagicMock()
        del mock_sb.cdp.gui_click_captcha
        mock_sb.uc_gui_click_captcha = MagicMock()
        self.assertEqual("uc_gui_click_captcha", _click_frc_with_screen_coords(mock_sb))
        mock_sb.uc_gui_click_captcha.assert_called_once()

    def test_044_click_frc_with_screen_coords_offset(self):
        """falls back to gui_click_with_offset"""
        mock_sb = MagicMock()
        del mock_sb.cdp.gui_click_captcha
        del mock_sb.uc_gui_click_captcha
        mock_sb.cdp.gui_click_with_offset = MagicMock()
        self.assertEqual(
            "gui_click_with_offset", _click_frc_with_screen_coords(mock_sb)
        )

    def test_045_click_frc_with_screen_coords_manual(self):
        """falls back to get_gui_element_rect + gui_click_x_y"""
        mock_sb = MagicMock()
        del mock_sb.cdp.gui_click_captcha
        del mock_sb.uc_gui_click_captcha
        del mock_sb.cdp.gui_click_with_offset
        mock_sb.cdp.get_gui_element_rect.return_value = {"x": 100, "y": 200}
        self.assertEqual("gui_click_x_y", _click_frc_with_screen_coords(mock_sb))
        mock_sb.cdp.gui_click_x_y.assert_called_once_with(127, 234)


class TestClickFrcCheckboxPaths(unittest.TestCase):
    """additional _click_frc_checkbox() paths"""

    def setUp(self):
        self._sleep_patcher = patch("dkb_robo.captcha.time.sleep", return_value=None)
        self._sleep_patcher.start()

    def tearDown(self):
        self._sleep_patcher.stop()

    @patch("dkb_robo.captcha._frc_token_value", return_value=".UNFINISHED")
    @patch("dkb_robo.captcha._dismiss_cookie_banner", return_value=True)
    @patch("dkb_robo.captcha._cookie_banner_visible", return_value=True)
    @patch(
        "dkb_robo.captcha._frc_iframe_rect",
        return_value={"x": 1, "y": 2, "w": 3, "h": 4},
    )
    @patch(
        "dkb_robo.captcha._click_frc_with_screen_coords",
        return_value="gui_click_captcha",
    )
    def test_046_dismisses_overlay_during_click(
        self, mock_screen, _mock_rect, mock_visible, mock_dismiss, _mock_token
    ):
        """_click_frc_checkbox() dismisses a still-visible cookie overlay"""
        mock_sb = MagicMock()
        self.assertTrue(_click_frc_checkbox(mock_sb, attempts=1))
        self.assertTrue(mock_dismiss.called)
        self.assertTrue(mock_screen.called)

    @patch("dkb_robo.captcha._frc_token_value", return_value=".UNFINISHED")
    @patch("dkb_robo.captcha._cookie_banner_visible", return_value=False)
    @patch(
        "dkb_robo.captcha._frc_iframe_rect",
        return_value={"x": 1, "y": 2, "w": 3, "h": 4},
    )
    @patch(
        "dkb_robo.captcha._click_frc_with_screen_coords",
        side_effect=Exception("screen fail"),
    )
    def test_047_falls_through_click_methods(
        self, _mock_screen, _mock_rect, _mock_visible, _mock_token
    ):
        """_click_frc_checkbox() tries CDP then mouse after screen click fails"""
        mock_sb = MagicMock()
        mock_sb.bring_active_window_to_front.side_effect = Exception("focus fail")
        mock_sb.cdp.click_with_offset.side_effect = Exception("cdp fail")
        elem = MagicMock()
        mock_sb.cdp.find_element.return_value = elem

        self.assertTrue(_click_frc_checkbox(mock_sb, attempts=1))
        self.assertTrue(mock_sb.cdp.click_with_offset.called)
        self.assertTrue(elem.scroll_into_view.called)
        self.assertTrue(elem.mouse_click.called)

    @patch("dkb_robo.captcha._frc_token_value", return_value=".UNACTIVATED")
    @patch("dkb_robo.captcha._cookie_banner_visible", return_value=False)
    @patch(
        "dkb_robo.captcha._frc_iframe_rect",
        return_value={"x": 1, "y": 2, "w": 3, "h": 4},
    )
    @patch(
        "dkb_robo.captcha._click_frc_with_screen_coords",
        side_effect=Exception("screen fail"),
    )
    def test_048_returns_false_when_clicks_never_start(
        self, _mock_screen, _mock_rect, _mock_visible, _mock_token
    ):
        """_click_frc_checkbox() returns False when widget stays .UNACTIVATED"""
        mock_sb = MagicMock()
        mock_sb.cdp.click_with_offset.side_effect = Exception("cdp fail")
        mock_sb.cdp.find_element.side_effect = Exception("mouse fail")
        self.assertFalse(_click_frc_checkbox(mock_sb, attempts=1))


class TestPollFrcTokenReclick(unittest.TestCase):
    """_poll_frc_token() reclick path"""

    def setUp(self):
        self._sleep_patcher = patch("dkb_robo.captcha.time.sleep", return_value=None)
        self._sleep_patcher.start()

    def tearDown(self):
        self._sleep_patcher.stop()

    @patch("dkb_robo.captcha._click_frc_checkbox")
    @patch("dkb_robo.captcha._dismiss_cookie_banner")
    def test_049_reclicks_on_interval(self, mock_dismiss, mock_click):
        """_poll_frc_token() re-dismisses/re-clicks every reclick_every seconds"""
        mock_sb = MagicMock()
        # seconds 0..5 return unfinished (reclick at second==5), token on second 6
        mock_sb.cdp.evaluate.side_effect = [".UNFINISHED"] * 6 + ["x" * 401]
        result = _poll_frc_token(mock_sb, timeout=7, reclick_every=5)
        self.assertEqual("x" * 401, result)
        self.assertTrue(mock_dismiss.called)
        self.assertTrue(mock_click.called)


if __name__ == "__main__":
    unittest.main()
