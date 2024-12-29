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
