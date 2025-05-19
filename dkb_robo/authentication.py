# pylint: disable=r0913
""" Module for handling dkb standing orders """
from typing import Dict, List, Tuple
import time
import json
import base64
import io
import threading
import logging
import requests
from dkb_robo.legacy import Wrapper as Legacywrapper
from dkb_robo.portfolio import Overview
from dkb_robo.utilities import DKBRoboError, JSON_CONTENT_TYPE


BASE_URL = "https://banking.dkb.de/api"
logger = logging.getLogger(__name__)


class Authentication:
    """Authentication class"""

    account_dic = {}
    base_url = BASE_URL
    chip_tan = False
    client = None
    dkb_user = None
    dkb_password = None
    dkb_br = None
    logger = None
    mfa_method = "seal_one"
    mfa_device = 0
    proxies = {}
    token_dic = None
    unfiltered = False

    def __init__(
        self,
        dkb_user: str = None,
        dkb_password: str = None,
        chip_tan: bool = False,
        proxies: Dict[str, str] = None,
        mfa_device: int = None,
        unfiltered: bool = False,
    ):
        """Constructor"""
        self.chip_tan = chip_tan
        self.dkb_user = dkb_user
        self.dkb_password = dkb_password
        self.proxies = proxies
        self.unfiltered = unfiltered
        if chip_tan:
            logger.info("Using to chip_tan to login")
            if chip_tan in ("qr", "chip_tan_qr"):
                self.mfa_method = "chip_tan_qr"
            else:
                self.mfa_method = "chip_tan_manual"
        try:
            self.mfa_device = int(mfa_device)
        except (ValueError, TypeError):
            self.mfa_device = 0

    def _mfa_challenge(
        self, mfa_dic: Dict[str, str], device_num: int = 0
    ) -> Tuple[str, str]:
        """get challenge dict with information on the 2nd factor"""
        logger.debug(
            "Authentication._mfa_challenge(): login with device_num: %s\n", device_num
        )

        device_name = None
        challenge_dic = {}
        if "data" in mfa_dic and "id" in mfa_dic["data"][device_num]:
            try:
                device_name = mfa_dic["data"][device_num]["attributes"]["deviceName"]
                logger.debug(
                    "api.Wrapper._mfa_challenge(): devicename: %s\n", device_name
                )
            except Exception as _err:
                logger.error(
                    "unable to get mfa-deviceName for device_num: %s", device_num
                )
                device_name = None

            # additional headers needed as this call requires it
            self.client.headers["Content-Type"] = JSON_CONTENT_TYPE
            self.client.headers["Accept"] = "application/vnd.api+json"

            # we are expecting the first method from mfa_dic to be used
            data_dic = {
                "data": {
                    "type": "mfa-challenge",
                    "attributes": {
                        "mfaId": self.token_dic["mfa_id"],
                        "methodId": mfa_dic["data"][device_num]["id"],
                        "methodType": self.mfa_method,
                    },
                }
            }
            response = self.client.post(
                self.base_url + "/mfa/mfa/challenges", data=json.dumps(data_dic)
            )

            # process response
            # challenge_id = self._process_challenge_response(response)
            if response.status_code in (200, 201):
                challenge_dic = response.json()
            else:
                raise DKBRoboError(
                    f"Login failed: post request to get the mfa challenges failed. RC: {response.status_code}"
                )

            # we rmove the headers we added earlier
            self.client.headers.pop("Content-Type")
            self.client.headers.pop("Accept")
        else:
            logger.error("mfa dictionary has an unexpected data structure")

        logger.debug("Authentication._mfa_challenge() ended\n")
        return challenge_dic, device_name

    def _mfa_challenge_id(self, challenge_dic: Dict[str, str]) -> str:
        """get challenge dict with information on the 2nd factor"""
        logger.debug("api.Wrapper._mfa_challenge_id()\n")
        challenge_id = None

        if (
            "data" in challenge_dic
            and "id" in challenge_dic["data"]
            and "type" in challenge_dic["data"]
        ):
            if challenge_dic["data"]["type"] == "mfa-challenge":
                challenge_id = challenge_dic["data"]["id"]
            else:
                raise DKBRoboError(
                    f"Login failed:: wrong challenge type: {challenge_dic}"
                )

        else:
            raise DKBRoboError(
                f"Login failed: challenge response format is other than expected: {challenge_dic}"
            )

        logger.debug("api.Wrapper._mfa_challenge_id() ended with: %s\n", challenge_id)
        return challenge_id

    def _mfa_finalize(self, challenge_dic: Dict[str, str], devicename: str) -> bool:
        """wait for confirmation for the 2nd factor"""
        logger.debug("Authentication._mfa_finalize()\n")

        challenge_id = self._mfa_challenge_id(challenge_dic)

        if self.mfa_method == "seal_one":
            mfa_auth = APPAuthentication(client=self.client, base_url=self.base_url)
        elif self.mfa_method in ("chip_tan_manual", "chip_tan_qr"):
            mfa_auth = TANAuthentication(
                client=self.client, base_url=self.base_url, mfa_method=self.mfa_method
            )
        else:
            raise DKBRoboError(f"Login failed: unknown mfa method: {self.mfa_method}")

        mfa_completed = False
        if mfa_auth:
            mfa_completed = mfa_auth.finalize(challenge_id, challenge_dic, devicename)

        logger.debug("Authentication._mfa_finalize() ended with %s\n", mfa_completed)
        return mfa_completed

    def _mfa_get(self) -> Dict[str, str]:
        """get mfa methods"""
        logger.debug("Authentication._mfa_get()\n")
        mfa_dic = {}

        # check for access_token and get mfa_methods
        if "access_token" in self.token_dic and "mfa_id" in self.token_dic:
            response = self.client.get(
                self.base_url
                + f"/mfa/mfa/{self.token_dic['mfa_id']}/methods?filter%5BmethodType%5D={self.mfa_method}"
            )
            if response.status_code == 200:
                mfa_dic = response.json()
            else:
                raise DKBRoboError(
                    f"Login failed: getting mfa_methods failed. RC: {response.status_code}"
                )
        else:
            raise DKBRoboError("Login failed: no 1fa access token.")

        logger.debug("Authentication._mfa_get() ended\n")
        return mfa_dic

    def _mfa_process(
        self,
        device_num: int,
        device_list: List[int],
        _tmp_device_num: str,
        deviceselection_completed: bool,
    ) -> Tuple[int, bool]:
        logger.debug("Authentication._mfa_process(%s)", _tmp_device_num)
        try:
            # we are referring to an index in a list thus we need to lower the user input by 1
            if int(_tmp_device_num) - 1 in device_list:
                deviceselection_completed = True
                device_num = int(_tmp_device_num) - 1
            else:
                print("\nWrong input!")
        except Exception:
            print("\nInvalid input!")

        logger.debug("Authentication._mfa_process()\n ended")
        return device_num, deviceselection_completed

    def _mfa_select(self, mfa_dic: Dict[str, str]) -> int:
        """pick mfa_device from dictionary"""
        logger.debug("Authentication._mfa_select()")
        device_num = 0

        # adjust self.mfa_device if the user input is too high
        if "data" in mfa_dic and len(mfa_dic["data"]) < self.mfa_device:
            logger.warning("User submitted mfa_device number is invalid. Ingoring...")
            self.mfa_device = 0

        if self.mfa_device > 0:
            # we need to lower by one as we refer to an index in a list
            logger.debug(
                "api.Wrapper._mfa_select(): using user submitted mfa_device number: %s",
                self.mfa_device,
            )
            device_num = self.mfa_device - 1

        elif "data" in mfa_dic and len(mfa_dic["data"]) > 1:
            device_list = []
            deviceselection_completed = False
            while not deviceselection_completed:
                print("\nPick an authentication device from the below list:")
                # we have multiple devices to select
                for idx, device_dic in enumerate(mfa_dic["data"]):
                    device_list.append(idx)
                    if (
                        "attributes" in device_dic
                        and "deviceName" in device_dic["attributes"]
                    ):
                        # we should start counting with 1 for the user
                        print(f"[{idx + 1}] - {device_dic['attributes']['deviceName']}")
                _tmp_device_num = input(":")

                device_num, deviceselection_completed = self._mfa_process(
                    device_num, device_list, _tmp_device_num, deviceselection_completed
                )

        logger.debug("Authentication._mfa_select() ended with: %s", device_num)
        return device_num

    def _mfa_sort(self, mfa_dic):
        """sort mfa methods"""
        logger.debug("Authentication._mfa_sort()")

        mfa_list = mfa_dic["data"]
        if self.mfa_method == "seal_one":
            mfa_list.sort(
                key=lambda x: (
                    -x["attributes"]["preferredDevice"],
                    x["attributes"]["enrolledAt"],
                )
            )

        logger.debug(
            "Authentication._mfa_sort() ended with: %s elements", len(mfa_list)
        )
        return {"data": mfa_list}

    def _session_new(self):
        """new request session for the api calls"""
        logger.debug("Authentication._session_new()\n")

        headers = {
            "Accept-Language": "en-US,en;q=0.5",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "DNT": "1",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "te": "trailers",
            "priority": "u=0",
            "sec-gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
        }

        client = requests.session()
        client.headers = headers
        if self.proxies:
            client.proxies = self.proxies
            client.verify = False

        # get cookies
        client.get(self.base_url + "/login")

        # add csrf token
        if "__Host-xsrf" in client.cookies:
            headers["x-xsrf-token"] = client.cookies["__Host-xsrf"]
            client.headers = headers

        logger.debug("Authentication._session_new() ended\n")
        return client

    def _sso_redirect(self):
        """redirect to access legacy page"""
        logger.debug("Authentication._sso_redirect()\n")

        data_dic = {"data": {"cookieDomain": ".dkb.de"}}
        self.client.headers["Content-Type"] = "application/json"
        self.client.headers["Sec-Fetch-Dest"] = "empty"
        self.client.headers["Sec-Fetch-Mode"] = "cors"
        self.client.headers["Sec-Fetch-Site"] = "same-origin"

        response = self.client.post(
            self.base_url + "/sso-redirect", data=json.dumps(data_dic)
        )

        if response.status_code != 200 or response.text != "OK":
            logger.error(
                "SSO redirect failed. RC: %s text: %s",
                response.status_code,
                response.text,
            )
        clientcookies = self.client.cookies

        legacywrappper = Legacywrapper()
        # pylint: disable=w0212
        self.dkb_br = legacywrappper._new_instance(clientcookies)
        logger.debug("Authentication._sso_redirect() ended.\n")

    def _token_get(self):
        """get access token"""
        logger.debug("Authentication._token_get()\n")

        # login via API
        data_dic = {
            "grant_type": "banking_user_sca",
            "username": self.dkb_user,
            "password": self.dkb_password,
            "sca_type": "web-login",
        }
        response = self.client.post(self.base_url + "/token", data=data_dic)
        if response.status_code == 200:
            self.token_dic = response.json()
        else:
            raise DKBRoboError(
                f"Login failed: 1st factor authentication failed. RC: {response.status_code}"
            )
        logger.debug("Authentication._token_get() ended\n")

    def _token_update(self):
        """update token information with 2fa iformation"""
        logger.debug("Authentication._token_update()\n")

        data_dic = {
            "grant_type": "banking_user_mfa",
            "mfa_id": self.token_dic["mfa_id"],
            "access_token": self.token_dic["access_token"],
        }
        response = self.client.post(self.base_url + "/token", data=data_dic)
        if response.status_code == 200:
            self.token_dic = response.json()
        else:
            raise DKBRoboError(
                f"Login failed: token update failed. RC: {response.status_code}"
            )

    def login(self) -> Tuple[Dict, None]:
        """login into DKB banking area and perform an sso redirect"""
        logger.debug("Authentication.login()\n")

        mfa_dic = {}

        # create new session
        self.client = self._session_new()

        # get token for 1fa
        self._token_get()

        # get mfa methods
        mfa_dic = self._mfa_get()

        if mfa_dic:
            # sort mfa methods
            mfa_dic = self._mfa_sort(mfa_dic)

        # pick mfa device from list
        device_number = self._mfa_select(mfa_dic)

        # we need a challege-id for polling so lets try to get it
        mfa_challenge_dic = None
        if "mfa_id" in self.token_dic and "data" in mfa_dic:
            mfa_challenge_dic, device_name = self._mfa_challenge(mfa_dic, device_number)
        else:
            raise DKBRoboError("Login failed: no 1fa access token.")

        # lets complete 2fa
        mfa_completed = False
        if mfa_challenge_dic:
            mfa_completed = self._mfa_finalize(mfa_challenge_dic, device_name)
        else:
            raise DKBRoboError("Login failed: No challenge id.")

        # update token dictionary
        if mfa_completed and "access_token" in self.token_dic:
            self._token_update()
        else:
            raise DKBRoboError("Login failed: mfa did not complete")

        if "token_factor_type" not in self.token_dic:
            raise DKBRoboError("Login failed: token_factor_type is missing")

        if (
            "token_factor_type" in self.token_dic
            and self.token_dic["token_factor_type"] != "2fa"
        ):

            raise DKBRoboError(
                "Login failed: 2nd factor authentication did not complete"
            )

        # get account overview
        overview = Overview(client=self.client, unfiltered=self.unfiltered)
        self.account_dic = overview.get()

        # redirect to legacy page
        self._sso_redirect()
        logger.debug("Authentication.login() ended\n")
        return self.account_dic, None

    def logout(self):
        """logout function"""
        logger.debug("Authentication.logout()\n")


class APPAuthentication:
    """APPAuthentication class"""

    def __init__(self, client: requests.Session, base_url: str = BASE_URL):
        self.client = client
        self.base_url = base_url

    def _check(self, polling_dic: Dict[str, str], cnt: 1) -> bool:
        logger.debug("APPAuthentication._check()\n")

        if (
            "data" in polling_dic
            and "attributes" in polling_dic["data"]
            and "verificationStatus" in polling_dic["data"]["attributes"]
        ):

            logger.debug(
                "APPAuthentication._check: cnt %s got %s flag",
                cnt,
                polling_dic["data"]["attributes"]["verificationStatus"],
            )

            mfa_completed = False
            if (polling_dic["data"]["attributes"]["verificationStatus"]) == "processed":
                mfa_completed = True
            elif (
                polling_dic["data"]["attributes"]["verificationStatus"]
            ) == "processing":
                logger.info(
                    "Status: %s. Waiting for confirmation",
                    polling_dic["data"]["attributes"]["verificationStatus"],
                )
            elif (
                polling_dic["data"]["attributes"]["verificationStatus"]
            ) == "canceled":
                raise DKBRoboError("2fa chanceled by user")
            else:
                logger.info(
                    "Unknown processing status: %s",
                    polling_dic["data"]["attributes"]["verificationStatus"],
                )
        else:
            raise DKBRoboError(
                "Login failed: processing status format is other than expected"
            )

        logger.debug("APPAuthentication._check() ended with: %s\n", mfa_completed)
        return mfa_completed

    def _print(self, devicename: str):
        """2fa confirmation message"""
        logger.debug("api.Wrapper._print()\n")
        if devicename:
            print(f'check your banking app on "{devicename}" and confirm login...')
        else:
            print("check your banking app and confirm login...")

    def finalize(
        self, challenge_id: str, _challenge_dic: Dict[str, str], devicename: str
    ) -> bool:
        """wait for confirmation for the 2nd factor"""
        logger.debug("APPAuthentication.finalize()\n")

        self._print(devicename)

        cnt = 0
        mfa_completed = False
        # we give us 50 seconds to press a button on the phone
        while cnt <= 10:
            response = self.client.get(
                self.base_url + f"/mfa/mfa/challenges/{challenge_id}"
            )
            cnt += 1
            if response.status_code == 200:
                polling_dic = response.json()
                if (
                    "data" in polling_dic
                    and "attributes" in polling_dic["data"]
                    and "verificationStatus" in polling_dic["data"]["attributes"]
                ):
                    # check processing status
                    mfa_completed = self._check(polling_dic, cnt)
                    if mfa_completed:
                        break
                else:
                    logger.error("error parsing polling response: %s", polling_dic)
            else:
                logger.error("Polling request failed. RC: %s", response.status_code)
            time.sleep(5)

        logger.debug("APPAuthentication.finalize(): %s\n", mfa_completed)
        return mfa_completed


class TANAuthentication:
    """TANAuthentication class"""

    def __init__(
        self,
        client: requests.Session,
        base_url: str = BASE_URL,
        mfa_method: str = "chip_tan_manual",
    ):
        self.client = client
        self.base_url = base_url
        self.mfa_method = mfa_method

    def _image(self, qr_data: str) -> None:
        """show qr code"""
        logger.debug("TANAuthentication._image()\n")

        # pylint: disable=c0415
        from PIL import Image

        qr_data = qr_data.replace("data:image/png;base64,", "")
        qr_data = qr_data.replace(" ", "+")
        qr_data = base64.b64decode(qr_data)
        data = io.BytesIO()
        data.write(qr_data)
        img = Image.open(data)
        img.show()

        logger.debug("TANAuthentication._image() ended\n")

    def _print(self, challenge_dic: Dict[str, str]) -> str:
        """print instructions for chip tan"""
        logger.debug("TANAuthentication._print()\n")

        if (
            "data" in challenge_dic
            and "attributes" in challenge_dic["data"]
            and "chipTan" in challenge_dic["data"]["attributes"]
            and "qrData" in challenge_dic["data"]["attributes"]["chipTan"]
        ):
            my_thread = threading.Thread(
                target=self._image,
                args=(challenge_dic["data"]["attributes"]["chipTan"]["qrData"],),
            )
            my_thread.daemon = True
            my_thread.start()
            my_thread.join(timeout=0.5)

        tan = None
        if (
            "data" in challenge_dic
            and "attributes" in challenge_dic["data"]
            and "chipTan" in challenge_dic["data"]["attributes"]
        ):
            if "headline" in challenge_dic["data"]["attributes"]["chipTan"]:
                print(f"{challenge_dic['data']['attributes']['chipTan']['headline']}\n")
            if "instructions" in challenge_dic["data"]["attributes"]["chipTan"]:
                for idx, instruction in enumerate(
                    challenge_dic["data"]["attributes"]["chipTan"]["instructions"],
                    start=1,
                ):
                    print(f"{idx}. {instruction}\n")

            tan = input("TAN: ")

        logger.debug("TANAuthentication._print() ended\n")
        return tan

    def finalize(
        self, challenge_id: str, challenge_dic: Dict[str, str], _device_name: str = None
    ) -> bool:
        """complete 2fa with chip tan manual"""
        logger.debug("TANAuthentication.finalize()\n")

        tan = self._print(challenge_dic)

        data_dic = {
            "data": {
                "attributes": {"challengeResponse": tan, "methodType": self.mfa_method},
                "type": "mfa-challenge",
            }
        }
        self.client.headers["Content-Type"] = JSON_CONTENT_TYPE
        self.client.headers["Accept"] = "application/vnd.api+json"

        response = self.client.post(
            self.base_url + f"/mfa/mfa/challenges/{challenge_id}",
            data=json.dumps(data_dic),
        )
        mfa_completed = False
        if response.status_code <= 300:
            result_dic = response.json()
            if (
                "data" in result_dic
                and "attributes" in result_dic["data"]
                and "verificationStatus" in result_dic["data"]["attributes"]
                and result_dic["data"]["attributes"]["verificationStatus"]
                == "authorized"
            ):
                mfa_completed = True
        else:
            raise DKBRoboError(
                f"Login failed: 2fa failed. RC: {response.status_code} text: {response.text}"
            )

        self.client.headers.pop("Content-Type")
        self.client.headers.pop("Accept")

        logger.debug("TANAuthentication.finalize() ended with %s\n", mfa_completed)
        return mfa_completed
