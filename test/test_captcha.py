# -*- coding: utf-8 -*-
# pylint: disable=r0904, c0415, c0413, w0212
"""unittests for dkb_robo.captcha"""
import sys
import unittest
import logging
from unittest.mock import patch, MagicMock

sys.path.insert(0, ".")
sys.path.insert(0, "..")
from dkb_robo.captcha import _poll_frc_token, get_dkb_redeem_token


class TestPollFrcToken(unittest.TestCase):
    """tests for _poll_frc_token()"""

    def test_001_returns_token_when_available(self):
        """_poll_frc_token() returns token when input has value >400 chars"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = "x" * 401

        result = _poll_frc_token(mock_sb, timeout=5)
        self.assertEqual("x" * 401, result)

    def test_002_returns_false_on_timeout(self):
        """_poll_frc_token() returns False when no token arrives within timeout"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = ".UNFINISHED"

        result = _poll_frc_token(mock_sb, timeout=0)
        self.assertFalse(result)

    def test_003_returns_false_when_value_too_short(self):
        """_poll_frc_token() returns False when value is a placeholder (<= 400 chars)"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = ".ACTIVATED"

        result = _poll_frc_token(mock_sb, timeout=0)
        self.assertFalse(result)

    def test_004_returns_false_when_evaluate_raises(self):
        """_poll_frc_token() returns False when cdp.evaluate raises an exception"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.side_effect = Exception("js error")

        result = _poll_frc_token(mock_sb, timeout=0)
        self.assertFalse(result)

    def test_005_returns_false_when_value_is_none(self):
        """_poll_frc_token() returns False when evaluate returns None"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.return_value = None

        result = _poll_frc_token(mock_sb, timeout=0)
        self.assertFalse(result)

    def test_006_retries_until_token_ready(self):
        """_poll_frc_token() retries and returns token once it becomes available"""
        mock_sb = MagicMock()
        mock_sb.cdp.evaluate.side_effect = [".UNFINISHED", ".UNFINISHED", "x" * 401]

        result = _poll_frc_token(mock_sb, timeout=5)
        self.assertEqual("x" * 401, result)
        self.assertEqual(3, mock_sb.cdp.evaluate.call_count)


class TestGetDkbRedeemToken(unittest.TestCase):
    """tests for get_dkb_redeem_token()"""

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_001_returns_token(self, mock_sb, mock_poll):
        """get_dkb_redeem_token() returns token from _poll_frc_token"""
        mock_poll.return_value = "captcha-token-xyz"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        result = get_dkb_redeem_token()
        self.assertEqual("captcha-token-xyz", result)

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_002_returns_false_on_timeout(self, mock_sb, mock_poll):
        """get_dkb_redeem_token() returns False when no token obtained"""
        mock_poll.return_value = False
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        result = get_dkb_redeem_token()
        self.assertFalse(result)

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_003_sb_called_with_uc_true(self, mock_sb, mock_poll):
        """get_dkb_redeem_token() calls SB with uc=True"""
        mock_poll.return_value = "token"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        get_dkb_redeem_token()
        mock_sb.assert_called_once_with(uc=True, locale="de", headless=False, xvfb=False)

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_004_headless_param_forwarded(self, mock_sb, mock_poll):
        """get_dkb_redeem_token(headless=True) passes headless=True to SB"""
        mock_poll.return_value = "token"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        get_dkb_redeem_token(headless=True)
        _, kwargs = mock_sb.call_args
        self.assertTrue(kwargs["headless"])

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_006_xvfb_param_forwarded(self, mock_sb, mock_poll):
        """get_dkb_redeem_token(xvfb=True) passes xvfb=True to SB"""
        mock_poll.return_value = "token"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        get_dkb_redeem_token(xvfb=True)
        _, kwargs = mock_sb.call_args
        self.assertTrue(kwargs["xvfb"])

    @patch("dkb_robo.captcha._poll_frc_token", new_callable=MagicMock)
    @patch("dkb_robo.captcha.SB")
    def test_005_opens_dkb_login(self, mock_sb, mock_poll):
        """get_dkb_redeem_token() opens the DKB login URL"""
        mock_poll.return_value = "token"
        mock_sb_instance = MagicMock()
        mock_sb.return_value.__enter__.return_value = mock_sb_instance

        get_dkb_redeem_token()
        mock_sb_instance.open.assert_called_once_with("https://banking.dkb.de/login")


if __name__ == "__main__":
    unittest.main()
