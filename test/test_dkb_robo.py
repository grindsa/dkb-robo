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

@patch('dkb_robo.DKBRobo.dkb_br')
class TestDKBRobo(unittest.TestCase):
    """ test class """

    def setUp(self):
        self.dkb = DKBRobo()

    def test_get_cc_limit(self, mock_browser):
        """ test DKBRobo.get_credit_limits() method """
        html = """"
            <form action="/DkbTransactionBanking/content/service/CreditcardLimit.xhtml" method="post" id="form597962073_1" name="form597962073_1" class="form" data-xpopup-mode="auto"><button style="position: absolute; left: -9999px; width: 1px; height: 1px;" name="hiddenSubmit" type="submit">&nbsp;</button>
                <table style="width:100%;" class="dropdownAnchor" id="overdraftLimit" border="0" cellspacing="0" cellpadding="0">
                    <tbody>
                        <tr>
                            <td class="account limit">
                                <strong class="hide-for-medium-up">Girokonto-1</strong>
                                <div class="minorLine">
                                            DE01 1111 1111 1111 1111 11
                                </div>
                            </td>
                            <td class="show-for-medium-up">Girokonto-1</td>
                            <th class="alignRight">
                                <span style="white-space: nowrap">1.000,00</span>
                            </th>
                        </tr>
                        <tr>
                            <td class="account limit">
                                <strong class="hide-for-medium-up">Girokonto-2</strong>
                                <div class="minorLine">
                                            DE02 1111 1111 1111 1111 12
                                </div>
                            </td>
                            <td class="show-for-medium-up">Girokonto-2</td>
                            <th class="alignRight">
                                <span style="white-space: nowrap">2000,00</span>
                            </th>
                        </tr>
                    </tbody>
                </table>
                <table style="width:100%;" class="multiColumn" id="creditCardLimit" border="0" cellspacing="0" cellpadding="0">
                    <tbody>
                        <tr>
                            <td class="account limit">
                                <strong class="hide-for-medium-up">CC-1</strong>
                                <div class="minorLine">1111********1111</div>
                            </td>
                            <td class="show-for-medium-up">
                                CC-1
                            </td>
                            <th class="alignRight">
                                        <span style="white-space: nowrap">100,00</span>
                            </th>
                        </tr>
                        <tr>
                            <td class="account limit">
                                <strong class="hide-for-medium-up">CC-2</strong>
                                <div class="minorLine">1111********1112</div>
                            </td>
                            <td class="show-for-medium-up">
                                CC-2
                            </td>
                            <th class="alignRight">
                                        <span style="white-space: nowrap">2.000,00</span>
                            </th>
                        </tr>
                        <tr>
                            <td class="account limit">
                                <strong class="hide-for-medium-up">CC-3</strong>
                                <div class="minorLine">1111********1113</div>
                            </td>
                            <td class="show-for-medium-up">
                                CC-3
                            </td>
                            <th class="alignRight">
                                        <span style="white-space: nowrap">3.000,00</span>
                            </th>
                        </tr>

                </tbody>
                </table>
            </form>
            """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        e_result = {u'1111********1111': u'100.00',
                    u'1111********1112': u'2000.00',
                    u'1111********1113': u'3000.00',
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
                        gelöscht
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
                    {'amount': 200.0, 'interval': u'1. monatlich gel\xc3\xb6scht', 'recipient': u'RECPIPIENT-2', 'purpose': u'KV 0987654321'}]
        self.assertEqual(self.dkb.get_standing_orders(), e_result)

    @patch('dkb_robo.DKBRobo.new_instance')
    def test_login(self, moc_instance, mock_browser):
        """ test DKBRobo.login() method """
        html = """
                <div id="lastLoginContainer" class="lastLogin deviceFloatRight ">
                        Letzte Anmeldung:
                        01.03.2017, 01:00 Uhr
                </div>
               """
        mock_browser.get_current_page.return_value = BeautifulSoup(html, 'html5lib')
        moc_instance.return_value = mock_browser
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

if __name__ == '__main__':

    unittest.main()
