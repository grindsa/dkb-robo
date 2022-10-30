#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" unittests for dkb_robo """
import sys
import os
import unittest
from unittest.mock import patch, MagicMock, Mock, mock_open
from bs4 import BeautifulSoup
from mechanicalsoup import LinkNotFoundError
from datetime import date

sys.path.insert(0, '.')
sys.path.insert(0, '..')
from dkb_robo import DKBRobo
import logging

def read_file(fname):
    """ read file into string """
    with open(fname, "rb") as myfile:
        data = myfile.read()

    return data

def cnt_list(value):
    """ customized function return just the number if entries in input list """
    return len(value)

@patch('dkb_robo.DKBRobo.dkb_br')
class TestDKBRobo(unittest.TestCase):
    """ test class """

    maxDiff = None

    def setUp(self):
        self.dkb = DKBRobo()
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        from dkb_robo.dkb_robo import validate_dates, generate_random_string, logger_setup, string2float
        self.validate_dates = validate_dates
        self.string2float = string2float
        self.generate_random_string = generate_random_string
        self.logger_setup = logger_setup
        self.logger = logging.getLogger('dkb_robo')

    def test_020_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() exception depot """
        html = read_file(self.dir_path + '/mocks/finanzstatus-error3.html')
        e_result = {0: {'account': u'XY99 1111 1111 0000 1111 99',
                        'amount': 1367.82,
                        'date': u'27.04.2018',
                        'details': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=0',
                        'name': u'hauptkonto',
                        'transactions': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=0',
                        'type': 'account'},
                    1: {'account': u'9999********1111',
                        'amount': 9613.31,
                        'date': u'27.04.2018',
                        'details': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=0',
                        'name': u'first visa',
                        'transactions': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=0',
                        'type': 'creditcard'},
                    2: {'account': u'9999********8888',
                        'amount': -260.42,
                        'date': u'26.04.2018',
                        'details': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=0',
                        'name': u'MilesnMoreMaster',
                        'transactions': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=0',
                        'type': 'creditcard'},
                    3: {'account': u'9999********2222',
                        'amount': 515.52,
                        'date': u'27.04.2018',
                        'details': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=1',
                        'name': u'second visa',
                        'transactions': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=1',
                        'type': 'creditcard'},
                    4: {'account': u'XY99 1111 1111 2155 2788 99',
                        'amount': 588.37,
                        'date': u'27.04.2018',
                        'details': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=1',
                        'name': u'zweitkonto',
                        'transactions': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=1',
                        'type': 'account'},
                    5: {'account': u'9999********3333',
                        'amount': 515.52,
                        'date': u'27.04.2018',
                        'details': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=1',
                        'name': u'3rd visa',
                        'transactions': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=1',
                        'type': 'creditcard'},
                    6: {'account': u'XY99 3333 1111 0000 3333 99',
                        'amount': -334.34,
                        'date': u'27.04.2018',
                        'details': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=3&group=1',
                        'name': u'3rd acc',
                        'type': 'depot'}}
        self.assertEqual(e_result, self.dkb._parse_overview(BeautifulSoup(html, 'html5lib')))

if __name__ == '__main__':

    unittest.main()
