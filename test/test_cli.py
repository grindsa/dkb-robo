#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""unittests for dkb_robo"""

import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock, Mock, mock_open
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
            _store_http1_only,
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
            DataclassJSONEncoder,
        )

        self.logger = logging.getLogger("dkb_robo")
        self._load_format = _load_format
        self._login = _login
        self._store_http1_only = _store_http1_only
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
        self.DataclassJSONEncoder = DataclassJSONEncoder

    def test_001_default(self):
        """default test which always passes"""
        self.assertEqual("foo", "foo")

    def test_002_dataclass_json_encoder(self):
        """test DataclassJSONEncoder serializes dataclass objects"""
        from dkb_robo.utilities import Account

        payload = Account(accountNr="123", iban="DE001234", name="Main")

        result = json.dumps(payload, cls=self.DataclassJSONEncoder)

        self.assertEqual(
            '{"accountNr": "123", "accountId": null, "bic": null, "blz": null, "iban": "DE001234", "id": null, "intermediaryName": null, "name": "Main"}',
            result,
        )

    def test_003_dataclass_json_encoder_non_dataclass(self):
        """test DataclassJSONEncoder fallback raises TypeError for unknown objects"""

        with self.assertRaises(TypeError):
            self.DataclassJSONEncoder().default(object())

    def test_004_login(self):
        """test login"""
        cursor = MagicMock()
        cursor.__iter__.return_value = []
        self.assertTrue(self._login(cursor))

    @patch("dkb_robo.cli.dkb_robo.DKBRobo")
    def test_005_login_headless(self, mock_dkb_robo):
        """test _login() forwards HEADLESS option to DKBRobo"""
        ctx = MagicMock()
        ctx.obj = {
            "USERNAME": "user",
            "PASSWORD": "password",
            "CHIP_TAN": False,
            "DEBUG": False,
            "UNFILTERED": False,
            "MFA_DEVICE": None,
            "HEADLESS": True,
            "XVFB": False,
            "SESSION_BACKEND": "requests",
            "HTTP1_ONLY": False,
        }

        self._login(ctx)

        self.assertTrue(mock_dkb_robo.call_args.kwargs["headless"])

    @patch("dkb_robo.cli.dkb_robo.DKBRobo")
    def test_006_login_http1_only(self, mock_dkb_robo):
        """test _login() forwards HTTP1_ONLY option to DKBRobo"""
        ctx = MagicMock()
        ctx.obj = {
            "USERNAME": "user",
            "PASSWORD": "password",
            "CHIP_TAN": False,
            "DEBUG": False,
            "UNFILTERED": False,
            "MFA_DEVICE": None,
            "HEADLESS": False,
            "XVFB": False,
            "SESSION_BACKEND": "curl-cffi",
            "HTTP1_ONLY": True,
        }

        self._login(ctx)

        self.assertTrue(mock_dkb_robo.call_args.kwargs["http1_only"])

    @patch("dkb_robo.cli.dkb_robo.DKBRobo")
    def test_007_login_proxy(self, mock_dkb_robo):
        """test _login() maps PROXY option to http/https proxies"""
        ctx = MagicMock()
        ctx.obj = {
            "USERNAME": "user",
            "PASSWORD": "password",
            "CHIP_TAN": False,
            "DEBUG": False,
            "UNFILTERED": False,
            "MFA_DEVICE": None,
            "HEADLESS": False,
            "XVFB": False,
            "SESSION_BACKEND": "curl-cffi",
            "HTTP1_ONLY": False,
            "PROXY": "http://127.0.0.1:8080",
        }

        self._login(ctx)

        self.assertEqual(
            {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"},
            mock_dkb_robo.call_args.kwargs["proxies"],
        )

    def test_008_store_http1_only_initializes_ctx_obj(self):
        """test _store_http1_only initializes ctx.obj when missing"""
        ctx = MagicMock()
        ctx.obj = None

        result = self._store_http1_only(ctx, None, True)

        self.assertTrue(result)
        self.assertEqual({"HTTP1_ONLY": True}, ctx.obj)

    @patch("dkb_robo.cli.dkb_robo.DKBRobo")
    def test_009_main_accepts_proxy_after_subcommand(self, mock_dkb_robo):
        """test main accepts --proxy/--http1-only after subcommand"""
        mock_dkb = MagicMock()
        mock_dkb.account_dic = {}
        mock_dkb_robo.return_value.__enter__.return_value = mock_dkb

        runner = CliRunner()
        result = runner.invoke(
            self.main,
            [
                "-u",
                "user",
                "-p",
                "password",
                "accounts",
                "--proxy",
                "http://127.0.0.1:8080",
                "--http1-only",
            ],
        )

        self.assertEqual(0, result.exit_code)
        self.assertEqual(
            {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"},
            mock_dkb_robo.call_args.kwargs["proxies"],
        )
        self.assertTrue(mock_dkb_robo.call_args.kwargs["http1_only"])

    def test_010_load_format(self):
        """test _load_format()"""
        oformat = "pprint"
        self.assertIn("pprint", self._load_format(oformat).__code__.co_names)

    def test_011_load_format(self):
        """test _load_format()"""
        oformat = "csv"
        self.assertIn("csv", self._load_format(oformat).__code__.co_names)

    def test_012_load_format(self):
        """test _load_format()"""
        oformat = "table"
        self.assertIn("tabulate", self._load_format(oformat).__code__.co_names)

    def test_013_load_format(self):
        """test _load_format()"""
        oformat = "json"
        self.assertIn("json", self._load_format(oformat).__code__.co_names)

    def test_014_load_format(self):
        """test _load_format()"""
        oformat = "foo"
        with self.assertRaises(Exception) as err:
            self._load_format(oformat)
        self.assertEqual("Unknown format: foo", str(err.exception))

    @patch("dkb_robo.cli._account_lookup")
    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_015_standing_orders(self, mock_login, mock_click, mock_lookup):
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
    def test_016_standing_orders(self, mock_login, mock_click, mock_lookup):
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
    def test_017_standing_orders(self, mock_login, mock_click):
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
    def test_018_credit_limits(self, mock_login, mock_click):
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
    def test_019_credit_limits(self, mock_login, mock_click):
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
    def test_020_last_login(self, mock_login, mock_click):
        """test last login"""
        obj = Config()
        obj.FORMAT = Mock()
        runner = CliRunner()
        self.assertEqual("<Result okay>", str(runner.invoke(self.last_login, obj=obj)))
        self.assertFalse(mock_click.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_021_last_login(self, mock_login, mock_click):
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
    def test_022_accounts(self, mock_login, mock_click):
        """test accounts"""
        obj = Config()
        obj.FORMAT = Mock()
        runner = CliRunner()
        self.assertEqual("<Result okay>", str(runner.invoke(self.accounts, obj=obj)))
        self.assertFalse(mock_click.called)

    @patch("dkb_robo.cli.object2dictionary")
    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_023_accounts(self, mock_login, mock_click, mock_object2dictionary):
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

    @patch("dkb_robo.cli._login")
    def test_024_accounts_removes_details_and_transactions(self, mock_login):
        """test accounts removes details/transactions fields before formatting"""
        account_dic = {
            1: {
                "id": "acc-1",
                "name": "Main",
                "details": {"foo": "bar"},
                "transactions": "/tx/1",
            }
        }
        mock_login.return_value.__enter__.return_value.account_dic = account_dic
        formatter = Mock()

        runner = CliRunner()
        result = runner.invoke(
            self.accounts,
            obj={"FORMAT": formatter, "UNFILTERED": False},
        )

        self.assertEqual("<Result okay>", str(result))
        formatter.assert_called_once_with([{"id": "acc-1", "name": "Main"}])
        self.assertNotIn("details", account_dic[1])
        self.assertNotIn("transactions", account_dic[1])

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_025_accounts(self, mock_login, mock_click):
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
    def test_026_main(self, mock_pass, mock_option):
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
    def test_027_id_lookup(self, mock_account_lookup):
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
    def test_028_id_lookup(self, mock_account_lookup):
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
    def test_029_id_lookup(self, mock_account_lookup):
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

    def test_030_account_lookup(self):
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

    def test_031_account_lookup(self):
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

    def test_032_account_lookup(self):
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

    def test_033_account_lookup(self):
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
    def test_034_account_lookup(self, mock_echo):
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

    def test_035_account_lookup(self):
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
    def test_036_transactionlink_lookup(self, mock_account_lookup):
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
    def test_037_transactionlink_lookup(self, mock_account_lookup):
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
    def test_038_transactionlink_lookup(self, mock_account_lookup):
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
    def test_039_transactionlink_lookup(self, mock_account_lookup):
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
    def test_040_scan_postbox(self, mock_login, mock_click, mock_scanpb):
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
    def test_041_scan_postbox(self, mock_login, mock_click):
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
    def test_042_scan_postbox(self, mock_login, mock_click, mock_o2d, mock_scanpb):
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

    @patch("dkb_robo.cli._login")
    def test_043_scan_postbox_passthrough_when_filtered(self, mock_login):
        """test scan_postbox keeps doc_list unchanged when UNFILTERED=False"""
        formatter = Mock()
        doc_list = {"doc-1": {"id": "doc-1"}}

        dkb = Mock()
        dkb.scan_postbox.return_value = doc_list
        mock_login.return_value.__enter__.return_value = dkb

        runner = CliRunner()
        result = runner.invoke(
            self.scan_postbox,
            obj={"FORMAT": formatter, "UNFILTERED": False},
        )

        self.assertEqual("<Result okay>", str(result))
        formatter.assert_called_once_with(doc_list)

    @patch("dkb_robo.cli.object2dictionary")
    @patch("dkb_robo.cli._login")
    def test_044_scan_postbox_converts_each_doc_when_unfiltered(
        self, mock_login, mock_o2d
    ):
        """test scan_postbox converts each doc when UNFILTERED=True"""
        formatter = Mock()
        doc_a = object()
        doc_b = object()
        doc_list = {"a": doc_a, "b": doc_b}

        dkb = Mock()
        dkb.scan_postbox.return_value = doc_list
        mock_login.return_value.__enter__.return_value = dkb

        mock_o2d.side_effect = [{"id": "a"}, {"id": "b"}]

        runner = CliRunner()
        result = runner.invoke(
            self.scan_postbox,
            obj={"FORMAT": formatter, "UNFILTERED": True},
        )

        self.assertEqual("<Result okay>", str(result))
        self.assertEqual(2, mock_o2d.call_count)
        mock_o2d.assert_any_call(doc_a)
        mock_o2d.assert_any_call(doc_b)
        formatter.assert_called_once_with([{"id": "a"}, {"id": "b"}])

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_045_download(self, mock_login, mock_click):
        """test scan postbox"""
        obj = Config()
        obj.FORMAT = Mock()
        obj.UNFILTERED = False
        runner = CliRunner()
        self.assertEqual("<Result okay>", str(runner.invoke(self.download, obj=obj)))
        self.assertFalse(mock_click.called)

    @patch("click.echo")
    @patch("dkb_robo.cli._login")
    def test_046_download(self, mock_login, mock_click):
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
