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









    def _get_overview(self) -> Dict[str, str]:
        """ get overview """
        self.logger.debug('api.Wrapper._get_overview()\n')
        # this is just a dummy function to keep unittests happy
        self.logger.debug('api.Wrapper._get_overview() ended\n')
        return {'foo': 'bar'}





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

