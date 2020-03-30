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
    with DKBRobo(DKB_USER, DKB_PASSWORD) as dkb:
        print(dkb.last_login)
        pprint(dkb.account_dic)

        # get transaction
        LINK = dkb.account_dic[0]['transactions']
        TYPE = dkb.account_dic[0]['type']
        DATE_FROM = '01.03.2020'
        DATE_TO = '31.03.2020'

        TRANSACTION_LIST = dkb.get_transactions(LINK, TYPE, DATE_FROM, DATE_TO)
        pprint(TRANSACTION_LIST)

        # get dkb postbox
        POSTBOX_DIC = dkb.scan_postbox()
        pprint(POSTBOX_DIC)

        # get credit limits
        CLI = dkb.get_credit_limits()
        pprint(CLI)

        # get standing orders (daueraufträge)
        STO = dkb.get_standing_orders()
        pprint(STO)

        # get freitstellungsaufträge
        EXO = dkb.get_exemption_order()
        pprint(EXO)

        POINTS_DIC = dkb.get_points()
        pprint(POINTS_DIC)
