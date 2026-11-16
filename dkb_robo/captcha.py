# pylint: disable=broad-except
"""Module to solve DKB Friendly Captcha via SeleniumBase + undetected-chromedriver"""

import logging
import time
from seleniumbase import SB
import requests

logger = logging.getLogger(__name__)

FRC_INPUT_SELECTOR = 'input[name="frc-captcha-response"]'
DKB_LOGIN_URL = "https://banking.dkb.de/login"


class _UcDebugPortGuard:
    """Make SeleniumBase pick a free debug port instead of 9222.

    UC mode probes http://127.0.0.1:9222 and treats any non-200 response as
    "port free". A running Chrome instance is already listening on 9222 and answers 404, so the new
    browser is launched on that taken port and the WebDriver handshake hangs
    on a blank window.
    """

    def __enter__(self):
        self._original_get = requests.Session.get

        def _get(session, url, *args, **kwargs):
            if isinstance(url, str) and url.startswith("http://127.0.0.1:9222"):
                return type("_Probe", (), {"status_code": 200})()
            return self._original_get(session, url, *args, **kwargs)

        requests.Session.get = _get
        return self

    def __exit__(self, exc_type, exc, tb):
        requests.Session.get = self._original_get
        return False


def _apply_browser_headers(sb, headers=None):
    """Apply selected request headers to Chromium via CDP before navigation."""
    if not headers:
        return

    try:
        normalized = {
            str(key): str(value) for key, value in headers.items() if value is not None
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
        logger.debug(
            "captcha._apply_browser_headers(): unable to apply headers: %s", err
        )


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

    with _UcDebugPortGuard(), SB(
        uc=True, locale="de", headless=headless, xvfb=xvfb
    ) as sb:
        _apply_browser_headers(sb, headers=headers)
        sb.open(DKB_LOGIN_URL)

        _dismiss_cookie_banner(sb)
        _click_frc_checkbox(sb, attempts=30)

        token = _poll_frc_token(sb, timeout)
        _transfer_browser_state_to_client(sb, client)

    logger.debug("captcha.get_dkb_redeem_token() ended")
    return token


def _deny_cookie_banner(sb, timeout):
    """Wait for the cookie banner and click deny."""
    for _ in range(timeout):
        try:
            logger.debug("login_via_browser: Checking for cookie banner")
            banner_present = sb.cdp.evaluate(
                "document.querySelector('#usercentrics-cmp-ui') !== null"
            )
            if not banner_present:
                time.sleep(1)
                continue
            sb.cdp.evaluate(
                "document.querySelector('#usercentrics-cmp-ui')"
                ".shadowRoot.querySelector('button.uc-deny-button').click()"
            )
            logger.debug("login_via_browser: Cookie deny button clicked")
            return
        except Exception:
            time.sleep(1)


def _click_login_captcha(sb, timeout):
    """Click the Friendly Captcha widget once it is present."""
    for _ in range(timeout):
        print("looping to find captcha checkbox")
        try:
            elem = sb.cdp.find_element("iframe.frc-i-widget")
            elem.scroll_into_view()
            time.sleep(0.5)
            elem.mouse_click()
            logger.debug("captcha: FRC checkbox mouse-clicked")
            return
        except Exception:
            time.sleep(1)


def _click_optional(sb, selector, found_message, missing_message):
    """Click a selector and log when it is missing."""
    try:
        sb.click(selector)
        logger.debug(found_message)
    except Exception:
        logger.debug(missing_message)


def _read_xsrf_token(sb):
    """Return the page XSRF token when the field is present."""
    try:
        return sb.cdp.evaluate(
            "document.querySelector('input[name=xsrf-token]')"
            " ? document.querySelector('input[name=xsrf-token]').value : null"
        )
    except Exception:
        return None


def _apply_session_headers(session, headers):
    """Copy present header values onto the API session."""
    for key, value in headers.items():
        if key and value is not None:
            session.headers[str(key)] = str(value)


def _sync_xsrf_header(session, headers, cookie_dict):
    """Keep the canonical x-xsrf-token header in sync for API calls."""
    xsrf_token = (
        headers.get("X-XSRF-TOKEN")
        or headers.get("x-xsrf-token")
        or cookie_dict.get("__Host-xsrf")
        or cookie_dict.get("XSRF-TOKEN")
    )
    if not xsrf_token:
        return
    session.headers["x-xsrf-token"] = str(xsrf_token)
    headers["x-xsrf-token"] = str(xsrf_token)


def _session_from_browser(sb, client):
    """Copy cookies and request headers from the browser into a session."""
    session = client or requests.session()
    if getattr(session, "headers", None) is None:
        session.headers = {}

    cookie_dict = {cookie["name"]: cookie["value"] for cookie in sb.get_cookies()}
    for name, value in cookie_dict.items():
        session.cookies.set(name, value)

    headers = {"User-Agent": sb.cdp.evaluate("navigator.userAgent")}
    xsrf_token = _read_xsrf_token(sb)
    if xsrf_token:
        headers["X-XSRF-TOKEN"] = xsrf_token

    _apply_session_headers(session, headers)
    _sync_xsrf_header(session, headers, cookie_dict)

    session_info = {"cookies": cookie_dict, "headers": headers}
    logger.debug("Session info: %s", session_info)
    return session, session_info


# not used yet, but might be useful in the future
def login_via_browser(
    dkb_user, dkb_password, timeout=30, headless=False, xvfb=False, client=None
):
    """Open DKB login page, solve Friendly Captcha, perform login via browser."""
    logger.debug("login_via_browser: Starting login flow via browser")

    print("login_via_browser: Starting login flow via browser")
    with _UcDebugPortGuard(), SB(
        uc=True, locale="de", headless=headless, xvfb=xvfb
    ) as sb:
        sb.open(DKB_LOGIN_URL)
        _deny_cookie_banner(sb, timeout)

        sb.type('input[name="username"]', dkb_user)
        sb.type('input[name="password"]', dkb_password)
        print("login_via_browser: Username and password entered")

        time.sleep(2)
        _click_login_captcha(sb, timeout)
        time.sleep(2)

        sb.click('[data-t-id="login"]')
        _click_optional(
            sb,
            'input[id="seal_one"]',
            "login_via_browser: DKB-App radio button clicked",
            "login_via_browser: DKB-App radio button not found",
        )
        _click_optional(
            sb,
            'button[type="submit"] span._sui-button__inner__text_4101u_278',
            "login_via_browser: 'Weiter' button clicked",
            "login_via_browser: 'Weiter' button not found",
        )
        return _session_from_browser(sb, client)
