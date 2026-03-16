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


def get_dkb_redeem_token(timeout=120, headless=False, xvfb=False):
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
                logger.debug("captcha: cookie banner dismissed (deny)")
            except Exception:
                try:
                    sb.cdp.evaluate(
                        "document.querySelector('#usercentrics-cmp-ui')"
                        ".shadowRoot.querySelector('button.uc-accept-button').click()"
                    )
                    logger.debug("captcha: cookie banner dismissed (accept)")
                except Exception:
                    pass
            # Click the FRC captcha checkbox via real mouse click on iframe.
            # A JS .click() on the iframe element does not propagate into the
            # cross-origin iframe; mouse_click() dispatches a real mouse event
            # that reaches the checkbox button inside the iframe.
            try:
                elem = sb.cdp.find_element("iframe.frc-i-widget")
                elem.scroll_into_view()
                time.sleep(0.5)
                elem.mouse_click()
                logger.debug("captcha: FRC checkbox mouse-clicked")
                break
            except Exception:
                time.sleep(1)

        token = _poll_frc_token(sb, timeout)

    logger.debug("captcha.get_dkb_redeem_token() ended")
    return token
