#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" unittests for dkb_robo """
import sys
import os
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch
from bs4 import BeautifulSoup
sys.path.insert(0, '.')
sys.path.insert(0, '..')
from dkb_robo import DKBRobo

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

    def test_001_get_cc_limit(self, mock_browser):
        """ test DKBRobo.get_credit_limits() method """
        html = read_file(self.dir_path + '/mocks/konto-kreditkarten-limits.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'1111********1111': u'100.00',
                    u'1111********1112': u'2000.00',
                    u'DE01 1111 1111 1111 1111 11': u'1000.00',
                    u'DE02 1111 1111 1111 1111 12': u'2000.00'}
        self.assertEqual(self.dkb.get_credit_limits(), e_result)

    def test_002_get_exo_single(self, mock_browser):
        """ test DKBRobo.get_exemption_order() method for a single exemption order """
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0, 'amount': 1000.0, 'used': 0.0, 'description': u'Gemeinsam mit Firstname Familyname', 'validity': u'01.01.2016 unbefristet'}}
        self.assertEqual(self.dkb.get_exemption_order(), e_result)

    def test_003_get_exo_single_nobr(self, mock_browser):
        """ test DKBRobo.get_exemption_order() method for a single exemption order without line-breaks"""
        html = read_file(self.dir_path + '/mocks/freistellungsauftrag-nobr.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0, 'amount': 1000.0, 'used': 0.0, 'description': u'Gemeinsam mit Firstname Familyname', 'validity': u'01.01.2016 unbefristet'}}
        self.assertEqual(self.dkb.get_exemption_order(), e_result)

    def test_004_get_exo_multiple(self, mock_browser):
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

    def test_005_new_instance(self, _unused):
        """ test DKBRobo.new_instance() method """
        self.assertIn('mechanicalsoup.stateful_browser.StatefulBrowser object at', str(self.dkb.new_instance()))

    def test_006_get_points(self, mock_browser):
        """ test DKBRobo.get_points() method """
        html = read_file(self.dir_path + '/mocks/dkb_punkte.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'DKB-Punkte': 100000, u'davon verfallen zum  31.12.2017': 90000}
        self.assertEqual(self.dkb.get_points(), e_result)

    def test_007_get_so_multiple(self, mock_browser):
        """ test DKBRobo.get_standing_orders() method """
        html = read_file(self.dir_path + '/mocks/dauerauftraege.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = [{'amount': 100.0, 'interval': u'1. monatlich 01.03.2017', 'recipient': u'RECPIPIENT-1', 'purpose': u'KV 1234567890'},
                    {'amount': 200.0, 'interval': u'1. monatlich geloescht', 'recipient': u'RECPIPIENT-2', 'purpose': u'KV 0987654321'}]
        self.assertEqual(self.dkb.get_standing_orders(), e_result)

    @patch('dkb_robo.DKBRobo.new_instance')
    def test_008_login(self, mock_instance, mock_browser):
        """ test DKBRobo.login() method """
        html = """
                <div id="lastLoginContainer" class="lastLogin deviceFloatRight ">
                        Letzte Anmeldung:
                        01.03.2017, 01:00 Uhr
                </div>
               """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        mock_instance.return_value = mock_browser
        self.assertEqual(self.dkb.login(), None)

    def test_009_parse_overview(self, _unused):
        """ test DKBRobo.parse_overview() method """
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
        self.assertEqual(self.dkb.parse_overview(BeautifulSoup(html, 'html5lib')), e_result)

    def test_010_parse_overview_mbank(self, _unused):
        """ test DKBRobo.parse_overview() method for accounts from other banks"""
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
        self.assertEqual(self.dkb.parse_overview(BeautifulSoup(html, 'html5lib')), e_result)

    def test_011_get_document_links(self, mock_browser):
        """ test DKBRobo.get_document_links() method """
        html = read_file(self.dir_path + '/mocks/doclinks.html')
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'Kontoauszug Nr. 003_2017 zu Konto 87654321': u'https://www.dkb.de/doc-2',
                    u'Kontoauszug Nr. 003_2017 zu Konto 12345678': u'https://www.dkb.de/doc-1'}
        self.assertEqual(self.dkb.get_document_links('http://foo.bar/foo'), e_result)

    @patch('dkb_robo.DKBRobo.get_document_links')
    def test_012_scan_postbox(self, mock_doclinks, mock_browser):
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

    def test_013_get_tr_invalid(self, _unused):
        """ test DKBRobo.get_transactions() method with an invalid account type"""
        self.assertEqual(self.dkb.get_transactions('url', 'foo', '01.03.2017', '02.03.2017'), [])

    @patch('dkb_robo.DKBRobo.get_creditcard_transactions')
    def test_014_get_tr_cc(self, mock_cc_tran, _unused):
        """ test DKBRobo.get_transactions() method with an credit-card account"""
        mock_cc_tran.return_value = ['credit_card']
        self.assertEqual(self.dkb.get_transactions('url', 'creditcard', '01.03.2017', '02.03.2017'), ['credit_card'])

    @patch('dkb_robo.DKBRobo.get_account_transactions')
    def test_015_get_tr_ac(self, mock_ca_tran, _unused):
        """ test DKBRobo.get_transactions() method with an checking account"""
        mock_ca_tran.return_value = ['account']
        self.assertEqual(self.dkb.get_transactions('url', 'account', '01.03.2017', '02.03.2017'), ['account'])

    def test_016_parse_account_tr(self, _mock_browser):
        """ test DKBRobo.get_account_transactions for one page only """
        csv = read_file(self.dir_path + '/mocks/test_parse_account_tr.csv')
        self.assertEqual(self.dkb.parse_account_transactions(csv), [{'amount': 'AAAAA',
                                                                     'bdate': '01.03.2017',
                                                                     'customerreferenz': 'AA',
                                                                     'date': '01.03.2017',
                                                                     'mandatereference': 'AAA',
                                                                     'peer': 'AAAAAAAA',
                                                                     'peeraccount': '-100,00',
                                                                     'peerbic': 'AAAAAA',
                                                                     'peerid': 'AAAA',
                                                                     'postingtext': 'AAAAAAAAA',
                                                                     'reasonforpayment': 'AAAAAAA',
                                                                     'text': 'AAAAAAAAA AAAAAAAA AAAAAAA',
                                                                     'vdate': '01.03.2017'},
                                                                    {'amount': 'BBBBB',
                                                                     'bdate': '02.03.2017',
                                                                     'customerreferenz': 'BB',
                                                                     'date': '02.03.2017',
                                                                     'mandatereference': 'BBB',
                                                                     'peer': 'BBBBBBBB',
                                                                     'peeraccount': '-200,00',
                                                                     'peerbic': 'BBBBBB',
                                                                     'peerid': 'BBBB',
                                                                     'postingtext': 'BBBBBBBBB',
                                                                     'reasonforpayment': 'BBBBBBB',
                                                                     'text': 'BBBBBBBBB BBBBBBBB BBBBBBB',
                                                                     'vdate': '02.03.2017'}])

    def test_017_parse_no_account_tr(self, _mock_browser):
        """ test DKBRobo.get_account_transactions for one page only """
        csv = read_file(self.dir_path + '/mocks/test_parse_no_account_tr.csv')
        self.assertEqual(self.dkb.parse_account_transactions(csv), [])

    def test_018_parse_dkb_cc_tr(self, _mock_browser):
        """ test DKBRobo.parse_cc_transactions """
        csv = read_file(self.dir_path + '/mocks/test_parse_dkb_cc_tr.csv')
        self.assertEqual(self.dkb.parse_cc_transactions(csv), [{'amount': '-100.00"',
                                                                'bdate': '01.03.2017',
                                                                'show_date': '01.03.2017',
                                                                'store_date': '01.03.2017',
                                                                'text': 'AAA',
                                                                'vdate': '01.03.2017'},
                                                               {'amount': '-200.00"',
                                                                'bdate': '02.03.2017',
                                                                'show_date': '02.03.2017',
                                                                'store_date': '02.03.2017',
                                                                'text': 'BBB',
                                                                'vdate': '02.03.2017'},
                                                               {'amount': '-300.00"',
                                                                'bdate': '03.03.2017',
                                                                'show_date': '03.03.2017',
                                                                'store_date': '03.03.2017',
                                                                'text': 'CCC',
                                                                'vdate': '03.03.2017'}])

    def test_019_parse_no_cc_tr(self, _mock_browser):
        """ test DKBRobo.parse_cc_transactions """
        csv = read_file(self.dir_path + '/mocks/test_parse_no_cc_tr.csv')
        self.assertEqual(self.dkb.parse_cc_transactions(csv), [])

if __name__ == '__main__':

    unittest.main()
