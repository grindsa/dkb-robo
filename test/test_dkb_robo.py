#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" unittests for dkb_robo """

import unittest
import sys

try:
    from mock import patch
except:
    from unittest.mock import patch    
    
from bs4 import BeautifulSoup
sys.path.insert(0, '..')
from dkb_robo import DKBRobo

@patch('dkb_robo.DKBRobo.dkb_br')
class TestDKBRobo(unittest.TestCase):
    """ test class """

    def setUp(self):
        self.dkb = DKBRobo()

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

if __name__ == '__main__':

    unittest.main()
