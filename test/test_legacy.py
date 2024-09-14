# -*- coding: utf-8 -*-
# pylint: disable=r0904, c0415, c0413, r0913, w0212
""" unittests for dkb_robo """
import sys
import os
from datetime import date
import unittest
import logging
import json
from unittest.mock import patch, Mock, mock_open
from bs4 import BeautifulSoup
from mechanicalsoup import LinkNotFoundError
sys.path.insert(0, '.')
sys.path.insert(0, '..')
from dkb_robo.legacy import Wrapper


def json_load(fname):
    """ simple json load """

    with open(fname, 'r', encoding='utf8') as myfile:
        data_dic = json.load(myfile)

    return data_dic


def read_file(fname):
    """ read file into string """
    with open(fname, "rb") as myfile:
        data = myfile.read()

    return data


def cnt_list(value):
    """ customized function return just the number if entries in input list """
    return len(value)


def my_side_effect(*args):
    """ my sideeffect funtion """
    return [200, args[1], [args[4]]]


@patch('dkb_robo.legacy.Wrapper.dkb_br')
class TestDKBRobo(unittest.TestCase):
    """ test class """

    maxDiff = None

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')
        self.wrapper = Wrapper(logger=self.logger)

    def test_001_get_cc_limit(self, mock_browser):
        """ test Legacy._get_credit_limits() method """
        html = read_file(self.dir_path + '/mocks/konto-kreditkarten-limits.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {'1111********1111': 100.00,
                    '1111********1112': 2000.00,
                    'DE01 1111 1111 1111 1111 11': 1000.00,
                    'DE02 1111 1111 1111 1111 12': 2000.00}

        self.assertEqual(e_result, self.wrapper.get_credit_limits())

    def test_002_get_cc_limit(self, mock_browser):
        """ test legacy.get_credit_limits() triggers exceptions """
        html = read_file(self.dir_path + '/mocks/konto-kreditkarten-limits-exception.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {'DE01 1111 1111 1111 1111 11': 1000.00, 'DE02 1111 1111 1111 1111 12': 2000.00}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(e_result, self.wrapper.get_credit_limits())
        self.assertIn("ERROR:dkb_robo:legacy.Wrapper.get_credit_limits() get credit card limits: 'NoneType' object has no attribute 'find'\n", lcm.output)

    def test_003_get_cc_limit(self, mock_browser):
        """ test legacy.get_credit_limits() no limits """
        # html = read_file(self.dir_path + '/mocks/konto-kreditkarten-limits-exception.html')
        html = '<html><body>fooo</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {}
        self.assertEqual(e_result, self.wrapper.get_credit_limits())

    def test_004_get_exo_single(self, mock_browser):
        """ test legacy.get_exemption_order() method for a single exemption order """
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0, 'amount': 1000.0, 'used': 0.0, 'description': 'Gemeinsam mit Firstname Familyname', 'validity': '01.01.2016 unbefristet'}}
        self.assertEqual(self.wrapper.get_exemption_order(), e_result)

    def test_005_get_exo_single_nobr(self, mock_browser):
        """ test legacy.get_exemption_order() method for a single exemption order without line-breaks"""
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag-nobr.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0, 'amount': 1000.0, 'used': 0.0, 'description': 'Gemeinsam mit Firstname Familyname', 'validity': '01.01.2016 unbefristet'}}
        self.assertEqual(self.wrapper.get_exemption_order(), e_result)

    def test_006_get_exo_multiple(self, mock_browser):
        """ test legacy.get_exemption_order() method for a multiple exemption orders """
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag-multiple.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0,
                        'amount': 1000.0,
                        'used': 0.0,
                        'description': 'Gemeinsam mit Firstname1 Familyname1',
                        'validity': '01.01.2016 unbefristet'},
                    2: {'available': 2000.0,
                        'amount': 2000.0,
                        'used': 0.0,
                        'description': 'Gemeinsam mit Firstname2 Familyname2',
                        'validity': '02.01.2016 unbefristet'}}

        self.assertEqual(self.wrapper.get_exemption_order(), e_result)

    def test_007_get_exo_single(self, mock_browser):
        """ test legacy.get_exemption_order() method try throws exception """
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag-indexerror.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(self.wrapper.get_exemption_order(), e_result)
        self.assertIn('ERROR:dkb_robo:legacy.Wrapper.get_exemption_order(): list index out of range\n', lcm.output)

    def test_008_new_instance(self, _unused):
        """ test legacy._new_instance() method """
        self.assertIn('mechanicalsoup.stateful_browser.StatefulBrowser object at', str(self.wrapper._new_instance()))

    def test_009_new_instance(self, _unused):
        """ test legacy._new_instance() method with proxies """
        self.wrapper.proxies = 'proxies'
        self.assertIn('mechanicalsoup.stateful_browser.StatefulBrowser object at', str(self.wrapper._new_instance()))
        self.assertEqual('proxies', self.wrapper.dkb_br.session.proxies)

    def test_010_new_instance(self, _unused):
        """ test legacy._new_instance() method with clientcookies """
        cookieobj = Mock()
        cookieobj.value = 'value'
        cookieobj.name = 'name'
        self.assertIn('mechanicalsoup.stateful_browser.StatefulBrowser object at', str(self.wrapper._new_instance([cookieobj])))

    def test_011_get_points(self, mock_browser):
        """ test legacy.get_points() method """
        html = read_file(self.dir_path + '/mocks/dkb_punkte.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {'DKB-Punkte': 100000, 'davon verfallen zum  31.12.2017': 90000}
        self.assertEqual(self.wrapper.get_points(), e_result)

    def test_012_get_so_multiple(self, mock_browser):
        """ test legacy._get_standing_orders() method """
        html = read_file(self.dir_path + '/mocks/dauerauftraege.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = [{'amount': 100.0, 'interval': '1. monatlich 01.03.2017', 'recipient': 'RECPIPIENT-1', 'purpose': 'KV 1234567890'},
                    {'amount': 200.0, 'interval': '1. monatlich geloescht', 'recipient': 'RECPIPIENT-2', 'purpose': 'KV 0987654321'}]
        self.assertEqual(self.wrapper.get_standing_orders(), e_result)

    @patch('dkb_robo.legacy.Wrapper._parse_overview')
    @patch('dkb_robo.legacy.Wrapper._get_financial_statement')
    @patch('dkb_robo.legacy.Wrapper._login_confirm')
    @patch('dkb_robo.legacy.Wrapper._ctan_check')
    @patch('dkb_robo.legacy.Wrapper._new_instance')
    def test_013_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test legacy._login() method - no confirmation """
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
        self.assertEqual(({}, '01.03.2017, 01:00 Uhr'), self.wrapper.login())
        self.assertTrue(mock_confirm.called)
        self.assertFalse(mock_ctan.called)
        self.assertFalse(mock_fs.called)
        self.assertFalse(mock_pov.called)

    @patch('dkb_robo.legacy.Wrapper._parse_overview')
    @patch('dkb_robo.legacy.Wrapper._get_financial_statement')
    @patch('dkb_robo.legacy.Wrapper._login_confirm')
    @patch('dkb_robo.legacy.Wrapper._ctan_check')
    @patch('dkb_robo.legacy.Wrapper._new_instance')
    def test_014_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test legacy.login() method - confirmation """
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
        self.assertEqual(('_parse_overview', '01.03.2017, 01:00 Uhr'), self.wrapper.login())
        self.assertTrue(mock_confirm.called)
        self.assertFalse(mock_ctan.called)
        self.assertTrue(mock_fs.called)
        self.assertTrue(mock_pov.called)

    @patch('dkb_robo.legacy.Wrapper._parse_overview')
    @patch('dkb_robo.legacy.Wrapper._get_financial_statement')
    @patch('dkb_robo.legacy.Wrapper._login_confirm')
    @patch('dkb_robo.legacy.Wrapper._ctan_check')
    @patch('dkb_robo.legacy.Wrapper._new_instance')
    def test_015_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test legacy._login() method - no confirmation """
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
        self.wrapper.tan_insert = True
        self.assertEqual(({}, '01.03.2017, 01:00 Uhr'), self.wrapper.login())
        self.assertFalse(mock_confirm.called)
        self.assertTrue(mock_ctan.called)
        self.assertFalse(mock_fs.called)
        self.assertFalse(mock_pov.called)

    @patch('dkb_robo.legacy.Wrapper._parse_overview')
    @patch('dkb_robo.legacy.Wrapper._get_financial_statement')
    @patch('dkb_robo.legacy.Wrapper._login_confirm')
    @patch('dkb_robo.legacy.Wrapper._ctan_check')
    @patch('dkb_robo.legacy.Wrapper._new_instance')
    def test_016_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test legacy._login() method - confirmation """
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
        self.wrapper.tan_insert = True
        self.assertEqual(('_parse_overview', '01.03.2017, 01:00 Uhr'), self.wrapper.login())
        self.assertFalse(mock_confirm.called)
        self.assertTrue(mock_ctan.called)
        self.assertTrue(mock_fs.called)
        self.assertTrue(mock_pov.called)

    @patch('dkb_robo.legacy.Wrapper._parse_overview')
    @patch('dkb_robo.legacy.Wrapper._get_financial_statement')
    @patch('dkb_robo.legacy.Wrapper._login_confirm')
    @patch('dkb_robo.legacy.Wrapper._ctan_check')
    @patch('dkb_robo.legacy.Wrapper._new_instance')
    def test_017_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test legacy._login() login failed """
        html = """
                <div id="lastLoginContainer" class="clearfix module text errorMessage">foo</div>
               """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_ctan.return_value = True
        mock_confirm.return_value = False
        mock_instance.return_value = mock_browser
        mock_pov.return_value = '_parse_overview'
        mock_fs.return_value = 'mock_fs'
        self.wrapper.tan_insert = True
        with self.assertRaises(Exception) as err:
            self.assertEqual(self.wrapper.login(), None)
        self.assertEqual('Login failed', str(err.exception))
        self.assertFalse(mock_confirm.called)
        self.assertFalse(mock_ctan.called)
        self.assertFalse(mock_fs.called)
        self.assertFalse(mock_pov.called)

    @patch('dkb_robo.legacy.Wrapper._parse_overview')
    @patch('dkb_robo.legacy.Wrapper._get_financial_statement')
    @patch('dkb_robo.legacy.Wrapper._login_confirm')
    @patch('dkb_robo.legacy.Wrapper._ctan_check')
    @patch('dkb_robo.legacy.Wrapper._new_instance')
    def test_018_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test legacy._login() login failed """
        mock_browser.select_form.side_effect = LinkNotFoundError
        mock_ctan.return_value = True
        mock_confirm.return_value = False
        mock_instance.return_value = mock_browser
        mock_pov.return_value = '_parse_overview'
        mock_fs.return_value = 'mock_fs'
        self.wrapper.tan_insert = True
        with self.assertRaises(Exception) as err:
            self.assertEqual(self.wrapper.login(), None)
        self.assertEqual('Login failed: LinkNotFoundError', str(err.exception))
        self.assertFalse(mock_confirm.called)
        self.assertFalse(mock_ctan.called)
        self.assertFalse(mock_fs.called)
        self.assertFalse(mock_pov.called)

    @patch('dkb_robo.legacy.Wrapper._parse_overview')
    @patch('dkb_robo.legacy.Wrapper._get_financial_statement')
    @patch('dkb_robo.legacy.Wrapper._login_confirm')
    @patch('dkb_robo.legacy.Wrapper._ctan_check')
    @patch('dkb_robo.legacy.Wrapper._new_instance')
    def test_019_login(self, mock_instance, mock_ctan, mock_confirm, mock_fs, mock_pov, mock_browser):
        """ test legacy._login() method - notice form """
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
        self.wrapper.tan_insert = True
        self.assertEqual(('_parse_overview', '01.03.2017, 01:00 Uhr'), self.wrapper.login())
        self.assertFalse(mock_confirm.called)
        self.assertTrue(mock_ctan.called)
        self.assertTrue(mock_fs.called)
        self.assertTrue(mock_pov.called)

    def test_020_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() method """
        html = read_file(self.dir_path + '/mocks/finanzstatus.html')
        e_result = {0: {'account': 'XY99 1111 1111 0000 1111 99',
                        'amount': 1367.82,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=0',
                        'name': 'hauptkonto',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=0',
                        'type': 'account'},
                    1: {'account': '9999********1111',
                        'amount': 9613.31,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=0',
                        'name': 'first visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=0',
                        'type': 'creditcard'},
                    2: {'account': '9999********8888',
                        'amount': -260.42,
                        'date': '26.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=0',
                        'name': 'MilesnMoreMaster',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=0',
                        'type': 'creditcard'},
                    3: {'account': '9999********2222',
                        'amount': 515.52,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=1',
                        'name': 'second visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=1',
                        'type': 'creditcard'},
                    4: {'account': 'XY99 1111 1111 2155 2788 99',
                        'amount': 588.37,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=1',
                        'name': 'zweitkonto',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=1',
                        'type': 'account'},
                    5: {'account': '9999********3333',
                        'amount': 515.52,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=1',
                        'name': '3rd visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=1',
                        'type': 'creditcard'},
                    6: {'account': 'XY99 3333 1111 0000 3333 99',
                        'amount': -334.34,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=3&group=1',
                        'name': '3rd acc',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=3&group=1',
                        'type': 'account'}}

        self.assertEqual(self.wrapper._parse_overview(BeautifulSoup(html, 'html5lib')), e_result)

    def test_021_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() method """
        html = read_file(self.dir_path + '/mocks/finanzstatus-error1.html')
        e_result = {0: {'account': 'XY99 1111 1111 0000 1111 99',
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=0',
                        'name': 'hauptkonto',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=0',
                        'type': 'account'},
                    1: {'account': '9999********1111',
                        'amount': 9613.31,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=0',
                        'name': 'first visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=0',
                        'type': 'creditcard'},
                    2: {'account': '9999********8888',
                        'amount': -260.42,
                        'date': '26.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=0',
                        'name': 'MilesnMoreMaster',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=0',
                        'type': 'creditcard'},
                    3: {'account': '9999********2222',
                        'amount': 515.52,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=1',
                        'name': 'second visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=1',
                        'type': 'creditcard'},
                    4: {'account': 'XY99 1111 1111 2155 2788 99',
                        'amount': 588.37,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=1',
                        'name': 'zweitkonto',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=1',
                        'type': 'account'},
                    5: {'account': '9999********3333',
                        'amount': 515.52,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=1',
                        'name': '3rd visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=1',
                        'type': 'creditcard'},
                    6: {'account': 'XY99 3333 1111 0000 3333 99',
                        'amount': -334.34,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=3&group=1',
                        'name': '3rd acc',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=3&group=1',
                        'type': 'account'}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(self.wrapper._parse_overview(BeautifulSoup(html, 'html5lib')), e_result)
        self.assertIn("ERROR:dkb_robo:legacy.Wrapper._parse_overview() convert amount: could not convert string to float: 'aaa'\n", lcm.output)

    def test_022_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() exception detail link"""
        html = read_file(self.dir_path + '/mocks/finanzstatus-error2.html')
        e_result = {0: {'account': 'XY99 1111 1111 0000 1111 99',
                        'amount': 1367.82,
                        'date': '27.04.2018',
                        'name': 'hauptkonto',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=0',
                        'type': 'account'},
                    1: {'account': '9999********1111',
                        'amount': 9613.31,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=0',
                        'name': 'first visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=0',
                        'type': 'creditcard'},
                    2: {'account': '9999********8888',
                        'amount': -260.42,
                        'date': '26.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=0',
                        'name': 'MilesnMoreMaster',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=0',
                        'type': 'creditcard'},
                    3: {'account': '9999********2222',
                        'amount': 515.52,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=1',
                        'name': 'second visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=1',
                        'type': 'creditcard'},
                    4: {'account': 'XY99 1111 1111 2155 2788 99',
                        'amount': 588.37,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=1',
                        'name': 'zweitkonto',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=1',
                        'type': 'account'},
                    5: {'account': '9999********3333',
                        'amount': 515.52,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=1',
                        'name': '3rd visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=1',
                        'type': 'creditcard'},
                    6: {'account': 'XY99 3333 1111 0000 3333 99',
                        'amount': -334.34,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=3&group=1',
                        'name': '3rd acc',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=3&group=1',
                        'type': 'account'}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(self.wrapper._parse_overview(BeautifulSoup(html, 'html5lib')), e_result)
        self.assertIn("ERROR:dkb_robo:legacy.Wrapper._parse_overview() get link: 'NoneType' object is not subscriptable\n", lcm.output)

    def test_023_parse_overview(self, _unused):
        """ test DKBRobo._parse_overview() exception depot """
        html = read_file(self.dir_path + '/mocks/finanzstatus-error3.html')
        e_result = {0: {'account': 'XY99 1111 1111 0000 1111 99',
                        'amount': 1367.82,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=0',
                        'name': 'hauptkonto',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=0',
                        'type': 'account'},
                    1: {'account': '9999********1111',
                        'amount': 9613.31,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=0',
                        'name': 'first visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=0',
                        'type': 'creditcard'},
                    2: {'account': '9999********8888',
                        'amount': -260.42,
                        'date': '26.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=0',
                        'name': 'MilesnMoreMaster',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=0',
                        'type': 'creditcard'},
                    3: {'account': '9999********2222',
                        'amount': 515.52,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=0&group=1',
                        'name': 'second visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=0&group=1',
                        'type': 'creditcard'},
                    4: {'account': 'XY99 1111 1111 2155 2788 99',
                        'amount': 588.37,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=1&group=1',
                        'name': 'zweitkonto',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=1&group=1',
                        'type': 'account'},
                    5: {'account': '9999********3333',
                        'amount': 515.52,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=2&group=1',
                        'name': '3rd visa',
                        'transactions': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=paymentTransaction&row=2&group=1',
                        'type': 'creditcard'},
                    6: {'account': 'XY99 3333 1111 0000 3333 99',
                        'amount': -334.34,
                        'date': '27.04.2018',
                        'details': 'https://www.ib.dkb.de/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=details&row=3&group=1',
                        'name': '3rd acc',
                        'type': 'depot'}}
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(e_result, self.wrapper._parse_overview(BeautifulSoup(html, 'html5lib')))
        self.assertIn("ERROR:dkb_robo:legacy.Wrapper._parse_overview() parse depot: 'NoneType' object is not subscriptable\n", lcm.output)

    def test_024_parse_overview_mbank(self, _unused):
        """ test DKBRobo._parse_overview() method for accounts from other banks"""
        html = read_file(self.dir_path + '/mocks/finanzstatus-mbank.html')
        e_result = {0: {'account': '1111********1111',
                        'name': 'credit-card-1',
                        'transactions': 'https://www.ib.dkb.de/tcc-1',
                        'amount': 1000.0,
                        'details': 'https://www.ib.dkb.de/dcc-1',
                        'date': '01.03.2017',
                        'type': 'creditcard'},
                    1: {'account': '1111********1112',
                        'name': 'credit-card-2',
                        'transactions': 'https://www.ib.dkb.de/tcc-2',
                        'amount': 2000.0,
                        'details': 'https://www.ib.dkb.de/dcc-2',
                        'date': '02.03.2017',
                        'type': 'creditcard'},
                    2: {'account': 'DE11 1111 1111 1111 1111 11',
                        'name': 'checking-account-1',
                        'transactions': 'https://www.ib.dkb.de/tac-1',
                        'amount': 1000.0,
                        'details': 'https://www.ib.dkb.de/banking/dac-1',
                        'date': '03.03.2017',
                        'type': 'account'},
                    3: {'account': 'DE11 1111 1111 1111 1111 12',
                        'name': 'checking-account-2',
                        'transactions': 'https://www.ib.dkb.de/tac-2',
                        'amount': 2000.0,
                        'details': 'https://www.ib.dkb.de/banking/dac-2',
                        'date': '04.03.2017',
                        'type': 'account'},
                    4: {'account': '1111111',
                        'name': 'Depot-1',
                        'transactions': 'https://www.ib.dkb.de/tdepot-1',
                        'amount': 5000.0,
                        'details': 'https://www.ib.dkb.de/ddepot-1',
                        'date': '06.03.2017',
                        'type': 'depot'},
                    5: {'account': '1111112',
                        'name': 'Depot-2',
                        'transactions': 'https://www.ib.dkb.de/tdepot-2',
                        'amount': 6000.0,
                        'details': 'https://www.ib.dkb.de/ddepot-2',
                        'date': '06.03.2017',
                        'type': 'depot'}}
        self.assertEqual(self.wrapper._parse_overview(BeautifulSoup(html, 'html5lib')), e_result)

    def test_025_get_document_links(self, mock_browser):
        """ test DKBRobo._get_document_links() method """
        html = read_file(self.dir_path + '/mocks/doclinks.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {'Kontoauszug Nr. 003_2017 zu Konto 87654321': 'https://www.ib.dkb.de/doc-2',
                    'Kontoauszug Nr. 003_2017 zu Konto 12345678': 'https://www.ib.dkb.de/doc-1'}
        self.assertEqual(self.wrapper._get_document_links('http://foo.bar/foo'), e_result)

    @patch('dkb_robo.legacy.Wrapper._update_downloadstate')
    @patch('dkb_robo.legacy.Wrapper._get_document')
    def test_026_get_document_links(self, mock_doc, mock_updow, mock_browser):
        """ test DKBRobo._get_document_links() method """
        html = read_file(self.dir_path + '/mocks/doclinks-2.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doc.return_value = (200, 'fname', ['foo'])
        e_result = {'Kontoauszug Nr. 003_2017 zu Konto 12345678': {'rcode': 200, 'link': 'https://www.ib.dkb.de/doc-1', 'fname': 'fname'}, 'Kontoauszug Nr. 003_2017 zu Konto 87654321': {'rcode': 200, 'link': 'https://www.ib.dkb.de/doc-2', 'fname': 'fname'}}
        self.assertEqual(e_result, self.wrapper._get_document_links('http://foo.bar/foo', path='path'))
        self.assertTrue(mock_updow.called)

    @patch('dkb_robo.legacy.Wrapper._update_downloadstate')
    @patch('dkb_robo.legacy.Wrapper._get_document')
    def test_027_get_document_links(self, mock_doc, mock_updow, mock_browser):
        """ test DKBRobo._get_document_links() method """
        html1 = read_file(self.dir_path + '/mocks/doclinks-3.html')
        html2 = read_file(self.dir_path + '/mocks/doclinks-2.html')
        mock_browser.get_current_page.side_effect = [BeautifulSoup(html1, 'html5lib'), BeautifulSoup(html2, 'html5lib')]
        mock_browser.open.return_value = True
        mock_doc.return_value = (None, 'fname', ['foo'])
        e_result = {'Kontoauszug Nr. 003_2017 zu Konto 23456789': 'https://www.ib.dkb.de/doc-1',
                    'Kontoauszug Nr. 003_2017 zu Konto 12345678': 'https://www.ib.dkb.de/doc-1',
                    'Kontoauszug Nr. 003_2017 zu Konto 87654321': 'https://www.ib.dkb.de/doc-2',
                    'Kontoauszug Nr. 003_2017 zu Konto 98765432': 'https://www.ib.dkb.de/doc-2'}
        self.assertEqual(e_result, self.wrapper._get_document_links('http://foo.bar/foo', path='path'))
        self.assertFalse(mock_updow.called)

    @patch('dkb_robo.legacy.Wrapper._update_downloadstate')
    @patch('dkb_robo.legacy.Wrapper._get_document')
    def test_028_get_document_links(self, mock_doc, mock_updow, mock_browser):
        """ test DKBRobo._get_document_links() method no html return """
        mock_browser.get_current_page.return_value = None
        mock_browser.open.return_value = True
        mock_doc.return_value = (None, 'fname', ['foo'])
        e_result = {}
        self.assertEqual(e_result, self.wrapper._get_document_links('http://foo.bar/foo', path='path'))
        self.assertFalse(mock_updow.called)

    @patch('dkb_robo.legacy.Wrapper._update_downloadstate')
    @patch('dkb_robo.legacy.Wrapper._get_document')
    def test_029_get_document_links(self, mock_doc, mock_updow, mock_browser):
        """ test DKBRobo._get_document_links() method  wrong html return """
        html = '<html><body>fooo</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_browser.open.return_value = True
        mock_doc.return_value = (None, 'fname', ['foo'])
        e_result = {}
        self.assertEqual(e_result, self.wrapper._get_document_links('http://foo.bar/foo', path='path'))
        self.assertFalse(mock_updow.called)

    @patch('dkb_robo.legacy.Wrapper._get_document_links')
    def test_030_scan_postbox(self, mock_doclinks, mock_browser):
        """ test DKBRobo.scan_postbox() method """
        html = read_file(self.dir_path + '/mocks/postbox.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doclinks.return_value = {}
        e_result = {'Kreditkartenabrechnungen': {'documents': {}, 'name': 'Kreditkartenabrechnungen', 'details': 'https://www.ib.dkb.de/banking/postfach/Kreditkartenabrechnungen'},
                    'Mitteilungen': {'documents': {}, 'name': 'Mitteilungen', 'details': 'https://www.ib.dkb.de/banking/postfach/Mitteilungen'},
                    'Vertragsinformationen': {'documents': {}, 'name': 'Vertragsinformationen', 'details': 'https://www.ib.dkb.de/banking/postfach/Vertragsinformationen'}}
        self.assertEqual(self.wrapper.scan_postbox(), e_result)

    @patch('dkb_robo.legacy.Wrapper._get_document_links')
    def test_031_scan_postbox(self, mock_doclinks, mock_browser):
        """ test DKBRobo.scan_postbox() method """
        html = read_file(self.dir_path + '/mocks/postbox.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doclinks.return_value = {}
        e_result = {'Kreditkartenabrechnungen':
                        {'documents': {},
                         'name': 'Kreditkartenabrechnungen',
                         'details': 'https://www.ib.dkb.de/banking/postfach/Kreditkartenabrechnungen'},
                    'Mitteilungen':
                        {'documents': {},
                         'name': 'Mitteilungen',
                         'details': 'https://www.ib.dkb.de/banking/postfach/Mitteilungen'},
                    'Vertragsinformationen':
                        {'documents': {},
                         'name': 'Vertragsinformationen',
                         'details': 'https://www.ib.dkb.de/banking/postfach/Vertragsinformationen'}}
        self.assertEqual(self.wrapper.scan_postbox(path='path'), e_result)

    @patch('dkb_robo.legacy.Wrapper._get_document_links')
    def test_032_scan_postbox(self, mock_doclinks, mock_browser):
        """ test DKBRobo.scan_postbox() method """
        html = read_file(self.dir_path + '/mocks/postbox-2.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_doclinks.return_value = {}
        e_result = {'Kreditkartenabrechnungen':
                        {'documents': {},
                         'name': 'Kreditkartenabrechnungen',
                         'details': 'https://www.ib.dkb.de/banking/postfach/Kreditkartenabrechnungen'},
                    'Mitteilungen':
                        {'documents': {},
                         'name': 'Mitteilungen',
                         'details': 'https://www.ib.dkb.de/banking/postfach/Mitteilungen'},
                    'Vertragsinformationen':
                        {'documents': {},
                         'name': 'Vertragsinformationen',
                         'details': 'https://www.ib.dkb.de/banking/postfach/Vertragsinformationen'}}
        self.assertEqual(self.wrapper.scan_postbox(archive=True), e_result)

    def test_033_get_tr_invalid(self, _unused):
        """ test DKBRobo.get_transactions() method with an invalid account type"""
        self.assertEqual(self.wrapper.get_transactions('url', 'foo', '01.03.2017', '02.03.2017'), [])

    @patch('dkb_robo.legacy.Wrapper._get_creditcard_transactions')
    def test_034_get_tr_cc(self, mock_cc_tran, _unused):
        """ test DKBRobo.get_transactions() method with an credit-card account"""
        mock_cc_tran.return_value = ['credit_card']
        self.assertEqual(self.wrapper.get_transactions('url', 'creditcard', '01.03.2017', '02.03.2017'), ['credit_card'])
        self.assertTrue(mock_cc_tran.called)

    @patch('dkb_robo.legacy.Wrapper._get_account_transactions')
    def test_035_get_tr_ac(self, mock_ca_tran, _unused):
        """ test DKBRobo.get_transactions() method with an checking account"""
        mock_ca_tran.return_value = ['account']
        self.assertEqual(self.wrapper.get_transactions('url', 'account', '01.03.2017', '02.03.2017'), ['account'])
        self.assertTrue(mock_ca_tran.called)

    @patch('dkb_robo.legacy.Wrapper._get_depot_status')
    def test_036_get_tr_ac(self, mock_dep_tran, _unused):
        """ test DKBRobo.get_transactions() method for a deptot """
        mock_dep_tran.return_value = ['dep']
        self.assertEqual(self.wrapper.get_transactions('url', 'depot', '01.03.2017', '02.03.2017'), ['dep'])
        self.assertTrue(mock_dep_tran.called)

    def test_037_parse_account_tr(self, _mock_browser):
        """ test DKBRobo.get_account_transactions for one page only """
        csv = read_file(self.dir_path + '/mocks/test_parse_account_tr.csv')
        result = [
            {'amount': 100.0, 'bdate': '01.03.2017', 'customerreferenz': 'Kundenreferenz1', 'customerreference': 'Kundenreferenz1', 'date': '01.03.2017', 'mandatereference': 'Mandatsreferenz1', 'peer': 'Auftraggeber1', 'peeraccount': 'Kontonummer1', 'peerbic': 'BLZ1', 'peerid': 'GID1', 'postingtext': 'Buchungstext1', 'reasonforpayment': 'Verwendungszweck1', 'text': 'Buchungstext1 Auftraggeber1 Verwendungszweck1', 'vdate': '01.03.2017'},
            {'amount': -200.0, 'bdate': '02.03.2017', 'customerreferenz': 'Kundenreferenz2', 'customerreference': 'Kundenreferenz2', 'date': '02.03.2017', 'mandatereference': 'Mandatsreferenz2', 'peer': 'Auftraggeber2', 'peeraccount': 'Kontonummer2', 'peerbic': 'BLZ2', 'peerid': 'GID2', 'postingtext': 'Buchungstext2', 'reasonforpayment': 'Verwendungszweck2', 'text': 'Buchungstext2 Auftraggeber2 Verwendungszweck2', 'vdate': '02.03.2017'},
            {'amount': 3000.0, 'bdate': '03.03.2017', 'customerreferenz': 'Kundenreferenz3', 'customerreference': 'Kundenreferenz3', 'date': '03.03.2017', 'mandatereference': 'Mandatsreferenz3', 'peer': 'Auftraggeber3', 'peeraccount': 'Kontonummer3', 'peerbic': 'BLZ3', 'peerid': 'GID3', 'postingtext': 'Buchungstext3', 'reasonforpayment': 'Verwendungszweck3', 'text': 'Buchungstext3 Auftraggeber3 Verwendungszweck3', 'vdate': '03.03.2017'},
            {'amount': -4000.0, 'bdate': '04.03.2017', 'customerreferenz': 'Kundenreferenz4', 'customerreference': 'Kundenreferenz4', 'date': '04.03.2017', 'mandatereference': 'Mandatsreferenz4', 'peer': 'Auftraggeber4', 'peeraccount': 'Kontonummer4', 'peerbic': 'BLZ4', 'peerid': 'GID4', 'postingtext': 'Buchungstext4', 'reasonforpayment': 'Verwendungszweck4', 'text': 'Buchungstext4 Auftraggeber4 Verwendungszweck4', 'vdate': '04.03.2017'}]

        self.assertEqual(result, self.wrapper._parse_account_transactions(csv))

    def test_038_parse_no_account_tr(self, _mock_browser):
        """ test DKBRobo.get_account_transactions for one page only """
        csv = read_file(self.dir_path + '/mocks/test_parse_no_account_tr.csv')
        self.assertEqual(self.wrapper._parse_account_transactions(csv), [])

    def test_039_parse_dkb_cc_tr(self, _mock_browser):
        """ test DKBRobo._parse_cc_transactions """
        csv = read_file(self.dir_path + '/mocks/test_parse_dkb_cc_tr.csv')
        self.assertEqual(self.wrapper._parse_cc_transactions(csv), [{'amount': -100.00,
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
        self.assertEqual(self.wrapper._parse_cc_transactions(csv), [])

    def test_041_get_financial_statement(self, mock_browser):
        """ get financial statement """
        html = '<html><head>header</head><body>body</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertEqual('<html><head></head><body>headerbody</body></html>', str(self.wrapper._get_financial_statement()))

    def test_042_get_financial_statement(self, mock_browser):
        """ get financial statement with tan_insert """
        html = '<html><head>header</head><body>body</body></html>'
        self.wrapper.tan_insert = True
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertEqual('<html><head></head><body>headerbody</body></html>', str(self.wrapper._get_financial_statement()))

    @patch('dkb_robo.legacy.Wrapper._parse_account_transactions')
    def test_043_get_account_transactions(self, mock_parse, mock_browser):
        """ test _get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.wrapper._get_account_transactions('url', 'date_from', 'date_to'))

    @patch('dkb_robo.legacy.Wrapper._parse_account_transactions')
    def test_044_get_account_transactions(self, mock_parse, mock_browser):
        """ test _get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.wrapper._get_account_transactions('url', 'date_from', 'date_to', transaction_type='reserved'))

    @patch('dkb_robo.legacy.Wrapper._parse_cc_transactions')
    def test_045_get_cc_transactions(self, mock_parse, mock_browser):
        """ test _get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.wrapper._get_creditcard_transactions('url', 'date_from', 'date_to'))

    @patch('dkb_robo.legacy.Wrapper._parse_cc_transactions')
    def test_046_get_cc_transactions(self, mock_parse, mock_browser):
        """ test _get_account_transactions """
        mock_browser.get_current_page.return_value = 'mock_browser'
        mock_parse.return_value = 'mock_parse'
        self.assertEqual('mock_parse', self.wrapper._get_creditcard_transactions('url', 'date_from', 'date_to', transaction_type='reserved'))

    def test_047_update_downloadstate(self, _unused):
        """ test update downloadstats """
        url = 'https://www.ib.dkb.de/DkbTransactionBanking/content/mailbox/MessageList/%24{1}.xhtml?$event=updateDownloadState&row=1'
        self.assertFalse(self.wrapper._update_downloadstate(link_name='link_name', url=url))

    def test_048_update_downloadstate(self, _unused):
        """ test update downloadstats """
        url = 'https://www.ib.dkb.de/DkbTransactionBanking/content/mailbox/MessageList/%24{1}.xhtml?$event=updateDownloadState&row=1'
        self.assertFalse(self.wrapper._update_downloadstate(link_name='Kontoauszüge', url=url))

    @patch('dkb_robo.legacy.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_049_get_document(self, mock_exists, mock_makedir, mock_rand, _unused):
        """ test get_document create path """
        mock_exists.return_value = False
        mock_rand.return_value = 'mock_rand'
        self.assertEqual((None, 'path/mock_rand.pdf', []), self.wrapper._get_document('folder_url', 'path', 'url', [], False))
        self.assertTrue(mock_makedir.called)
        self.assertTrue(mock_rand.called)

    @patch('dkb_robo.legacy.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_050_get_document(self, mock_exists, mock_makedir, mock_rand, _unused):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_rand.return_value = 'mock_rand'
        self.assertEqual((None, 'path/mock_rand.pdf', []), self.wrapper._get_document('folder_url', 'path', 'url', [], False))
        self.assertFalse(mock_makedir.called)
        self.assertTrue(mock_rand.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('re.findall')
    @patch('dkb_robo.utilities.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_051_get_document(self, mock_exists, mock_makedir, mock_rand, mock_re, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_rand.return_value = 'mock_rand'
        mock_browser.open.return_value.headers = {'Content-Disposition': ['foo', 'bar']}
        mock_browser.open.return_value.status_code = 200
        mock_re.return_value = ['mock_re.pdf', 'mock_re2.pdf']
        self.assertEqual((200, 'path/mock_re.pdf', ['mock_re.pdf']), self.wrapper._get_document('folder_url', 'path', 'url', [], False))
        self.assertFalse(mock_makedir.called)

    @patch('dkb_robo.legacy.datetime', Mock(now=lambda: date(2022, 9, 30)))
    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('re.findall')
    @patch('dkb_robo.utilities.generate_random_string')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_052_get_document(self, mock_exists, mock_makedir, mock_rand, mock_re, mock_browser):
        """ test get_document override """
        mock_exists.return_value = True
        mock_rand.return_value = 'mock_rand'
        mock_browser.open.return_value.headers = {'Content-Disposition': ['foo', 'bar']}
        mock_browser.open.return_value.status_code = 200
        mock_re.return_value = ['mock_re.pdf', 'mock_re2.pdf']
        self.assertEqual((200, 'path/2022-09-30-00-00-00_mock_re.pdf', ['mock_re.pdf', '2022-09-30-00-00-00_mock_re.pdf']), self.wrapper._get_document('folder_url', 'path', 'url', ['mock_re.pdf'], False))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_053_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers = {'Content-Disposition': 'inline; filename=Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf', ['Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf']), self.wrapper._get_document('folder_url', 'path', 'url', [], False))
        self.assertFalse(mock_makedir.called)

    @patch('dkb_robo.legacy.datetime', Mock(now=lambda: date(2022, 9, 30)))
    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_054_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers = {'Content-Disposition': 'inline; filename=Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/2022-09-30-00-00-00_Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf', ['Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf', '2022-09-30-00-00-00_Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf']), self.wrapper._get_document('folder_url', 'path', 'url', ['Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf'], False))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_055_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers = {'Content-Disposition': 'inline; filename=foo.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/foo.pdf', ['foo.pdf']), self.wrapper._get_document('folder_url', 'path', 'url', [], False))
        self.assertFalse(mock_makedir.called)

    @patch('dkb_robo.legacy.datetime', Mock(now=lambda: date(2022, 9, 30)))
    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_056_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers = {'Content-Disposition': 'inline; filename=foo.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/2022-09-30-00-00-00_foo.pdf', ['foo.pdf', '2022-09-30-00-00-00_foo.pdf']), self.wrapper._get_document('folder_url', 'path', 'url', ['foo.pdf'], False))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('urllib.parse.unquote')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_057_get_document(self, mock_exists, mock_makedir, mock_parse, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers = {'Content-Disposition': 'inline; filename=Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf'}
        mock_browser.open.return_value.status_code = 200
        mock_parse.side_effect = [Exception('exc1')]
        self.assertEqual((200, 'path/Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf', ['Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf']), self.wrapper._get_document('folder_url', 'path', 'url', [], False))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_058_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document prepend string """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers = {'Content-Disposition': 'inline; filename=Mitteilung_%c3%bcber_steigende_Sollzinss%c3%a4tze_ab_01.10.2022.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/prepend_Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf', ['prepend_Mitteilung_über_steigende_Sollzinssätze_ab_01.10.2022.pdf']), self.wrapper._get_document('folder_url', 'path', 'url', [], 'prepend_'))
        self.assertFalse(mock_makedir.called)

    @patch("builtins.open", mock_open(read_data='test'), create=True)
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_059_get_document(self, mock_exists, mock_makedir, mock_browser):
        """ test get_document create path """
        mock_exists.return_value = True
        mock_browser.open.return_value.headers = {'Content-Disposition': 'inline; filename=foo.pdf'}
        mock_browser.open.return_value.status_code = 200
        self.assertEqual((200, 'path/prepend_foo.pdf', ['prepend_foo.pdf']), self.wrapper._get_document('folder_url', 'path', 'url', [], 'prepend_'))
        self.assertFalse(mock_makedir.called)

    @patch('builtins.input')
    def test_060_ctan_check(self, mock_input, mock_browser):
        """ test ctan_check """
        mock_input.return_value = 'tan'
        html = '<html><head>header</head><body><ol><li>li</li></ol></body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertTrue(self.wrapper._ctan_check('soup'))

    @patch('builtins.input')
    def test_061_ctan_check(self, mock_input, mock_browser):
        """ test ctan_check """
        mock_input.return_value = 'tan'
        html = '<html><head>header</head><body>body</body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertTrue(self.wrapper._ctan_check('soup'))

    @patch('builtins.input')
    def test_062_ctan_check(self, mock_input, mock_browser):
        """ test ctan_check wrong tan """
        mock_input.return_value = 'tan'
        html = '<html><head>header</head><body><div class="clearfix module text errorMessage">div</div></body></html>'
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        with self.assertRaises(Exception) as err:
            self.wrapper._ctan_check('soup')
        self.assertEqual('Login failed due to wrong TAN', str(err.exception))

    @patch('dkb_robo.legacy.Wrapper._check_confirmation')
    def test_063_login_confirm(self, mock_confirm, mock_browser, ):
        """ test login confirmed check_cofirmation returns true """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_confirm.return_value = True
        self.assertTrue(self.wrapper._login_confirm())

    @patch('time.sleep', return_value=None)
    @patch('dkb_robo.legacy.Wrapper._check_confirmation')
    def test_064_login_confirm(self, mock_confirm, _mock_sleep, mock_browser):
        """ test login confirmed check_cofirmation returns multiple false but then true """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_confirm.side_effect = [False, False, False, True]
        self.assertTrue(self.wrapper._login_confirm())

    @patch('time.sleep', return_value=None)
    @patch('dkb_robo.legacy.Wrapper._check_confirmation')
    def test_065_login_confirm(self, mock_confirm, _mock_sleep, mock_browser):
        """ test login confirmed  """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_confirm.return_value = False
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.wrapper._login_confirm())
        self.assertEqual('No session confirmation after 120 polls', str(err.exception))

    def test_066_login_confirm(self, mock_browser):
        """ test login confirmed - exception when getting the token """
        mock_browser.open.return_value.json.return_value = {"foo": "bar"}
        mock_browser.get_current_page.side_effect = Exception('exc')
        with self.assertRaises(Exception) as err:
            self.assertTrue(self.wrapper._login_confirm())
        self.assertEqual('Error while getting the confirmation page', str(err.exception))

    def test_067_check_confirmation(self, _unused):
        """ test confirmation """
        result = {'foo': 'bar'}
        with self.assertRaises(Exception) as err:
            self.wrapper._check_confirmation(result, 1)
        self.assertEqual('Error during session confirmation', str(err.exception))

    def test_068_check_confirmation(self, _unused):
        """ test confirmation state expired"""
        result = {'state': 'EXPIRED'}
        with self.assertRaises(Exception) as err:
            self.wrapper._check_confirmation(result, 1)
        self.assertEqual('Session expired', str(err.exception))

    def test_069_check_confirmation(self, _unused):
        """ test confirmation state processed"""
        result = {'state': 'PROCESSED'}
        self.assertTrue(self.wrapper._check_confirmation(result, 1))

    def test_070_check_confirmation(self, _unused):
        """ test confirmation state unknown """
        result = {'state': 'UNK'}
        self.assertFalse(self.wrapper._check_confirmation(result, 1))

    def test_071_check_confirmation(self, _unused):
        """ test confirmation guiState expired"""
        result = {'guiState': 'EXPIRED'}
        with self.assertRaises(Exception) as err:
            self.wrapper._check_confirmation(result, 1)
        self.assertEqual('Session expired', str(err.exception))

    def test_072_check_confirmation(self, _unused):
        """ test confirmation guiState MAP_TO_EXIT"""
        result = {'guiState': 'MAP_TO_EXIT'}
        self.assertTrue(self.wrapper._check_confirmation(result, 1))

    def test_073_check_confirmation(self, _unused):
        """ test confirmation guiState unknown """
        result = {'guiState': 'UNK'}
        self.assertFalse(self.wrapper._check_confirmation(result, 1))

    def test_074_parse_depot_status_tr(self, _mock_browser):
        """ test DKBRobo._parse_cc_transactions """
        csv = read_file(self.dir_path + '/mocks/test_parse_depot.csv')
        result = [{'shares': 10.0, 'shares_unit': 'cnt1', 'isin_wkn': 'WKN1', 'text': 'Bezeichnung1', 'price': 11.0, 'win_loss': '', 'win_loss_currency': '', 'aquisition_cost': '', 'aquisition_cost_currency': '', 'dev_price': '', 'price_euro': 1110.1, 'availability': 'Frei'}, {'shares': 20.0, 'shares_unit': 'cnt2', 'isin_wkn': 'WKN2', 'text': 'Bezeichnung2', 'price': 12.0, 'win_loss': '', 'win_loss_currency': '', 'aquisition_cost': '', 'aquisition_cost_currency': '', 'dev_price': '', 'price_euro': 2220.2, 'availability': 'Frei'}]
        self.assertEqual(result, self.wrapper._parse_depot_status(csv))

    @patch('dkb_robo.legacy.Wrapper._parse_depot_status')
    def test_075_get_depot_status(self, mock_pds, _unused):
        """ test get depot status """
        mock_pds.return_value = 'mock_pds'
        self.assertEqual('mock_pds', self.wrapper._get_depot_status('url', 'fdate', 'tdate', 'booked'))

    @patch('dkb_robo.legacy.Wrapper._get_document')
    def test_076_legacy_download_document(self, mock_get_doc, _ununsed):
        """ test download document """
        html = read_file(self.dir_path + '/mocks/document_list.html')
        table = BeautifulSoup(html, 'html5lib')
        mock_get_doc.side_effect = my_side_effect
        class_filter = {}
        doc_dic = {'Name 04.01.2022': {'rcode': 200, 'link': 'https://www.ib.dkb.dehttps://www.dkb.de/DkbTransactionBanking/content/mailbox/MessageList.xhtml?$event=getMailboxAttachment&filename=Name+04.01.2022&row=0', 'fname': 'path/link_name'}}
        result = (doc_dic, [''])
        self.assertEqual(result, self.wrapper._download_document('folder_url', 'path', class_filter, 'link_name', table, False))

    @patch('dkb_robo.legacy.Wrapper._get_document')
    def test_077_legacy_download_document(self, mock_get_doc, _ununsed):
        """ test download document prepend date """
        html = read_file(self.dir_path + '/mocks/document_list.html')
        table = BeautifulSoup(html, 'html5lib')
        mock_get_doc.side_effect = my_side_effect
        class_filter = {}
        doc_dic = {'Name 04.01.2022': {'rcode': 200, 'link': 'https://www.ib.dkb.dehttps://www.dkb.de/DkbTransactionBanking/content/mailbox/MessageList.xhtml?$event=getMailboxAttachment&filename=Name+04.01.2022&row=0', 'fname': 'path/link_name'}}
        result = (doc_dic, ['2022-01-04_'])
        self.assertEqual(result, self.wrapper._download_document('folder_url', 'path', class_filter, 'link_name', table, True))

    @patch('dkb_robo.legacy.Wrapper._get_document')
    def test_078_legacy_download_document(self, mock_get_doc, _ununsed):
        """ test download document prepend date """
        html = read_file(self.dir_path + '/mocks/document_list-2.html')
        table = BeautifulSoup(html, 'html5lib')
        mock_get_doc.side_effect = my_side_effect
        class_filter = {}
        doc_dic = {'Name 04.01.2022': {'rcode': 200, 'link': 'https://www.ib.dkb.dehttps://www.dkb.de/DkbTransactionBanking/content/mailbox/MessageList.xhtml?$event=getMailboxAttachment&filename=Name+04.01.2022&row=0', 'fname': 'path/link_name'}}
        result = (doc_dic, [''])
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(result, self.wrapper._download_document('folder_url', 'path', class_filter, 'link_name', table, True))
        self.assertIn("ERROR:dkb_robo:Can't parse date, this could i.e. be for archived documents.", lcm.output)

    def test_079__get_formatted_date(self, _ununsed):
        """ test _get_formatted_date() prepend True """
        html = '<table><tr><td>foo</td><td class="abaxx-aspect-messageWithState-mailboxMessage-created">04.01.2022</td><td>bar</td></tr><table>'
        table = BeautifulSoup(html, 'html5lib')
        self.assertEqual('2022-01-04_', self.wrapper._get_formatted_date(True, table))

    def test_080__get_formatted_date(self, _ununsed):
        """ test _get_formatted_date() prepend False """
        html = '<table><tr><td>foo</td><td class="abaxx-aspect-messageWithState-mailboxMessage-created">04.01.2022</td><td>bar</td></tr><table>'
        table = BeautifulSoup(html, 'html5lib')
        self.assertEqual('', self.wrapper._get_formatted_date(False, table))

    def test_081__get_formatted_date(self, _ununsed):
        """ test _get_formatted_date() prepend False """
        html = '<table><tr><td>foo</td><td class="abaxx-aspect-messageWithState-mailboxMessage-created">fii</td><td>bar</td></tr><table>'
        table = BeautifulSoup(html, 'html5lib')
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual('', self.wrapper._get_formatted_date(True, table))
        self.assertIn("ERROR:dkb_robo:Can't parse date, this could i.e. be for archived documents.", lcm.output)

    def test_082_logout(self, _unused):
        """" test logout """
        self.wrapper.dkb_br = Mock()
        self.wrapper.dkb_br.open = Mock()
        self.assertFalse(self.wrapper.logout())
        self.assertTrue(self.wrapper.dkb_br.open.called)

    def test_083_logout(self, _unused):
        """" test logout """
        self.wrapper.dkb_br = None
        self.assertFalse(self.wrapper.logout())


if __name__ == '__main__':

    unittest.main()
