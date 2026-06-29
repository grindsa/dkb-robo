# pylint: disable=broad-except
"""Module to solve DKB Friendly Captcha via SeleniumBase + undetected-chromedriver"""
import logging
import time
from seleniumbase import SB
import requests

logger = logging.getLogger(__name__)

FRC_INPUT_SELECTOR = 'input[name="frc-captcha-response"]'
DKB_LOGIN_URL = "https://banking.dkb.de/login"


def _apply_browser_headers(sb, headers=None):
    """Apply selected request headers to Chromium via CDP before navigation."""
    if not headers:
        return

    try:
        normalized = {
            str(key): str(value)
            for key, value in headers.items()
            if value is not None
        }
    except Exception:
        logger.debug("captcha._apply_browser_headers(): invalid headers payload")
        return

    ua_key = next(
        (key for key in normalized if key.lower() == "user-agent"),
        None,
    )
    user_agent = normalized.pop(ua_key, None) if ua_key else None

    # These are managed by the browser/network stack and should not be forced.
    blocked = {
        "host",
        "content-length",
        "cookie",
        "connection",
        "sec-fetch-dest",
        "sec-fetch-mode",
        "sec-fetch-site",
    }
    extra_headers = {
        key: value for key, value in normalized.items() if key.lower() not in blocked
    }

    try:
        sb.driver.execute_cdp_cmd("Network.enable", {})

        if user_agent:
            sb.driver.execute_cdp_cmd(
                "Network.setUserAgentOverride", {"userAgent": user_agent}
            )

        if extra_headers:
            sb.driver.execute_cdp_cmd(
                "Network.setExtraHTTPHeaders", {"headers": extra_headers}
            )
    except Exception as err:
        logger.debug("captcha._apply_browser_headers(): unable to apply headers: %s", err)


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


def _dismiss_cookie_banner(sb):
    """Best-effort dismiss of the cookie banner."""
    try:
        sb.cdp.evaluate(
            "document.querySelector('#usercentrics-cmp-ui')"
            ".shadowRoot.querySelector('button.uc-deny-button').click()"
        )
        logger.debug("captcha: cookie banner dismissed (deny)")
        return
    except Exception:
        pass

    try:
        sb.cdp.evaluate(
            "document.querySelector('#usercentrics-cmp-ui')"
            ".shadowRoot.querySelector('button.uc-accept-button').click()"
        )
        logger.debug("captcha: cookie banner dismissed (accept)")
    except Exception:
        pass


def _click_frc_checkbox(sb, attempts=30):
    """Try to click the Friendly Captcha iframe widget."""
    for _ in range(attempts):
        try:
            elem = sb.cdp.find_element("iframe.frc-i-widget")
            elem.scroll_into_view()
            time.sleep(0.5)
            elem.mouse_click()
            logger.debug("captcha: FRC checkbox mouse-clicked")
            return True
        except Exception:
            time.sleep(1)
    return False


def _transfer_browser_state_to_client(sb, client):
    """Copy browser anti-bot state to the API client."""
    if client is None:
        return

    try:
        for cookie in sb.get_cookies():
            name = cookie.get("name")
            value = cookie.get("value")
            if name and value is not None:
                client.cookies.set(name, value)
    except Exception as err:
        logger.debug("captcha: unable to transfer cookies to client: %s", err)

    try:
        browser_ua = sb.cdp.evaluate("navigator.userAgent")
        if browser_ua:
            client.headers["User-Agent"] = browser_ua
    except Exception as err:
        logger.debug("captcha: unable to transfer user-agent to client: %s", err)


def get_dkb_redeem_token(
    timeout=120,
    headless=False,
    xvfb=False,
    headers=None,
    client=None,
):
    """Open DKB login page, solve Friendly Captcha, return the redeem_token."""
    logger.debug("captcha.get_dkb_redeem_token()")

    with SB(uc=True, locale="de", headless=headless, xvfb=xvfb) as sb:
        _apply_browser_headers(sb, headers=headers)
        sb.open(DKB_LOGIN_URL)

        _dismiss_cookie_banner(sb)
        _click_frc_checkbox(sb, attempts=30)

        token = _poll_frc_token(sb, timeout)
        _transfer_browser_state_to_client(sb, client)

    logger.debug("captcha.get_dkb_redeem_token() ended")
    return token


def login_via_browser(logger, dkb_user, dkb_password, timeout=30, headless=False, xvfb=False, client=None):
    """Open DKB login page, solve Friendly Captcha, perform login via browser."""


    print('login_via_browser: Starting login flow via browser')
    with SB(uc=True, locale="de", headless=headless, xvfb=xvfb) as sb:
        sb.open(DKB_LOGIN_URL)

        # Wait for cookie message to appear and click deny
        for _ in range(timeout):
            try:
                logger.debug("login_via_browser: Checking for cookie banner")
                if sb.cdp.evaluate("document.querySelector('#usercentrics-cmp-ui') !== null"):
                    sb.cdp.evaluate(
                        "document.querySelector('#usercentrics-cmp-ui')"
                        ".shadowRoot.querySelector('button.uc-deny-button').click()"
                    )
                    logger.debug("login_via_browser: Cookie deny button clicked")
                    break
            except Exception:
                pass
            time.sleep(1)

        # Fill username and password fields
        sb.type('input[name="username"]', dkb_user)
        sb.type('input[name="password"]', dkb_password)
        print("login_via_browser: Username and password entered")

        time.sleep(2)  # Brief pause before clicking captcha
        for _ in range(timeout):
            print('looping to find captcha checkbox')
            try:
                elem = sb.cdp.find_element("iframe.frc-i-widget")
                elem.scroll_into_view()
                time.sleep(0.5)
                elem.mouse_click()
                logger.debug("captcha: FRC checkbox mouse-clicked")
                break
            except Exception:
                time.sleep(1)

        time.sleep(2)  # Brief pause before clicking login button

        # Click the login button using data-t-id property
        sb.click('[data-t-id="login"]')

        # After login, select DKB-App radio button and click 'Weiter'
        try:
            # Click the DKB-App radio button
            sb.click('input[id="seal_one"]')
            logger.debug("login_via_browser: DKB-App radio button clicked")
        except Exception:
            logger.debug("login_via_browser: DKB-App radio button not found")

        try:
            # Click the 'Weiter' button
            sb.click('button[type="submit"] span._sui-button__inner__text_4101u_278')
            logger.debug("login_via_browser: 'Weiter' button clicked")
        except Exception:
            logger.debug("login_via_browser: 'Weiter' button not found")

        # After successful login, extract session headers and cookies

        session = client
        # Get cookies from SeleniumBase browser
        cookies = sb.get_cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}

        print("Cookies extracted from browser:")
        print(cookie_dict)

        for name, value in cookie_dict.items():
            session.cookies.set(name, value)

        # Extract headers (User-Agent, XSRF tokens, etc.)
        headers = {}
        # User-Agent
        headers['User-Agent'] = sb.cdp.evaluate('navigator.userAgent')
        # XSRF token (if present)
        try:
            xsrf_token = sb.cdp.evaluate('document.querySelector("input[name=xsrf-token]") ? document.querySelector("input[name=xsrf-token]").value : null')
            if xsrf_token:
                headers['X-XSRF-TOKEN'] = xsrf_token
        except Exception:
            pass

        # Dump all session info into a dictionary
        session_info = {
            'cookies': cookie_dict,
            'headers': headers
        }

        time.sleep(20)
        # logger.info(f"Session info: {session_info}")

        # session object is ready for use
        return session, session_info