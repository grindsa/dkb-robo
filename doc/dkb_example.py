#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" example script for dkb-robo """
from __future__ import print_function
import sys
from pprint import pprint
from dkb_robo import DKBRobo

if sys.version_info > (3, 0):
    import http.cookiejar as cookielib
    import importlib
    importlib.reload(sys)
else:
    import cookielib
    reload(sys)
    sys.setdefaultencoding('utf8')


if __name__ == "__main__":

    DKB_USER = 'xxxxxxx'
    DKB_PASSWORD = '*****'

    DKB = DKBRobo()
    
    # Using a Contexthandler (with) makes sure that the connection is closed after use
    with DKBRobo('USER','PWD') as dkb:
        print(dkb.last_login)
        pprint(dkb.overview_dic)

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

    # get standing orders (daueraufträge)
    STO = DKB.get_standing_orders(DKB_BR)
    pprint(STO)
    
    # get freitstellungsaufträge
    EXO = DKB.get_excemption_order(DKB_BR)
    pprint(EXO)
    
    POINTS_DIC = DKB.get_points(DKB_BR)
    pprint(POINTS_DIC)
    
    # logout
    DKB.logout(DKB_BR)
