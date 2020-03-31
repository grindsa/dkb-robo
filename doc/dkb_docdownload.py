#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" example script for dkb-robo """
from __future__ import print_function
import sys
import os
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

    DKB_USER = 'xxx'
    DKB_PASSWORD = 'xxx'
    try:
        path = sys.argv[1]
    except:
        print("No path given")
        exit(1)

    DKB = DKBRobo()

    # Using a Contexthandler (with) makes sure that the connection is closed after use
    with DKBRobo(DKB_USER, DKB_PASSWORD, False, True) as dkb:
        print(dkb.last_login)

        print(f'Writing documents to {path}')
        POSTBOX_DIC = dkb.scan_postbox(path)

