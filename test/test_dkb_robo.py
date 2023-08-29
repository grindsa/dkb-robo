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
import io

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

def my_side_effect(*args, **kwargs):
    return [200, args[1], [args[4]]]

@patch('dkb_robo.DKBRobo.dkb_br')
class TestDKBRobo(unittest.TestCase):
    """ test class """

    maxDiff = None

    def setUp(self):
        self.dkb = DKBRobo()
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        from dkb_robo.dkb_robo import validate_dates, generate_random_string, logger_setup, string2float, convert_date_format, enforce_date_format
        self.validate_dates = validate_dates
        self.string2float = string2float
        self.generate_random_string = generate_random_string
        self.logger_setup = logger_setup
        self.convert_date_format = convert_date_format
        self.enforce_date_format = enforce_date_format
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

    def test_003_get_cc_limit(self, mock_browser):
        """ test DKBRobo.get_credit_limits() no limits """
        # html = read_file(self.dir_path + '/mocks/konto-kreditkarten-limits-exception.html')
        html = '<html><body>fooo</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {}
        self.assertEqual(e_result, self.dkb.get_credit_limits())

    def test_004_get_exo_single(self, mock_browser):
        """ test DKBRobo.get_exemption_order() method for a single exemption order """
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0, 'amount': 1000.0, 'used': 0.0, 'description': u'Gemeinsam mit Firstname Familyname', 'validity': u'01.01.2016 unbefristet'}}
        self.assertEqual(self.dkb.get_exemption_order(), e_result)

    def test_005_get_exo_single_nobr(self, mock_browser):
        """ test DKBRobo.get_exemption_order() method for a single exemption order without line-breaks"""
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag-nobr.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0, 'amount': 1000.0, 'used': 0.0, 'description': u'Gemeinsam mit Firstname Familyname', 'validity': u'01.01.2016 unbefristet'}}
        self.assertEqual(self.dkb.get_exemption_order(), e_result)

    def test_006_get_exo_multiple(self, mock_browser):
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

    def test_007_get_exo_single(self, mock_browser):
        """ test DKBRobo.get_exemption_order() method try throws exception """
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag-indexerror.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1:{}}
        # with self.assertRaises(Exception) as err:
        self.assertEqual(self.dkb.get_exemption_order(), e_result)
        # print(err.exception)
        # self.assertEqual("foo could not convert string to float: 'aaa'", str(err.exception))

    def test_008_new_instance(self, _unused):
        """ test DKBRobo._new_instance() method """
        self.assertIn('mechanicalsoup.stateful_browser.StatefulBrowser object at', str(self.dkb._new_instance()))

    def test_009_new_instance(self, _unused):
        """ test DKBRobo._new_instance() method with proxies """
        self.dkb.proxies = 'proxies'
        self.assertIn('mechanicalsoup.stateful_browser.StatefulBrowser object at', str(self.dkb._new_instance()))
        self.assertEqual('proxies', self.dkb.dkb_br.session.proxies)

    def test_010_new_instance(self, _unused):
        """ test DKBRobo._new_instance() method with clientcookies """
        cookieobj = Mock()
        cookieobj.value = 'value'
        cookieobj.name = 'name'
        self.assertIn('mechanicalsoup.stateful_browser.StatefulBrowser object at', str(self.dkb._new_instance([cookieobj])))

    def test_011_get_points(self, mock_browser):
        """ test DKBRobo.get_points() method """
        html = read_file(self.dir_path + '/mocks/dkb_punkte.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'DKB-Punkte': 100000, u'davon verfallen zum  31.12.2017': 90000}
        self.assertEqual(self.dkb.get_points(), e_result)

    def test_012_get_so_multiple(self, mock_browser):
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
    def test_013_legacy_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
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
        self.assertEqual(self.dkb._legacy_login(), None)
        self.assertTrue(mock_confirm.called)
        self.assertFalse(mock_ctan.called)
        self.assertFalse(mock_fs.called)
        self.assertFalse(mock_pov.called)

    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._login_confirm')
    @patch('dkb_robo.DKBRobo._ctan_check')
    @patch('dkb_robo.DKBRobo._new_instance')
    def test_014_legacy_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
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
        self.assertEqual(self.dkb._legacy_login(), None)
        self.assertTrue(mock_confirm.called)
        self.assertFalse(mock_ctan.called)
        self.assertTrue(mock_fs.called)
        self.assertTrue(mock_pov.called)

    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._login_confirm')
    @patch('dkb_robo.DKBRobo._ctan_check')
    @patch('dkb_robo.DKBRobo._new_instance')
    def test_015_legacy_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
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
        self.assertEqual(self.dkb._legacy_login(), None)
        self.assertFalse(mock_confirm.called)
        self.assertTrue(mock_ctan.called)
        self.assertFalse(mock_fs.called)
        self.assertFalse(mock_pov.called)

    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._login_confirm')
    @patch('dkb_robo.DKBRobo._ctan_check')
    @patch('dkb_robo.DKBRobo._new_instance')
    def test_016_legacy_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
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
        self.assertEqual(self.dkb._legacy_login(), None)
        self.assertFalse(mock_confirm.called)
        self.assertTrue(mock_ctan.called)
        self.assertTrue(mock_fs.called)
        self.assertTrue(mock_pov.called)

    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._login_confirm')
    @patch('dkb_robo.DKBRobo._ctan_check')
    @patch('dkb_robo.DKBRobo._new_instance')
    def test_017_legacy_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
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
            self.assertEqual(self.dkb._legacy_login(), None)
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
    def test_018_legacy_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test DKBRobo._login() login failed """
        mock_browser.select_form.side_effect = LinkNotFoundError
        mock_ctan.return_value = True
        mock_confirm.return_value = False
        mock_instance.return_value = mock_browser
        mock_pov.return_value = '_parse_overview'
        mock_fs.return_value = 'mock_fs'
        self.dkb.tan_insert = True
        with self.assertRaises(Exception) as err:
            self.assertEqual(self.dkb._legacy_login(), None)
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
    def test_019_legacy_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
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
        self.assertEqual(self.dkb._legacy_login(), None)
        self.assertFalse(mock_confirm.called)
        self.assertTrue(mock_ctan.called)
        self.assertTrue(mock_fs.called)
        self.assertTrue(mock_pov.called)

    def test_020_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() method """
        html = read_file(self.dir_path + '/mocks/finanzstatus.html')
        e_result = {0: {'account': u'XY99 1111 1111 0000 1111 99',
                        'amount': 1367.82,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=0',
                        'name': u'hauptkonto',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=0',
                        'type': 'account'},
                    1: {'account': u'9999********1111',
                        'amount': 9613.31,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=0',
                        'name': u'first visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=0',
                        'type': 'creditcard'},
                    2: {'account': u'9999********8888',
                        'amount': -260.42,
                        'date': u'26.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=0',
                        'name': u'MilesnMoreMaster',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=0',
                        'type': 'creditcard'},
                    3: {'account': u'9999********2222',
                        'amount': 515.52,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=1',
                        'name': u'second visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=1',
                        'type': 'creditcard'},
                    4: {'account': u'XY99 1111 1111 2155 2788 99',
                        'amount': 588.37,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=1',
                        'name': u'zweitkonto',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=1',
                        'type': 'account'},
                    5: {'account': u'9999********3333',
                        'amount': 515.52,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=1',
                        'name': u'3rd visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=1',
                        'type': 'creditcard'},
                    6: {'account': u'XY99 3333 1111 0000 3333 99',
                        'amount': -334.34,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=3&group=1',
                        'name': u'3rd acc',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=3&group=1',
                        'type': 'account'}}
        self.assertEqual(self.dkb._parse_overview(BeautifulSoup(html, 'html5lib')), e_result)

    def test_021_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() method """
        html = read_file(self.dir_path + '/mocks/finanzstatus-error1.html')
        e_result = {0: {'account': u'XY99 1111 1111 0000 1111 99',
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=0',
                        'name': u'hauptkonto',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=0',
                        'type': 'account'},
                    1: {'account': u'9999********1111',
                        'amount': 9613.31,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=0',
                        'name': u'first visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=0',
                        'type': 'creditcard'},
                    2: {'account': u'9999********8888',
                        'amount': -260.42,
                        'date': u'26.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=0',
                        'name': u'MilesnMoreMaster',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=0',
                        'type': 'creditcard'},
                    3: {'account': u'9999********2222',
                        'amount': 515.52,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=1',
                        'name': u'second visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=1',
                        'type': 'creditcard'},
                    4: {'account': u'XY99 1111 1111 2155 2788 99',
                        'amount': 588.37,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=1',
                        'name': u'zweitkonto',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=1',
                        'type': 'account'},
                    5: {'account': u'9999********3333',
                        'amount': 515.52,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=1',
                        'name': u'3rd visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=1',
                        'type': 'creditcard'},
                    6: {'account': u'XY99 3333 1111 0000 3333 99',
                        'amount': -334.34,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=3&group=1',
                        'name': u'3rd acc',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=3&group=1',
                        'type': 'account'}}
        self.assertEqual(self.dkb._parse_overview(BeautifulSoup(html, 'html5lib')), e_result)

    def test_022_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() exception detail link"""
        html = read_file(self.dir_path + '/mocks/finanzstatus-error2.html')
        e_result = {0: {'account': u'XY99 1111 1111 0000 1111 99',
                        'amount': 1367.82,
                        'date': u'27.04.2018',
                        'name': u'hauptkonto',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=0',
                        'type': 'account'},
                    1: {'account': u'9999********1111',
                        'amount': 9613.31,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=0',
                        'name': u'first visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=0',
                        'type': 'creditcard'},
                    2: {'account': u'9999********8888',
                        'amount': -260.42,
                        'date': u'26.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=0',
                        'name': u'MilesnMoreMaster',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=0',
                        'type': 'creditcard'},
                    3: {'account': u'9999********2222',
                        'amount': 515.52,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=1',
                        'name': u'second visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=1',
                        'type': 'creditcard'},
                    4: {'account': u'XY99 1111 1111 2155 2788 99',
                        'amount': 588.37,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=1',
                        'name': u'zweitkonto',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=1',
                        'type': 'account'},
                    5: {'account': u'9999********3333',
                        'amount': 515.52,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=1',
                        'name': u'3rd visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=1',
                        'type': 'creditcard'},
                    6: {'account': u'XY99 3333 1111 0000 3333 99',
                        'amount': -334.34,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=3&group=1',
                        'name': u'3rd acc',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=3&group=1',
                        'type': 'account'}}
        self.assertEqual(e_result, self.dkb._parse_overview(BeautifulSoup(html, 'html5lib')))

    def test_023_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() exception depot """
        html = read_file(self.dir_path + '/mocks/finanzstatus-error3.html')
        e_result = {0: {'account': u'XY99 1111 1111 0000 1111 99',
                        'amount': 1367.82,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=0',
                        'name': u'hauptkonto',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=0',
                        'type': 'account'},
                    1: {'account': u'9999********1111',
                        'amount': 9613.31,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=0',
                        'name': u'first visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=0',
                        'type': 'creditcard'},
                    2: {'account': u'9999********8888',
                        'amount': -260.42,
                        'date': u'26.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=0',
                        'name': u'MilesnMoreMaster',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=0',
                        'type': 'creditcard'},
                    3: {'account': u'9999********2222',
                        'amount': 515.52,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=1',
                        'name': u'second visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=1',
                        'type': 'creditcard'},
                    4: {'account': u'XY99 1111 1111 2155 2788 99',
                        'amount': 588.37,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=1',
                        'name': u'zweitkonto',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=1',
                        'type': 'account'},
                    5: {'account': u'9999********3333',
                        'amount': 515.52,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=1',
                        'name': u'3rd visa',
                        'transactions': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=1',
                        'type': 'creditcard'},
                    6: {'account': u'XY99 3333 1111 0000 3333 99',
                        'amount': -334.34,
                        'date': u'27.04.2018',
                        'details': u'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=3&group=1',
                        'name': u'3rd acc',
                        'type': 'depot'}}
        self.assertEqual(e_result, self.dkb._parse_overview(BeautifulSoup(html, 'html5lib')))

    def test_024_parse_overview_mbank(self, _unused):
        """ test DKBRobo._parse_overview() method for accounts from other banks"""
        html = read_file(self.dir_path + '/mocks/finanzstatus-mbank.html')
        e_result = {0: {'account': u'1111********1111',
                        'name': u'credit-card-1',
                        'transactions': u'https://www.ib.dkb.de/tcc-1',
                        'amount': 1000.0,
                        'details': u'https://www.ib.dkb.de/dcc-1',
                        'date': u'01.03.2017',
                        'type': 'creditcard'},
                    1: {'account': u'1111********1112',
                        'name': u'credit-card-2',
                        'transactions': u'https://www.ib.dkb.de/tcc-2',
                        'amount': 2000.0,
                        'details': u'https://www.ib.dkb.de/dcc-2',
                        'date': u'02.03.2017',
                        'type': 'creditcard'},
                    2: {'account': u'DE11 1111 1111 1111 1111 11',
                        'name': u'checking-account-1',
                        'transactions': u'https://www.ib.dkb.de/tac-1',
                        'amount': 1000.0,
                        'details': u'https://www.ib.dkb.de/banking/dac-1',
                        'date': u'03.03.2017',
                        'type': 'account'},
                    3: {'account': u'DE11 1111 1111 1111 1111 12',
                        'name': u'checking-account-2',
                        'transactions': u'https://www.ib.dkb.de/tac-2',
                        'amount': 2000.0,
                        'details': u'https://www.ib.dkb.de/banking/dac-2',
                        'date': u'04.03.2017',
                        'type': 'account'},
                    4: {'account': u'1111111',
                        'name': u'Depot-1',
                        'transactions': u'https://www.ib.dkb.de/tdepot-1',
                        'amount': 5000.0,
                        'details': u'https://www.ib.dkb.de/ddepot-1',
                        'date': u'06.03.2017',
                        'type': 'depot'},
                    5: {'account': u'1111112',
                        'name': u'Depot-2',
                        'transactions': u'https://www.ib.dkb.de/tdepot-2',
                        'amount': 6000.0,
                        'details': u'https://www.ib.dkb.de/ddepot-2',
                        'date': u'06.03.2017',
                        'type': 'depot'}}
        self.assertEqual(self.dkb._parse_overview(BeautifulSoup(html, 'html5lib')), e_result)

    def test_025_get_document_links(self, mock_browser):
        """ test DKBRobo._get_document_links() method """
        html = read_file(self.dir_path + '/mocks/doclinks.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'Kontoauszug Nr. 003_2017 zu Konto 87654321': u'https://www.ib.dkb.de/doc-2',
                    u'Kontoauszug Nr. 003_2017 zu Konto 12345678': u'https://www.ib.dkb.de/doc-1'}
        self.assertEqual(self.dkb._get_document_links('http://foo.bar/foo'), e_result)

    @patch('dkb_robo.DKBRobo._update_downloadstate')
    @patch('dkb_robo.DKBRobo._get_document')
    def test_026_get_document_links(self, mock_doc, mock_updow, mock_browser):
        """ test DKBRobo._get_document_links() method """
        html = read_file(self.dir_path + '/mocks/doclinks-2.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doc.return_value=(200, 'fname', ['foo'])
        e_result = {'Kontoauszug Nr. 003_2017 zu Konto 12345678': {'rcode': 200, 'link': 'https://www.ib.dkb.de/doc-1', 'fname': 'fname'}, 'Kontoauszug Nr. 003_2017 zu Konto 87654321': {'rcode': 200, 'link': 'https://www.ib.dkb.de/doc-2', 'fname': 'fname'}}
        self.assertEqual(e_result, self.dkb._get_document_links('http://foo.bar/foo', path='path'))
        self.assertTrue(mock_updow.called)

    @patch('dkb_robo.DKBRobo._update_downloadstate')
    @patch('dkb_robo.DKBRobo._get_document')
    def test_027_get_document_links(self, mock_doc, mock_updow, mock_browser):
        """ test DKBRobo._get_document_links() method """
        html1 = read_file(self.dir_path + '/mocks/doclinks-3.html')
        html2 = read_file(self.dir_path + '/mocks/doclinks-2.html')
        mock_browser.get_current_page.side_effect = [BeautifulSoup(html1, 'html5lib'), BeautifulSoup(html2, 'html5lib')]
        mock_browser.open.return_value = True
        mock_doc.return_value=(None, 'fname', ['foo'])
        e_result = {u'Kontoauszug Nr. 003_2017 zu Konto 23456789': 'https://www.ib.dkb.de/doc-1',
                    u'Kontoauszug Nr. 003_2017 zu Konto 12345678': u'https://www.ib.dkb.de/doc-1',
                    u'Kontoauszug Nr. 003_2017 zu Konto 87654321': 'https://www.ib.dkb.de/doc-2',
                    u'Kontoauszug Nr. 003_2017 zu Konto 98765432': 'https://www.ib.dkb.de/doc-2'}
        self.assertEqual(e_result, self.dkb._get_document_links('http://foo.bar/foo', path='path'))
        self.assertFalse(mock_updow.called)

    @patch('dkb_robo.DKBRobo._update_downloadstate')
    @patch('dkb_robo.DKBRobo._get_document')
    def test_028_get_document_links(self, mock_doc, mock_updow, mock_browser):
        """ test DKBRobo._get_document_links() method no html return """
        mock_browser.get_current_page.return_value = None
        mock_browser.open.return_value = True
        mock_doc.return_value=(None, 'fname', ['foo'])
        e_result = {}
        self.assertEqual(e_result, self.dkb._get_document_links('http://foo.bar/foo', path='path'))
        self.assertFalse(mock_updow.called)


    @patch('dkb_robo.DKBRobo._update_downloadstate')
    @patch('dkb_robo.DKBRobo._get_document')
    def test_029_get_document_links(self, mock_doc, mock_updow, mock_browser):
        """ test DKBRobo._get_document_links() method  wrong html return """
        html = '<html><body>fooo</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_browser.open.return_value = True
        mock_doc.return_value=(None, 'fname', ['foo'])
        e_result = {}
        self.assertEqual(e_result, self.dkb._get_document_links('http://foo.bar/foo', path='path'))
        self.assertFalse(mock_updow.called)

    @patch('dkb_robo.DKBRobo._get_document_links')
    def test_030_scan_postbox(self, mock_doclinks, mock_browser):
        """ test DKBRobo.scan_postbox() method """
        html = read_file(self.dir_path + '/mocks/postbox.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doclinks.return_value = {}
        e_result = {u'Kreditkartenabrechnungen':
                        {'documents': {},
                         'name': u'Kreditkartenabrechnungen',
                         'details': u'https://www.ib.dkb.de/banking/postfach/Kreditkartenabrechnungen'},
                    u'Mitteilungen':
                        {'documents': {},
                         'name': u'Mitteilungen',
                         'details': u'https://www.ib.dkb.de/banking/postfach/Mitteilungen'},
                    u'Vertragsinformationen':
                        {'documents': {},
                         'name': u'Vertragsinformationen',
                         'details': u'https://www.ib.dkb.de/banking/postfach/Vertragsinformationen'}
                   }
        self.assertEqual(self.dkb.scan_postbox(), e_result)

    @patch('dkb_robo.DKBRobo._get_document_links')
    def test_031_scan_postbox(self, mock_doclinks, mock_browser):
        """ test DKBRobo.scan_postbox() method """
        html = read_file(self.dir_path + '/mocks/postbox.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doclinks.return_value = {}
        e_result = {u'Kreditkartenabrechnungen':
                        {'documents': {},
                         'name': u'Kreditkartenabrechnungen',
                         'details': u'https://www.ib.dkb.de/banking/postfach/Kreditkartenabrechnungen'},
                    u'Mitteilungen':
                        {'documents': {},
                         'name': u'Mitteilungen',
                         'details': u'https://www.ib.dkb.de/banking/postfach/Mitteilungen'},
                    u'Vertragsinformationen':
                        {'documents': {},
                         'name': u'Vertragsinformationen',
                         'details': u'https://www.ib.dkb.de/banking/postfach/Vertragsinformationen'}
                   }
        self.assertEqual(self.dkb.scan_postbox(path='path'), e_result)

    @patch('dkb_robo.DKBRobo._get_document_links')
    def test_032_scan_postbox(self, mock_doclinks, mock_browser):
        """ test DKBRobo.scan_postbox() method """
        html = read_file(self.dir_path + '/mocks/postbox-2.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doclinks.return_value = {}
        e_result = {u'Kreditkartenabrechnungen':
                        {'documents': {},
                         'name': u'Kreditkartenabrechnungen',
                         'details': u'https://www.ib.dkb.de/banking/postfach/Kreditkartenabrechnungen'},
                    u'Mitteilungen':
                        {'documents': {},
                         'name': u'Mitteilungen',
                         'details': u'https://www.ib.dkb.de/banking/postfach/Mitteilungen'},
                    u'Vertragsinformationen':
                        {'documents': {},
                         'name': u'Vertragsinformationen',
                         'details': u'https://www.ib.dkb.de/banking/postfach/Vertragsinformationen'}
                   }
        self.assertEqual(self.dkb.scan_postbox(archive=True), e_result)

    def test_033_get_tr_invalid(self, _unused):
        """ test DKBRobo._legacy_get_transactions() method with an invalid account type"""
        self.assertEqual(self.dkb._legacy_get_transactions('url', 'foo', '01.03.2017', '02.03.2017'), [])

    @patch('dkb_robo.DKBRobo._legacy_get_creditcard_transactions')
    def test_034_get_tr_cc(self, mock_cc_tran, _unused):
        """ test DKBRobo._legacy_get_transactions() method with an credit-card account"""
        mock_cc_tran.return_value = ['credit_card']
        self.assertEqual(self.dkb._legacy_get_transactions('url', 'creditcard', '01.03.2017', '02.03.2017'), ['credit_card'])
        self.assertTrue(mock_cc_tran.called)

    @patch('dkb_robo.DKBRobo._legacy_get_account_transactions')
    def test_035_get_tr_ac(self, mock_ca_tran, _unused):
        """ test DKBRobo._legacy_get_transactions() method with an checking account"""
        mock_ca_tran.return_value = ['account']
        self.assertEqual(self.dkb._legacy_get_transactions('url', 'account', '01.03.2017', '02.03.2017'), ['account'])
        self.assertTrue(mock_ca_tran.called)

    @patch('dkb_robo.DKBRobo._legacy_get_depot_status')
    def test_036_get_tr_ac(self, mock_dep_tran, _unused):
        """ test DKBRobo._legacy_get_transactions() method for a deptot """
        mock_dep_tran.return_value = ['dep']
        self.assertEqual(self.dkb._legacy_get_transactions('url', 'depot', '01.03.2017', '02.03.2017'), ['dep'])
        self.assertTrue(mock_dep_tran.called)

    def test_037_parse_account_tr(self, _mock_browser):
        """ test DKBRobo._legacy_get_account_transactions for one page only """
        csv = read_file(self.dir_path + '/mocks/test_parse_account_tr.csv')
        result = [
            {'amount':  100.0, 'bdate': '01.03.2017', 'customerreferenz': 'Kundenreferenz1', 'date': '01.03.2017', 'mandatereference': 'Mandatsreferenz1', 'peer': 'Auftraggeber1', 'peeraccount': 'Kontonummer1', 'peerbic': 'BLZ1', 'peerid': 'GID1', 'postingtext': 'Buchungstext1', 'reasonforpayment': 'Verwendungszweck1', 'text': 'Buchungstext1 Auftraggeber1 Verwendungszweck1', 'vdate': '01.03.2017'},
            {'amount': -200.0, 'bdate': '02.03.2017', 'customerreferenz': 'Kundenreferenz2', 'date': '02.03.2017', 'mandatereference': 'Mandatsreferenz2', 'peer': 'Auftraggeber2', 'peeraccount': 'Kontonummer2', 'peerbic': 'BLZ2', 'peerid': 'GID2', 'postingtext': 'Buchungstext2', 'reasonforpayment': 'Verwendungszweck2', 'text': 'Buchungstext2 Auftraggeber2 Verwendungszweck2', 'vdate': '02.03.2017'},
            {'amount': 3000.0, 'bdate': '03.03.2017', 'customerreferenz': 'Kundenreferenz3', 'date': '03.03.2017', 'mandatereference': 'Mandatsreferenz3', 'peer': 'Auftraggeber3', 'peeraccount': 'Kontonummer3', 'peerbic': 'BLZ3', 'peerid': 'GID3', 'postingtext': 'Buchungstext3', 'reasonforpayment': 'Verwendungszweck3', 'text': 'Buchungstext3 Auftraggeber3 Verwendungszweck3', 'vdate': '03.03.2017'},
             {'amount': -4000.0, 'bdate': '04.03.2017', 'customerreferenz': 'Kundenreferenz4', 'date': '04.03.2017', 'mandatereference': 'Mandatsreferenz4', 'peer': 'Auftraggeber4', 'peeraccount': 'Kontonummer4', 'peerbic': 'BLZ4', 'peerid': 'GID4', 'postingtext': 'Buchungstext4', 'reasonforpayment': 'Verwendungszweck4', 'text': 'Buchungstext4 Auftraggeber4 Verwendungszweck4', 'vdate': '04.03.2017'}
            ]

        self.assertEqual(result, self.dkb._parse_account_transactions(csv))

    def test_038_parse_no_account_tr(self, _mock_browser):
        """ test DKBRobo._legacy_get_account_transactions for one page only """
        csv = read_file(self.dir_path + '/mocks/test_parse_no_account_tr.csv')
        self.assertEqual(self.dkb._parse_account_transactions(csv), [])

    def test_039_parse_dkb_cc_tr(self, _mock_browser):
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

    def test_040_parse_no_cc_tr(self, _mock_browser):
        """ test DKBRobo._parse_cc_transactions """
        csv = read_file(self.dir_path + '/mocks/test_parse_no_cc_tr.csv')
        self.assertEqual(self.dkb._parse_cc_transactions(csv), [])

    @patch('time.time')
    def test_041_validate_dates(self, mock_time, mock_browser):
        """ test validate dates with correct data """
        date_from = '01.12.2021'
        date_to = '10.12.2021'
        mock_time.return_value = 1639232579
        self.assertEqual(('01.12.2021', '10.12.2021'), self.validate_dates(self.logger, date_from, date_to))

    @patch('time.time')
    def test_042_validate_dates(self, mock_time, mock_browser):
        """ test validate dates date_from to be corrected """
        date_from = '12.12.2021'
        date_to = '11.12.2021'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('11.12.2021', '11.12.2021'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 11.12.2021', lcm.output)

    @patch('time.time')
    def test_043_validate_dates(self, mock_time, mock_browser):
        """ test validate dates date_to to be corrected """
        date_from = '01.12.2021'
        date_to = '12.12.2021'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('01.12.2021', '11.12.2021'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_to to 11.12.2021', lcm.output)

    @patch('time.time')
    def test_044_validate_dates(self, mock_time, mock_browser):
        """ test validate dates date_from to be corrected past past > 3 years """
        date_from = '01.01.1980'
        date_to = '12.12.2021'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('12.12.2018', '11.12.2021'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 12.12.2018', lcm.output)

    @patch('time.time')
    def test_045_validate_dates(self, mock_time, mock_browser):
        """ test validate dates date_from to be corrected past past > 3 years """
        date_from = '01.01.1980'
        date_to = '02.01.1980'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('12.12.2018', '12.12.2018'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 12.12.2018', lcm.output)
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_to to 12.12.2018', lcm.output)

    @patch('time.time')
    def test_046_validate_dates(self, mock_time, mock_browser):
        """ test validate dates with correct data """
        date_from = '2021-12-01'
        date_to = '2021-12-10'
        mock_time.return_value = 1639232579
        self.assertEqual(('2021-12-01', '2021-12-10'), self.validate_dates(self.logger, date_from, date_to, 1))

    @patch('time.time')
    def test_047_validate_dates(self, mock_time, mock_browser):
        """ test validate dates with correct data """
        date_from = '2021-12-01'
        date_to = '2021-12-10'
        mock_time.return_value = 1639232579
        self.assertEqual(('01.12.2021', '10.12.2021'), self.validate_dates(self.logger, date_from, date_to, 3))


    @patch('random.choice')
    def test_048_generate_random_string(self, mock_rc, mock_browser):
        mock_rc.return_value = '1a'
        length = 5
        self.assertEqual('1a1a1a1a1a', self.generate_random_string(length))

    @patch('random.choice')
    def test_049_generate_random_string(self, mock_rc, mock_browser):
        mock_rc.return_value = '1a'
        length = 10
        self.assertEqual('1a1a1a1a1a1a1a1a1a1a', self.generate_random_string(length))

    def test_050_get_financial_statement(self, mock_browser):
        """ get financial statement """
        html = '<html><head>header</head><body>body</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertEqual('<html><head></head><body>headerbody</body></html>', str(self.dkb._get_financial_statement()))

    def test_051_get_financial_statement(self, mock_browser):
        """ get financial statement with tan_insert """
        html = '<html><head>header</head><body>body</body></html>'
        self.dkb.tan_insert = True
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertEqual('<html><head></head><body>headerbody</body></html>', str(self.dkb._get_financial_statement()))

    @patch('dkb_robo.DKBRobo._legacy_login')
    @patch('dkb_robo.DKBRobo._login')
    def test_052__enter(self, mock_login, mock_legacy_login, mock_browser):
        """ test enter """
        self.dkb.legacy_login = True
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy_login.called)
        self.assertFalse(mock_login.called)

    @patch('dkb_robo.DKBRobo._legacy_login')
    @patch('dkb_robo.DKBRobo._login')
    def test_053__enter(self, mock_login, mock_legacy_login, _unused):
        """ test enter """
        self.dkb.dkb_br = None
        self.dkb.legacy_login = True
        self.assertTrue(self.dkb.__enter__())
        self.assertTrue(mock_legacy_login.called)
        self.assertFalse(mock_login.called)

    @patch('dkb_robo.DKBRobo._legacy_login')
    @patch('dkb_robo.DKBRobo._login')
    def test_054__enter(self, mock_login, mock_legacy_login, _unused):
        """ test enter """
        self.dkb.client = None
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy_login.called)
        self.assertTrue(mock_login.called)

    @patch('dkb_robo.DKBRobo._legacy_login')
    @patch('dkb_robo.DKBRobo._login')
    def test_055__enter(self, mock_login, mock_legacy_login, _unused):
        """ test enter """
        self.dkb.client = 'foo'
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy_login.called)
        self.assertFalse(mock_login.called)

    @patch('dkb_robo.DKBRobo._legacy_login')
    @patch('dkb_robo.DKBRobo._login')
    def test_056__enter(self, mock_login, mock_legacy_login, _unused):
        """ test enter """
        self.dkb.dkb_br = None
        self.dkb.legacy_login = False
        self.dkb.tan_insert = True
        self.assertTrue(self.dkb.__enter__())
        self.assertTrue(mock_legacy_login.called)
        self.assertFalse(mock_login.called)

    @patch('dkb_robo.DKBRobo._logout')
    def test_057__exit(self, mock_logout, _ununsed):
        """ test enter """
        self.assertFalse(self.dkb.__exit__())
        self.assertTrue(mock_logout.called)

    @patch('dkb_robo.DKBRobo._parse_account_transactions')
    def test_058__legacy_get_account_transactions(self, mock_parse, mock_browser):
        """ test _legacy_get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.dkb._legacy_get_account_transactions('url', 'date_from', 'date_to'))

    @patch('dkb_robo.DKBRobo._parse_account_transactions')
    def test_059__legacy_get_account_transactions(self, mock_parse, mock_browser):
        """ test _legacy_get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.dkb._legacy_get_account_transactions('url', 'date_from', 'date_to', transaction_type='reserved'))

    @patch('dkb_robo.DKBRobo._parse_cc_transactions')
    def test_060_get_cc_transactions(self, mock_parse, mock_browser):
        """ test _legacy_get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.dkb._legacy_get_creditcard_transactions('url', 'date_from', 'date_to'))

    @patch('dkb_robo.DKBRobo._parse_cc_transactions')
    def test_061_get_cc_transactions(self, mock_parse, mock_browser):
        """ test _legacy_get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.dkb._legacy_get_creditcard_transactions('url', 'date_from', 'date_to', transaction_type='reserved'))

    def test_062_logout(self, _unused):
        """ test logout """
        self.assertFalse(self.dkb._logout())

    @patch('logging.getLogger')
    def test_063_logger_setup(self, mock_logging, _unused):
        """ test logger setup with debug false """
        mock_logging.return_value = 'logging'
        self.assertEqual('logging', self.logger_setup(False))

    @patch('logging.getLogger')
    def test_064_logger_setup(self, mock_logging, _unused):
        """ test logger setup with debug true """
        mock_logging.return_value = 'logging'
        self.assertEqual('logging', self.logger_setup(True))

    def test_065_update_downloadstate(self, _unused):
        """ test update downloadstats """
        url = 'https://www.ib.dkb.de/DkbTransactionBanking/content/mailbox/MessageList/%24{1}.xhtml?$event=updateDownloadState&row=1'
        self.assertFalse(self.dkb._update_downloadstate(link_name='link_name', url=url))

    def test_066_update_downloadstate(self, _unused):
        """ test update downloadstats """
        url = 'https://www.ib.dkb.de/DkbTransactionBanking/content/mailbox/MessageList/%24{1}.xhtml?$event=updateDownloadState&row=1'
        self.assertFalse(self.dkb._update_downloadstate(link_name='Kontoauszüge', url=url))

    @patch('dkb_robo.dkb_robo.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_067_get_document(self, mock_exists, mock_makedir, mock_rand, _unused):
        """ test get_document create path """
        mock_exists.return_value = False
        mock_rand.return_value = 'mock_rand'
        self.assertEqual((None, 'path/mock_rand.pdf', []), self.dkb._get_document('folder_url', 'path', 'url', [], False))
        self.assertTrue(mock_makedir.called)
        self.assertTrue(mock_rand.called)

    @patch('dkb_robo.dkb_robo.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_068_get_document(self, mock_exists, mock_makedir, mock_rand, _unused):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_rand.return_value = 'mock_rand'
        self.assertEqual((None, 'path/mock_rand.pdf', []), self.dkb._get_document('folder_url', 'path', 'url', [], False))
        self.assertFalse(mock_makedir.called)
        self.assertTrue(mock_rand.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('re.findall')
    @patch('dkb_robo.dkb_robo.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_069_get_document(self, mock_exists, mock_makedir, mock_rand, mock_re, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_rand.return_value = 'mock_rand'
        mock_browser.open.return_value.headers = {'Content-Disposition': ['foo', 'bar']}
        mock_browser.open.return_value.status_code = 200
        mock_re.return_value = ['mock_re.pdf', 'mock_re2.pdf']
        self.assertEqual((200, 'path/mock_re.pdf', ['mock_re.pdf']), self.dkb._get_document('folder_url', 'path', 'url', [], False))
        self.assertFalse(mock_makedir.called)

    @patch('dkb_robo.dkb_robo.datetime', Mock(now=lambda: date(2022, 9, 30)))
    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('re.findall')
    @patch('dkb_robo.dkb_robo.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_070_get_document(self, mock_exists, mock_makedir, mock_rand, mock_re, mock_browser):
        """ test get_document override """
        mock_exists.return_value = True
        mock_rand.return_value = 'mock_rand'
        mock_browser.open.return_value.headers = {'Content-Disposition': ['foo', 'bar']}
        mock_browser.open.return_value.status_code = 200
        mock_re.return_value = ['mock_re.pdf', 'mock_re2.pdf']
        self.assertEqual((200, 'path/2022-09-30-00-00-00_mock_re.pdf', ['mock_re.pdf', '2022-09-30-00-00-00_mock_re.pdf']), self.dkb._get_document('folder_url', 'path', 'url', ['mock_re.pdf'], False))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_071_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers =  {'Content-Disposition': 'inline; filename=Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf', ['Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf']), self.dkb._get_document('folder_url', 'path', 'url', [], False))
        self.assertFalse(mock_makedir.called)

    @patch('dkb_robo.dkb_robo.datetime', Mock(now=lambda: date(2022, 9, 30)))
    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_072_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers =  {'Content-Disposition': 'inline; filename=Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/2022-09-30-00-00-00_Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf', ['Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf', '2022-09-30-00-00-00_Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf']), self.dkb._get_document('folder_url', 'path', 'url', ['Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf'], False))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_073_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers =  {'Content-Disposition': 'inline; filename=foo.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/foo.pdf', ['foo.pdf']), self.dkb._get_document('folder_url', 'path', 'url', [], False))
        self.assertFalse(mock_makedir.called)

    @patch('dkb_robo.dkb_robo.datetime', Mock(now=lambda: date(2022, 9, 30)))
    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_074_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers =  {'Content-Disposition': 'inline; filename=foo.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/2022-09-30-00-00-00_foo.pdf', ['foo.pdf', '2022-09-30-00-00-00_foo.pdf']), self.dkb._get_document('folder_url', 'path', 'url', ['foo.pdf'], False))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('urllib.parse.unquote')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_075_get_document(self, mock_exists, mock_makedir, mock_parse, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers =  {'Content-Disposition': 'inline; filename=Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf'}
        mock_browser.open.return_value.status_code = 200
        mock_parse.side_effect = [Exception('exc1')]
        self.assertEqual((200, 'path/Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf', ['Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf']), self.dkb._get_document('folder_url', 'path', 'url', [], False))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_076_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document prepend string """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers =  {'Content-Disposition': 'inline; filename=Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/prepend_Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf', ['prepend_Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf']), self.dkb._get_document('folder_url', 'path', 'url', [], 'prepend_'))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_077_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers =  {'Content-Disposition': 'inline; filename=foo.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/prepend_foo.pdf', ['prepend_foo.pdf']), self.dkb._get_document('folder_url', 'path', 'url', [], 'prepend_'))
        self.assertFalse(mock_makedir.called)

    @patch('builtins.input')
    def test_078_ctan_check(self, mock_input, mock_browser):
        """ test ctan_check """
        mock_input.return_value = 'tan'
        html = '<html><head>header</head><body><ol><li>li</li></ol></body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertTrue(self.dkb._ctan_check('soup'))

    @patch('builtins.input')
    def test_079_ctan_check(self, mock_input, mock_browser):
        """ test ctan_check """
        mock_input.return_value = 'tan'
        html = '<html><head>header</head><body>body</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertTrue(self.dkb._ctan_check('soup'))

    @patch('builtins.input')
    def test_080_ctan_check(self, mock_input, mock_browser):
        """ test ctan_check wrong tan """
        mock_input.return_value = 'tan'
        html = '<html><head>header</head><body><div class="clearfix module text errorMessage">div</div></body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        with self.assertRaises(Exception) as err:
             self.dkb._ctan_check('soup')
        self.assertEqual('Login failed due to wrong TAN', str(err.exception))

    @patch('sys.exit')
    @patch('builtins.input')
    def test_081_ctan_check(self, mock_input, mock_sexit, mock_browser):
        """ test ctan_check """
        mock_input.return_value = 'tan'
        html = '<html><head>header</head><body>body</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_browser.select_form.side_effect =  [Exception('exc1'), Exception('exc2'), 'foo']
        self.assertTrue(self.dkb._ctan_check('soup'))

    @patch('dkb_robo.DKBRobo._check_confirmation')
    def test_082_login_confirm(self, mock_confirm, mock_browser, ):
        """ test login confirmed check_cofirmation returns true """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_confirm.return_value = True
        self.assertTrue(self.dkb._login_confirm())

    @patch('time.sleep', return_value=None)
    @patch('dkb_robo.DKBRobo._check_confirmation')
    def test_083_login_confirm(self, mock_confirm, mock_sleep, mock_browser):
        """ test login confirmed check_cofirmation returns multiple false but then true """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_confirm.side_effect = [False, False, False, True]
        self.assertTrue(self.dkb._login_confirm())

    @patch('time.sleep', return_value=None)
    @patch('dkb_robo.DKBRobo._check_confirmation')
    def test_084_login_confirm(self, mock_confirm, mock_sleep, mock_browser):
        """ test login confirmed  """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_confirm.return_value = False
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb._login_confirm())
        self.assertEqual('No session confirmation after 120 polls', str(err.exception))

    @patch('dkb_robo.dkb_robo.generate_random_string')
    def test_085_login_confirm(self, mock_rand, mock_browser):
        """ test login confirmed - exception when getting the token """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_browser.get_current_page.side_effect =  Exception('exc')
        with self.assertRaises(Exception) as err:
            self.assertTrue(self.dkb._login_confirm())
        self.assertEqual('Error while getting the confirmation page', str(err.exception))

    def test_086_check_confirmation(self, _unused):
        """ test confirmation """
        result = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._check_confirmation(result, 1)
        self.assertEqual('Error during session confirmation', str(err.exception))

    def test_087_check_confirmation(self, _unused):
        """ test confirmation state expired"""
        result = {'state': 'EXPIRED'}
        with self.assertRaises(Exception) as err:
            self.dkb._check_confirmation(result, 1)
        self.assertEqual('Session expired', str(err.exception))

    def test_088_check_confirmation(self, _unused):
        """ test confirmation state processed"""
        result = {'state': 'PROCESSED'}
        self.assertTrue(self.dkb._check_confirmation(result, 1))

    def test_089_check_confirmation(self, _unused):
        """ test confirmation state unknown """
        result = {'state': 'UNK'}
        self.assertFalse(self.dkb._check_confirmation(result, 1))

    def test_090_check_confirmation(self, _unused):
        """ test confirmation guiState expired"""
        result = {'guiState': 'EXPIRED'}
        with self.assertRaises(Exception) as err:
            self.dkb._check_confirmation(result, 1)
        self.assertEqual('Session expired', str(err.exception))

    def test_091_check_confirmation(self, _unused):
        """ test confirmation guiState MAP_TO_EXIT"""
        result = {'guiState': 'MAP_TO_EXIT'}
        self.assertTrue(self.dkb._check_confirmation(result, 1))

    def test_092_check_confirmation(self, _unused):
        """ test confirmation guiState unknown """
        result = {'guiState': 'UNK'}
        self.assertFalse(self.dkb._check_confirmation(result, 1))

    def test_093_parse_depot_status_tr(self, _mock_browser):
        """ test DKBRobo._parse_cc_transactions """
        csv = read_file(self.dir_path + '/mocks/test_parse_depot.csv')
        result = [{'shares': 10.0, 'shares_unit': 'cnt1', 'isin_wkn': 'WKN1', 'text': 'Bezeichnung1', 'price': 11.0, 'win_loss': '', 'win_loss_currency': '', 'aquisition_cost': '', 'aquisition_cost_currency': '', 'dev_price': '', 'price_euro': 1110.1, 'availability': 'Frei'}, {'shares': 20.0, 'shares_unit': 'cnt2', 'isin_wkn': 'WKN2', 'text': 'Bezeichnung2', 'price': 12.0, 'win_loss': '', 'win_loss_currency': '', 'aquisition_cost': '', 'aquisition_cost_currency': '', 'dev_price': '', 'price_euro': 2220.2, 'availability': 'Frei'}]
        self.assertEqual(result, self.dkb._parse_depot_status(csv))

    def test_094_string2float(self, _unused):
        """ test string2float """
        value = 1000
        self.assertEqual(1000.0, self.string2float(value))

    def test_095_string2float(self, _unused):
        """ test string2float """
        value = 1000.0
        self.assertEqual(1000.0, self.string2float(value))

    def test_096_string2float(self, _unused):
        """ test string2float """
        value = '1.000,00'
        self.assertEqual(1000.0, self.string2float(value))

    def test_097_string2float(self, _unused):
        """ test string2float """
        value = '1000,00'
        self.assertEqual(1000.0, self.string2float(value))

    def test_098_string2float(self, _unused):
        """ test string2float """
        value = '1.000'
        self.assertEqual(1000.0, self.string2float(value))

    def test_099_string2float(self, _unused):
        """ test string2float """
        value = '1.000,23'
        self.assertEqual(1000.23, self.string2float(value))

    def test_100_string2float(self, _unused):
        """ test string2float """
        value = '1000,23'
        self.assertEqual(1000.23, self.string2float(value))

    def test_101_string2float(self, _unused):
        """ test string2float """
        value = 1000.23
        self.assertEqual(1000.23, self.string2float(value))

    def test_102_string2float(self, _unused):
        """ test string2float """
        value = '-1.000'
        self.assertEqual(-1000.0, self.string2float(value))

    def test_103_string2float(self, _unused):
        """ test string2float """
        value = '-1.000,23'
        self.assertEqual(-1000.23, self.string2float(value))

    def test_104_string2float(self, _unused):
        """ test string2float """
        value = '-1000,23'
        self.assertEqual(-1000.23, self.string2float(value))

    def test_105_string2float(self, _unused):
        """ test string2float """
        value = -1000.23
        self.assertEqual(-1000.23, self.string2float(value))

    @patch('dkb_robo.DKBRobo._parse_depot_status')
    def test_106__legacy_get_depot_status(self, mock_pds, _unused):
        """ test get depot status """
        mock_pds.return_value = 'mock_pds'
        self.assertEqual('mock_pds', self.dkb._legacy_get_depot_status('url', 'fdate', 'tdate', 'booked'))

    @patch('dkb_robo.DKBRobo._get_document')
    def test_107_download_document(self, mock_get_doc, _ununsed):
        """ test download document """
        html = read_file(self.dir_path + '/mocks/document_list.html')
        table = BeautifulSoup(html, 'html5lib')
        mock_get_doc.side_effect = my_side_effect
        class_filter = {}
        doc_dic = {'Name 04.01.2022': {'rcode': 200, 'link': 'https://www.ib.dkb.dehttps://www.dkb.de/DkbTransactionBanking/content/mailbox/MessageList.xhtml?$event=getMailboxAttachment&filename=Name+04.01.2022&row=0', 'fname': 'path/link_name'}}
        result = (doc_dic, [''])
        self.assertEqual(result, self.dkb._download_document('folder_url', 'path',  class_filter, 'link_name', table, False))

    @patch('dkb_robo.DKBRobo._get_document')
    def test_108_download_document(self, mock_get_doc, _ununsed):
        """ test download document prepend date """
        html = read_file(self.dir_path + '/mocks/document_list.html')
        table = BeautifulSoup(html, 'html5lib')
        mock_get_doc.side_effect = my_side_effect
        class_filter = {}
        doc_dic = {'Name 04.01.2022': {'rcode': 200, 'link': 'https://www.ib.dkb.dehttps://www.dkb.de/DkbTransactionBanking/content/mailbox/MessageList.xhtml?$event=getMailboxAttachment&filename=Name+04.01.2022&row=0', 'fname': 'path/link_name'}}
        result = (doc_dic, ['2022-01-04_'])
        self.assertEqual(result, self.dkb._download_document('folder_url', 'path',  class_filter, 'link_name', table, True))

    @patch('dkb_robo.DKBRobo._get_document')
    def test_109_download_document(self, mock_get_doc, _ununsed):
        """ test download document prepend date """
        html = read_file(self.dir_path + '/mocks/document_list-2.html')
        table = BeautifulSoup(html, 'html5lib')
        mock_get_doc.side_effect = my_side_effect
        class_filter = {}
        doc_dic = {'Name 04.01.2022': {'rcode': 200, 'link': 'https://www.ib.dkb.dehttps://www.dkb.de/DkbTransactionBanking/content/mailbox/MessageList.xhtml?$event=getMailboxAttachment&filename=Name+04.01.2022&row=0', 'fname': 'path/link_name'}}
        result = (doc_dic, [''])
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(result, self.dkb._download_document('folder_url', 'path',  class_filter, 'link_name', table, True))
        self.assertIn("ERROR:dkb_robo:Can't parse date, this could i.e. be for archived documents.", lcm.output)

    def test_110__get_formatted_date(self, _ununsed):
        """ test _get_formatted_date() prepend True """
        html = '<table><tr><td>foo</td><td class="abaxx-aspect-messageWithState-mailboxMessage-created">04.01.2022</td><td>bar</td></tr><table>'
        table = BeautifulSoup(html, 'html5lib')
        self.assertEqual('2022-01-04_', self.dkb._get_formatted_date(True, table))

    def test_111__get_formatted_date(self, _ununsed):
        """ test _get_formatted_date() prepend False """
        html = '<table><tr><td>foo</td><td class="abaxx-aspect-messageWithState-mailboxMessage-created">04.01.2022</td><td>bar</td></tr><table>'
        table = BeautifulSoup(html, 'html5lib')
        self.assertEqual('', self.dkb._get_formatted_date(False, table))

    def test_112__get_formatted_date(self, _ununsed):
        """ test _get_formatted_date() prepend False """
        html = '<table><tr><td>foo</td><td class="abaxx-aspect-messageWithState-mailboxMessage-created">fii</td><td>bar</td></tr><table>'
        table = BeautifulSoup(html, 'html5lib')
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual('', self.dkb._get_formatted_date(True, table))
        self.assertIn("ERROR:dkb_robo:Can't parse date, this could i.e. be for archived documents.", lcm.output)

    def test_113_get_accounts(self, _unused):
        """ test _get_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_accounts())

    def test_114_get_accounts(self, _unused):
        """ test _get_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_accounts())
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_accounts(): RC is not 200 but 400', lcm.output)

    def test_115_get_brokerage_accounts(self, _unused):
        """ test _get_brokerage_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_brokerage_accounts())

    def test_116_get_brokerage_accounts(self, _unused):
        """ test _get_brokerage_accounts() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_brokerage_accounts())
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_brokerage_accounts(): RC is not 200 but 400', lcm.output)

    def test_117_get_cards(self, _unused):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_cards())

    def test_118_get_cards(self, _unused):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_cards())
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_cards(): RC is not 200 but 400', lcm.output)

    def test_119_get_loans(self, _unused):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb._get_loans())

    def test_120_get_loans(self, _unused):
        """ test _get_loans() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._get_loans())
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_loans(): RC is not 200 but 400', lcm.output)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_121_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        atype = 'account'
        self.assertFalse(self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_122_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans_unused, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {}
        atype = 'account'
        self.assertFalse(self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_atrans.called)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_123_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        atype = 'account'
        self.assertFalse(self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_124_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'data': {'foo': 'bar'}}
        atype = 'account'
        mock_atrans.return_value = {'mock_foo': 'mock_bar'}
        self.assertEqual({'mock_foo': 'mock_bar'}, self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertTrue(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_125_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'data': {'foo': 'bar'}}
        atype = 'creditcard'
        mock_ctrans.return_value = {'mock_foo': 'mock_bar'}
        self.assertEqual({'mock_foo': 'mock_bar'}, self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertTrue(mock_ctrans.called)
        self.assertFalse(mock_btrans.called)

    @patch('dkb_robo.DKBRobo._format_brokerage_account')
    @patch('dkb_robo.DKBRobo._format_card_transactions')
    @patch('dkb_robo.DKBRobo._format_account_transactions')
    @patch('dkb_robo.DKBRobo._filter_transactions')
    def test_126_get_transactions(self, mock_ftrans, mock_atrans, mock_ctrans, mock_btrans, _unused):
        """ test __legacy_get_transactions() ok """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'data': {'foo': 'bar'}}
        atype = 'depot'
        mock_btrans.return_value = {'mock_foo': 'mock_bar'}
        self.assertEqual({'mock_foo': 'mock_bar'}, self.dkb._get_transactions('transaction_url', atype, 'date_from', 'date_to', 'transaction_type'))
        self.assertFalse(mock_atrans.called)
        self.assertFalse(mock_ctrans.called)
        self.assertTrue(mock_btrans.called)

    def test_127_update_token(self, _unused):
        """ test _update_token() ok """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token'}
        self.dkb.client = Mock()
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        self.dkb._update_token()
        self.assertEqual({'foo': 'bar'}, self.dkb.token_dic)

    def test_128_update_token(self, _unused):
        """ test _update_token() nok """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token'}
        self.dkb.client = Mock()
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._update_token()
        self.assertEqual('Login failed: token update failed. RC: 400', str(err.exception))
        self.assertEqual({'mfa_id': 'mfa_id', 'access_token': 'access_token'}, self.dkb.token_dic)

    def test_129_get_token(self, _unused):
        """ test _get_token() ok """
        self.dkb.dkb_user = 'dkb_user'
        self.dkb.dkb_password = 'dkb_password'
        self.dkb.client = Mock()
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        self.dkb._get_token()
        self.assertEqual({'foo': 'bar'}, self.dkb.token_dic)

    def test_130_get_token(self, _unused):
        """ test _get_token() ok """
        self.dkb.dkb_user = 'dkb_user'
        self.dkb.dkb_password = 'dkb_password'
        self.dkb.client = Mock()
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._get_token()
        self.assertEqual('Login failed: 1st factor authentication failed. RC: 400', str(err.exception))
        self.assertFalse(self.dkb.token_dic)

    @patch('dkb_robo.DKBRobo._new_instance')
    def test_131_do_sso_redirect(self, mock_instance, _unused):
        """ test _do_sso_redirect() ok """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.text = 'OK'
        self.dkb._do_sso_redirect()
        self.assertTrue(mock_instance.called)

    @patch('dkb_robo.DKBRobo._new_instance')
    def test_132_do_sso_redirect(self, mock_instance, _unused):
        """ test _do_sso_redirect() nok """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.text = 'NOK'
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb._do_sso_redirect()
        self.assertIn('ERROR:dkb_robo:SSO redirect failed. RC: 200 text: NOK', lcm.output)
        self.assertTrue(mock_instance.called)

    @patch('dkb_robo.DKBRobo._new_instance')
    def test_133_do_sso_redirect(self, mock_instance, _unused):
        """ test _do_sso_redirect() nok """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.text = 'OK'
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb._do_sso_redirect()
        self.assertIn('ERROR:dkb_robo:SSO redirect failed. RC: 400 text: OK', lcm.output)
        self.assertTrue(mock_instance.called)

    def test_134_get_mfa_methods(self, _unused):
        """ test _get_mfa_methods() """
        self.dkb.token_dic = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._get_mfa_methods()
        self.assertEqual('Login failed: no 1fa access token.', str(err.exception))

    def test_135_get_mfa_methods(self, _unused):
        """ test _get_mfa_methods() """
        self.dkb.token_dic = {'access_token': 'bar'}
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        with self.assertRaises(Exception) as err:
            self.dkb._get_mfa_methods()
        self.assertEqual('Login failed: getting mfa_methods failed. RC: 400', str(err.exception))

    def test_136_get_mfa_methods(self, _unused):
        """ test _get_mfa_methods() """
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo1': 'bar1'}
        self.dkb.token_dic = {'access_token': 'bar'}
        self.assertEqual({'foo1': 'bar1'}, self.dkb._get_mfa_methods())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('time.sleep', return_value=None)
    def test_137__complete_2fa(self, _mock_sleep, mock_stdout, _unused):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 400
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._complete_2fa('challengeid', 'devicename'))
        self.assertIn('ERROR:dkb_robo:DKBRobo._complete_2fa(): polling request failed. RC: 400', lcm.output)
        self.assertIn('check your banking app on "devicename" and confirm login...', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('time.sleep', return_value=None)
    def test_138__complete_2fa(self, _mock_sleep, mock_stdout, _unused):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 400
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._complete_2fa('challengeid', None))
        self.assertIn('ERROR:dkb_robo:DKBRobo._complete_2fa(): polling request failed. RC: 400', lcm.output)
        self.assertIn('check your banking app and confirm login...', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('time.sleep', return_value=None)
    def test_139__complete_2fa(self, _mock_sleep, mock_stdout, _unused):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo1': 'bar1'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertFalse(self.dkb._complete_2fa('challengeid', 'devicename'))
        self.assertIn("ERROR:dkb_robo:DKBRobo._complete_2fa(): error parsing polling response: {'foo1': 'bar1'}", lcm.output)
        self.assertIn('check your banking app on "devicename" and confirm login...', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('time.sleep', return_value=None)
    def test_140__complete_2fa(self, _mock_sleep, mock_stdout, _unused):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.side_effect = [{'foo1': 'bar1'}, {'data': {'attributes': {'verificationStatus': 'processed'}}}]
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertTrue(self.dkb._complete_2fa('challengeid', 'devicename'))
        self.assertIn("ERROR:dkb_robo:DKBRobo._complete_2fa(): error parsing polling response: {'foo1': 'bar1'}", lcm.output)
        self.assertIn('check your banking app on "devicename" and confirm login...', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('time.sleep', return_value=None)
    def test_141__complete_2fa(self, _mock_sleep, mock_stdout, _unused):
        """ test _complete_2fa() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.side_effect = [{'foo1': 'bar1'}, {'data': {'attributes': {'verificationStatus': 'canceled'}}}]
        with self.assertRaises(Exception) as err:
            self.assertTrue(self.dkb._complete_2fa('challengeid', 'devicename'))
        self.assertEqual('2fa chanceled by user', str(err.exception))

    @patch('requests.session')
    def test_142_new_instance_new_session(self, mock_session, _unused):
        """ test _new_session() """
        mock_session.headers = {}
        client = self.dkb._new_session()
        exp_headers = {'Accept-Language': 'en-US,en;q=0.5', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'DNT': '1', 'Pragma': 'no-cache', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0'}
        self.assertEqual(exp_headers, client.headers)

    @patch('requests.session')
    def test_143_new_instance_new_session(self, mock_session, _unused):
        """ test _new_session() """
        mock_session.headers = {}
        self.dkb.proxies = 'proxies'
        client = self.dkb._new_session()
        self.assertEqual('proxies', client.proxies)

    @patch('requests.session')
    def test_144_new_instance_new_session(self, mock_session, _unused):
        """ test _new_session() """
        mock_session.headers = {}
        mock_session.get.return_value.status_code = 200
        mock_session.return_value.cookies = {'__Host-xsrf': 'foo'}
        client = self.dkb._new_session()
        exp_headers = {'Accept-Language': 'en-US,en;q=0.5', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'DNT': '1', 'Pragma': 'no-cache', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0', 'x-xsrf-token': 'foo'}
        self.assertEqual(exp_headers, client.headers)

    @patch('requests.session')
    def test_145_get_mfa_challenge_id(self, mock_session, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual((None, None), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_mfa_challenge_id(): mfa_dic has an unexpected data structure', lcm.output)

    @patch('requests.session')
    def test_146_get_mfa_challenge_id(self, mock_session, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'foo': 'bar'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual((None, None), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_mfa_challenge_id(): mfa_dic has an unexpected data structure', lcm.output)

    def test_147_get_mfa_challenge_id(self, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'data': [{'id': 'id', 'attributes': {'deviceName': 'deviceName', 'foo': 'bar'}}]}
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'data': {'type': 'mfa-challenge', 'id': 'id'}}
        self.dkb.mfa_method = 'mfa_method'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        self.assertEqual(('id', 'deviceName'), self.dkb._get_mfa_challenge_id(mfa_dic))

    def test_148_get_mfa_challenge_id(self, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'data': [{'id': 'id', 'attributes': {'foo': 'bar'}}]}
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'data': {'type': 'mfa-challenge', 'id': 'id'}}
        self.dkb.mfa_method = 'mfa_method'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('id', None), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertIn('ERROR:dkb_robo:DKBRobo._get_mfa_challenge_id(): unable to get deviceName', lcm.output)

    def test_149_get_mfa_challenge_id(self, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'data': [{'id': 'id', 'attributes': {'deviceName': 'deviceName', 'foo': 'bar'}}]}
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 400
        self.dkb.client.post.return_value.json.return_value = {'data': {'type': 'mfa-challenge', 'id': 'id'}}
        self.dkb.mfa_method = 'mfa_method'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        with self.assertRaises(Exception) as err:
            self.assertEqual(('id', 'deviceName'), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertEqual('Login failed: post request to get the mfa challenges failed. RC: 400', str(err.exception))

    def test_150_get_mfa_challenge_id(self, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'data': [{'id': 'id', 'attributes': {'deviceName': 'deviceName', 'foo': 'bar'}}]}
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'data': {'type': 'unknown', 'id': 'id'}}
        self.dkb.mfa_method = 'mfa_method'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        with self.assertRaises(Exception) as err:
            self.assertEqual(('id', 'deviceName'), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertEqual("Login failed:: wrong challenge type: {'data': {'type': 'unknown', 'id': 'id'}}", str(err.exception))

    def test_151_get_mfa_challenge_id(self, _unused):
        """ test _get_mfa_challenge_id() """
        mfa_dic = {'data': [{'id': 'id', 'attributes': {'deviceName': 'deviceName', 'foo': 'bar'}}]}
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.post.return_value.status_code = 200
        self.dkb.client.post.return_value.json.return_value = {'foo': 'bar'}
        self.dkb.mfa_method = 'mfa_method'
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        with self.assertRaises(Exception) as err:
            self.assertEqual(('id', 'deviceName'), self.dkb._get_mfa_challenge_id(mfa_dic))
        self.assertEqual("Login failed: challenge response format is other than expected: {'foo': 'bar'}", str(err.exception))

    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_152_login(self, mock_sess, mock_tok, mock_meth,_ununsed):
        """ test login() """
        self.dkb.token_dic = {'foo': 'bar'}
        mock_meth.return_value = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: no 1fa access token.', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_153_login(self, mock_sess, mock_tok, mock_meth, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'foo': 'bar'}
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: no 1fa access token.', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_154_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = (None, None)
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: No challenge id.', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._complete_2fa')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_155_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_2fa.return_value = False
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: mfa did not complete', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._do_sso_redirect')
    @patch('dkb_robo.DKBRobo._update_token')
    @patch('dkb_robo.DKBRobo._complete_2fa')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_156_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_gf, mock_po, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_2fa.return_value = True
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: mfa did not complete', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertFalse(mock_redir.called)
        self.assertFalse(mock_gf.called)
        self.assertFalse(mock_po.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._do_sso_redirect')
    @patch('dkb_robo.DKBRobo._update_token')
    @patch('dkb_robo.DKBRobo._complete_2fa')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_157_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_gf, mock_po, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_2fa.return_value = True
        mock_mfa.return_value = 0
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: token_factor_type is missing', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertFalse(mock_redir.called)
        self.assertFalse(mock_gf.called)
        self.assertFalse(mock_po.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._parse_overview')
    @patch('dkb_robo.DKBRobo._get_financial_statement')
    @patch('dkb_robo.DKBRobo._do_sso_redirect')
    @patch('dkb_robo.DKBRobo._update_token')
    @patch('dkb_robo.DKBRobo._complete_2fa')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_158_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_gf, mock_po, mock_mfa, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token', 'token_factor_type': 'token_factor_type'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_mfa.return_value = 0
        mock_2fa.return_value = True
        with self.assertRaises(Exception) as err:
            self.dkb._login()
        self.assertEqual('Login failed: 2nd factor authentication did not complete', str(err.exception))
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertFalse(mock_redir.called)
        self.assertFalse(mock_gf.called)
        self.assertFalse(mock_po.called)
        self.assertTrue(mock_mfa.called)

    @patch('dkb_robo.DKBRobo._get_overview')
    @patch('dkb_robo.DKBRobo._select_mfa_device')
    @patch('dkb_robo.DKBRobo._do_sso_redirect')
    @patch('dkb_robo.DKBRobo._update_token')
    @patch('dkb_robo.DKBRobo._complete_2fa')
    @patch('dkb_robo.DKBRobo._get_mfa_challenge_id')
    @patch('dkb_robo.DKBRobo._get_mfa_methods')
    @patch('dkb_robo.DKBRobo._get_token')
    @patch('dkb_robo.DKBRobo._new_session')
    def test_159_login(self, mock_sess, mock_tok, mock_meth, mock_chall, mock_2fa, mock_upd, mock_redir, mock_mfa, mock_overview, _ununsed):
        """ test login() """
        self.dkb.token_dic = {'mfa_id': 'mfa_id', 'access_token': 'access_token', 'token_factor_type': '2fa'}
        mock_meth.return_value = {'data': 'bar'}
        mock_chall.return_value = ('mfa_challenge_id', 'deviceName')
        mock_mfa.return_value = 0
        mock_2fa.return_value = True
        self.dkb._login()
        self.assertTrue(mock_sess.called)
        self.assertTrue(mock_tok.called)
        self.assertTrue(mock_meth.called)
        self.assertTrue(mock_chall.called)
        self.assertTrue(mock_2fa.called)
        self.assertTrue(mock_upd.called)
        self.assertTrue(mock_redir.called)
        self.assertTrue(mock_mfa.called)
        self.assertTrue(mock_overview.called)

    def test_160__select_mfa_device(self, _unused):
        """ test _select_mfa_device() """
        mfa_dic = {'foo': 'bar'}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_161__select_mfa_device(self, mock_input, mock_stdout, _unused):
        """ test _select_mfa_device() """
        mock_input.return_value=0
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[0] - device-1\n[1] - device-2\n", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_162__select_mfa_device(self, mock_input, mock_stdout, _unused):
        """ test _select_mfa_device() """
        mock_input.return_value=1
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(1, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[0] - device-1\n[1] - device-2\n", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_163__select_mfa_device(self, mock_input, mock_stdout, _unused):
        """ test _select_mfa_device() """
        mock_input.side_effect = [3, 0]
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[0] - device-1\n[1] - device-2\n", mock_stdout.getvalue())
        self.assertIn('Wrong input!', mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input')
    def test_164__select_mfa_device(self, mock_input, mock_stdout, _unused):
        """ test _select_mfa_device() """
        mock_input.side_effect = ['a', 3, 0]
        mfa_dic = {'data': [{'attributes': {'deviceName': 'device-1'}}, {'attributes': {'deviceName': 'device-2'}}]}
        self.assertEqual(0, self.dkb._select_mfa_device(mfa_dic))
        self.assertIn("\nPick an authentication device from the below list:\n[0] - device-1\n[1] - device-2\n", mock_stdout.getvalue())
        self.assertIn('Invalid input!', mock_stdout.getvalue())
        self.assertIn('Wrong input!', mock_stdout.getvalue())

    def test_165_convert_date_format(self, _unused):
        """ test convert_date_format() """
        self.assertEqual('01.01.2023', self.convert_date_format(self.logger, '2023/01/01', ['%Y/%m/%d'], '%d.%m.%Y'))

    def test_166_convert_date_format(self, _unused):
        """ test convert_date_format() """
        self.assertEqual('wrong date', self.convert_date_format(self.logger, 'wrong date', ['%Y/%m/%d'], '%d.%m.%Y'))

    def test_167_convert_date_format(self, _unused):
        """ test convert_date_format() first match """
        self.assertEqual('01.01.2023', self.convert_date_format(self.logger, '2023/01/01', ['%Y/%m/%d', '%d.%m.%Y'], '%d.%m.%Y'))

    def test_168_convert_date_format(self, _unused):
        """ test convert_date_format() last match """
        self.assertEqual('01.01.2023', self.convert_date_format(self.logger, '2023/01/01', ['%d.%m.%Y', '%Y/%m/%d'], '%d.%m.%Y'))

    def test_169_convert_date_format(self, _unused):
        """ test convert_date_format() last match """
        self.assertEqual('2023/01/01', self.convert_date_format(self.logger, '2023/01/01', ['%Y/%m/%d', '%d.%m.%Y'], '%Y/%m/%d'))

    def test_170_convert_date_format(self, _unused):
        """ test convert_date_format() first match """
        self.assertEqual('2023/01/01', self.convert_date_format(self.logger, '2023/01/01', ['%d.%m.%Y', '%Y/%m/%d'], '%Y/%m/%d'))

    def test_171_convert_date_format(self, _unused):
        """ test convert_date_format() no match """
        self.assertEqual('wrong date', self.convert_date_format(self.logger, 'wrong date', ['%Y/%m/%d', '%Y-%m-%d'], '%d.%m.%Y'))

    def test_172__display_name_lookup(self, _ununsed):
        """ test _display_name_lookup() """
        display_settings = {}
        product_name = 'product_name'
        self.assertEqual(product_name, self.dkb._display_name_lookup('oid', display_settings, product_name))

    def test_173__display_name_lookup(self, _ununsed):
        """ test _display_name_lookup() """
        display_settings = {'oid': {'foo': 'bar'}}
        product_name = 'product_name'
        self.assertEqual(product_name, self.dkb._display_name_lookup('oid', display_settings, product_name))

    def test_174__display_name_lookup(self, _ununsed):
        """ test _display_name_lookup() """
        display_settings = {'oid': {'name': 'name'}}
        product_name = 'name'
        self.assertEqual(product_name, self.dkb._display_name_lookup('oid', display_settings, product_name))

    @patch('dkb_robo.DKBRobo._build_account_dic')
    @patch('dkb_robo.DKBRobo._get_loans')
    @patch('dkb_robo.DKBRobo._get_brokerage_accounts')
    @patch('dkb_robo.DKBRobo._get_cards')
    @patch('dkb_robo.DKBRobo._get_accounts')
    def test_175_get_overview(self, mock_acc, mock_cards, mock_br, mock_loans, mock_bac, _unused):
        """ test _get_overview() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.dkb._get_overview()
        self.assertTrue(mock_acc.called)
        self.assertTrue(mock_cards.called)
        self.assertTrue(mock_br.called)
        self.assertTrue(mock_loans.called)
        self.assertTrue(mock_bac.called)

    @patch('dkb_robo.DKBRobo._build_account_dic')
    @patch('dkb_robo.DKBRobo._get_loans')
    @patch('dkb_robo.DKBRobo._get_brokerage_accounts')
    @patch('dkb_robo.DKBRobo._get_cards')
    @patch('dkb_robo.DKBRobo._get_accounts')
    def test_176_get_overview(self, mock_acc, mock_cards, mock_br, mock_loans, mock_bac, _unused):
        """ test _get_overview() """
        self.dkb.client = Mock()
        self.dkb.client.headers = {}
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.json.return_value = {'foo': 'bar'}
        self.dkb._get_overview()
        self.assertFalse(mock_acc.called)
        self.assertFalse(mock_cards.called)
        self.assertFalse(mock_br.called)
        self.assertFalse(mock_loans.called)
        self.assertTrue(mock_bac.called)

    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_177__get_account_details(self, mock_dnl, _unused):
        """ test _get_account_details() """
        account_dic = {}
        product_settings_dic = {}
        mock_dnl.return_value = 'mock_dnl'
        self.assertFalse(self.dkb._get_account_details('aid', account_dic, 'group_name', product_settings_dic))
        self.assertFalse(mock_dnl.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_178__get_account_details(self, mock_dnl, mock_date, _unused):
        """ test _get_account_details() """
        account_dic = {'data': [{'id': 'aid', 'attributes': {'iban': 'iban', 'product': {'displayName': 'displayName'}, 'holderName': 'holdername', 'balance': {'value': 'value', 'currencyCode': 'currencycode'}, 'overdraftLimit': 'overdraftLimit', 'updatedAt': 'updatedat'}}]}
        product_settings_dic = {}
        mock_dnl.return_value = 'mock_dnl'
        mock_date.return_value = 'mock_date'
        result = {'type': 'account', 'id': 'aid', 'productgroup': 'group_name', 'iban': 'iban', 'name': 'displayName', 'account': 'iban', 'holdername': 'holdername', 'amount': 'value', 'currencycode': 'currencycode', 'date': 'updatedat', 'limit': 'overdraftLimit', 'transactions': 'https://banking.dkb.de/api/accounts/accounts/aid/transactions'}
        self.assertEqual(result, self.dkb._get_account_details('aid', account_dic, 'group_name', product_settings_dic))
        self.assertFalse(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_179__get_account_details(self, mock_dnl, mock_date, _unused):
        """ test _get_account_details() """
        account_dic = {'data': [{'id': 'aid', 'attributes': {'iban': 'iban', 'product': {'displayName': 'displayName'}, 'holderName': 'holdername', 'balance': {'value': 'value', 'currencyCode': 'currencycode'}, 'overdraftLimit': 'overdraftLimit', 'updatedAt': 'updatedat'}}]}
        product_settings_dic = {'accounts': {'foo': 'bar'}}
        mock_dnl.return_value = 'mock_dnl'
        mock_date.return_value = 'mock_date'
        result = {'type': 'account', 'id': 'aid', 'productgroup': 'group_name', 'iban': 'iban', 'name': 'mock_dnl', 'account': 'iban', 'holdername': 'holdername', 'amount': 'value', 'currencycode': 'currencycode', 'date': 'updatedat', 'limit': 'overdraftLimit', 'transactions': 'https://banking.dkb.de/api/accounts/accounts/aid/transactions'}
        self.assertEqual(result, self.dkb._get_account_details('aid', account_dic, 'group_name', product_settings_dic))
        self.assertTrue(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_180__get_account_details(self, mock_dnl, mock_date, _unused):
        """ test _get_account_details() """
        account_dic = {'data': [{'id': 'aid1', 'attributes': {'iban': 'iban', 'product': {'displayName': 'displayName'}, 'holderName': 'holdername', 'balance': {'value': 'value', 'currencyCode': 'currencycode'}, 'overdraftLimit': 'overdraftLimit', 'updatedAt': 'updatedat'}}, {'id': 'aid', 'attributes': {'iban': 'iban2', 'product': {'displayName': 'displayName2'}, 'holderName': 'holdername2', 'balance': {'value': 'value2', 'currencyCode': 'currencycode2'}, 'overdraftLimit': 'overdraftLimit2', 'updatedAt': 'updatedat2'}}]}
        product_settings_dic = {'accounts': {'foo': 'bar'}}
        mock_dnl.return_value = 'mock_dnl'
        mock_date.return_value = 'mock_date'
        result = {'type': 'account', 'id': 'aid', 'productgroup': 'group_name', 'iban': 'iban2', 'name': 'mock_dnl', 'account': 'iban2', 'holdername': 'holdername2', 'amount': 'value2', 'currencycode': 'currencycode2', 'date': 'updatedat2', 'limit': 'overdraftLimit2', 'transactions': 'https://banking.dkb.de/api/accounts/accounts/aid/transactions'}
        self.assertEqual(result, self.dkb._get_account_details('aid', account_dic, 'group_name', product_settings_dic))
        self.assertTrue(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_181__get_card_details(self, mock_dnl, mock_date, _unused):
        """ test _get_card_details() """
        card_dic = {}
        product_settings_dic = {}
        self.assertFalse(self.dkb._get_card_details('cid', card_dic, 'group_name', product_settings_dic))
        self.assertFalse(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_182__get_card_details(self, mock_dnl, mock_date, _unused):
        """ test _get_card_details() """
        card_dic = {}
        product_settings_dic = {'data': [{'foo': 'bar'}]}
        self.assertFalse(self.dkb._get_card_details('cid', card_dic, 'group_name', product_settings_dic))
        self.assertFalse(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_183__get_card_details(self, mock_dnl, mock_date, _unused):
        """ test _get_card_details() """
        card_dic = {'data': [{'id': 'cid'}]}
        product_settings_dic = {}
        self.assertFalse(self.dkb._get_card_details('cid', card_dic, 'group_name', product_settings_dic))
        self.assertFalse(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_184__get_card_details(self, mock_dnl, mock_date, _unused):
        """ test _get_card_details() """
        card_dic = {'data': [{'id': 'cid', 'attributes': {'product': {'displayName': 'displayname'}, 'holder': {'person': {'firstName': 'firstname', 'lastName': 'lastname'}}, 'maskedPan': 'maskedPan', 'limit': {'value': 'value'}, 'balance': {'date': 'date', 'value': '101', 'currencyCode': 'currencycode'}}}]}
        product_settings_dic = {}
        mock_dnl.return_value = 'mock_dnl'
        mock_date.return_value = 'mock_date'
        result = {'type': 'creditcard', 'id': 'cid', 'productgroup': 'group_name', 'maskedpan': 'maskedPan', 'account': 'maskedPan', 'amount': -101.0, 'currencycode': 'currencycode', 'date': 'date', 'limit': 'value', 'holdername': 'firstname lastname', 'name': 'displayname', 'transactions': 'https://banking.dkb.de/api/credit-card/cards/cid/transactions'}
        self.assertEqual(result, self.dkb._get_card_details('cid', card_dic, 'group_name', product_settings_dic))
        self.assertFalse(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_185__get_card_details(self, mock_dnl, mock_date, _unused):
        """ test _get_card_details() """
        card_dic = {'data': [{'id': 'cid', 'attributes': {'product': {'displayName': 'displayname'}, 'holder': {'person': {'firstName': 'firstname', 'lastName': 'lastname'}}, 'maskedPan': 'maskedPan', 'limit': {'value': 'value'}, 'balance': {'date': 'date', 'value': '101', 'currencyCode': 'currencycode'}}}]}
        product_settings_dic = {'creditCards': {'foo': 'bar'}}
        mock_dnl.return_value = 'mock_dnl'
        mock_date.return_value = 'mock_date'
        result = {'type': 'creditcard', 'id': 'cid', 'productgroup': 'group_name', 'maskedpan': 'maskedPan', 'account': 'maskedPan', 'amount': -101.0, 'currencycode': 'currencycode', 'date': 'date', 'limit': 'value', 'holdername': 'firstname lastname', 'name': 'mock_dnl', 'transactions': 'https://banking.dkb.de/api/credit-card/cards/cid/transactions'}
        self.assertEqual(result, self.dkb._get_card_details('cid', card_dic, 'group_name', product_settings_dic))
        self.assertTrue(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_186__get_brokerage_details(self, mock_dnl, mock_date, _unused):
        """ test _get_brokerage_details() """
        product_settings_dic = {}
        brok_dic = {}
        mock_dnl.return_value = 'mock_dnl'
        mock_date.return_value = 'mock_date'
        self.assertFalse(self.dkb._get_brokerage_details('bid', brok_dic, 'group_name', product_settings_dic))
        self.assertFalse(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_187__get_brokerage_details(self, mock_dnl, mock_date, _unused):
        """ test _get_brokerage_details() """
        product_settings_dic = {}
        brok_dic = {'data': []}
        mock_dnl.return_value = 'mock_dnl'
        mock_date.return_value = 'mock_date'
        self.assertFalse(self.dkb._get_brokerage_details('bid', brok_dic, 'group_name', product_settings_dic))
        self.assertFalse(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_188__get_brokerage_details(self, mock_dnl, mock_date, _unused):
        """ test _get_brokerage_details() """
        product_settings_dic = {}
        brok_dic = {'data': [{'id': 'bid'}]}
        mock_dnl.return_value = 'mock_dnl'
        mock_date.return_value = 'mock_date'
        self.assertFalse(self.dkb._get_brokerage_details('bid', brok_dic, 'group_name', product_settings_dic))
        self.assertFalse(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_189__get_brokerage_details(self, mock_dnl, mock_date, _unused):
        """ test _get_brokerage_details() """
        product_settings_dic = {}
        brok_dic = {'data': [{'id': 'bid', 'attributes': {'holderName': 'holdername', 'depositAccountId': 'depositaccountid', 'brokerageAccountPerformance': {'currentValue': {'currencyCode': 'currentcycode', 'value': 'value'} }}}]}
        mock_dnl.return_value = 'mock_dnl'
        mock_date.return_value = 'mock_date'
        result = {'type': 'depot', 'id': 'bid', 'productgroup': 'group_name', 'name': 'holdername', 'holdername': 'holdername', 'account': 'depositaccountid', 'currencycode': 'currentcycode', 'amount': 'value', 'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/bid/positions?include=instrument%2Cquote'}
        self.assertEqual(result, self.dkb._get_brokerage_details('bid', brok_dic, 'group_name', product_settings_dic))
        self.assertFalse(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.dkb_robo.convert_date_format')
    @patch('dkb_robo.DKBRobo._display_name_lookup')
    def test_190__get_brokerage_details(self, mock_dnl, mock_date, _unused):
        """ test _get_brokerage_details() """
        product_settings_dic = {'brokerageAccounts': {'foo': 'bar'}}
        brok_dic = {'data': [{'id': 'bid', 'attributes': {'holderName': 'holdername', 'depositAccountId': 'depositaccountid', 'brokerageAccountPerformance': {'currentValue': {'currencyCode': 'currentcycode', 'value': 'value'} }}}]}
        mock_dnl.return_value = 'mock_dnl'
        mock_date.return_value = 'mock_date'
        result = {'type': 'depot', 'id': 'bid', 'productgroup': 'group_name', 'name': 'mock_dnl', 'holdername': 'holdername', 'account': 'depositaccountid', 'currencycode': 'currentcycode', 'amount': 'value', 'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/bid/positions?include=instrument%2Cquote'}
        self.assertEqual(result, self.dkb._get_brokerage_details('bid', brok_dic, 'group_name', product_settings_dic))
        self.assertTrue(mock_dnl.called)
        self.assertFalse(mock_date.called)

    @patch('dkb_robo.DKBRobo._get_brokerage_details')
    @patch('dkb_robo.DKBRobo._get_card_details')
    @patch('dkb_robo.DKBRobo._get_account_details')
    def test_191__sort_product_group(self, mock_acc, mock_card, mock_br, _unused):
        """ test _sort_product_group() """
        product_group = {}
        self.assertEqual(({}, 0), self.dkb._sort_product_group(0, {}, 'group_name', product_group, {}, {}, {}))
        self.assertFalse(mock_acc.called)
        self.assertFalse(mock_card.called)
        self.assertFalse(mock_br.called)

    @patch('dkb_robo.DKBRobo._get_brokerage_details')
    @patch('dkb_robo.DKBRobo._get_card_details')
    @patch('dkb_robo.DKBRobo._get_account_details')
    def test_192__sort_product_group(self, mock_acc, mock_card, mock_br, _unused):
        """ test _sort_product_group() """
        product_group = {'products': {'foo': {'product1': {'index': 1}}}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(({},1), self.dkb._sort_product_group(0, {}, 'group_name', product_group, {}, {}, {}))
        self.assertIn('ERROR:dkb_robo:DKBRobo._sort_product_group(): product foo not implemented yet.', lcm.output)
        self.assertFalse(mock_acc.called)
        self.assertFalse(mock_card.called)
        self.assertFalse(mock_br.called)

    @patch('dkb_robo.DKBRobo._get_brokerage_details')
    @patch('dkb_robo.DKBRobo._get_card_details')
    @patch('dkb_robo.DKBRobo._get_account_details')
    def test_193__sort_product_group(self, mock_acc, mock_card, mock_br, _unused):
        """ test _sort_product_group() """
        product_group = {'products': {'accounts': {'product1': {'index': 1}}}}
        mock_acc.return_value = 'mock_acc'
        mock_card.return_value = 'mock_card'
        mock_br.return_value = 'mock_br'
        self.assertEqual(({0: 'mock_acc'}, 1), self.dkb._sort_product_group(0, {}, 'group_name', product_group, {}, {}, {}))
        self.assertTrue(mock_acc.called)
        self.assertFalse(mock_card.called)
        self.assertFalse(mock_br.called)

    @patch('dkb_robo.DKBRobo._get_brokerage_details')
    @patch('dkb_robo.DKBRobo._get_card_details')
    @patch('dkb_robo.DKBRobo._get_account_details')
    def test_194__sort_product_group(self, mock_acc, mock_card, mock_br, _unused):
        """ test _sort_product_group() """
        product_group = {'products': {'creditCards': {'product1': {'index': 1}}}}
        mock_acc.return_value = 'mock_acc'
        mock_card.return_value = 'mock_card'
        mock_br.return_value = 'mock_br'
        self.assertEqual(({0: 'mock_card'}, 1), self.dkb._sort_product_group(0, {}, 'group_name', product_group, {}, {}, {}))
        self.assertFalse(mock_acc.called)
        self.assertTrue(mock_card.called)
        self.assertFalse(mock_br.called)

    @patch('dkb_robo.DKBRobo._get_brokerage_details')
    @patch('dkb_robo.DKBRobo._get_card_details')
    @patch('dkb_robo.DKBRobo._get_account_details')
    def test_195__sort_product_group(self, mock_acc, mock_card, mock_br, _unused):
        """ test _sort_product_group() """
        product_group = {'products': {'brokerageAccounts': {'product1': {'index': 1}}}}
        mock_acc.return_value = 'mock_acc'
        mock_card.return_value = 'mock_card'
        mock_br.return_value = 'mock_br'
        self.assertEqual(({0: 'mock_br'}, 1), self.dkb._sort_product_group(0, {}, 'group_name', product_group, {}, {}, {}))
        self.assertFalse(mock_acc.called)
        self.assertFalse(mock_card.called)
        self.assertTrue(mock_br.called)

    @patch('dkb_robo.DKBRobo._get_brokerage_details')
    @patch('dkb_robo.DKBRobo._get_card_details')
    @patch('dkb_robo.DKBRobo._get_account_details')
    def test_196__sort_product_group(self, mock_acc, mock_card, mock_br, _unused):
        """ test _sort_product_group() """
        product_group = {'products': {'accounts': {'product1': {'index': 2}}, 'creditCards': {'product2': {'index': 1}}, 'brokerageAccounts': {'product3': {'index': 0}}}}
        mock_acc.return_value = 'mock_acc'
        mock_card.return_value = 'mock_card'
        mock_br.return_value = 'mock_br'
        self.assertEqual(({0: 'mock_acc', 1: 'mock_card', 2: 'mock_br'}, 3), self.dkb._sort_product_group(0, {}, 'group_name', product_group, {}, {}, {}))
        self.assertTrue(mock_acc.called)
        self.assertTrue(mock_card.called)
        self.assertTrue(mock_br.called)

    def test_197__build_account_dic(self, _unused):
        """ test _build_account_dic() """
        portfolio_dic = {}
        self.assertFalse(self.dkb._build_account_dic(portfolio_dic))


    def test_198__build_account_dic(self, _unused):
        """ test _build_account_dic() """
        portfolio_dic = {'product_display': {'data': []}}
        self.assertFalse(self.dkb._build_account_dic(portfolio_dic))

    @patch('dkb_robo.DKBRobo._sort_product_group')
    def test_199__build_account_dic(self, mock_sort, _unused):
        """ test _build_account_dic() """
        portfolio_dic = {'accounts': {}, 'cards': {}, 'brokerage_accounts': {}, 'product_display': {'data': [{'attributes': {'productGroups':{'bla': {'index': 0, 'name': 'name'}}}}]}}
        mock_sort.side_effect = [({'foo': 'bar'}, 1), ({'foo2': 'bar2'}, 2)]
        self.assertEqual({'foo': 'bar'}, self.dkb._build_account_dic(portfolio_dic))

    @patch('dkb_robo.DKBRobo._sort_product_group')
    def test_200__build_account_dic(self, mock_sort, _unused):
        """ test _build_account_dic() """
        portfolio_dic = {'accounts': {}, 'cards': {}, 'brokerage_accounts': {}, 'product_display': {'data': [{'attributes': {'productGroups':{'bla': {'index': 0, 'name': 'name'}, 'bla1': {'index': 1, 'name': 'name1'}}}}]}}
        mock_sort.side_effect = [({'foo': 'bar'}, 1), ({'foo2': 'bar2'}, 2)]
        self.assertEqual({'foo': 'bar', 'foo2': 'bar2'}, self.dkb._build_account_dic(portfolio_dic))

    @patch('dkb_robo.DKBRobo._sort_product_group')
    def test_201__build_account_dic(self, mock_sort, _unused):
        """ test _build_account_dic() """
        portfolio_dic = {'accounts': {}, 'cards': {}, 'brokerage_accounts': {}, 'product_display': {'data': [{'attributes': {'productGroups':{'bla': {'index': 0, 'name': 'name'}, 'bla1': {'index': 1, 'name': 'name1'}}, 'productSettings': {'pfoo': {'fbar'}}}}]}}
        mock_sort.side_effect = [({'foo': 'bar'}, 1), ({'foo2': 'bar2'}, 2)]
        self.assertEqual({'foo': 'bar', 'foo2': 'bar2'}, self.dkb._build_account_dic(portfolio_dic))

    def test_202__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = []
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        self.assertFalse(self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_203__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = [{'foo': 'bar', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo': 'bar', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_204__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-15'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_205__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype', 'bookingDate': '2023-02-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_206__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype2', 'bookingDate': '2023-01-15'}}]
        from_date = '01.01.2023'
        to_date = '31.01.2023'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_207__filter_transactions(self, _unused):
        """ test _filter_transactions() """
        transaction_list = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}, {'foo2': 'bar2', 'attributes': {'status': 'trtype2', 'bookingDate': '2023-01-15'}}]
        from_date = '2023-01-01'
        to_date = '2023-01-31'
        result = [{'foo1': 'bar1', 'attributes': {'status': 'trtype', 'bookingDate': '2023-01-10'}}]
        self.assertEqual(result, self.dkb._filter_transactions(transaction_list, from_date, to_date, 'trtype'))

    def test_208_format_card_transactions(self, _unused):
        """ _format_card_transactions() """
        transaction_list = []
        self.assertFalse(self.dkb._format_card_transactions(transaction_list))

    def test_209_format_card_transactions(self, _unused):
        """ _format_card_transactions() """
        transaction_list = [{'foo':'bar', 'attributes': {'description': 'description', 'bookingDate': '2023-01-01', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'CC', 'bdate': '2023-01-01', 'vdate': '2023-01-01', 'text': 'description'}]
        self.assertEqual(result, self.dkb._format_card_transactions(transaction_list))

    def test_210_format_card_transactions(self, _unused):
        """ _format_card_transactions() """
        transaction_list = [{'foo':'bar', 'attributes': {'bookingDate': '2023-01-01', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'CC', 'bdate': '2023-01-01', 'vdate': '2023-01-01'}]
        self.assertEqual(result, self.dkb._format_card_transactions(transaction_list))

    def test_211_format_card_transactions(self, _unused):
        """ _format_card_transactions() """
        transaction_list = [{'foo':'bar', 'attributes': {'description': 'description', 'amount': {'value': 1000, 'currencyCode': 'CC'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'CC', 'text': 'description'}]
        self.assertEqual(result, self.dkb._format_card_transactions(transaction_list))

    def test_212_format_brokerage_account(self, _unused):
        """ test _format_brokerage_account() """
        included_list = []
        data_dic = [{'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id'}}, 'quote': {'data': {'id': 'id', 'value': 'value'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_213_format_brokerage_account(self, _unused):
        """ test _format_brokerage_account() """
        included_list = []
        data_dic = [
            {'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id'}}, 'quote': {'data': {'id': 'id', 'value': 'value'}}}},
            {'attributes': {'performance': {'currentValue': {'value': 2000}}, 'lastOrderDate': '2020-02-01', 'quantity': {'value': 2000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'id2'}}, 'quote': {'data': {'id': 'id2', 'value': 'value2'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000}, {'shares': 2000, 'quantity': 2000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-02-01', 'price_euro': 2000}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_214_format_brokerage_account(self, _unused):
        """ test _format_brokerage_account() """
        included_list = [{'id': 'inid', 'attributes': {'identifiers': [{'identifier': 'isin', 'value': 'value'}, {'identifier': 'isin', 'value': 'value2'}], 'name': {'short': 'short'}}}]
        data_dic = [{'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'inid'}}, 'quote': {'data': {'id': 'quoteid', 'value': 'value'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000, 'text': 'short', 'isin_wkn': 'value'}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_215_format_brokerage_account(self, _unused):
        """ test _format_brokerage_account() """
        included_list = [{'id': 'quoteid', 'attributes': {'market': 'market', 'price': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        data_dic = [{'attributes': {'performance': {'currentValue': {'value': 1000}}, 'lastOrderDate': '2020-01-01', 'quantity': {'value': 1000, 'unit': 'unit'}}, 'relationships': {'instrument': {'data': {'id': 'inid'}}, 'quote': {'data': {'id': 'quoteid', 'value': 'value'}}}}]
        brokerage_dic = {'included': included_list, 'data': data_dic}
        result = [{'shares': 1000, 'quantity': 1000.0, 'shares_unit': 'unit', 'lastorderdate': '2020-01-01', 'price_euro': 1000, 'price': 1000.0, 'currencycode': 'currencyCode', 'market': 'market'}]
        self.assertEqual(result, self.dkb._format_brokerage_account(brokerage_dic))

    def test_216_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'foo': 'bar'}]
        self.assertFalse(self.dkb._format_account_transactions(transaction_list))

    def test_217_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'debtor': {'name': 'name', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}, 'amount': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'peerid': '', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreferenz': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_218_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'debtor': {'intermediaryName': 'intermediaryName', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}, 'amount': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'intermediaryName', 'peerid': '', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreferenz': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType intermediaryName description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_219_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'debtor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'debtorAccount': {'iban': 'iban'}}, 'amount': {'value': 1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': 1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'peerid': 'id', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreferenz': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_220_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'creditor': {'id': 'id', 'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}, 'amount': {'value': -1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': -1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'peerid': 'id', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreferenz': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    def test_221_format_account_transactions(self, _unused):
        """ test _format_account_transactions() """
        transaction_list = [{'attributes': {'description': 'description', 'transactionType': 'transactionType', 'endToEndId': 'endToEndId', 'valueDate': '2023-01-02', 'bookingDate': '2023-01-01', 'creditor': {'name': 'name', 'agent': {'bic': 'bic'}, 'creditorAccount': {'iban': 'iban'}}, 'amount': {'value': -1000, 'currencyCode': 'currencyCode'}}}]
        result = [{'amount': -1000.0, 'currencycode': 'currencyCode', 'peeraccount': 'iban', 'peerbic': 'bic', 'peer': 'name', 'peerid': '', 'date': '2023-01-01', 'bdate': '2023-01-01', 'vdate': '2023-01-02', 'customerreferenz': 'endToEndId', 'postingtext': 'transactionType', 'reasonforpayment': 'description', 'text': 'transactionType name description'}]
        self.assertEqual(result, self.dkb._format_account_transactions(transaction_list))

    @patch('dkb_robo.dkb_robo.validate_dates')
    @patch('dkb_robo.DKBRobo._get_transactions')
    @patch('dkb_robo.DKBRobo._legacy_get_transactions')
    def test_222_get_transactions(self, mock_legacy, mock_new, mock_date, _unused):
        """ test get_transactions() """
        mock_new.return_value = 'foo'
        mock_date.return_value = ('from', 'to')
        self.assertEqual('foo', self.dkb.get_transactions('url', 'atype', 'from', 'to', 'btype'))
        self.assertTrue(mock_new.called)
        self.assertFalse(mock_legacy.called)

    @patch('dkb_robo.dkb_robo.validate_dates')
    @patch('dkb_robo.DKBRobo._get_transactions')
    @patch('dkb_robo.DKBRobo._legacy_get_transactions')
    def test_223_get_transactions(self, mock_legacy, mock_new, mock_date, _unused):
        """ test get_transactions() """
        mock_legacy.return_value = 'foo_legacy'
        mock_date.return_value = ('from', 'to')
        self.dkb.legacy_login = True
        self.assertEqual('foo_legacy', self.dkb.get_transactions('url', 'atype', 'from', 'to', 'btype'))
        self.assertFalse(mock_new.called)
        self.assertTrue(mock_legacy.called)

    @patch('dkb_robo.dkb_robo.validate_dates')
    @patch('dkb_robo.DKBRobo._get_transactions')
    @patch('dkb_robo.DKBRobo._legacy_get_transactions')
    def test_224_get_transactions(self, mock_legacy, mock_new, mock_date, _unused):
        """ test get_transactions() """
        mock_new.return_value = 'foo'
        mock_date.return_value = ('from', 'to')
        self.dkb.legacy_login = False
        self.assertEqual('foo', self.dkb.get_transactions('url', 'atype', 'from', 'to', 'btype'))
        self.assertTrue(mock_new.called)
        self.assertFalse(mock_legacy.called)

    def test_225_enforce_date_format(self, _unused):
        """ test enforce_date_format() - old frontend - old date format """
        self.assertEqual(('01.01.2023', '02.01.2023'), self.enforce_date_format(self.logger, '01.01.2023', '02.01.2023', 3))

    def test_226_enforce_date_format(self, _unused):
        """ test enforce_date_format() - old frontend - new date format """
        self.assertEqual(('01.04.2023', '02.04.2023'), self.enforce_date_format(self.logger, '2023-04-01', '2023-04-02', 3))

    def test_227_enforce_date_format(self, _unused):
        """ test enforce_date_format() - new frontend - new date format """
        self.assertEqual(('2023-01-01', '2023-01-02'), self.enforce_date_format(self.logger, '2023-01-01', '2023-01-02', 1))

    def test_228_enforce_date_format(self, _unused):
        """ test enforce_date_format() - new frontend - old date format """
        self.assertEqual(('2023-01-01', '2023-01-02'), self.enforce_date_format(self.logger, '01.01.2023', '02.01.2023', 1))


if __name__ == '__main__':

    unittest.main()
