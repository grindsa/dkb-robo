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
import click
from click.testing import CliRunner

sys.path.insert(0, ".")
sys.path.insert(0, "..")
import logging


class Config:
    def __init__(self):
        self.FORMAT = None
        self.UNFILTERED = False

    def __getitem__(self, key):  # this allows getting an element (overrided method)
        return self.FORMAT(key)


class TestDKBRobo(unittest.TestCase):
    """test class"""

    maxDiff = None

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        from dkb_robo.cli import (
            _load_format,
            _login,
            standing_orders,
            credit_limits,
            last_login,
            accounts,
            main,
            transactions,
            _id_lookup,
            _account_lookup,
            _transactionlink_lookup,
            scan_postbox,
            download,
        )

        self.logger = logging.getLogger("dkb_robo")
        self._load_format = _load_format
        self._login = _login
        self.standing_orders = standing_orders
        self.credit_limits = credit_limits
        self.last_login = last_login
        self.accounts = accounts
        self.main = main
        self.transactions = transactions
        self._id_lookup = _id_lookup
        self._account_lookup = _account_lookup
        self._transactionlink_lookup = _transactionlink_lookup
        self.scan_postbox = scan_postbox
        self.download = download

    def test_001_default(self):
        """default test which always passes"""
        self.assertEqual("foo", "foo")

    def test_002__login(self):
        """test login"""
        cursor = MagicMock()
        cursor.__iter__.return_value = []
        self.assertTrue(self._login(cursor))

    def test_003__load_format(self):
        """test _load_format()"""
        oformat = "pprint"
        self.assertIn("pprint", self._load_format(oformat).__code__.co_names)

    def test_004__load_format(self):
        """test _load_format()"""
        oformat = "csv"
        self.assertIn("csv", self._load_format(oformat).__code__.co_names)

    def test_005__load_format(self):
        """test _load_format()"""
        oformat = "table"
        self.assertIn("tabulate", self._load_format(oformat).__code__.co_names)

    def test_006__load_format(self):
        """test _load_format()"""
        oformat = "json"
        self.assertIn("json", self._load_format(oformat).__code__.co_names)

    def test_007__load_format(self):
        """test _load_format()"""
        oformat = "foo"
        with self.assertRaises(Exception) as err:
            self._load_format(oformat)
        self.assertEqual("Unknown format: foo", str(err.exception))

    @patch("dkb_robo.cli._account_lookup")
    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_008_standing_orders(self, mock_login, mock_click, mock_lookup):
        """test standing orders"""
        obj = Config()
        obj.FORMAT = Mock()
        obj.UNFILTERED = True
        runner = CliRunner()
        mock_lookup.return_value = "id"
        self.assertEqual(
            "<Result okay>", str(runner.invoke(self.standing_orders, obj=obj))
        )
        self.assertFalse(mock_click.called)

    @patch("dkb_robo.cli._id_lookup")
    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_009_standing_orders(self, mock_login, mock_click, mock_lookup):
        """test standing orders"""
        obj = Config()
        obj.FORMAT = Mock()
        obj.UNFILTERED = False
        runner = CliRunner()
        mock_lookup.return_value = "id"
        self.assertEqual(
            "<Result okay>", str(runner.invoke(self.standing_orders, obj=obj))
        )
        self.assertFalse(mock_click.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_010_standing_orders(self, mock_login, mock_click):
        """standing orders"""
        from dkb_robo import DKBRoboError

        mock_login.side_effect = DKBRoboError("Error during session confirmation")
        obj = Config()
        obj.FORMAT = "foo"
        runner = CliRunner()
        self.assertIn(
            "<Result okay>", str(runner.invoke(self.standing_orders, obj=obj))
        )
        self.assertTrue(mock_click.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_010_credit_limits(self, mock_login, mock_click):
        """credit limits"""
        obj = Config()
        obj.FORMAT = Mock()
        runner = CliRunner()
        self.assertEqual(
            "<Result okay>", str(runner.invoke(self.credit_limits, obj=obj))
        )
        self.assertFalse(mock_click.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_011_credit_limits(self, mock_login, mock_click):
        """credit limits"""
        from dkb_robo import DKBRoboError

        mock_login.side_effect = DKBRoboError("Error during session confirmation")
        obj = Config()
        obj.FORMAT = "foo"
        runner = CliRunner()
        self.assertIn("<Result okay>", str(runner.invoke(self.credit_limits, obj=obj)))
        self.assertTrue(mock_click.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_012_last_login(self, mock_login, mock_click):
        """test last login"""
        obj = Config()
        obj.FORMAT = Mock()
        runner = CliRunner()
        self.assertEqual("<Result okay>", str(runner.invoke(self.last_login, obj=obj)))
        self.assertFalse(mock_click.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_013_last_login(self, mock_login, mock_click):
        """test last login"""
        from dkb_robo import DKBRoboError

        mock_login.side_effect = DKBRoboError("Error during session confirmation")
        obj = Config()
        obj.FORMAT = "foo"
        runner = CliRunner()
        self.assertIn("<Result okay>", str(runner.invoke(self.last_login, obj=obj)))
        self.assertTrue(mock_click.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_014_accounts(self, mock_login, mock_click):
        """test accounts"""
        obj = Config()
        obj.FORMAT = Mock()
        runner = CliRunner()
        self.assertEqual("<Result okay>", str(runner.invoke(self.accounts, obj=obj)))
        self.assertFalse(mock_click.called)

    @patch("dkb_robo.cli.object2dictionary")
    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_015_accounts(self, mock_login, mock_click, mock_object2dictionary):
        """test accounts"""
        mock_login.return_value.__enter__.return_value.account_dic = {
            1: {"details": "details", "transactions": "transactions"},
            2: {"details": "details", "transactions": "transactions"},
        }
        obj = Config()
        obj.FORMAT = Mock()
        obj.UNFILTERED = True
        runner = CliRunner()
        self.assertEqual("<Result okay>", str(runner.invoke(self.accounts, obj=obj)))
        self.assertFalse(mock_click.called)
        self.assertTrue(mock_object2dictionary.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_016_accounts(self, mock_login, mock_click):
        """test accounts"""
        from dkb_robo import DKBRoboError

        mock_login.side_effect = DKBRoboError("Error during session confirmation")
        obj = Config()
        obj.FORMAT = "foo"
        runner = CliRunner()
        self.assertIn("<Result okay>", str(runner.invoke(self.accounts, obj=obj)))
        self.assertTrue(mock_click.called)

    @patch("click.option")
    @patch("click.pass_context")
    def test_017_main(self, mock_pass, mock_option):
        """test main"""

        ctx = MagicMock()
        debug = "debug"
        use_tan = "use_tan"
        username = "username"
        password = "password"
        format = "format"
        obj = Config()
        obj.FORMAT = "foo"

        # self.assertEqual('foo', self.main(ctx, use_tan, username, password, format))
        runner = CliRunner()
        self.assertIn(
            "<Result SystemExit(2)>",
            str(
                runner.invoke(
                    self.accounts, [use_tan, username, password, format], obj=obj
                )
            ),
        )

    @patch("dkb_robo.cli._account_lookup", autospec=True)
    def test_018_id_lookup(self, mock_account_lookup):
        """test id look with unfiltered True"""
        ctx = MagicMock()
        name = "test_name"
        account = "test_account"
        account_dic = {"test_account": {"id": "123"}}
        mock_account_lookup.return_value = MagicMock(id="123")
        result = self._id_lookup(ctx, name, account, account_dic, True)
        mock_account_lookup.assert_called_once_with(
            ctx, name, account, account_dic, True
        )
        self.assertEqual(result, "123")

    @patch("dkb_robo.cli._account_lookup", autospec=True)
    def test_019_id_lookup(self, mock_account_lookup):
        """test id look with unfiltered False"""
        ctx = MagicMock()
        name = "test_name"
        account = "test_account"
        account_dic = {"test_account": {"id": "123"}}
        mock_account_lookup.return_value = {"id": "123"}
        result = self._id_lookup(ctx, name, account, account_dic, False)

        mock_account_lookup.assert_called_once_with(
            ctx, name, account, account_dic, False
        )
        self.assertEqual(result, "123")

    @patch("dkb_robo.cli._account_lookup", autospec=True)
    def test_020_id_lookup(self, mock_account_lookup):
        """test id look with unfiltered False"""
        ctx = MagicMock()
        name = "test_name"
        account = "test_account"
        account_dic = {"test_account": {"id": "123"}}
        mock_account_lookup.return_value = MagicMock(id=None)
        result = self._id_lookup(ctx, name, account, account_dic, True)
        mock_account_lookup.assert_called_once_with(
            ctx, name, account, account_dic, True
        )
        self.assertIsNone(result)

    def test_021_account_lookup(self):
        """test account lookup by name filtered"""
        ctx = MagicMock()
        name = "Test Account"
        account = None
        account_dic = {
            "acc1": {"name": "Test Account", "account": "123456"},
            "acc2": {"name": "Other Account", "account": "654321"},
        }
        unfiltered = False
        self.assertEqual(
            self._account_lookup(ctx, name, account, account_dic, unfiltered),
            account_dic["acc1"],
        )

    def test_022_account_lookup(self):
        """test account lookup by name unfiltered"""
        ctx = MagicMock()
        name = "Test Account"
        account = None
        account_dic = {
            "acc1": MagicMock(product=MagicMock(displayName="Test Account")),
            "acc2": MagicMock(product=MagicMock(displayName="Other Account")),
        }
        unfiltered = True
        self.assertEqual(
            self._account_lookup(ctx, name, account, account_dic, unfiltered),
            account_dic["acc1"],
        )

    def test_023_account_lookup(self):
        """test account lookup by account unfiltered"""
        ctx = MagicMock()
        name = None
        account = "123456"
        account_dic = {
            "acc1": {"name": "Test Account", "account": "123456"},
            "acc2": {"name": "Other Account", "account": "654321"},
        }
        unfiltered = False
        result = self._account_lookup(ctx, name, account, account_dic, unfiltered)
        self.assertEqual(result, account_dic["acc1"])

    def test_024_account_lookup(self):
        """test account lookup by account unfiltered"""
        ctx = MagicMock()
        name = None
        account = "123456"
        account_dic = {
            "acc1": MagicMock(type="account", iban="123456"),
            "acc2": MagicMock(type="account", iban="654321"),
        }
        unfiltered = True
        self.assertEqual(
            self._account_lookup(ctx, name, account, account_dic, unfiltered),
            account_dic["acc1"],
        )

    @patch("dkb_robo.cli.click.echo", autospec=True)
    def test_025_account_lookup(self, mock_echo):
        """test account lookup no name match"""
        ctx = MagicMock()
        name = "Nonexistent Account"
        account = None
        account_dic = {
            "acc1": {"name": "Test Account", "account": "123456"},
            "acc2": {"name": "Other Account", "account": "654321"},
        }
        unfiltered = False
        with self.assertRaises(click.Abort):
            self._account_lookup(ctx, name, account, account_dic, unfiltered)
        mock_echo.assert_called_once_with(
            "No account found matching 'Nonexistent Account'", err=True
        )

    def test_026_account_lookup(self):
        """test account lookup neiner name nor account"""
        ctx = MagicMock()
        name = None
        account = None
        account_dic = {
            "acc1": {"name": "Test Account", "account": "123456"},
            "acc2": {"name": "Other Account", "account": "654321"},
        }
        unfiltered = False
        with self.assertRaises(click.UsageError):
            self._account_lookup(ctx, name, account, account_dic, unfiltered)

    @patch("dkb_robo.cli._account_lookup", autospec=True)
    def test_027_transactionlink_lookup(self, mock_account_lookup):
        """test transaction link lookup unfiltered True"""
        self.ctx = MagicMock()
        name = "Test Account"
        account = None
        account_dic = {
            "acc1": MagicMock(
                id="123", type="account", transactions="transactions_link"
            )
        }
        unfiltered = True
        mock_account_lookup.return_value = account_dic["acc1"]
        result = self._transactionlink_lookup(
            self.ctx, name, account, account_dic, unfiltered
        )
        expected_output = {
            "id": "123",
            "type": "account",
            "transactions": "transactions_link",
        }
        mock_account_lookup.assert_called_once_with(
            self.ctx, name, account, account_dic, unfiltered
        )
        self.assertEqual(result, expected_output)

    @patch("dkb_robo.cli._account_lookup", autospec=True)
    def test_028_transactionlink_lookup(self, mock_account_lookup):
        """test transaction link lookup unfiltered False"""
        self.ctx = MagicMock()
        name = "Test Account"
        account = None
        account_dic = {
            "acc1": {
                "id": "123",
                "type": "account",
                "transactions": "transactions_link",
            }
        }
        unfiltered = False
        mock_account_lookup.return_value = account_dic["acc1"]
        result = self._transactionlink_lookup(
            self.ctx, name, account, account_dic, unfiltered
        )
        expected_output = {
            "id": "123",
            "type": "account",
            "transactions": "transactions_link",
        }
        mock_account_lookup.assert_called_once_with(
            self.ctx, name, account, account_dic, unfiltered
        )
        self.assertEqual(result, expected_output)

    @patch("dkb_robo.cli._account_lookup", autospec=True)
    def test_029_transactionlink_lookup(self, mock_account_lookup):
        """test transaction link lookup unfiltered True no id"""
        self.ctx = MagicMock()
        name = "Test Account"
        account = None
        account_dic = {
            "acc1": MagicMock(id=None, type="account", transactions="transactions_link")
        }
        unfiltered = True
        mock_account_lookup.return_value = account_dic["acc1"]
        result = self._transactionlink_lookup(
            self.ctx, name, account, account_dic, unfiltered
        )
        expected_output = {
            "id": None,
            "type": "account",
            "transactions": "transactions_link",
        }
        mock_account_lookup.assert_called_once_with(
            self.ctx, name, account, account_dic, unfiltered
        )
        self.assertEqual(result, expected_output)

    @patch("dkb_robo.cli._account_lookup", autospec=True)
    def test_030_transactionlink_lookup(self, mock_account_lookup):
        """test transaction link lookup unfiltered False no id"""
        self.ctx = MagicMock()
        name = "Test Account"
        account = None
        account_dic = {
            "acc1": {"id": None, "type": "account", "transactions": "transactions_link"}
        }
        unfiltered = False
        mock_account_lookup.return_value = account_dic["acc1"]
        result = self._transactionlink_lookup(
            self.ctx, name, account, account_dic, unfiltered
        )
        expected_output = {
            "id": None,
            "type": "account",
            "transactions": "transactions_link",
        }
        mock_account_lookup.assert_called_once_with(
            self.ctx, name, account, account_dic, unfiltered
        )
        self.assertEqual(result, expected_output)

    @patch("dkb_robo.dkb_robo.DKBRobo.scan_postbox", autospec=True)
    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_031_scan_postbox(self, mock_login, mock_click, mock_scanpb):
        """test scan postbox"""
        mock_login.return_value.__enter__.return_value.account_dic = {
            1: {"details": "details", "transactions": "transactions"},
            2: {"details": "details", "transactions": "transactions"},
        }
        mock_scanpb.return_value = {"foo": "bar"}
        obj = Config()
        obj.FORMAT = Mock()
        obj.UNFILTERED = False
        runner = CliRunner()
        self.assertEqual(
            "<Result okay>", str(runner.invoke(self.scan_postbox, obj=obj))
        )
        self.assertFalse(mock_click.called)
        # self.assertTrue(mock_scanpb.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_032_scan_postbox(self, mock_login, mock_click):
        """test scan postbox"""
        from dkb_robo import DKBRoboError

        mock_login.side_effect = DKBRoboError("Error during session confirmation")
        obj = Config()
        obj.FORMAT = Mock()
        obj.UNFILTERED = False
        runner = CliRunner()
        self.assertEqual(
            "<Result okay>", str(runner.invoke(self.scan_postbox, obj=obj))
        )
        self.assertTrue(mock_click.called)

    @patch("dkb_robo.dkb_robo.DKBRobo.scan_postbox", autospec=True)
    @patch("dkb_robo.cli.object2dictionary")
    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_033_scan_postbox(self, mock_login, mock_click, mock_o2d, mock_scanpb):
        """test scan postbox"""
        mock_login.return_value.__enter__.return_value.account_dic = {
            1: {"details": "details", "transactions": "transactions"},
            2: {"details": "details", "transactions": "transactions"},
        }
        mock_scanpb.return_value = {"foo": "bar"}
        obj = Config()
        obj.FORMAT = Mock()
        obj.UNFILTERED = True
        runner = CliRunner()
        self.assertEqual(
            "<Result okay>", str(runner.invoke(self.scan_postbox, obj=obj))
        )
        self.assertFalse(mock_click.called)
        # self.assertTrue(mock_o2d.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_033_download(self, mock_login, mock_click):
        """test scan postbox"""
        obj = Config()
        obj.FORMAT = Mock()
        obj.UNFILTERED = False
        runner = CliRunner()
        self.assertEqual("<Result okay>", str(runner.invoke(self.download, obj=obj)))
        self.assertFalse(mock_click.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_034_download(self, mock_login, mock_click):
        """test scan postbox"""
        from dkb_robo import DKBRoboError

        mock_login.side_effect = DKBRoboError("Error during session confirmation")
        obj = Config()
        obj.FORMAT = Mock()
        obj.UNFILTERED = False
        runner = CliRunner()
        self.assertEqual("<Result okay>", str(runner.invoke(self.download, obj=obj)))
        self.assertTrue(mock_click.called)


if __name__ == "__main__":

    unittest.main()
