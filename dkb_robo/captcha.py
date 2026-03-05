# pylint: disable=broad-except
"""Module to solve DKB Friendly Captcha via SeleniumBase + undetected-chromedriver"""
import logging
import time
from seleniumbase import SB

logger = logging.getLogger(__name__)

FRC_INPUT_SELECTOR = 'input[name="frc-captcha-response"]'
DKB_LOGIN_URL = "https://banking.dkb.de/login"


def _poll_frc_token(sb, timeout=30):
    """Poll the frc-captcha-response hidden input until a real token (>400 chars) appears."""
    logger.debug("captcha._poll_frc_token(): waiting for token")
    for _ in range(timeout):
        try:
            val = sb.cdp.evaluate(
                f"document.querySelector('{FRC_INPUT_SELECTOR}').value"
            )
            if val and len(val) > 400:
                logger.debug("captcha._poll_frc_token(): got token")
                return val
        except Exception:
            pass
        time.sleep(1)
    logger.error("captcha._poll_frc_token(): timeout")
    return False


def get_dkb_redeem_token(timeout=30, headless=False, xvfb=False):
    """Open DKB login page, solve Friendly Captcha, return the redeem_token."""
    logger.debug("captcha.get_dkb_redeem_token()")

    with SB(uc=True, locale="de", headless=headless, xvfb=xvfb) as sb:
        sb.open(DKB_LOGIN_URL)

        for _ in range(30):
            # Dismiss cookie banner via CDP evaluate (works in UC/CDP mode)
            try:
                sb.cdp.evaluate(
                    "document.querySelector('#usercentrics-cmp-ui')"
                    ".shadowRoot.querySelector('button.uc-deny-button').click()"
                )
            except Exception:
                pass
            # Click the FRC iframe element via CDP (avoids cross-origin switch_to_frame)
            try:
                sb.cdp.find_element("iframe.frc-i-widget").click()
                logger.debug("captcha: FRC checkbox clicked")
                break
            except Exception:
                time.sleep(1)

        token = _poll_frc_token(sb, timeout)

    logger.debug("captcha.get_dkb_redeem_token() ended")
    return token
