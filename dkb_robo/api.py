# pylint: disable=c0302, r0913
""" legacy api """
# -*- coding: utf-8 -*-
import os
import datetime
import time
import logging
import json
import base64
import io
import threading
from typing import Dict, List, Tuple
import requests
from dkb_robo.utilities import get_dateformat, get_valid_filename
from dkb_robo.portfolio import Overview
from dkb_robo.legacy import Wrapper as Legacywrapper


LEGACY_DATE_FORMAT, API_DATE_FORMAT = get_dateformat()
JSON_CONTENT_TYPE = 'application/vnd.api+json'


class DKBRoboError(Exception):
    """ dkb-robo exception class """


class Wrapper(object):
    """ this is the wrapper for the legacy api """
    base_url = 'https://banking.dkb.de'
    api_prefix = '/api'
    mfa_method = 'seal_one'
    mfa_device = 0
    dkb_user = None
    dkb_password = None
    dkb_br = None
    logger = None
    proxies = {}
    client = None
    token_dic = None
    account_dic = {}

    def __init__(self, dkb_user: str = None, dkb_password: str = None, chip_tan: bool = False, proxies: Dict[str, str] = None, logger: logging.Logger = False, mfa_device: int = None):
        self.dkb_user = dkb_user
        self.dkb_password = dkb_password
        self.proxies = proxies
        self.logger = logger
        if chip_tan:
            self.logger.info('Using to chip_tan to login')
            if chip_tan in ('qr', 'chip_tan_qr'):
                self.mfa_method = 'chip_tan_qr'
            else:
                self.mfa_method = 'chip_tan_manual'
        try:
            self.mfa_device = int(mfa_device)
        except (ValueError, TypeError):
            self.mfa_device = 0

    def _check_processing_status(self, polling_dic: Dict[str, str], cnt: 1) -> bool:
        self.logger.debug('api.Wrapper._check_processing_status()\n')

        if 'data' in polling_dic and 'attributes' in polling_dic['data'] and 'verificationStatus' in polling_dic['data']['attributes']:

            self.logger.debug('api.Wrapper._check_processing_status: cnt %s got %s flag', cnt, polling_dic['data']['attributes']['verificationStatus'])

            mfa_completed = False
            if (polling_dic['data']['attributes']['verificationStatus']) == 'processed':
                mfa_completed = True
            elif (polling_dic['data']['attributes']['verificationStatus']) == 'processing':
                self.logger.info('Status: %s. Waiting for confirmation', polling_dic['data']['attributes']['verificationStatus'])
            elif (polling_dic['data']['attributes']['verificationStatus']) == 'canceled':
                raise DKBRoboError('2fa chanceled by user')
            else:
                self.logger.info('Unknown processing status: %s', polling_dic['data']['attributes']['verificationStatus'])
        else:
            raise DKBRoboError('Login failed: processing status format is other than expected')

        self.logger.debug('api.Wrapper._check_processing_status() ended with: %s\n', mfa_completed)
        return mfa_completed

    def _complete_app_2fa(self, challenge_id: str, devicename: str) -> bool:
        """ wait for confirmation for the 2nd factor """
        self.logger.debug('api.Wrapper._complete_app_2fa()\n')

        self._print_app_2fa_confirmation(devicename)

        cnt = 0
        mfa_completed = False
        # we give us 50 seconds to press a button on the phone
        while cnt <= 10:
            response = self.client.get(self.base_url + self.api_prefix + f"/mfa/mfa/challenges/{challenge_id}")
            cnt += 1
            if response.status_code == 200:
                polling_dic = response.json()
                if 'data' in polling_dic and 'attributes' in polling_dic['data'] and 'verificationStatus' in polling_dic['data']['attributes']:
                    # check processing status
                    mfa_completed = self._check_processing_status(polling_dic, cnt)
                    if mfa_completed:
                        break
                else:
                    self.logger.error('api.Wrapper._complete_app_2fa(): error parsing polling response: %s', polling_dic)
            else:
                self.logger.error('api.Wrapper._complete_app_2fa(): polling request failed. RC: %s', response.status_code)
            time.sleep(5)

        self.logger.debug('api.Wrapper._complete_app_2fa() ended with: %s\n', mfa_completed)
        return mfa_completed

    def _print_ctan_instructions(self, challenge_dic: Dict[str, str]) -> str:
        """ print instructions for chip tan """
        self.logger.debug('api.Wrapper._print_ctan_instructions()\n')

        if 'data' in challenge_dic and 'attributes' in challenge_dic['data'] and 'chipTan' in challenge_dic['data']['attributes'] and 'qrData' in challenge_dic['data']['attributes']['chipTan']:
            my_thread = threading.Thread(target=self._show_image, args=(challenge_dic['data']['attributes']['chipTan']['qrData'], ))
            my_thread.daemon = True
            my_thread.start()
            my_thread.join(timeout=0.5)

        tan = None
        if 'data' in challenge_dic and 'attributes' in challenge_dic['data'] and 'chipTan' in challenge_dic['data']['attributes']:
            if 'headline' in challenge_dic['data']['attributes']['chipTan']:
                print(f"{challenge_dic['data']['attributes']['chipTan']['headline']}\n")
            if 'instructions' in challenge_dic['data']['attributes']['chipTan']:
                for idx, instruction in enumerate(challenge_dic['data']['attributes']['chipTan']['instructions'], start=1):
                    print(f'{idx}. {instruction}\n')

            tan = input("TAN: ")

        self.logger.debug('api.Wrapper._print_ctan_instructions() ended\n')
        return tan

    def _complete_ctm_2fa(self, challenge_id: str, challenge_dic: Dict[str, str]) -> bool:
        """ complete 2fa with chip tan manual """
        self.logger.debug('api.Wrapper._complete_ctm_2fa()\n')

        tan = self._print_ctan_instructions(challenge_dic)

        data_dic = {"data": {"attributes": {"challengeResponse": tan, "methodType": self.mfa_method}, "type": "mfa-challenge"}}
        self.client.headers['Content-Type'] = JSON_CONTENT_TYPE
        self.client.headers["Accept"] = "application/vnd.api+json"

        response = self.client.post(self.base_url + self.api_prefix + f"/mfa/mfa/challenges/{challenge_id}", data=json.dumps(data_dic))
        mfa_completed = False
        if response.status_code <= 300:
            result_dic = response.json()
            if 'data' in result_dic and 'attributes' in result_dic['data'] and 'verificationStatus' in result_dic['data']['attributes'] and result_dic['data']['attributes']['verificationStatus'] == 'authorized':
                mfa_completed = True
        else:
            raise DKBRoboError(f'Login failed: 2fa failed. RC: {response.status_code} text: {response.text}')

        self.client.headers.pop('Content-Type')
        self.client.headers.pop('Accept')

        self.logger.debug('api.Wrapper._complete_ctm_2fa() ended with %s\n', mfa_completed)
        return mfa_completed

    def _get_overview(self) -> Dict[str, str]:
        """ get overview """
        self.logger.debug('api.Wrapper._get_overview()\n')
        # this is just a dummy function to keep unittests happy
        self.logger.debug('api.Wrapper._get_overview() ended\n')
        return {'foo': 'bar'}

    def _show_image(self, qr_data: str) -> None:
        """ show qr code """
        self.logger.debug('api.Wrapper._show_image()\n')

        # pylint: disable=c0415
        from PIL import Image
        qr_data = qr_data.replace('data:image/png;base64,', '')
        qr_data = qr_data.replace(' ', '+')
        qr_data = base64.b64decode(qr_data)
        data = io.BytesIO()
        data.write(qr_data)
        img = Image.open(data)
        img.show()

        self.logger.debug('api.Wrapper._show_image() ended\n')

    def _complete_2fa(self, challenge_dic: Dict[str, str], devicename: str) -> bool:
        """ wait for confirmation for the 2nd factor """
        self.logger.debug('api.Wrapper._complete_2fa()\n')

        challenge_id = self._get_challenge_id(challenge_dic)

        if self.mfa_method == 'seal_one':
            mfa_completed = self._complete_app_2fa(challenge_id, devicename)
        elif self.mfa_method in ('chip_tan_manual', 'chip_tan_qr'):
            mfa_completed = self._complete_ctm_2fa(challenge_id, challenge_dic)
        else:
            mfa_completed = False
            raise DKBRoboError(f'Login failed: unknown 2fa method: {self.mfa_method}')

        self.logger.debug('api.Wrapper._complete_2fa() ended with %s\n', mfa_completed)
        return mfa_completed

    def _do_sso_redirect(self):
        """  redirect to access legacy page """
        self.logger.debug('api.Wrapper._do_sso_redirect()\n')

        data_dic = {'data': {'cookieDomain': '.dkb.de'}}
        self.client.headers['Content-Type'] = 'application/json'
        self.client.headers['Sec-Fetch-Dest'] = 'empty'
        self.client.headers['Sec-Fetch-Mode'] = 'cors'
        self.client.headers['Sec-Fetch-Site'] = 'same-origin'

        response = self.client.post(self.base_url + self.api_prefix + '/sso-redirect', data=json.dumps(data_dic))

        if response.status_code != 200 or response.text != 'OK':
            self.logger.error('SSO redirect failed. RC: %s text: %s', response.status_code, response.text)
        clientcookies = self.client.cookies

        legacywrappper = Legacywrapper(logger=self.logger)
        # pylint: disable=w0212
        self.dkb_br = legacywrappper._new_instance(clientcookies)
        self.logger.debug('api.Wrapper._do_sso_redirect() ended.\n')

    def _get_mfa_challenge_dic(self, mfa_dic: Dict[str, str], device_num: int = 0) -> Tuple[str, str]:
        """ get challenge dict with information on the 2nd factor """
        self.logger.debug('api.Wrapper._get_mfa_challenge_dic(): login with device_num: %s\n', device_num)

        device_name = None
        challenge_dic = {}
        if 'data' in mfa_dic and 'id' in mfa_dic['data'][device_num]:
            try:
                device_name = mfa_dic['data'][device_num]['attributes']['deviceName']
                self.logger.debug('api.Wrapper._get_mfa_challenge_dic(): devicename: %s\n', device_name)
            except Exception as _err:
                self.logger.error('api.Wrapper._get_mfa_challenge_dic(): unable to get deviceName')
                device_name = None

            # additional headers needed as this call requires it
            self.client.headers['Content-Type'] = JSON_CONTENT_TYPE
            self.client.headers["Accept"] = "application/vnd.api+json"

            # we are expecting the first method from mfa_dic to be used
            data_dic = {'data': {'type': 'mfa-challenge', 'attributes': {'mfaId': self.token_dic['mfa_id'], 'methodId': mfa_dic['data'][device_num]['id'], 'methodType': self.mfa_method}}}
            response = self.client.post(self.base_url + self.api_prefix + '/mfa/mfa/challenges', data=json.dumps(data_dic))

            # process response
            # challenge_id = self._process_challenge_response(response)
            if response.status_code in (200, 201):
                challenge_dic = response.json()
            else:
                raise DKBRoboError(f'Login failed: post request to get the mfa challenges failed. RC: {response.status_code}')

            # we rmove the headers we added earlier
            self.client.headers.pop('Content-Type')
            self.client.headers.pop('Accept')
        else:
            self.logger.error('api.Wrapper._get_mfa_challenge_dic(): mfa_dic has an unexpected data structure')

        self.logger.debug('api.Wrapper._get_mfa_challenge_dic() ended\n')
        return challenge_dic, device_name

    def _get_mfa_methods(self) -> Dict[str, str]:
        """ get mfa methods """
        self.logger.debug('api.Wrapper._get_mfa_methods()\n')
        mfa_dic = {}

        # check for access_token and get mfa_methods
        if 'access_token' in self.token_dic and 'mfa_id' in self.token_dic:
            response = self.client.get(self.base_url + self.api_prefix + f'/mfa/mfa/{self.token_dic["mfa_id"]}/methods?filter%5BmethodType%5D={self.mfa_method}')
            if response.status_code == 200:
                mfa_dic = response.json()
            else:
                raise DKBRoboError(f'Login failed: getting mfa_methods failed. RC: {response.status_code}')
        else:
            raise DKBRoboError('Login failed: no 1fa access token.')

        self.logger.debug('api.Wrapper._get_mfa_methods() ended\n')
        return mfa_dic

    def _get_token(self):
        """ get access token """
        self.logger.debug('api.Wrapper._get_token()\n')

        # login via API
        data_dic = {'grant_type': 'banking_user_sca', 'username': self.dkb_user, 'password': self.dkb_password, 'sca_type': 'web-login'}
        response = self.client.post(self.base_url + self.api_prefix + '/token', data=data_dic)
        if response.status_code == 200:
            self.token_dic = response.json()
        else:
            raise DKBRoboError(f'Login failed: 1st factor authentication failed. RC: {response.status_code}')
        self.logger.debug('api.Wrapper._get_token() ended\n')

    def _new_session(self):
        """ new request session for the api calls """
        self.logger.debug('api.Wrapper._new_session()\n')

        headers = {
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'te': 'trailers',
            'priority': 'u=0',
            'sec-gpc': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0'}
        client = requests.session()
        client.headers = headers
        if self.proxies:
            client.proxies = self.proxies
            client.verify = False

        # get cookies
        client.get(self.base_url + '/login')

        # add csrf token
        if '__Host-xsrf' in client.cookies:
            headers['x-xsrf-token'] = client.cookies['__Host-xsrf']
            client.headers = headers

        self.logger.debug('api.Wrapper._new_session()\n ended')
        return client

    def _print_app_2fa_confirmation(self, devicename: str):
        """ 2fa confirmation message """
        self.logger.debug('api.Wrapper._print_app_2fa_confirmation()\n')
        if devicename:
            print(f'check your banking app on "{devicename}" and confirm login...')
        else:
            print('check your banking app and confirm login...')

    def _get_challenge_id(self, challenge_dic: Dict[str, str]) -> str:
        """ get challenge dict with information on the 2nd factor """
        self.logger.debug('api.Wrapper._get_challenge_id()\n')
        challenge_id = None

        if 'data' in challenge_dic and 'id' in challenge_dic['data'] and 'type' in challenge_dic['data']:
            if challenge_dic['data']['type'] == 'mfa-challenge':
                challenge_id = challenge_dic['data']['id']
            else:
                raise DKBRoboError(f'Login failed:: wrong challenge type: {challenge_dic}')

        else:
            raise DKBRoboError(f'Login failed: challenge response format is other than expected: {challenge_dic}')

        self.logger.debug('api.Wrapper._get_challenge_id() ended with: %s\n', challenge_id)
        return challenge_id

    def _process_userinput(self, device_num: int, device_list: List[int], _tmp_device_num: str, deviceselection_completed: bool) -> Tuple[int, bool]:
        self.logger.debug('api.Wrapper._process_userinput(%s)', _tmp_device_num)
        try:
            # we are referring to an index in a list thus we need to lower the user input by 1
            if int(_tmp_device_num) - 1 in device_list:
                deviceselection_completed = True
                device_num = int(_tmp_device_num) - 1
            else:
                print('\nWrong input!')
        except Exception:
            print('\nInvalid input!')

        self.logger.debug('api.Wrapper._process_userinput()\n ended')
        return device_num, deviceselection_completed

    def _select_mfa_device(self, mfa_dic: Dict[str, str]) -> int:
        """ pick mfa_device from dictionary """
        self.logger.debug('_select_mfa_device()')
        device_num = 0

        # adjust self.mfa_device if the user input is too high
        if 'data' in mfa_dic and len(mfa_dic['data']) < self.mfa_device:
            self.logger.warning('User submitted mfa_device number is invalid. Ingoring...')
            self.mfa_device = 0

        if self.mfa_device > 0:
            # we need to lower by one as we refer to an index in a list
            self.logger.debug('api.Wrapper._select_mfa_device(): using user submitted mfa_device number: %s', self.mfa_device)
            device_num = self.mfa_device - 1

        elif 'data' in mfa_dic and len(mfa_dic['data']) > 1:
            device_list = []
            deviceselection_completed = False
            while not deviceselection_completed:
                print('\nPick an authentication device from the below list:')
                # we have multiple devices to select
                for idx, device_dic in enumerate(mfa_dic['data']):
                    device_list.append(idx)
                    if 'attributes' in device_dic and 'deviceName' in device_dic['attributes']:
                        # we should start counting with 1 for the user
                        print(f"[{idx + 1}] - {device_dic['attributes']['deviceName']}")
                _tmp_device_num = input(':')

                device_num, deviceselection_completed = self._process_userinput(device_num, device_list, _tmp_device_num, deviceselection_completed)

        self.logger.debug('_select_mfa_device() ended with: %s', device_num)
        return device_num

    def _sort_mfa_devices(self, mfa_dic):
        """ sort mfa methods """
        self.logger.debug('_sort_mfa_devices()')
        mfa_list = mfa_dic['data']
        if self.mfa_method == 'seal_one':
            mfa_list.sort(key=lambda x: (-x['attributes']['preferredDevice'], x['attributes']['enrolledAt']))
        self.logger.debug('_sort_mfa_devices() ended with: %s elements', len(mfa_list))
        return {'data': mfa_list}

    def _update_token(self):
        """ update token information with 2fa iformation """
        self.logger.debug('api.Wrapper._update_token()\n')

        data_dic = {'grant_type': 'banking_user_mfa', 'mfa_id': self.token_dic['mfa_id'], 'access_token': self.token_dic['access_token']}
        response = self.client.post(self.base_url + self.api_prefix + '/token', data=data_dic)
        if response.status_code == 200:
            self.token_dic = response.json()
        else:
            raise DKBRoboError(f'Login failed: token update failed. RC: {response.status_code}')

    def get_credit_limits(self) -> Dict[str, str]:
        """ get credit limits """
        self.logger.debug('api.Wrapper.get_credit_limits()\n')
        limit_dic = {}

        for _aid, account_data in self.account_dic.items():
            if 'limit' in account_data:
                if 'iban' in account_data:
                    limit_dic[account_data['iban']] = account_data['limit']
                elif 'maskedpan' in account_data:
                    limit_dic[account_data['maskedpan']] = account_data['limit']

        self.logger.debug('api.Wrapper.get_credit_limits() ended\n')
        return limit_dic

    def login(self) -> Tuple[Dict, None]:
        """ login into DKB banking area and perform an sso redirect """
        self.logger.debug('api.Wrapper.login()\n')

        mfa_dic = {}

        # create new session
        self.client = self._new_session()

        # get token for 1fa
        self._get_token()

        # get mfa methods
        mfa_dic = self._get_mfa_methods()

        if mfa_dic:
            # sort mfa methods
            mfa_dic = self._sort_mfa_devices(mfa_dic)

        # pick mfa device from list
        device_number = self._select_mfa_device(mfa_dic)

        # we need a challege-id for polling so lets try to get it
        mfa_challenge_dic = None
        if 'mfa_id' in self.token_dic and 'data' in mfa_dic:
            mfa_challenge_dic, device_name = self._get_mfa_challenge_dic(mfa_dic, device_number)
        else:
            raise DKBRoboError('Login failed: no 1fa access token.')

        # lets complete 2fa
        mfa_completed = False
        if mfa_challenge_dic:
            mfa_completed = self._complete_2fa(mfa_challenge_dic, device_name)
        else:
            raise DKBRoboError('Login failed: No challenge id.')

        # update token dictionary
        if mfa_completed and 'access_token' in self.token_dic:
            self._update_token()
        else:
            raise DKBRoboError('Login failed: mfa did not complete')

        if 'token_factor_type' not in self.token_dic:
            raise DKBRoboError('Login failed: token_factor_type is missing')

        if 'token_factor_type' in self.token_dic and self.token_dic['token_factor_type'] != '2fa':

            raise DKBRoboError('Login failed: 2nd factor authentication did not complete')

        # get account overview
        overview = Overview(logger=self.logger, client=self.client)
        self.account_dic = overview.get()

        # redirect to legacy page
        self._do_sso_redirect()
        self.logger.debug('api.Wrapper.login() ended\n')
        return self.account_dic, None

    def get_exemption_order(self) -> Dict[str, str]:
        """ get_exemption_order() """
        self.logger.debug('api.Wrapper.logout()\n')

        legacywrappper = Legacywrapper(logger=self.logger)
        legacywrappper.dkb_br = self.dkb_br

        self.logger.debug('api.Wrapper.logout() ended.\n')
        return legacywrappper.get_exemption_order()

    def logout(self):
        """ logout function """
        self.logger.debug('api.Wrapper.logout()\n')
