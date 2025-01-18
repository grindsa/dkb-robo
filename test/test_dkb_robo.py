#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" unittests for dkb_robo """
import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock, mock_open
from bs4 import BeautifulSoup
from mechanicalsoup import LinkNotFoundError
from datetime import date
import io
import json

sys.path.insert(0, '.')
sys.path.insert(0, '..')
from dkb_robo import DKBRobo
import logging


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

def my_side_effect(*args, **kwargs):
    """ my sideeffect funtion """
    return [200, args[1], [args[4]]]


class TestDKBRobo(unittest.TestCase):
    """ test class """

    maxDiff = None

    def setUp(self):
        self.dkb = DKBRobo()
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')

    @patch('dkb_robo.authentication.Authentication.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_001__enter(self, mock_legacy, mock_api):
        """ test enter """
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)

    @patch('dkb_robo.authentication.Authentication.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_002__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.legacy_login = False
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)

    @patch('dkb_robo.authentication.Authentication.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_003__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.legacy_login = True
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        with self.assertRaises(Exception) as err:
            self.dkb.__enter__()
        self.assertEqual('Legacy Login got deprecated. Please do not use this option anymore', str(err.exception))
        self.assertFalse(mock_legacy.called)
        self.assertFalse(mock_api.called)

    @patch('dkb_robo.authentication.Authentication.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_004__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.tan_insert = True
        # self.dkb.wrapper = Mock()
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb.__enter__()
        self.assertIn("INFO:dkb_robo:tan_insert is a legacy login option and will be disabled soon. Please use chip_tan instead", lcm.output)
        self.assertTrue(self.dkb.chip_tan)
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)

    @patch('dkb_robo.authentication.Authentication.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_005__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.mfa_device = 1
        # self.dkb.wrapper = Mock()
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)
        self.assertEqual(1, self.dkb.mfa_device)

    @patch('dkb_robo.authentication.Authentication.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_006__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.mfa_device = 2
        # self.dkb.wrapper = Mock()
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)
        self.assertEqual(2, self.dkb.mfa_device)

    @patch('dkb_robo.authentication.Authentication.login')
    @patch('dkb_robo.legacy.Wrapper.login')
    def test_007__enter(self, mock_legacy, mock_api):
        """ test enter """
        self.dkb.mfa_device = 'm'
        # self.dkb.wrapper = Mock()
        mock_legacy.return_value = ('legacy', 'foo')
        mock_api.return_value = ('api', 'foo')
        self.assertTrue(self.dkb.__enter__())
        self.assertFalse(mock_legacy.called)
        self.assertTrue(mock_api.called)
        self.assertEqual(1, self.dkb.mfa_device)

    def test_008__exit(self):
        """ test enter """
        self.dkb.wrapper = Mock()
        self.dkb.wrapper.logout = Mock()
        self.assertFalse(self.dkb.__exit__())
        self.assertTrue(self.dkb.wrapper.logout.called)

    @patch('dkb_robo.transaction.Transactions.get')
    @patch('dkb_robo.dkb_robo.validate_dates')
    def test_009_get_transactions(self, mock_date, mock_transaction):
        """ test get_transactions() """
        self.dkb.legacy_login = True
        mock_date.return_value = ('from', 'to')
        self.dkb.wrapper = Mock()
        mock_transaction.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb.get_transactions('url', 'account', 'from', 'to', 'btype'))

    @patch('dkb_robo.transaction.Transactions.get')
    @patch('dkb_robo.dkb_robo.validate_dates')
    def test_010_get_transactions(self, mock_date, mock_transaction):
        """ test get_transactions() """
        self.dkb.legacy_login = False
        mock_date.return_value = ('from', 'to')
        self.dkb.wrapper = Mock()
        mock_transaction.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb.get_transactions('url', 'atype', 'from', 'to', 'btype'))

    def test_011_get_points(self):
        """ test get_exemption_order()"""
        self.dkb.wrapper = Mock()
        with self.assertRaises(Exception) as err:
            self.dkb.get_points()
        self.assertEqual('Method not supported...', str(err.exception))

    @patch('dkb_robo.exemptionorder.ExemptionOrders.fetch')
    def test_012_get_exemption_order(self, mock_fetch):
        """ test get_exemption_order()"""
        self.dkb.wrapper = Mock()
        mock_fetch.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb.get_exemption_order())

    def test_013_get_credit_limits(self):
        """ test get_credit_limits()"""
        self.dkb.account_dic = {1: {'limit': 1000, 'foo': 'bar', 'iban': 'iban'}, 2: {'limit': 2000, 'foo': 'bar', 'maskedpan': 'maskedpan'}}
        self.assertEqual({'iban': 1000, 'maskedpan': 2000}, self.dkb.get_credit_limits())

    @patch('dkb_robo.standingorder.StandingOrders.fetch')
    def test_014_get_standing_orders(self, mock_fetch):
        """ test get_standing_orders()"""
        self.dkb.wrapper = Mock()
        mock_fetch.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb.get_standing_orders())

    def test_015_scan_postbox(self):
        """ test get_standing_orders()"""
        self.dkb.download = Mock()
        self.dkb.download.return_value = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, self.dkb.scan_postbox())

    @patch('dkb_robo.postbox.PostBox.fetch_items')
    @patch('dkb_robo.dkb_robo.DKBRobo.download_doc', autospec=True)
    def test_016_download(self, mock_download_doc, mock_fetch_items):
        """ download_all_documents"""
        path = Path('/some/path')
        self.dkb.wrapper = Mock()
        self.dkb.wrapper.client = Mock()
        self.dkb.wrapper.account_dic = {'id1': {'id': 'id1', 'account': 'account1', 'read': False, 'foo': 'bar', 'iban': 'iban'}, 'id2': {'id': 'id2', 'account': 'account2', 'read': True, 'foo': 'bar'}}
        mock_fetch_items.return_value = {
            'doc1': 'document1',
            'doc2': 'document2'
        }

        documents = self.dkb.download(path=path, download_all=True)
        self.assertEqual({'doc1': 'document1', 'doc2': 'document2'}, documents)
        mock_download_doc.assert_any_call(self.dkb, path=path, doc=documents['doc1'], prepend_date=False, mark_read=True, use_account_folders=False, list_only=False, accounts_by_id={'id1': 'account1', 'id2': 'account2'})
        mock_download_doc.assert_any_call(self.dkb, path=path, doc=documents['doc2'], prepend_date=False, mark_read=True, use_account_folders=False, list_only=False, accounts_by_id={'id1': 'account1', 'id2': 'account2'})

    @patch('dkb_robo.postbox.PostBox.fetch_items')
    @patch('dkb_robo.dkb_robo.DKBRobo.download_doc', autospec=True)
    def test_017_download(self, mock_download_doc, mock_fetch_items):
        """ download_all_documents"""
        path = Path('/some/path')
        self.dkb.wrapper = Mock()
        self.dkb.wrapper.client = Mock()
        self.dkb.wrapper.account_dic = {'id1': {'id': 'id1', 'account': 'account1', 'read': False, 'foo': 'bar', 'iban': 'iban'}, 'id2': {'id': 'id2', 'account': 'account2', 'read': True, 'foo': 'bar'}}
        unread_doc = MagicMock()
        unread_doc.message.read = False
        read_doc = MagicMock()
        read_doc.message.read = True
        mock_fetch_items.return_value = {
            'doc1': unread_doc,
            'doc2': read_doc
        }
        documents = self.dkb.download(path=path, download_all=False)
        self.assertEqual(1, len(documents))
        mock_download_doc.assert_any_call(self.dkb, path=path, doc=documents['doc1'], prepend_date=False, mark_read=True, use_account_folders=False, list_only=False, accounts_by_id={'id1': 'account1', 'id2': 'account2'})

    @patch('dkb_robo.postbox.PostBox.fetch_items')
    @patch('dkb_robo.dkb_robo.DKBRobo.download_doc', autospec=True)
    def test_018_download(self, mock_download_doc, mock_fetch_items):
        """ download_all_documents"""
        path = Path('/some/path')
        self.dkb.wrapper = Mock()
        self.dkb.wrapper.client = Mock()
        self.dkb.wrapper.account_dic = {'id1': {'id': 'id1', 'account': 'account1', 'read': False, 'foo': 'bar', 'iban': 'iban'}, 'id2': {'id': 'id2', 'account': 'account2', 'read': True, 'foo': 'bar'}}
        mock_fetch_items.return_value = {
            'doc1': 'document1',
            'doc2': 'document2'
        }

        documents = self.dkb.download(path=None, download_all=True)
        self.assertEqual({'doc1': 'document1', 'doc2': 'document2'}, documents)
        mock_download_doc.assert_not_called()

    @patch('dkb_robo.dkb_robo.time.sleep', autospec=True)
    def test_019_download_doc(self, mock_sleep):
        """ download a single document """
        path = Path('/some/path')
        doc = MagicMock()
        doc.category.return_value = 'category'
        doc.account.return_value = 'account'
        doc.date.return_value = '2022-01-01'
        doc.filename.return_value = 'document.pdf'
        doc.subject.return_value = 'Document Subject'
        doc.download.return_value = True
        self.dkb.wrapper = MagicMock()
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.dkb.download_doc(path=path, doc=doc, prepend_date=True, mark_read=True, use_account_folders=True, list_only=False, accounts_by_id={})
        self.assertIn('INFO:dkb_robo:Downloading Document Subject to \\some\\path\\category\\account...', lcm.output)

        target = path / 'category' / 'account'
        filename = '2022-01-01_document.pdf'
        doc.download.assert_called_with(self.dkb.wrapper.client, target / filename)
        doc.mark_read.assert_called_with(self.dkb.wrapper.client, True)
        mock_sleep.assert_called_once_with(0.5)

    def test_020_download_doc(self):
        """ list only   """
        path = Path('/some/path')
        doc = MagicMock()
        doc.category.return_value = 'category'
        doc.account.return_value = 'account'
        doc.date.return_value = '2022-01-01'
        doc.filename.return_value = 'document.pdf'
        doc.subject.return_value = 'Document Subject'
        doc.download.return_value = True
        self.dkb.logger = MagicMock()
        self.dkb.wrapper = MagicMock()
        self.dkb.download_doc(path=path, doc=doc, prepend_date=True, mark_read=True, use_account_folders=True, list_only=True, accounts_by_id={})
        self.dkb.logger.info.assert_not_called()
        doc.download.assert_not_called()
        doc.mark_read.assert_not_called()

    @patch('dkb_robo.dkb_robo.time.sleep', autospec=True)
    def test_021_download_doc(self, mock_sleep):
        """ test existing file """
        path = Path('/some/path')
        doc = MagicMock()
        doc.category.return_value = 'category'
        doc.account.return_value = 'account'
        doc.date.return_value = '2022-01-01'
        doc.filename.return_value = 'document.pdf'
        doc.subject.return_value = 'Document Subject'
        doc.download.return_value = False
        self.dkb.logger = MagicMock()
        self.dkb.wrapper = MagicMock()
        self.dkb.download_doc(path=path, doc=doc, prepend_date=True, mark_read=True, use_account_folders=True, list_only=False, accounts_by_id={})
        target = path / 'category' / 'account'
        filename = '2022-01-01_document.pdf'
        self.dkb.logger.info.assert_called_with("File already exists. Skipping %s.", filename)
        doc.download.assert_called_with(self.dkb.wrapper.client, target / filename)
        doc.mark_read.assert_not_called()
        mock_sleep.assert_not_called()



if __name__ == '__main__':

    unittest.main()
