#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" unittests for dkb_robo """

import sys
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from bs4 import BeautifulSoup
sys.path.insert(0, '..')
from dkb_robo import DKBRobo

def cnt_list(value):
    """ customized function return just the number if entries in input list """
    return len(value)

@patch('dkb_robo.DKBRobo.dkb_br')
class TestDKBRobo(unittest.TestCase):
    """ test class """

    def setUp(self):
        self.dkb = DKBRobo()

    def test_get_cc_limit(self, mock_browser):
        """ test DKBRobo.get_credit_limits() method """
        html = """"
            <form action="/foo" method="post" id="form597962073_1">
                <table class="dropdownAnchor">
                    <tbody>
                        <tr>
                            <td><strong>Girokonto-1</strong><div class="minorLine">DE01 1111 1111 1111 1111 11</div></td>
                            <td>Girokonto-1</td>
                            <th><span style="white-space: nowrap">1.000,00</span></th>
                        </tr>
                        <tr>
                            <td><strong>Girokonto-2</strong><div class="minorLine">DE02 1111 1111 1111 1111 12</div></td>
                            <td>Girokonto-2</td>
                            <th><span>2000,00</span></th>
                        </tr>
                    </tbody>
                </table>
                <table class="multiColumn" id="creditCardLimit" border="0">
                    <tbody>
                        <tr>
                            <td><strong>CC-1</strong><div class="minorLine">1111********1111</div></td>
                            <td>CC-1</td>
                            <th><span>100,00</span></th>
                        </tr>
                        <tr>
                            <td><strong>CC-2</strong><div class="minorLine">1111********1112</div></td>
                            <td>CC-2</td>
                            <th><span>2.000,00</span></th>
                        </tr>
                    </tbody>
                </table>
            </form>
            """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'1111********1111': u'100.00',
                    u'1111********1112': u'2000.00',
                    u'DE01 1111 1111 1111 1111 11': u'1000.00',
                    u'DE02 1111 1111 1111 1111 12': u'2000.00'}
        self.assertEqual(self.dkb.get_credit_limits(), e_result)

    def test_get_exo_single(self, mock_browser):
        """ test DKBRobo.get_excemption_order() method for a single exemption order """
        html = """
            <table class="expandableTable">
                <tbody>
                <tr class="mainRow">
                    <td>
                        <img src="/binary-content.xhtml?id=1687952233" alt="dkb_micro" title="dkb_micro">
                    </td>
                    <td>
                        Gemeinsam mit
                        <br>
                        Firstname Familyname
                    </td>
                    <td>
                        01.01.2016
                        <br>
                        unbefristet
                    </td>
                    <td class="use_colspan_2 add_col_before_2 use_new_row_on_small">
                        1.000&nbsp;EUR
                    </td>
                    <td>
                        0&nbsp;EUR
                    </td>
                    <td class="hide-for-small-down">
                        1.000&nbsp;EUR
                    </td>
                    <td class="alignRight actions">
                        <a data-abx-jsevent="deleteExemptionOrderDkb" href="/DkbTransactionBanking/content/personaldata/ExemptionOrder/ExemptionOrderOverview.xhtml?$event=deleteExemptionOrderDkb&amp;selection=1" class="hreficons actions evt-deleteExemptionOrderDkb" tid="deleteExemptionOrderDkb"><span class="icons iconDelete0" title="Löschen">Löschen</span></a>
                        <a data-abx-jsevent="editExemptionOrderDkb" href="/DkbTransactionBanking/content/personaldata/ExemptionOrder/ExemptionOrderOverview.xhtml?$event=editExemptionOrderDkb&amp;selection=1" class="hreficons actions evt-editExemptionOrderDkb" tid="editExemptionOrderDkb"><span class="icons iconEdit0" title="Freistellungsdaten ändern">Freistellungsdaten ändern</span></a>
                    </td>
                </tr>
                </tbody>
            </table>
        """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0, 'amount': 1000.0, 'used': 0.0, 'description': u'Gemeinsam mit Firstname Familyname', 'validity': u'01.01.2016 unbefristet'}}
        self.assertEqual(self.dkb.get_exemption_order(), e_result)

    def test_get_exo_single_nobr(self, mock_browser):
        """ test DKBRobo.get_excemption_order() method for a single exemption order without line-breaks"""
        html = """
            <table class="expandableTable">
                <tbody>
                <tr class="mainRow">
                    <td>
                        <img src="/binary-content.xhtml?id=1687952233" alt="dkb_micro" title="dkb_micro">
                    </td>
                    <td>
                        Gemeinsam mit Firstname Familyname
                    </td>
                    <td>
                        01.01.2016 unbefristet
                    </td>
                    <td class="use_colspan_2 add_col_before_2 use_new_row_on_small">
                        1.000&nbsp;EUR
                    </td>
                    <td>
                        0&nbsp;EUR
                    </td>
                    <td class="hide-for-small-down">
                        1.000&nbsp;EUR
                    </td>
                    <td class="alignRight actions">
                        <a data-abx-jsevent="deleteExemptionOrderDkb" href="/DkbTransactionBanking/content/personaldata/ExemptionOrder/ExemptionOrderOverview.xhtml?$event=deleteExemptionOrderDkb&amp;selection=1" class="hreficons actions evt-deleteExemptionOrderDkb" tid="deleteExemptionOrderDkb"><span class="icons iconDelete0" title="Löschen">Löschen</span></a>
                        <a data-abx-jsevent="editExemptionOrderDkb" href="/DkbTransactionBanking/content/personaldata/ExemptionOrder/ExemptionOrderOverview.xhtml?$event=editExemptionOrderDkb&amp;selection=1" class="hreficons actions evt-editExemptionOrderDkb" tid="editExemptionOrderDkb"><span class="icons iconEdit0" title="Freistellungsdaten ändern">Freistellungsdaten ändern</span></a>
                    </td>
                </tr>
                </tbody>
            </table>
        """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {1: {'available': 1000.0, 'amount': 1000.0, 'used': 0.0, 'description': u'Gemeinsam mit Firstname Familyname', 'validity': u'01.01.2016 unbefristet'}}
        self.assertEqual(self.dkb.get_exemption_order(), e_result)

    def test_get_exo_multiple(self, mock_browser):
        """ test DKBRobo.get_excemption_order() method for a multiple exemption orders """
        html = """
            <table class="expandableTable">
                <tbody>
                <tr class="mainRow">
                    <td>
                        <img src="/binary-content.xhtml?id=1687952233" alt="dkb_micro" title="dkb_micro">
                    </td>
                    <td>
                        Gemeinsam mit
                        <br>
                        Firstname1 Familyname1
                    </td>
                    <td>
                        01.01.2016
                        <br>
                        unbefristet
                    </td>
                    <td class="use_colspan_2 add_col_before_2 use_new_row_on_small">
                        1.000&nbsp;EUR
                    </td>
                    <td>
                        0&nbsp;EUR
                    </td>
                    <td class="hide-for-small-down">
                        1.000&nbsp;EUR
                    </td>
                    <td class="alignRight actions">
                        <a data-abx-jsevent="deleteExemptionOrderDkb" href="/DkbTransactionBanking/content/personaldata/ExemptionOrder/ExemptionOrderOverview.xhtml?$event=deleteExemptionOrderDkb&amp;selection=1" class="hreficons actions evt-deleteExemptionOrderDkb" tid="deleteExemptionOrderDkb"><span class="icons iconDelete0" title="Löschen">Löschen</span></a>
                        <a data-abx-jsevent="editExemptionOrderDkb" href="/DkbTransactionBanking/content/personaldata/ExemptionOrder/ExemptionOrderOverview.xhtml?$event=editExemptionOrderDkb&amp;selection=1" class="hreficons actions evt-editExemptionOrderDkb" tid="editExemptionOrderDkb"><span class="icons iconEdit0" title="Freistellungsdaten ändern">Freistellungsdaten ändern</span></a>
                    </td>
                </tr>
                <tr class="mainRow">
                    <td>
                        <img src="/binary-content.xhtml?id=1687952233" alt="dkb_micro" title="dkb_micro">
                    </td>
                    <td>
                        Gemeinsam mit
                        <br>
                        Firstname2 Familyname2
                    </td>
                    <td>
                        02.01.2016
                        <br>
                        unbefristet
                    </td>
                    <td class="use_colspan_2 add_col_before_2 use_new_row_on_small">
                        2.000&nbsp;EUR
                    </td>
                    <td>
                        0&nbsp;EUR
                    </td>
                    <td class="hide-for-small-down">
                        2.000&nbsp;EUR
                    </td>
                    <td class="alignRight actions">
                        <a data-abx-jsevent="deleteExemptionOrderDkb" href="/DkbTransactionBanking/content/personaldata/ExemptionOrder/ExemptionOrderOverview.xhtml?$event=deleteExemptionOrderDkb&amp;selection=1" class="hreficons actions evt-deleteExemptionOrderDkb" tid="deleteExemptionOrderDkb"><span class="icons iconDelete0" title="Löschen">Löschen</span></a>
                        <a data-abx-jsevent="editExemptionOrderDkb" href="/DkbTransactionBanking/content/personaldata/ExemptionOrder/ExemptionOrderOverview.xhtml?$event=editExemptionOrderDkb&amp;selection=1" class="hreficons actions evt-editExemptionOrderDkb" tid="editExemptionOrderDkb"><span class="icons iconEdit0" title="Freistellungsdaten ändern">Freistellungsdaten ändern</span></a>
                    </td>
                </tr>
                </tbody>
            </table>
        """
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

    def test_new_instance(self, _unused):
        """ test DKBRobo.new_instance() method """
        self.assertIn('mechanicalsoup.stateful_browser.StatefulBrowser object at', str(self.dkb.new_instance()))

    def test_get_points(self, mock_browser):
        """ test DKBRobo.get_points() method """
        html = """
                <table class="expandableTable">
                    <tbody>
                            <tr class="mainRow">
                                <td align="left">
                                    <b>DKB-Punkte</b>
                                        <br>&nbsp;&nbsp;&nbsp;	davon verfallen zum  31.12.2017
                                </td>
                                <td style="text-align: right;padding-right: 130px;">
                                            <b>100.000</b>
                                                <br>90.000
                                </td>
                                <td class="actions">
                                    <p class="clearfix floatRight">
                                            <a data-abx-jsevent="plusPointsOverview" href="/DkbTransactionBanking/content/FavorableWorld/Overview/Overview.xhtml?$event=plusPointsOverview" class="evt-plusPointsOverview" tid="plusPointsOverview"><span class="icons iconSales0" title="Ihre DKB-Punkte"></span></a>
                                    </p>
                                </td>
                            </tr>
                    </tbody>
                </table>
            """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'DKB-Punkte': 100000, u'davon verfallen zum  31.12.2017': 90000}
        self.assertEqual(self.dkb.get_points(), e_result)

    def test_get_so_multiple(self, mock_browser):
        """ test DKBRobo.get_standing_orders() method """
        html = """
            <table class="expandableTable">
            <tbody>
                <tr class="mainRow">
                    <td>
                        <span class="overflow_on_150_for_xsmall">RECPIPIENT-1&nbsp;</span>
                    </td>
                    <td>
                        100,00
                        <span class="show-for-medium-up default-display-inline">&nbsp;EUR</span>
                    </td>
                    <td class="use_new_row_on_small use_colspan_3 special_executionDay alignCenter ">
                        1.<br>
                        monatlich
                        <br>
                        01.03.2017
                    </td>
                    <td class="hide-for-small-down" headers="table4438440f:paymentPurposeLine">
                        KV 1234567890&nbsp;
                    </td>
                </tr>
                <tr class="mainRow">
                    <td>
                        <span class="overflow_on_150_for_xsmall">RECPIPIENT-2&nbsp;</span>
                    </td>
                    <td>
                        200,00
                        <span class="show-for-medium-up default-display-inline">&nbsp;EUR</span>
                    </td>
                    <td class="use_new_row_on_small use_colspan_3 special_executionDay alignCenter ">
                        1.<br>
                        monatlich
                        <br>
                        geloescht
                    </td>
                    <td class="hide-for-small-down" headers="table4438440f:paymentPurposeLine">
                        KV 0987654321&nbsp;
                    </td>
                </tr>
            </tbody>
            </table>
            """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = [{'amount': 100.0, 'interval': u'1. monatlich 01.03.2017', 'recipient': u'RECPIPIENT-1', 'purpose': u'KV 1234567890'},
                    {'amount': 200.0, 'interval': u'1. monatlich geloescht', 'recipient': u'RECPIPIENT-2', 'purpose': u'KV 0987654321'}]
        self.assertEqual(self.dkb.get_standing_orders(), e_result)

    @patch('dkb_robo.DKBRobo.new_instance')
    def test_login(self, mock_instance, mock_browser):
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

    def test_parse_overview(self, _unused):
        """ test DKBRobo.parse_overview() method """
        html = """
                <table>
                <tbody>
                    <tr class="mainRow">
                        <td><div>credit-card-1</div><div>1111********1111</div></td>
                        <td><div>1111********1111</div></td>
                        <td>01.03.2017</td>
                        <td><span>1.000,00</span></td>
                        <td>
                            <p><a href="/tcc-1" class="evt-paymentTransaction"><span>Umsätze</span></a></p>
                            <div><ul><li><a href="/dcc-1" class="evt-details">Details</a></li></ul></div>
                        </td>
                    </tr>
                    <tr class="mainRow">
                        <td><div>credit-card-2</div><div>1111********1112</div></td>
                        <td><div>1111********1112</div></td>
                        <td>02.03.2017</td>
                        <td><span>2.000,00</span></td>
                        <td>
                            <p><a href="/tcc-2" class="evt-paymentTransaction"><span>Umsätze</span></a></p>
                            <div><ul><li><a href="/dcc-2" class="evt-details">Details</a></li></ul></div>
                        </td>
                    </tr>

                    <tr class="mainRow">
                        <td><div>checking-account-1</div><div class="iban hide-for-small-down">DE11 1111 1111 1111 1111 11</div></td>
                        <td><div>DE11 1111 1111 1111 1111 11</div></td>
                        <td>03.03.2017</td>
                        <td><span>1.000,00</span></td>
                        <td>
                            <p><a href="/tac-1" class="evt-paymentTransaction"><span>Umsätze</span></a></p>
                            <div><ul><li><a href="/banking/dac-1" class="evt-details"><span class="icons linkLoupe1"> Details</a></li><li>cash</li></ul></div>
                        </td>
                    </tr>
                    <tr class="mainRow">
                        <td><div>checking-account-2</div><div class="iban hide-for-small-down">DE11 1111 1111 1111 1111 12</div></td>
                        <td><div>DE11 1111 1111 1111 1111 12</div></td>
                        <td>04.03.2017</td>
                        <td><span>2.000,00</span></td>
                        <td>
                            <p><a href="/tac-2" class="evt-paymentTransaction"><span>Umsätze</span></a></p>
                            <div><ul><li><a href="/banking/dac-2" class="evt-details"><span class="icons linkLoupe1">Details</a></li><li>cash</li></ul></div>
                        </td>
                    </tr>

                    <tr class="mainRow">
                        <td><div>Depot-1</div><div>1111111</div></td>
                        <td><div>1111111</div></td>
                        <td>06.03.2017</td>
                        <td><span>5.000,00</span></td>
                        <td>
                            <p><a href="/tdepot-1" class="evt-depot" tid="depot"><span>Depotstatus</span></a></p>
                            <div><ul><li><a href="/ddepot-1" class="evt-details"><span class="icons linkLoupe1">Details</a></li></ul></div>
                        </td>
                    </tr>
                    <tr class="mainRow">
                        <td><div>Depot-2</div><div>1111112</div></td>
                        <td><div>1111112</div></td>
                        <td>06.03.2017</td>
                        <td><span>6.000,00</span></td>
                        <td>
                            <p><a href="/tdepot-2" class="evt-depot" tid="depot"><span>Depotstatus</span></a></p>
                            <div><ul><li><a href="/ddepot-2" class="evt-details"><span class="icons linkLoupe1">Details</a></li></ul></div>
                        </td>
                    </tr>
                </tbody>
                </table>
               """
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

    def test_get_document_links(self, mock_browser):
        """ test DKBRobo.get_document_links() method """
        html = """
                <table class="widget widget abaxx-table expandableTable expandableTable-with-sort">
                <tbody>
                    <tr>
                        <td><input name="rowSelector" value="0"></td>
                        <td>02.03.2017</td>
                        <td>02.03.2017</div><a href="/doc-1">Kontoauszug Nr. 003_2017 zu Konto 12345678</a><p>Löschung zum&nbsp;02.03.2017</p></td>
                    </tr>
                    <tr>
                        <td><input name="rowSelector" value="0"></td>
                        <td>02.03.2017</td>
                        <td>02.03.2017</div><a href="/doc-2">Kontoauszug Nr. 003_2017 zu Konto 87654321</a><p>Löschung zum&nbsp;02.03.2017</p></td>
                    </tr>
                </tbody>
                </table>
               """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'Kontoauszug Nr. 003_2017 zu Konto 87654321': u'https://www.dkb.de/doc-2',
                    u'Kontoauszug Nr. 003_2017 zu Konto 12345678': u'https://www.dkb.de/doc-1'}
        self.assertEqual(self.dkb.get_document_links('http://foo.bar/foo'), e_result)

    @patch('dkb_robo.DKBRobo.get_document_links')
    def test_scan_postbox(self, mock_doclinks, mock_browser):
        """ test DKBRobo.scan_postbox() method """
        html = """
                <table class="widget widget abaxx-table expandableTable" id="welcomeMboTable" cellspacing="0" cellpadding="0">
                    <tbody>
                        <tr id="Mitteilungen">
                            <td></td>
                            <td></td>
                            <td><a href="/banking/postfach/Mitteilungen">Mitteilungen</a></td>
                        </tr>

                        <tr id="Vertragsinformationen">
                            <td></td>
                            <td></td>
                            <td><a href="/banking/postfach/Vertragsinformationen">Vertragsinformationen</a></td>
                        </tr>

                        <tr id="Kreditkartenabrechnungen">
                            <td></td>
                            <td></td>
                            <td><a href="/banking/postfach/Kreditkartenabrechnungen">Kreditkartenabrechnungen</a></td>
                        </tr>
                    </tbody>
                </table>
               """
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

    def test_get_tr_invalid(self, _unused):
        """ test DKBRobo.get_transactions() method with an invalid account type"""
        self.assertEqual(self.dkb.get_transactions('url', 'foo', '01.03.2017', '02.03.2017'), [])

    @patch('dkb_robo.DKBRobo.get_creditcard_transactions')
    def test_get_tr_cc(self, mock_cc_tran, _unused):
        """ test DKBRobo.get_transactions() method with an credit-card account"""
        mock_cc_tran.return_value = ['credit_card']
        self.assertEqual(self.dkb.get_transactions('url', 'creditcard', '01.03.2017', '02.03.2017'), ['credit_card'])

    @patch('dkb_robo.DKBRobo.get_account_transactions')
    def test_get_tr_ac(self, mock_ca_tran, _unused):
        """ test DKBRobo.get_transactions() method with an checking account"""
        mock_ca_tran.return_value = ['account']
        self.assertEqual(self.dkb.get_transactions('url', 'account', '01.03.2017', '02.03.2017'), ['account'])

    @patch('dkb_robo.DKBRobo.parse_account_transactions', wraps=cnt_list)
    def test_get_tr_ac_one(self, _unused, mock_browser):
        """ test DKBRobo.get_account_transactions for one page only """
        html = """
            <p>foo</p>
        """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertEqual(self.dkb.get_account_transactions('url', '01.03.2017', '02.03.2017'), 1)

    @patch('dkb_robo.DKBRobo.parse_account_transactions', wraps=cnt_list)
    def test_get_tr_ac_two(self, _unused, mock_browser):
        """ test DKBRobo.get_account_transactions for two pages """
        html = """
            <p>foo</p>
            <ul>
                <li><a href="/foo-2" class="gotoPage">2</a></li>
            </ul>
        """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        # mock_parse_ca_tran.return_value = 1
        self.assertEqual(self.dkb.get_account_transactions('url', '01.03.2017', '02.03.2017'), 2)

    @patch('dkb_robo.DKBRobo.parse_account_transactions', wraps=cnt_list)
    def test_get_tr_ac_three(self, _unused, mock_browser):
        """ test DKBRobo.get_account_transactions for three pages """
        html = """
            <p>foo</p>
            <ul>
                <li><a href="/foo-2" class="gotoPage">2</a></li>
                <li><a href="/foo-3" class="gotoPage">3</a></li>
            </ul>
        """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        # mock_parse_ca_tran.return_value = 1
        self.assertEqual(self.dkb.get_account_transactions('url', '01.03.2017', '02.03.2017'), 3)

    @patch('dkb_robo.DKBRobo.parse_cc_transactions', wraps=cnt_list)
    def test_get_tr_cc_single(self, _unused, mock_browser):
        """ test DKBRobo.get_creditcard_transactions for one page only """
        html = """
            <p>foo</p>
        """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertEqual(self.dkb.get_creditcard_transactions('url', '01.03.2017', '02.03.2017'), 1)

    @patch('dkb_robo.DKBRobo.parse_cc_transactions', wraps=cnt_list)
    def test_get_tr_cc_multiple(self, _unused, mock_browser):
        """ test DKBRobo.get_creditcard_transactions for multiple pages.
            force to end loop after 200 iterations
        """
        html = """
            <p>foo</p>
            <a href="/foo" class="icons butNext0" title="Nächste Seite"></a>
        """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        self.assertEqual(self.dkb.get_creditcard_transactions('url', '01.03.2017', '02.03.2017'), 200)

    def test_parse_atrans_single(self, _unused):
        """ test DKBRobo.parse_account_transactions() method for a single page"""
        html = """
            <table id="umsatzTabelle">
            <tbody>
                <tr class="mainRow">
                    <td>01.03.2017<br><span class="valueDate">01.03.2017</span></td>
                    <td><div>line-11</div><div>line-12</div><div>line-13</div></td>
                    <td><div>DE11 1111 1111 1111 1111 11</div>XXXXXXXXXXX</td>
                    <td><nobr><span>-100,00</span></nobr></td>
                </tr>
                <tr class="mainRow">
                    <td>01.03.2017<br><span class="valueDate">01.03.2017</span></td>
                    <td><div>line-21</div><div>line-22</div><div>line-23</div></td>
                    <td><div>DE11 1111 1111 1111 1111 11</div>XXXXXXXXXXX</td>
                    <td><nobr><span>-200,00</span></nobr></td>
                </tr>
            </tbody>
            </table>
        """
        e_result = [{'date': u'01.03.2017',
                     'text': u'line-11 line-12line-13',
                     'amount': u'-100.00'},
                    {'date': u'01.03.2017',
                     'text': u'line-21 line-22line-23',
                     'amount': u'-200.00'}]
        self.assertEqual(self.dkb.parse_account_transactions([BeautifulSoup(html, 'html5lib')]), e_result)

    def test_parse_atrans_multiple(self, _unused):
        """ test DKBRobo.parse_account_transactions() method for multiple pages"""
        html = """
            <table id="umsatzTabelle">
            <tbody>
                <tr class="mainRow">
                    <td>01.03.2017<br><span class="valueDate">01.03.2017</span></td>
                    <td><div>line-11</div><div>line-12</div><div>line-13</div></td>
                    <td><div>DE11 1111 1111 1111 1111 11</div>XXXXXXXXXXX</td>
                    <td><nobr><span>-100,00</span></nobr></td>
                </tr>
                <tr class="mainRow">
                    <td>01.03.2017<br><span class="valueDate">01.03.2017</span></td>
                    <td><div>line-21</div><div>line-22</div><div>line-23</div></td>
                    <td><div>DE11 1111 1111 1111 1111 11</div>XXXXXXXXXXX</td>
                    <td><nobr><span>-200,00</span></nobr></td>
                </tr>
            </tbody>
            </table>
        """
        e_result = [{'date': u'01.03.2017',
                     'text': u'line-11 line-12line-13',
                     'amount': u'-100.00'},
                    {'date': u'01.03.2017',
                     'text': u'line-21 line-22line-23',
                     'amount': u'-200.00'},
                    {'date': u'01.03.2017',
                     'text': u'line-11 line-12line-13',
                     'amount': u'-100.00'},
                    {'date': u'01.03.2017',
                     'text': u'line-21 line-22line-23',
                     'amount': u'-200.00'}]
        self.assertEqual(self.dkb.parse_account_transactions([BeautifulSoup(html, 'html5lib'), BeautifulSoup(html, 'html5lib')]), e_result)

    def test_parse_ctrans_single(self, _unused):
        """ test DKBRobo.parse_cc_transactions() method for a single line """
        html = """
                <table class="expandableTable dateHandling creditcardtransactionsTable">
                <tbody>
                <tr class="mainRow">
                    <td>&nbsp;</td>
                    <td><span class="valueDate">01.03.17</span><br>01.03.17</td>
                    <td><div>Line-1</div></td>
                    <td><nobr><span>-100,00</span></nobr></td>
                    <td>EUR</td>
                </tr>
                <tr class="mainRow">
                    <td>&nbsp;</td>
                    <td><span class="valueDate">02.03.17</span><br>02.03.17</td>
                    <td><div>Line-2</div></td>
                    <td><nobr><span>-200,00</span></nobr></td>
                    <td>EUR</td>
                </tr>
                </tbody>
                </table>
        """
        e_result = [{'bdate': '01.03.2017',
                     'vdate': '01.03.2017',
                     'text': u'Line-1',
                     'show_date': '01.03.2017',
                     'store_date': '01.03.2017',
                     'amount': u'-100.00'},
                    {'bdate': '02.03.2017',
                     'vdate': '02.03.2017',
                     'text': u'Line-2',
                     'show_date': '02.03.2017',
                     'store_date': '02.03.2017',
                     'amount': u'-200.00'}]
        self.assertEqual(self.dkb.parse_cc_transactions([BeautifulSoup(html, 'html5lib')]), e_result)

    def test_parse_ctrans_multiple(self, _unused):
        """ test DKBRobo.parse_cc_transactions() method for multiple pages """
        html = """
                <table class="expandableTable dateHandling creditcardtransactionsTable">
                <tbody>
                <tr class="mainRow">
                    <td>&nbsp;</td>
                    <td><span class="valueDate">01.03.17</span><br>01.03.17</td>
                    <td><div>Line-1</div></td>
                    <td><nobr><span>-100,00</span></nobr></td>
                    <td>EUR</td>
                </tr>
                <tr class="mainRow">
                    <td>&nbsp;</td>
                    <td><span class="valueDate">02.03.17</span><br>02.03.17</td>
                    <td><div>Line-2</div></td>
                    <td><nobr><span>-200,00</span></nobr></td>
                    <td>EUR</td>
                </tr>
                </tbody>
                </table>
        """
        e_result = [{'bdate': '01.03.2017',
                     'vdate': '01.03.2017',
                     'text': u'Line-1',
                     'show_date': '01.03.2017',
                     'store_date': '01.03.2017',
                     'amount': u'-100.00'},
                    {'bdate': '02.03.2017',
                     'vdate': '02.03.2017',
                     'text': u'Line-2',
                     'show_date': '02.03.2017',
                     'store_date': '02.03.2017',
                     'amount': u'-200.00'},
                    {'bdate': '01.03.2017',
                     'vdate': '01.03.2017',
                     'text': u'Line-1',
                     'show_date': '01.03.2017',
                     'store_date': '01.03.2017',
                     'amount': u'-100.00'},
                    {'bdate': '02.03.2017',
                     'vdate': '02.03.2017',
                     'text': u'Line-2',
                     'show_date': '02.03.2017',
                     'store_date': '02.03.2017',
                     'amount': u'-200.00'}]
        self.assertEqual(self.dkb.parse_cc_transactions([BeautifulSoup(html, 'html5lib'), BeautifulSoup(html, 'html5lib')]), e_result)

if __name__ == '__main__':

    unittest.main()
