# pylint: disable=broad-except
"""Module to solve DKB Friendly Captcha via SeleniumBase + undetected-chromedriver"""

import logging
import time
from seleniumbase import SB
import requests

logger = logging.getLogger(__name__)

FRC_INPUT_SELECTOR = 'input[name="frc-captcha-response"]'
FRC_WIDGET_SELECTOR = "iframe.frc-i-widget, iframe[data--frc-frame-id]"
FRC_FRAME_SELECTOR = "iframe[data--frc-frame-id]"
# Checkbox is near the top-left of the Friendly Captcha iframe.
FRC_CHECKBOX_OFFSET = (27, 34)
DKB_LOGIN_URL = "https://banking.dkb.de/login"
MIN_FRC_TOKEN_LENGTH = 400


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


def _is_active_frc_token(value):
    """Return True when the Friendly Captcha response looks solved."""
    if not value or not isinstance(value, str):
        return False
    # Placeholders before solving start with '.' (e.g. .UNACTIVATED).
    if value.startswith("."):
        return False
    return len(value) > MIN_FRC_TOKEN_LENGTH


def _poll_frc_token(sb, timeout=30, reclick_every=5):
    """Poll the frc-captcha-response hidden input until a real token appears."""
    logger.debug("captcha._poll_frc_token(): waiting for token")
    for second in range(max(timeout, 0)):
        try:
            val = sb.cdp.evaluate(
                f"document.querySelector('{FRC_INPUT_SELECTOR}')"
                f" ? document.querySelector('{FRC_INPUT_SELECTOR}').value : null"
            )
            if _is_active_frc_token(val):
                logger.debug("captcha._poll_frc_token(): got token")
                return val
        except Exception:
            pass
        if reclick_every and second > 0 and second % reclick_every == 0:
            _dismiss_cookie_banner(sb, timeout=1)
            _click_frc_checkbox(sb, attempts=1)
        time.sleep(1)
    logger.error("captcha._poll_frc_token(): timeout")
    return False


def _cookie_banner_button_rects(sb):
    """Return visible Usercentrics button rects from the CMP shadow root."""
    try:
        result = sb.cdp.evaluate("""(() => {
                const host = document.querySelector('#usercentrics-cmp-ui');
                if (!(host && host.shadowRoot)) {
                    return [];
                }
                return [...host.shadowRoot.querySelectorAll('button')]
                    .map((button) => {
                        const rect = button.getBoundingClientRect();
                        return {
                            text: (button.innerText || '').trim(),
                            className: button.className || '',
                            x: rect.x,
                            y: rect.y,
                            w: rect.width,
                            h: rect.height,
                        };
                    })
                    .filter((button) => button.w > 0 && button.h > 0);
            })()""")
        if not isinstance(result, list):
            return []
        return [button for button in result if isinstance(button, dict)]
    except Exception:
        return []


def _cookie_banner_visible(sb):
    """Return True when the Usercentrics banner still shows action buttons."""
    return bool(_cookie_banner_button_rects(sb))


def _remove_cookie_banner_host(sb):
    """Remove the CMP host node so it cannot intercept clicks."""
    try:
        sb.cdp.evaluate("""(() => {
                const host = document.querySelector('#usercentrics-cmp-ui');
                if (host) {
                    host.remove();
                    return true;
                }
                return false;
            })()""")
        return True
    except Exception:
        return False


def _uc_ui_dismiss_cookies(sb):
    """Deny/accept consents and close the CMP UI via UC_UI."""
    try:
        result = sb.cdp.evaluate("""(() => {
                try {
                    if (!(window.UC_UI && window.UC_UI.isInitialized
                          && window.UC_UI.isInitialized())) {
                        return false;
                    }
                    if (typeof window.UC_UI.denyAllConsents === 'function') {
                        window.UC_UI.denyAllConsents();
                    } else if (typeof window.UC_UI.acceptAllConsents === 'function') {
                        window.UC_UI.acceptAllConsents();
                    } else {
                        return false;
                    }
                    // denyAllConsents alone leaves the overlay up on current DKB.
                    if (typeof window.UC_UI.closeCMP === 'function') {
                        window.UC_UI.closeCMP();
                    }
                    return true;
                } catch (err) {
                    return false;
                }
            })()""")
        return bool(result)
    except Exception:
        return False


def _gui_click_cookie_button(sb):
    """OS-level click on Ablehnen / Alles akzeptieren when JS dismiss fails."""
    buttons = _cookie_banner_button_rects(sb)
    if not buttons:
        return False

    preferred = None
    for button in buttons:
        class_name = (button.get("className") or "").lower()
        text = (button.get("text") or "").lower()
        if "deny" in class_name or "ablehnen" in text:
            preferred = button
            break
    if preferred is None:
        preferred = buttons[0]

    x = preferred["x"] + preferred["w"] / 2
    y = preferred["y"] + preferred["h"] / 2
    try:
        if hasattr(sb, "bring_active_window_to_front"):
            sb.bring_active_window_to_front()
    except Exception:
        pass

    try:
        sb.cdp.gui_click_x_y(x, y)
        logger.debug("captcha: cookie banner clicked via gui_click_x_y")
        return True
    except Exception as err:
        logger.debug("captcha: gui cookie click failed: %s", err)
        return False


def _shadow_dom_dismiss_cookies(sb):
    """Fallback: JS click deny/accept buttons inside the Usercentrics shadow root."""
    try:
        sb.cdp.evaluate(
            "document.querySelector('#usercentrics-cmp-ui')"
            ".shadowRoot.querySelector('button.uc-deny-button').click()"
        )
        logger.debug("captcha: cookie banner dismissed (deny button)")
        return True
    except Exception:
        pass

    try:
        sb.cdp.evaluate(
            "document.querySelector('#usercentrics-cmp-ui')"
            ".shadowRoot.querySelector('button.uc-accept-button').click()"
        )
        logger.debug("captcha: cookie banner dismissed (accept button)")
        return True
    except Exception:
        return False


def _dismiss_cookie_banner(sb, timeout=30):
    """Wait for and dismiss the cookie banner (Usercentrics CMP)."""
    logger.debug("captcha._dismiss_cookie_banner()")
    for _ in range(max(timeout, 1)):
        if not _cookie_banner_visible(sb):
            # No visible buttons — still drop an empty host if present.
            _remove_cookie_banner_host(sb)
            logger.debug("captcha: cookie banner not visible")
            return True

        if _uc_ui_dismiss_cookies(sb):
            time.sleep(0.5)
            if not _cookie_banner_visible(sb):
                _remove_cookie_banner_host(sb)
                logger.debug("captcha: cookie banner dismissed via UC_UI+closeCMP")
                return True

        if _gui_click_cookie_button(sb):
            time.sleep(0.5)
            if not _cookie_banner_visible(sb):
                _remove_cookie_banner_host(sb)
                logger.debug("captcha: cookie banner dismissed via GUI click")
                return True

        if _shadow_dom_dismiss_cookies(sb):
            time.sleep(0.5)
            if not _cookie_banner_visible(sb):
                _remove_cookie_banner_host(sb)
                logger.debug("captcha: cookie banner dismissed via shadow DOM click")
                return True

        # Last resort for this attempt: remove the overlay so captcha is clickable.
        if _remove_cookie_banner_host(sb):
            logger.debug("captcha: cookie banner host removed")
            return True
        time.sleep(1)

    logger.debug("captcha: cookie banner still present after timeout")
    return False


def _frc_iframe_rect(sb):
    """Return the Friendly Captcha iframe bounding box, if present."""
    try:
        return sb.cdp.evaluate("""(() => {
                const iframe = document.querySelector('iframe.frc-i-widget')
                    || document.querySelector('iframe[data--frc-frame-id]');
                if (!iframe) {
                    return null;
                }
                const rect = iframe.getBoundingClientRect();
                if (!(rect.width && rect.height)) {
                    return null;
                }
                return {x: rect.x, y: rect.y, w: rect.width, h: rect.height};
            })()""")
    except Exception:
        return None


def _frc_token_value(sb):
    """Return the current Friendly Captcha response value, if any."""
    try:
        return sb.cdp.evaluate(
            f"document.querySelector('{FRC_INPUT_SELECTOR}')"
            f" ? document.querySelector('{FRC_INPUT_SELECTOR}').value : null"
        )
    except Exception:
        return None


def _frc_click_started(token):
    """Return True when a click has moved the widget out of .UNACTIVATED."""
    if not token or not isinstance(token, str):
        return False
    if token == ".UNACTIVATED":
        return False
    return True


def _click_frc_with_screen_coords(sb):
    """Click the FRC checkbox using screen coordinates (PyAutoGUI)."""
    # Prefer SeleniumBase's calibrated Friendly Captcha helper.
    if hasattr(sb.cdp, "gui_click_captcha"):
        sb.cdp.gui_click_captcha()
        return "gui_click_captcha"
    if hasattr(sb, "uc_gui_click_captcha"):
        sb.uc_gui_click_captcha()
        return "uc_gui_click_captcha"

    selector = FRC_FRAME_SELECTOR
    if hasattr(sb.cdp, "gui_click_with_offset"):
        sb.cdp.gui_click_with_offset(
            selector,
            FRC_CHECKBOX_OFFSET[0],
            FRC_CHECKBOX_OFFSET[1],
        )
        return "gui_click_with_offset"

    # Manual conversion: viewport box -> screen box via get_gui_element_rect.
    gui_rect = sb.cdp.get_gui_element_rect(selector, timeout=1)
    x = gui_rect["x"] + FRC_CHECKBOX_OFFSET[0]
    y = gui_rect["y"] + FRC_CHECKBOX_OFFSET[1]
    sb.cdp.gui_click_x_y(x, y)
    return "gui_click_x_y"


def _click_frc_checkbox(sb, attempts=30):
    """Activate the Friendly Captcha 'Ich bin ein Mensch' checkbox."""
    logger.debug("captcha._click_frc_checkbox()")
    for _ in range(max(attempts, 1)):
        # Overlay can swallow clicks even after consent is stored.
        if _cookie_banner_visible(sb):
            _dismiss_cookie_banner(sb, timeout=1)

        if not _frc_iframe_rect(sb):
            time.sleep(1)
            continue

        try:
            if hasattr(sb, "bring_active_window_to_front"):
                sb.bring_active_window_to_front()
        except Exception:
            pass

        # FRC ignores synthetic CDP clicks. Use OS-level clicks with screen
        # coordinates (getBoundingClientRect alone is NOT screen-relative).
        click_methods = [
            ("screen", _click_frc_with_screen_coords),
        ]

        def _cdp_offset(_sb):
            _sb.cdp.click_with_offset(
                FRC_WIDGET_SELECTOR,
                FRC_CHECKBOX_OFFSET[0],
                FRC_CHECKBOX_OFFSET[1],
            )
            return "click_with_offset"

        def _mouse_click(_sb):
            elem = _sb.cdp.find_element(FRC_WIDGET_SELECTOR)
            elem.scroll_into_view()
            time.sleep(0.3)
            elem.mouse_click()
            return "mouse_click"

        click_methods.append(("cdp_offset", _cdp_offset))
        click_methods.append(("mouse", _mouse_click))

        for name, method in click_methods:
            try:
                detail = method(sb)
                logger.debug("captcha: FRC click attempted via %s (%s)", name, detail)
            except Exception as err:
                logger.debug("captcha: FRC click via %s failed: %s", name, err)
                continue

            # Give the widget a moment to leave .UNACTIVATED before trying
            # the next strategy.
            time.sleep(1.5)
            token = _frc_token_value(sb)
            if _frc_click_started(token):
                logger.debug(
                    "captcha: FRC click accepted (token prefix=%s)",
                    (token or "")[:20],
                )
                return True

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

        # CMP loads asynchronously and can block the captcha checkbox.
        _dismiss_cookie_banner(sb, timeout=min(timeout, 30))
        _click_frc_checkbox(sb, attempts=min(timeout, 30))

        token = _poll_frc_token(sb, timeout=timeout, reclick_every=5)
        _transfer_browser_state_to_client(sb, client)

    logger.debug("captcha.get_dkb_redeem_token() ended")
    return token


def _deny_cookie_banner(sb, timeout):
    """Wait for the cookie banner and dismiss it (used by login_via_browser)."""
    _dismiss_cookie_banner(sb, timeout=timeout)


def _click_login_captcha(sb, timeout):
    """Click the Friendly Captcha widget once it is present."""
    _click_frc_checkbox(sb, attempts=timeout)


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
