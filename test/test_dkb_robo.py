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

    def test_001_get_cc_limit(self, mock_browser):
        """ test DKBRobo.get_credit_limits() method """
        html = read_file(self.dir_path + '/mocks/konto-kreditkarten-limits.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'1111********1111': 100.00,
                    u'1111********1112': 2000.00,
                    u'DE01 1111 1111 1111 1111 11': 1000.00,
                    u'DE02 1111 1111 1111 1111 12': 2000.00}
        self.assertEqual(e_result, self.dkb.get_credit_limits())

    def test_002_get_cc_limit(self, mock_browser):
        """ test DKBRobo.get_credit_limits() triggers exceptions """
        html = read_file(self.dir_path + '/mocks/konto-kreditkarten-limits-exception.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {'DE01 1111 1111 1111 1111 11': 1000.00, 'DE02 1111 1111 1111 1111 12': 2000.00}
        self.assertEqual(e_result, self.dkb.get_credit_limits())

    def test_003_get_exo_single(self, mock_browser):
        """ test DKBRobo.get_exemption_order() method for a single exemption order """
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0, 'amount': 1000.0, 'used': 0.0, 'description': u'Gemeinsam mit Firstname Familyname', 'validity': u'01.01.2016 unbefristet'}}
        self.assertEqual(self.dkb.get_exemption_order(), e_result)

    def test_004_get_exo_single_nobr(self, mock_browser):
        """ test DKBRobo.get_exemption_order() method for a single exemption order without line-breaks"""
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag-nobr.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0, 'amount': 1000.0, 'used': 0.0, 'description': u'Gemeinsam mit Firstname Familyname', 'validity': u'01.01.2016 unbefristet'}}
        self.assertEqual(self.dkb.get_exemption_order(), e_result)

    def test_005_get_exo_multiple(self, mock_browser):
        """ test DKBRobo.get_exemption_order() method for a multiple exemption orders """
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag-multiple.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0,
                        'amount': 1000.0,
                        'used': 0.0,
                        'description': u'Gemeinsam mit Firstname1 Familyname1',
                        'validity': u'01.01.2016 unbefristet'},
                    2: {'available': 2000.0,
                        'amount': 2000.0,
                        'used': 0.0,
                        'description': u'Gemeinsam mit Firstname2 Familyname2',
                        'validity': u'02.01.2016 unbefristet'}
                   }
        self.assertEqual(self.dkb.get_exemption_order(), e_result)

    def test_006_get_exo_single(self, mock_browser):
        """ test DKBRobo.get_exemption_order() method try throws exception """
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag-indexerror.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1:{}}
        # with self.assertRaises(Exception) as err:
        self.assertEqual(self.dkb.get_exemption_order(), e_result)
        # print(err.exception)
        # self.assertEqual("foo could not convert string to float: 'aaa'", str(err.exception))

    def test_007_new_instance(self, _unused):
        """ test DKBRobo._new_instance() method """
        self.assertIn('mechanicalsoup.stateful_browser.StatefulBrowser object at', str(self.dkb._new_instance()))

    def test_008_get_points(self, mock_browser):
        """ test DKBRobo.get_points() method """
        html = read_file(self.dir_path + '/mocks/dkb_punkte.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'DKB-Punkte': 100000, u'davon verfallen zum  31.12.2017': 90000}
        self.assertEqual(self.dkb.get_points(), e_result)

    def test_009_get_so_multiple(self, mock_browser):
        """ test DKBRobo.get_standing_orders() method """
        html = read_file(self.dir_path + '/mocks/dauerauftraege.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = [{'amount': 100.0, 'interval': u'1. monatlich 01.03.2017', 'recipient': u'RECPIPIENT-1', 'purpose': u'KV 1234567890'},
                    {'amount': 200.0, 'interval': u'1. monatlich geloescht', 'recipient': u'RECPIPIENT-2', 'purpose': u'KV 0987654321'}]
        self.assertEqual(self.dkb.get_standing_orders(), e_result)

    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._login_confirm')
    @patch('dkb_robo.DKBRobo._ctan_check')
    @patch('dkb_robo.DKBRobo._new_instance')
    def test_010_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test DKBRobo._login() method - no confirmation """
        html = """
                <h1>Anmeldung bestätigen</h1>
                <div id="lastLoginContainer" class="lastLogin deviceFloatRight ">
                        Letzte Anmeldung:
                        01.03.2017, 01:00 Uhr
                </div>
               """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_ctan.return_value = False
        mock_confirm.return_value = False
        mock_instance.return_value = mock_browser
        mock_pov.return_value = '_parse_overview'
        mock_fs.return_value = 'mock_fs'
        self.assertEqual(self.dkb._login(), None)
        self.assertTrue(mock_confirm.called)
        self.assertFalse(mock_ctan.called)
        self.assertFalse(mock_fs.called)
        self.assertFalse(mock_pov.called)

    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._login_confirm')
    @patch('dkb_robo.DKBRobo._ctan_check')
    @patch('dkb_robo.DKBRobo._new_instance')
    def test_011_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test DKBRobo.login() method - confirmation """
        html = """
                <h1>Anmeldung bestätigen</h1>
                <div id="lastLoginContainer" class="lastLogin deviceFloatRight ">
                        Letzte Anmeldung:
                        01.03.2017, 01:00 Uhr
                </div>
               """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_ctan.return_value = False
        mock_confirm.return_value = True
        mock_instance.return_value = mock_browser
        mock_pov.return_value = '_parse_overview'
        mock_fs.return_value = 'mock_fs'
        self.assertEqual(self.dkb._login(), None)
        self.assertTrue(mock_confirm.called)
        self.assertFalse(mock_ctan.called)
        self.assertTrue(mock_fs.called)
        self.assertTrue(mock_pov.called)

    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._login_confirm')
    @patch('dkb_robo.DKBRobo._ctan_check')
    @patch('dkb_robo.DKBRobo._new_instance')
    def test_012_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test DKBRobo._login() method - no confirmation """
        html = """
                <h1>Anmeldung bestätigen</h1>
                <div id="lastLoginContainer" class="lastLogin deviceFloatRight ">
                        Letzte Anmeldung:
                        01.03.2017, 01:00 Uhr
                </div>
               """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_ctan.return_value = False
        mock_confirm.return_value = False
        mock_instance.return_value = mock_browser
        mock_pov.return_value = '_parse_overview'
        mock_fs.return_value = 'mock_fs'
        self.dkb.tan_insert = True
        self.assertEqual(self.dkb._login(), None)
        self.assertFalse(mock_confirm.called)
        self.assertTrue(mock_ctan.called)
        self.assertFalse(mock_fs.called)
        self.assertFalse(mock_pov.called)

    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._login_confirm')
    @patch('dkb_robo.DKBRobo._ctan_check')
    @patch('dkb_robo.DKBRobo._new_instance')
    def test_013_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test DKBRobo._login() method - confirmation """
        html = """
                <h1>Anmeldung bestätigen</h1>
                <div id="lastLoginContainer" class="lastLogin deviceFloatRight ">
                        Letzte Anmeldung:
                        01.03.2017, 01:00 Uhr
                </div>
               """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_ctan.return_value = True
        mock_confirm.return_value = False
        mock_instance.return_value = mock_browser
        mock_pov.return_value = '_parse_overview'
        mock_fs.return_value = 'mock_fs'
        self.dkb.tan_insert = True
        self.assertEqual(self.dkb._login(), None)
        self.assertFalse(mock_confirm.called)
        self.assertTrue(mock_ctan.called)
        self.assertTrue(mock_fs.called)
        self.assertTrue(mock_pov.called)

    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._login_confirm')
    @patch('dkb_robo.DKBRobo._ctan_check')
    @patch('dkb_robo.DKBRobo._new_instance')
    def test_014_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test DKBRobo._login() login failed """
        html = """
                <div id="lastLoginContainer" class="clearfix module text errorMessage">foo</div>
               """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_ctan.return_value = True
        mock_confirm.return_value = False
        mock_instance.return_value = mock_browser
        mock_pov.return_value = '_parse_overview'
        mock_fs.return_value = 'mock_fs'
        self.dkb.tan_insert = True
        with self.assertRaises(Exception) as err:
            self.assertEqual(self.dkb._login(), None)
        self.assertEqual('Login failed', str(err.exception))
        self.assertFalse(mock_confirm.called)
        self.assertFalse(mock_ctan.called)
        self.assertFalse(mock_fs.called)
        self.assertFalse(mock_pov.called)

    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._login_confirm')
    @patch('dkb_robo.DKBRobo._ctan_check')
    @patch('dkb_robo.DKBRobo._new_instance')
    def test_015_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test DKBRobo._login() login failed """
        mock_browser.select_form.side_effect = LinkNotFoundError
        mock_ctan.return_value = True
        mock_confirm.return_value = False
        mock_instance.return_value = mock_browser
        mock_pov.return_value = '_parse_overview'
        mock_fs.return_value = 'mock_fs'
        self.dkb.tan_insert = True
        with self.assertRaises(Exception) as err:
            self.assertEqual(self.dkb._login(), None)
        self.assertEqual('Login failed: LinkNotFoundError', str(err.exception))
        self.assertFalse(mock_confirm.called)
        self.assertFalse(mock_ctan.called)
        self.assertFalse(mock_fs.called)
        self.assertFalse(mock_pov.called)

    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._login_confirm')
    @patch('dkb_robo.DKBRobo._ctan_check')
    @patch('dkb_robo.DKBRobo._new_instance')
    def test_016_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test DKBRobo._login() method - notice form """
        html = """
                <h1>Anmeldung bestätigen</h1>
                <form id="genericNoticeForm">foo</form>
                <div id="lastLoginContainer" class="lastLogin deviceFloatRight ">
                        Letzte Anmeldung:
                        01.03.2017, 01:00 Uhr
                </div>
               """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_ctan.return_value = True
        mock_confirm.return_value = False
        mock_instance.return_value = mock_browser
        mock_pov.return_value = '_parse_overview'
        mock_fs.return_value = 'mock_fs'
        self.dkb.tan_insert = True
        self.assertEqual(self.dkb._login(), None)
        self.assertFalse(mock_confirm.called)
        self.assertTrue(mock_ctan.called)
        self.assertTrue(mock_fs.called)
        self.assertTrue(mock_pov.called)

    def test_017_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() method """
        html = read_file(self.dir_path + '/mocks/finanzstatus.html')
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
                        'transactions': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=3&group=1',
                        'type': 'account'}}
        self.assertEqual(self.dkb._parse_overview(BeautifulSoup(html, 'html5lib')), e_result)

    def test_018_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() method """
        html = read_file(self.dir_path + '/mocks/finanzstatus-error1.html')
        e_result = {0: {'account': u'XY99 1111 1111 0000 1111 99',
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
                        'transactions': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=3&group=1',
                        'type': 'account'}}
        self.assertEqual(self.dkb._parse_overview(BeautifulSoup(html, 'html5lib')), e_result)

    def test_019_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() exception detail link"""
        html = read_file(self.dir_path + '/mocks/finanzstatus-error2.html')
        e_result = {0: {'account': u'XY99 1111 1111 0000 1111 99',
                        'amount': 1367.82,
                        'date': u'27.04.2018',
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
                        'transactions': u'https://www.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=3&group=1',
                        'type': 'account'}}
        self.assertEqual(e_result, self.dkb._parse_overview(BeautifulSoup(html, 'html5lib')))

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

    def test_021_parse_overview_mbank(self, _unused):
        """ test DKBRobo._parse_overview() method for accounts from other banks"""
        html = read_file(self.dir_path + '/mocks/finanzstatus-mbank.html')
        e_result = {0: {'account': u'1111********1111',
                        'name': u'credit-card-1',
                        'transactions': u'https://www.dkb.de/tcc-1',
                        'amount': 1000.0,
                        'details': u'https://www.dkb.de/dcc-1',
                        'date': u'01.03.2017',
                        'type': 'creditcard'},
                    1: {'account': u'1111********1112',
                        'name': u'credit-card-2',
                        'transactions': u'https://www.dkb.de/tcc-2',
                        'amount': 2000.0,
                        'details': u'https://www.dkb.de/dcc-2',
                        'date': u'02.03.2017',
                        'type': 'creditcard'},
                    2: {'account': u'DE11 1111 1111 1111 1111 11',
                        'name': u'checking-account-1',
                        'transactions': u'https://www.dkb.de/tac-1',
                        'amount': 1000.0,
                        'details': u'https://www.dkb.de/banking/dac-1',
                        'date': u'03.03.2017',
                        'type': 'account'},
                    3: {'account': u'DE11 1111 1111 1111 1111 12',
                        'name': u'checking-account-2',
                        'transactions': u'https://www.dkb.de/tac-2',
                        'amount': 2000.0,
                        'details': u'https://www.dkb.de/banking/dac-2',
                        'date': u'04.03.2017',
                        'type': 'account'},
                    4: {'account': u'1111111',
                        'name': u'Depot-1',
                        'transactions': u'https://www.dkb.de/tdepot-1',
                        'amount': 5000.0,
                        'details': u'https://www.dkb.de/ddepot-1',
                        'date': u'06.03.2017',
                        'type': 'depot'},
                    5: {'account': u'1111112',
                        'name': u'Depot-2',
                        'transactions': u'https://www.dkb.de/tdepot-2',
                        'amount': 6000.0,
                        'details': u'https://www.dkb.de/ddepot-2',
                        'date': u'06.03.2017',
                        'type': 'depot'}}
        self.assertEqual(self.dkb._parse_overview(BeautifulSoup(html, 'html5lib')), e_result)

    def test_022_get_document_links(self, mock_browser):
        """ test DKBRobo._get_document_links() method """
        html = read_file(self.dir_path + '/mocks/doclinks.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'Kontoauszug Nr. 003_2017 zu Konto 87654321': u'https://www.dkb.de/doc-2',
                    u'Kontoauszug Nr. 003_2017 zu Konto 12345678': u'https://www.dkb.de/doc-1'}
        self.assertEqual(self.dkb._get_document_links('http://foo.bar/foo'), e_result)

    @patch('dkb_robo.DKBRobo._update_downloadstate')
    @patch('dkb_robo.DKBRobo._get_document')
    def test_023_get_document_links(self, mock_doc, mock_updow, mock_browser):
        """ test DKBRobo._get_document_links() method """
        html = read_file(self.dir_path + '/mocks/doclinks-2.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doc.return_value=(200, 'fname', ['foo'])
        e_result = {'Kontoauszug Nr. 003_2017 zu Konto 12345678': {'rcode': 200, 'link': 'https://www.dkb.de/doc-1', 'fname': 'fname'}, 'Kontoauszug Nr. 003_2017 zu Konto 87654321': {'rcode': 200, 'link': 'https://www.dkb.de/doc-2', 'fname': 'fname'}}
        self.assertEqual(e_result, self.dkb._get_document_links('http://foo.bar/foo', path='path'))
        self.assertTrue(mock_updow.called)


    @patch('dkb_robo.DKBRobo._update_downloadstate')
    @patch('dkb_robo.DKBRobo._get_document')
    def test_024_get_document_links(self, mock_doc, mock_updow, mock_browser):
        """ test DKBRobo._get_document_links() method """
        html1 = read_file(self.dir_path + '/mocks/doclinks-3.html')
        html2 = read_file(self.dir_path + '/mocks/doclinks-2.html')
        mock_browser.get_current_page.side_effect = [BeautifulSoup(html1, 'html5lib'), BeautifulSoup(html2, 'html5lib')]
        mock_browser.open.return_value = True
        mock_doc.return_value=(None, 'fname', ['foo'])
        e_result = {u'Kontoauszug Nr. 003_2017 zu Konto 23456789': 'https://www.dkb.de/doc-1',
                    u'Kontoauszug Nr. 003_2017 zu Konto 12345678': u'https://www.dkb.de/doc-1',
                    u'Kontoauszug Nr. 003_2017 zu Konto 87654321': 'https://www.dkb.de/doc-2',
                    u'Kontoauszug Nr. 003_2017 zu Konto 98765432': 'https://www.dkb.de/doc-2'}
        self.assertEqual(e_result, self.dkb._get_document_links('http://foo.bar/foo', path='path'))
        self.assertFalse(mock_updow.called)

    @patch('dkb_robo.DKBRobo._update_downloadstate')
    @patch('dkb_robo.DKBRobo._get_document')
    def test_025_get_document_links(self, mock_doc, mock_updow, mock_browser):
        """ test DKBRobo._get_document_links() method """
        mock_browser.get_current_page.return_value = None
        mock_browser.open.return_value = True
        mock_doc.return_value=(None, 'fname', ['foo'])
        e_result = {}
        self.assertFalse(self.dkb._get_document_links('http://foo.bar/foo', path='path'))
        self.assertFalse(mock_updow.called)

    @patch('dkb_robo.DKBRobo._get_document_links')
    def test_026_scan_postbox(self, mock_doclinks, mock_browser):
        """ test DKBRobo.scan_postbox() method """
        html = read_file(self.dir_path + '/mocks/postbox.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doclinks.return_value = {}
        e_result = {u'Kreditkartenabrechnungen':
                        {'documents': {},
                         'name': u'Kreditkartenabrechnungen',
                         'details': u'https://www.dkb.de/banking/postfach/Kreditkartenabrechnungen'},
                    u'Mitteilungen':
                        {'documents': {},
                         'name': u'Mitteilungen',
                         'details': u'https://www.dkb.de/banking/postfach/Mitteilungen'},
                    u'Vertragsinformationen':
                        {'documents': {},
                         'name': u'Vertragsinformationen',
                         'details': u'https://www.dkb.de/banking/postfach/Vertragsinformationen'}
                   }
        self.assertEqual(self.dkb.scan_postbox(), e_result)

    @patch('dkb_robo.DKBRobo._get_document_links')
    def test_027_scan_postbox(self, mock_doclinks, mock_browser):
        """ test DKBRobo.scan_postbox() method """
        html = read_file(self.dir_path + '/mocks/postbox.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doclinks.return_value = {}
        e_result = {u'Kreditkartenabrechnungen':
                        {'documents': {},
                         'name': u'Kreditkartenabrechnungen',
                         'details': u'https://www.dkb.de/banking/postfach/Kreditkartenabrechnungen'},
                    u'Mitteilungen':
                        {'documents': {},
                         'name': u'Mitteilungen',
                         'details': u'https://www.dkb.de/banking/postfach/Mitteilungen'},
                    u'Vertragsinformationen':
                        {'documents': {},
                         'name': u'Vertragsinformationen',
                         'details': u'https://www.dkb.de/banking/postfach/Vertragsinformationen'}
                   }
        self.assertEqual(self.dkb.scan_postbox(path='path'), e_result)

    @patch('dkb_robo.DKBRobo._get_document_links')
    def test_028_scan_postbox(self, mock_doclinks, mock_browser):
        """ test DKBRobo.scan_postbox() method """
        html = read_file(self.dir_path + '/mocks/postbox-2.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doclinks.return_value = {}
        e_result = {u'Kreditkartenabrechnungen':
                        {'documents': {},
                         'name': u'Kreditkartenabrechnungen',
                         'details': u'https://www.dkb.de/banking/postfach/Kreditkartenabrechnungen'},
                    u'Mitteilungen':
                        {'documents': {},
                         'name': u'Mitteilungen',
                         'details': u'https://www.dkb.de/banking/postfach/Mitteilungen'},
                    u'Vertragsinformationen':
                        {'documents': {},
                         'name': u'Vertragsinformationen',
                         'details': u'https://www.dkb.de/banking/postfach/Vertragsinformationen'}
                   }
        self.assertEqual(self.dkb.scan_postbox(archive=True), e_result)

    def test_029_get_tr_invalid(self, _unused):
        """ test DKBRobo.get_transactions() method with an invalid account type"""
        self.assertEqual(self.dkb.get_transactions('url', 'foo', '01.03.2017', '02.03.2017'), [])

    @patch('dkb_robo.DKBRobo.get_creditcard_transactions')
    def test_030_get_tr_cc(self, mock_cc_tran, _unused):
        """ test DKBRobo.get_transactions() method with an credit-card account"""
        mock_cc_tran.return_value = ['credit_card']
        self.assertEqual(self.dkb.get_transactions('url', 'creditcard', '01.03.2017', '02.03.2017'), ['credit_card'])
        self.assertTrue(mock_cc_tran.called)

    @patch('dkb_robo.DKBRobo.get_account_transactions')
    def test_031_get_tr_ac(self, mock_ca_tran, _unused):
        """ test DKBRobo.get_transactions() method with an checking account"""
        mock_ca_tran.return_value = ['account']
        self.assertEqual(self.dkb.get_transactions('url', 'account', '01.03.2017', '02.03.2017'), ['account'])
        self.assertTrue(mock_ca_tran.called)

    @patch('dkb_robo.DKBRobo.get_depot_status')
    def test_032_get_tr_ac(self, mock_dep_tran, _unused):
        """ test DKBRobo.get_transactions() method for a deptot """
        mock_dep_tran.return_value = ['dep']
        self.assertEqual(self.dkb.get_transactions('url', 'depot', '01.03.2017', '02.03.2017'), ['dep'])
        self.assertTrue(mock_dep_tran.called)

    def test_033_parse_account_tr(self, _mock_browser):
        """ test DKBRobo.get_account_transactions for one page only """
        csv = read_file(self.dir_path + '/mocks/test_parse_account_tr.csv')
        result = [
            {'amount':  100.0, 'bdate': '01.03.2017', 'customerreferenz': 'Kundenreferenz1', 'date': '01.03.2017', 'mandatereference': 'Mandatsreferenz1', 'peer': 'Auftraggeber1', 'peeraccount': 'Kontonummer1', 'peerbic': 'BLZ1', 'peerid': 'GID1', 'postingtext': 'Buchungstext1', 'reasonforpayment': 'Verwendungszweck1', 'text': 'Buchungstext1 Auftraggeber1 Verwendungszweck1', 'vdate': '01.03.2017'},
            {'amount': -200.0, 'bdate': '02.03.2017', 'customerreferenz': 'Kundenreferenz2', 'date': '02.03.2017', 'mandatereference': 'Mandatsreferenz2', 'peer': 'Auftraggeber2', 'peeraccount': 'Kontonummer2', 'peerbic': 'BLZ2', 'peerid': 'GID2', 'postingtext': 'Buchungstext2', 'reasonforpayment': 'Verwendungszweck2', 'text': 'Buchungstext2 Auftraggeber2 Verwendungszweck2', 'vdate': '02.03.2017'},
            {'amount': 3000.0, 'bdate': '03.03.2017', 'customerreferenz': 'Kundenreferenz3', 'date': '03.03.2017', 'mandatereference': 'Mandatsreferenz3', 'peer': 'Auftraggeber3', 'peeraccount': 'Kontonummer3', 'peerbic': 'BLZ3', 'peerid': 'GID3', 'postingtext': 'Buchungstext3', 'reasonforpayment': 'Verwendungszweck3', 'text': 'Buchungstext3 Auftraggeber3 Verwendungszweck3', 'vdate': '03.03.2017'},
             {'amount': -4000.0, 'bdate': '04.03.2017', 'customerreferenz': 'Kundenreferenz4', 'date': '04.03.2017', 'mandatereference': 'Mandatsreferenz4', 'peer': 'Auftraggeber4', 'peeraccount': 'Kontonummer4', 'peerbic': 'BLZ4', 'peerid': 'GID4', 'postingtext': 'Buchungstext4', 'reasonforpayment': 'Verwendungszweck4', 'text': 'Buchungstext4 Auftraggeber4 Verwendungszweck4', 'vdate': '04.03.2017'}
            ]

        self.assertEqual(result, self.dkb._parse_account_transactions(csv))

    def test_034_parse_no_account_tr(self, _mock_browser):
        """ test DKBRobo.get_account_transactions for one page only """
        csv = read_file(self.dir_path + '/mocks/test_parse_no_account_tr.csv')
        self.assertEqual(self.dkb._parse_account_transactions(csv), [])

    def test_035_parse_dkb_cc_tr(self, _mock_browser):
        """ test DKBRobo._parse_cc_transactions """
        csv = read_file(self.dir_path + '/mocks/test_parse_dkb_cc_tr.csv')
        self.assertEqual(self.dkb._parse_cc_transactions(csv), [{'amount': -100.00,
                                                                'amount_original': '-110',
                                                                'bdate': '01.03.2017',
                                                                'show_date': '01.03.2017',
                                                                'store_date': '01.03.2017',
                                                                'text': 'AAA',
                                                                'vdate': '01.03.2017'},
                                                               {'amount': -200.00,
                                                                'amount_original': '-210',
                                                                'bdate': '02.03.2017',
                                                                'show_date': '02.03.2017',
                                                                'store_date': '02.03.2017',
                                                                'text': 'BBB',
                                                                'vdate': '02.03.2017'},
                                                               {'amount': -300.00,
                                                                'amount_original': '-310',
                                                                'bdate': '03.03.2017',
                                                                'show_date': '03.03.2017',
                                                                'store_date': '03.03.2017',
                                                                'text': 'CCC',
                                                                'vdate': '03.03.2017'}])

    def test_036_parse_no_cc_tr(self, _mock_browser):
        """ test DKBRobo._parse_cc_transactions """
        csv = read_file(self.dir_path + '/mocks/test_parse_no_cc_tr.csv')
        self.assertEqual(self.dkb._parse_cc_transactions(csv), [])

    @patch('time.time')
    def test_037_validate_dates(self, mock_time, mock_browser):
        """ test validate dates with correct data """
        date_from = '01.12.2021'
        date_to = '10.12.2021'
        mock_time.return_value = 1639232579
        self.assertEqual(('01.12.2021', '10.12.2021'), self.validate_dates(self.logger, date_from, date_to))

    @patch('time.time')
    def test_038_validate_dates(self, mock_time, mock_browser):
        """ test validate dates date_from to be corrected """
        date_from = '12.12.2021'
        date_to = '11.12.2021'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('11.12.2021', '11.12.2021'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 11.12.2021', lcm.output)

    @patch('time.time')
    def test_039_validate_dates(self, mock_time, mock_browser):
        """ test validate dates date_to to be corrected """
        date_from = '01.12.2021'
        date_to = '12.12.2021'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('01.12.2021', '11.12.2021'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_to to 11.12.2021', lcm.output)

    @patch('time.time')
    def test_040_validate_dates(self, mock_time, mock_browser):
        """ test validate dates date_from to be corrected past past > 3 years """
        date_from = '01.01.1980'
        date_to = '12.12.2021'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('12.12.2018', '11.12.2021'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 12.12.2018', lcm.output)

    @patch('time.time')
    def test_041_validate_dates(self, mock_time, mock_browser):
        """ test validate dates date_from to be corrected past past > 3 years """
        date_from = '01.01.1980'
        date_to = '02.01.1980'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('12.12.2018', '12.12.2018'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 12.12.2018', lcm.output)
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_to to 12.12.2018', lcm.output)

    @patch('random.choice')
    def test_042_generate_random_string(self, mock_rc, mock_browser):
        mock_rc.return_value = '1a'
        length = 5
        self.assertEqual('1a1a1a1a1a', self.generate_random_string(length))

    @patch('random.choice')
    def test_043_generate_random_string(self, mock_rc, mock_browser):
        mock_rc.return_value = '1a'
        length = 10
        self.assertEqual('1a1a1a1a1a1a1a1a1a1a', self.generate_random_string(length))

    def test_044_get_financial_statement(self, mock_browser):
        """ get financial statement """
        html = '<html><head>header</head><body>body</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertEqual('<html><head></head><body>headerbody</body></html>', str(self.dkb._get_financial_statement()))

    def test_045_get_financial_statement(self, mock_browser):
        """ get financial statement with tan_insert """
        html = '<html><head>header</head><body>body</body></html>'
        self.dkb.tan_insert = True
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertEqual('<html><head></head><body>headerbody</body></html>', str(self.dkb._get_financial_statement()))

    @patch('dkb_robo.DKBRobo._login')
    def test_046__enter(self, mock_login, mock_browser):
        """ test enter """
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_login.called)

    @patch('dkb_robo.DKBRobo._login')
    def test_047__enter(self, mock_login, _unused):
        """ test enter """
        self.dkb.dkb_br = None
        self.assertTrue(self.dkb.__enter__())
        self.assertTrue(mock_login.called)

    @patch('dkb_robo.DKBRobo._logout')
    def test_048__exit(self, mock_logout, _ununsed):
        """ test enter """
        self.assertFalse(self.dkb.__exit__())
        self.assertTrue(mock_logout.called)

    @patch('dkb_robo.DKBRobo._parse_account_transactions')
    def test_049_get_account_transactions(self, mock_parse, mock_browser):
        """ test get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.dkb.get_account_transactions('url', 'date_from', 'date_to'))

    @patch('dkb_robo.DKBRobo._parse_account_transactions')
    def test_050_get_account_transactions(self, mock_parse, mock_browser):
        """ test get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.dkb.get_account_transactions('url', 'date_from', 'date_to', transaction_type='reserved'))

    @patch('dkb_robo.DKBRobo._parse_cc_transactions')
    def test_051_get_cc_transactions(self, mock_parse, mock_browser):
        """ test get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.dkb.get_creditcard_transactions('url', 'date_from', 'date_to'))

    @patch('dkb_robo.DKBRobo._parse_cc_transactions')
    def test_052_get_cc_transactions(self, mock_parse, mock_browser):
        """ test get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.dkb.get_creditcard_transactions('url', 'date_from', 'date_to', transaction_type='reserved'))

    def test_053_logout(self, _unused):
        """ test logout """
        self.assertFalse(self.dkb._logout())

    @patch('logging.getLogger')
    def test_054_logger_setup(self, mock_logging, _unused):
        """ test logger setup with debug false """
        mock_logging.return_value = 'logging'
        self.assertEqual('logging', self.logger_setup(False))

    @patch('logging.getLogger')
    def test_055_logger_setup(self, mock_logging, _unused):
        """ test logger setup with debug true """
        mock_logging.return_value = 'logging'
        self.assertEqual('logging', self.logger_setup(True))

    def test_056_update_downloadstate(self, _unused):
        """ test update downloadstats """
        url = 'https://www.dkb.de/DkbTransactionBanking/content/mailbox/MessageList/%24{1}.xhtml?$event=updateDownloadState&row=1'
        self.assertFalse(self.dkb._update_downloadstate(link_name='link_name', url=url))

    def test_057_update_downloadstate(self, _unused):
        """ test update downloadstats """
        url = 'https://www.dkb.de/DkbTransactionBanking/content/mailbox/MessageList/%24{1}.xhtml?$event=updateDownloadState&row=1'
        self.assertFalse(self.dkb._update_downloadstate(link_name='Kontoauszüge', url=url))

    @patch('dkb_robo.dkb_robo.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_058_get_document(self, mock_exists, mock_makedir, mock_rand, _unused):
        """ test get_document create path """
        mock_exists.return_value = False
        mock_rand.return_value = 'mock_rand'
        self.assertEqual((None, 'path/mock_rand.pdf', []), self.dkb._get_document('path', 'url', []))
        self.assertTrue(mock_makedir.called)
        self.assertTrue(mock_rand.called)

    @patch('dkb_robo.dkb_robo.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_059_get_document(self, mock_exists, mock_makedir, mock_rand, _unused):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_rand.return_value = 'mock_rand'
        self.assertEqual((None, 'path/mock_rand.pdf', []), self.dkb._get_document('path', 'url', []))
        self.assertFalse(mock_makedir.called)
        self.assertTrue(mock_rand.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('re.findall')
    @patch('dkb_robo.dkb_robo.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_060_get_document(self, mock_exists, mock_makedir, mock_rand, mock_re, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_rand.return_value = 'mock_rand'
        mock_browser.open.return_value.headers = {'Content-Disposition': ['foo', 'bar']}
        mock_browser.open.return_value.status_code = 200
        mock_re.return_value = ['mock_re.pdf', 'mock_re2.pdf']
        self.assertEqual((200, 'path/mock_re.pdf', ['mock_re.pdf']), self.dkb._get_document('path', 'url', []))
        self.assertFalse(mock_makedir.called)

    @patch('dkb_robo.dkb_robo.datetime', Mock(now=lambda: date(2022, 9, 30)))
    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('re.findall')
    @patch('dkb_robo.dkb_robo.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_061_get_document(self, mock_exists, mock_makedir, mock_rand, mock_re, mock_browser):
        """ test get_document override """
        mock_exists.return_value = True
        mock_rand.return_value = 'mock_rand'
        mock_browser.open.return_value.headers = {'Content-Disposition': ['foo', 'bar']}
        mock_browser.open.return_value.status_code = 200
        mock_re.return_value = ['mock_re.pdf', 'mock_re2.pdf']
        self.assertEqual((200, 'path/2022-09-30-00-00-00-mock_re.pdf', ['mock_re.pdf', '2022-09-30-00-00-00-mock_re.pdf']), self.dkb._get_document('path', 'url', ['mock_re.pdf']))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_062_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers =  {'Content-Disposition': 'inline; filename=Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf', ['Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf']), self.dkb._get_document('path', 'url', []))
        self.assertFalse(mock_makedir.called)

    @patch('dkb_robo.dkb_robo.datetime', Mock(now=lambda: date(2022, 9, 30)))
    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_063_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers =  {'Content-Disposition': 'inline; filename=Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/2022-09-30-00-00-00-Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf', ['Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf', '2022-09-30-00-00-00-Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf']), self.dkb._get_document('path', 'url', ['Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf']))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_064_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers =  {'Content-Disposition': 'inline; filename=foo.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/foo.pdf', ['foo.pdf']), self.dkb._get_document('path', 'url', []))
        self.assertFalse(mock_makedir.called)

    @patch('dkb_robo.dkb_robo.datetime', Mock(now=lambda: date(2022, 9, 30)))
    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_065_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers =  {'Content-Disposition': 'inline; filename=foo.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/2022-09-30-00-00-00-foo.pdf', ['foo.pdf', '2022-09-30-00-00-00-foo.pdf']), self.dkb._get_document('path', 'url', ['foo.pdf']))
        self.assertFalse(mock_makedir.called)

    @patch('builtins.input')
    def test_066_ctan_check(self, mock_input, mock_browser):
        """ test ctan_check """
        mock_input.return_value = 'tan'
        html = '<html><head>header</head><body><ol><li>li</li></ol></body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertTrue(self.dkb._ctan_check('soup'))

    @patch('builtins.input')
    def test_067_ctan_check(self, mock_input, mock_browser):
        """ test ctan_check """
        mock_input.return_value = 'tan'
        html = '<html><head>header</head><body>body</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertTrue(self.dkb._ctan_check('soup'))

    @patch('builtins.input')
    def test_068_ctan_check(self, mock_input, mock_browser):
        """ test ctan_check wrong tan """
        mock_input.return_value = 'tan'
        html = '<html><head>header</head><body><div class="clearfix module text errorMessage">div</div></body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        with self.assertRaises(Exception) as err:
             self.dkb._ctan_check('soup')
        self.assertEqual('Login failed due to wrong TAN', str(err.exception))

    @patch('sys.exit')
    @patch('builtins.input')
    def test_069_ctan_check(self, mock_input, mock_sexit, mock_browser):
        """ test ctan_check """
        mock_input.return_value = 'tan'
        html = '<html><head>header</head><body>body</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_browser.select_form.side_effect =  [Exception('exc1'), Exception('exc2'), 'foo']
        self.assertTrue(self.dkb._ctan_check('soup'))

    @patch('dkb_robo.DKBRobo._check_confirmation')
    def test_070_login_confirm(self, mock_confirm, mock_browser, ):
        """ test login confirmed check_cofirmation returns true """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_confirm.return_value = True
        self.assertTrue(self.dkb._login_confirm())

    @patch('time.sleep', return_value=None)
    @patch('dkb_robo.DKBRobo._check_confirmation')
    def test_071_login_confirm(self, mock_confirm, mock_sleep, mock_browser):
        """ test login confirmed check_cofirmation returns multiple false but then true """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_confirm.side_effect = [False, False, False, True]
        self.assertTrue(self.dkb._login_confirm())

    @patch('time.sleep', return_value=None)
    @patch('dkb_robo.DKBRobo._check_confirmation')
    def test_072_login_confirm(self, mock_confirm, mock_sleep, mock_browser):
        """ test login confirmed  """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_confirm.return_value = False
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb._login_confirm())
        self.assertEqual('No session confirmation after 120 polls', str(err.exception))

    @patch('dkb_robo.dkb_robo.generate_random_string')
    def test_073_login_confirm(self, mock_rand, mock_browser):
        """ test login confirmed - exception when getting the token """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_browser.get_current_page.side_effect =  Exception('exc')
        with self.assertRaises(Exception) as err:
            self.assertTrue(self.dkb._login_confirm())
        self.assertEqual('Error while getting the confirmation page', str(err.exception))

    def test_074_check_confirmation(self, _unused):
        """ test confirmation """
        result = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._check_confirmation(result, 1)
        self.assertEqual('Error during session confirmation', str(err.exception))

    def test_075_check_confirmation(self, _unused):
        """ test confirmation state expired"""
        result = {'state': 'EXPIRED'}
        with self.assertRaises(Exception) as err:
            self.dkb._check_confirmation(result, 1)
        self.assertEqual('Session expired', str(err.exception))

    def test_076_check_confirmation(self, _unused):
        """ test confirmation state processed"""
        result = {'state': 'PROCESSED'}
        self.assertTrue(self.dkb._check_confirmation(result, 1))

    def test_077_check_confirmation(self, _unused):
        """ test confirmation state unknown """
        result = {'state': 'UNK'}
        self.assertFalse(self.dkb._check_confirmation(result, 1))

    def test_078_check_confirmation(self, _unused):
        """ test confirmation guiState expired"""
        result = {'guiState': 'EXPIRED'}
        with self.assertRaises(Exception) as err:
            self.dkb._check_confirmation(result, 1)
        self.assertEqual('Session expired', str(err.exception))

    def test_079_check_confirmation(self, _unused):
        """ test confirmation guiState MAP_TO_EXIT"""
        result = {'guiState': 'MAP_TO_EXIT'}
        self.assertTrue(self.dkb._check_confirmation(result, 1))

    def test_080_check_confirmation(self, _unused):
        """ test confirmation guiState unknown """
        result = {'guiState': 'UNK'}
        self.assertFalse(self.dkb._check_confirmation(result, 1))

    def test_081_parse_depot_status_tr(self, _mock_browser):
        """ test DKBRobo._parse_cc_transactions """
        csv = read_file(self.dir_path + '/mocks/test_parse_depot.csv')
        result = [{'shares': 10.0, 'shares_unit': 'cnt1', 'isin_wkn': 'WKN1', 'text': 'Bezeichnung1', 'price': 11.0, 'win_loss': '', 'win_loss_currency': '', 'aquisition_cost': '', 'aquisition_cost_currency': '', 'dev_price': '', 'price_euro': 1110.1, 'availability': 'Frei'}, {'shares': 20.0, 'shares_unit': 'cnt2', 'isin_wkn': 'WKN2', 'text': 'Bezeichnung2', 'price': 12.0, 'win_loss': '', 'win_loss_currency': '', 'aquisition_cost': '', 'aquisition_cost_currency': '', 'dev_price': '', 'price_euro': 2220.2, 'availability': 'Frei'}]
        self.assertEqual(result, self.dkb._parse_depot_status(csv))

    def test_082_string2float(self, _unused):
        """ test string2float """
        value = 1000
        self.assertEqual(1000.0, self.string2float(value))

    def test_083_string2float(self, _unused):
        """ test string2float """
        value = 1000.0
        self.assertEqual(1000.0, self.string2float(value))

    def test_084_string2float(self, _unused):
        """ test string2float """
        value = '1.000,00'
        self.assertEqual(1000.0, self.string2float(value))

    def test_085_string2float(self, _unused):
        """ test string2float """
        value = '1000,00'
        self.assertEqual(1000.0, self.string2float(value))

    def test_086_string2float(self, _unused):
        """ test string2float """
        value = '1.000'
        self.assertEqual(1000.0, self.string2float(value))

    def test_087_string2float(self, _unused):
        """ test string2float """
        value = '1.000,23'
        self.assertEqual(1000.23, self.string2float(value))

    def test_088_string2float(self, _unused):
        """ test string2float """
        value = '1000,23'
        self.assertEqual(1000.23, self.string2float(value))

    def test_089_string2float(self, _unused):
        """ test string2float """
        value = 1000.23
        self.assertEqual(1000.23, self.string2float(value))

    def test_090_string2float(self, _unused):
        """ test string2float """
        value = '-1.000'
        self.assertEqual(-1000.0, self.string2float(value))

    def test_091_string2float(self, _unused):
        """ test string2float """
        value = '-1.000,23'
        self.assertEqual(-1000.23, self.string2float(value))

    def test_092_string2float(self, _unused):
        """ test string2float """
        value = '-1000,23'
        self.assertEqual(-1000.23, self.string2float(value))

    def test_093_string2float(self, _unused):
        """ test string2float """
        value = -1000.23
        self.assertEqual(-1000.23, self.string2float(value))

    @patch('dkb_robo.DKBRobo._parse_depot_status')
    def test_094_get_depot_status(self, mock_pds, _unused):
        """ test get depot status """
        mock_pds.return_value = 'mock_pds'
        self.assertEqual('mock_pds', self.dkb.get_depot_status('url', 'fdate', 'tdate', 'booked'))

if __name__ == '__main__':

    unittest.main()
