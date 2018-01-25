#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" example script for dkb-robo """
from __future__ import print_function
import sys
from pprint import pprint
from lib.dkb_robo import DKBRobo

reload(sys)
sys.setdefaultencoding('utf8')


if __name__ == "__main__":

    DKB_USER = 'xxxxxxx'
    DKB_PASSWORD = '*****'

    DKB = DKBRobo()

    # login and get accounts overview
    (DKB_BR, LAST_LOGIN, OVERVIEW_DIC) = DKB.login(DKB_USER, DKB_PASSWORD)
    print(LAST_LOGIN)
    pprint(OVERVIEW_DIC)

    # get transaction
    LINK = OVERVIEW_DIC[3]['transactions']
    TYPE = OVERVIEW_DIC[3]['type']
    DATE_FROM = '14.03.2017'
    DATE_TO = '21.08.2017'

    TRANSACTION_LIST = DKB.get_transactions(DKB_BR, LINK, TYPE, DATE_FROM, DATE_TO)
    pprint(TRANSACTION_LIST)

    # get dkb postbox
    POSTBOX_DIC = DKB.scan_postbox(DKB_BR)
    pprint(POSTBOX_DIC)

    # get credit limits
    CLI = DKB.get_credit_limits(DKB_BR)
    pprint(CLI)

    EXO = DKB.get_excemption_order(DKB_BR)
    pprint(EXO)

    # logout
    DKB.logout(DKB_BR)
