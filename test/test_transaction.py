# -*- coding: utf-8 -*-
# pylint: disable=r0904, c0415, c0413, r0913, w0212
""" unittests for dkb_robo """
import sys
import os
from datetime import date
import unittest
import logging
import json
from unittest.mock import patch, Mock, MagicMock, mock_open
from bs4 import BeautifulSoup
from mechanicalsoup import LinkNotFoundError
import io

sys.path.insert(0, ".")
sys.path.insert(0, "..")
from dkb_robo.transaction import (
    Transactions,
    AccountTransactionItem,
    CreditCardTransactionItem,
    DepotTransactionItem,
)


def json_load(fname):
    """simple json load"""

    with open(fname, "r", encoding="utf8") as myfile:
        data_dic = json.load(myfile)

    return data_dic


class TestTransactions(unittest.TestCase):
    """Transactions test class"""

    @patch("requests.Session")
    def setUp(self, mock_session):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.transaction = Transactions(client=mock_session)
        self.maxDiff = None

    def test_001__fetch(self):
        """test Transactions._fetch() returning error"""
        self.transaction.client = Mock()
        self.transaction.client.get.return_value.status_code = 400
        self.transaction.client.get.return_value.json.return_value = {"foo": "bar"}
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(
                {"data": [], "included": []}, self.transaction._fetch("transaction_url")
            )
        self.assertIn(
            "ERROR:dkb_robo.transaction:fetch transactions: http status code is not 200 but 400",
            lcm.output,
        )

    def test_002__fetch(self):
        """test _get_transaction_list() with wrong response"""
        self.transaction.client = Mock()
        self.transaction.client.get.return_value.status_code = 200
        self.transaction.client.get.return_value.json.return_value = {"foo": "bar"}
        self.assertEqual(
            {"data": [], "included": []}, self.transaction._fetch("transaction_url")
        )

    def test_003__fetch(self):
        """test _get_transaction_list() without pagination"""
        self.transaction.client = Mock()
        self.transaction.client.get.return_value.status_code = 200
        self.transaction.client.get.return_value.json.return_value = {
            "data": [{"foo1": "bar1"}, {"foo2": "bar2"}]
        }
        self.assertEqual(
            {"data": [{"foo1": "bar1"}, {"foo2": "bar2"}], "included": []},
            self.transaction._fetch("transaction_url"),
        )

    def test_004__fetch(self):
        """test _get_transaction_list()"""
        self.transaction.client = Mock()
        self.transaction.client.get.return_value.status_code = 200
        self.transaction.client.get.return_value.json.side_effect = [
            {
                "data": [{"foo1": "bar1"}, {"foo2": "bar2"}],
                "links": {"next": "next_url"},
            },
            {"data": [{"foo3": "bar3"}, {"foo4": "bar4"}], "links": {"foo": "bar"}},
        ]
        self.assertEqual(
            {
                "data": [
                    {"foo1": "bar1"},
                    {"foo2": "bar2"},
                    {"foo3": "bar3"},
                    {"foo4": "bar4"},
                ],
                "included": [],
            },
            self.transaction._fetch("transaction_url"),
        )

    def test_005__fetch(self):
        """test _get_transaction_list() with pagination"""
        self.transaction.client = Mock()
        self.transaction.client.get.return_value.status_code = 200
        self.transaction.client.get.return_value.json.side_effect = [
            {
                "data": [{"foo1": "bar1"}, {"foo2": "bar2"}],
                "links": {"next": "next_url"},
                "included": ["1"],
            },
            {
                "data": [{"foo3": "bar3"}, {"foo4": "bar4"}],
                "links": {"foo": "bar"},
                "included": ["2"],
            },
        ]
        self.assertEqual(
            {
                "data": [
                    {"foo1": "bar1"},
                    {"foo2": "bar2"},
                    {"foo3": "bar3"},
                    {"foo4": "bar4"},
                ],
                "included": ["1", "2"],
            },
            self.transaction._fetch("transaction_url"),
        )

    def test_006__filter(self):
        """test _filter() with empty transaction list"""
        transaction_list = []
        from_date = "01.01.2023"
        to_date = "31.01.2023"
        self.assertFalse(
            self.transaction._filter(transaction_list, from_date, to_date, "trtype")
        )

    def test_007__filter(self):
        """test _filter() with a single transaction"""
        transaction_list = [
            {
                "foo": "bar",
                "attributes": {"status": "trtype", "bookingDate": "2023-01-15"},
            }
        ]
        from_date = "01.01.2023"
        to_date = "31.01.2023"
        result = [
            {
                "foo": "bar",
                "attributes": {"status": "trtype", "bookingDate": "2023-01-15"},
            }
        ]
        self.assertEqual(
            result,
            self.transaction._filter(transaction_list, from_date, to_date, "trtype"),
        )

    def test_008__filter(self):
        """test _filter_transactions() with two transactions"""
        transaction_list = [
            {
                "foo1": "bar1",
                "attributes": {"status": "trtype", "bookingDate": "2023-01-10"},
            },
            {
                "foo2": "bar2",
                "attributes": {"status": "trtype", "bookingDate": "2023-01-15"},
            },
        ]
        from_date = "01.01.2023"
        to_date = "31.01.2023"
        result = [
            {
                "foo1": "bar1",
                "attributes": {"status": "trtype", "bookingDate": "2023-01-10"},
            },
            {
                "foo2": "bar2",
                "attributes": {"status": "trtype", "bookingDate": "2023-01-15"},
            },
        ]
        self.assertEqual(
            result,
            self.transaction._filter(transaction_list, from_date, to_date, "trtype"),
        )

    def test_009__filter(self):
        """test _filter_transactions() with two transactions but only one is in range"""
        transaction_list = [
            {
                "foo1": "bar1",
                "attributes": {"status": "trtype", "bookingDate": "2023-01-10"},
            },
            {
                "foo2": "bar2",
                "attributes": {"status": "trtype", "bookingDate": "2023-02-15"},
            },
        ]
        from_date = "01.01.2023"
        to_date = "31.01.2023"
        result = [
            {
                "foo1": "bar1",
                "attributes": {"status": "trtype", "bookingDate": "2023-01-10"},
            }
        ]
        self.assertEqual(
            result,
            self.transaction._filter(transaction_list, from_date, to_date, "trtype"),
        )

    def test_010__filter(self):
        """test _filter_transactions() with two transaction but only one is the right type"""
        transaction_list = [
            {
                "foo1": "bar1",
                "attributes": {"status": "trtype", "bookingDate": "2023-01-10"},
            },
            {
                "foo2": "bar2",
                "attributes": {"status": "trtype2", "bookingDate": "2023-01-15"},
            },
        ]
        from_date = "01.01.2023"
        to_date = "31.01.2023"
        result = [
            {
                "foo1": "bar1",
                "attributes": {"status": "trtype", "bookingDate": "2023-01-10"},
            }
        ]
        self.assertEqual(
            result,
            self.transaction._filter(transaction_list, from_date, to_date, "trtype"),
        )

    def test_011__filter(self):
        """test _filter_transactions() with two transaction check for booked status"""
        transaction_list = [
            {
                "foo1": "bar1",
                "attributes": {"status": "booked", "bookingDate": "2023-01-10"},
            },
            {
                "foo2": "bar2",
                "attributes": {"status": "pending", "bookingDate": "2023-01-15"},
            },
        ]
        from_date = "01.01.2023"
        to_date = "31.01.2023"
        result = [
            {
                "foo1": "bar1",
                "attributes": {"status": "booked", "bookingDate": "2023-01-10"},
            }
        ]
        self.assertEqual(
            result,
            self.transaction._filter(transaction_list, from_date, to_date, "booked"),
        )

    def test_012__filter(self):
        """test _filter_transactions() with two transactions check for pending status"""
        transaction_list = [
            {
                "foo1": "bar1",
                "attributes": {"status": "booked", "bookingDate": "2023-01-10"},
            },
            {
                "foo2": "bar2",
                "attributes": {"status": "pending", "bookingDate": "2023-01-15"},
            },
        ]
        from_date = "2023-01-01"
        to_date = "2023-01-31"
        result = [
            {
                "foo2": "bar2",
                "attributes": {"status": "pending", "bookingDate": "2023-01-15"},
            }
        ]
        self.assertEqual(
            result,
            self.transaction._filter(transaction_list, from_date, to_date, "pending"),
        )

    def test_013__filter(self):
        """test _filter_transactions() with two transactions check for reserved status"""
        transaction_list = [
            {
                "foo1": "bar1",
                "attributes": {"status": "booked", "bookingDate": "2023-01-10"},
            },
            {
                "foo2": "bar2",
                "attributes": {"status": "pending", "bookingDate": "2023-01-15"},
            },
        ]
        from_date = "01.01.2023"
        to_date = "31.01.2023"
        result = [
            {
                "foo2": "bar2",
                "attributes": {"status": "pending", "bookingDate": "2023-01-15"},
            }
        ]
        self.assertEqual(
            result,
            self.transaction._filter(transaction_list, from_date, to_date, "reserved"),
        )

    @patch("dkb_robo.transaction.AccountTransactionItem")
    @patch("dkb_robo.transaction.Transactions._filter")
    @patch("dkb_robo.transaction.Transactions._fetch")
    def test_014_get(self, mock_fetch, mock_filter, mock_aformat):
        "" " test get() for acount transactions " ""
        mock_aformat.return_value = "mock_aformat"
        mock_aformat.format.return_value = "foo"
        mock_filter.return_value = [{"foo": "bar"}]
        self.transaction.unfiltered = True
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertFalse(
                self.transaction.get(
                    "transaction_url", "account", "from_date", "to_date"
                )
            )
        self.assertIn(
            "INFO:dkb_robo.transaction:fetching account transactions", lcm.output
        )
        self.assertTrue(mock_fetch.called)
        self.assertTrue(mock_filter.called)
        self.assertFalse(mock_aformat.called)

    @patch("dkb_robo.transaction.DepotTransactionItem")
    @patch("dkb_robo.transaction.CreditCardTransactionItem")
    @patch("dkb_robo.transaction.AccountTransactionItem")
    @patch("dkb_robo.transaction.Transactions._correlate")
    @patch("dkb_robo.transaction.Transactions._filter")
    @patch("dkb_robo.transaction.Transactions._fetch")
    def test_015_get(
        self,
        mock_fetch,
        mock_filter,
        mock_correlate,
        mock_aformat,
        mock_creditformat,
        mock_depotformat,
    ):
        "" " test get() for acount transactions " ""
        mock_aformat.return_value = "mock_aformat"
        mock_creditformat.return_value = "mock_creditformat"
        mock_depotformat.return_value = "mock_depotformat"
        mock_filter.return_value = [
            {"id": "id", "attributes": {"mock_filter": "mock_filter"}}
        ]
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(
                ["mock_aformat"],
                self.transaction.get(
                    "transaction_url", "account", "from_date", "to_date"
                ),
            )
        self.assertIn(
            "INFO:dkb_robo.transaction:fetching account transactions", lcm.output
        )
        self.assertTrue(mock_fetch.called)
        self.assertTrue(mock_filter.called)
        self.assertFalse(mock_correlate.called)
        self.assertTrue(mock_aformat.called)
        self.assertFalse(mock_creditformat.called)
        self.assertFalse(mock_depotformat.called)

    @patch("dkb_robo.transaction.AccountTransactionItem")
    @patch("dkb_robo.transaction.Transactions._filter")
    @patch("dkb_robo.transaction.Transactions._fetch")
    def test_016_get(self, mock_fetch, mock_filter, mock_aformat):
        "" " test get() for acount transactions " ""
        mock_aformat.return_value = "mock_aformat"
        mock_aformat.format.return_value = "foo"
        mock_filter.return_value = [
            {"id": "id", "attributes": {"mock_filter": "mock_filter"}}
        ]
        self.transaction.unfiltered = True
        self.assertEqual(
            ["mock_aformat"],
            self.transaction.get("transaction_url", "account", "from_date", "to_date"),
        )
        self.assertTrue(mock_fetch.called)
        self.assertTrue(mock_filter.called)
        self.assertTrue(mock_aformat.called)

    @patch("dkb_robo.transaction.DepotTransactionItem")
    @patch("dkb_robo.transaction.CreditCardTransactionItem")
    @patch("dkb_robo.transaction.AccountTransactionItem")
    @patch("dkb_robo.transaction.Transactions._correlate")
    @patch("dkb_robo.transaction.Transactions._filter")
    @patch("dkb_robo.transaction.Transactions._fetch")
    def test_017_get(
        self,
        mock_fetch,
        mock_filter,
        mock_correlate,
        mock_aformat,
        mock_creditformat,
        mock_depotformat,
    ):
        "" " test get() for card transactions " ""
        mock_aformat.return_value = "mock_aformat"
        mock_creditformat.return_value = "mock_creditformat"
        mock_depotformat.return_value = "mock_depotformat"
        mock_filter.return_value = [
            {"id": "id", "attributes": {"mock_filter": "mock_filter"}}
        ]
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(
                ["mock_creditformat"],
                self.transaction.get(
                    "transaction_url", "creditcard", "from_date", "to_date"
                ),
            )
        self.assertIn(
            "INFO:dkb_robo.transaction:fetching card transactions", lcm.output
        )
        self.assertTrue(mock_fetch.called)
        self.assertTrue(mock_filter.called)
        self.assertFalse(mock_correlate.called)
        self.assertFalse(mock_aformat.called)
        self.assertTrue(mock_creditformat.called)
        self.assertFalse(mock_depotformat.called)

    @patch("dkb_robo.transaction.DepotTransactionItem")
    @patch("dkb_robo.transaction.CreditCardTransactionItem")
    @patch("dkb_robo.transaction.AccountTransactionItem")
    @patch("dkb_robo.transaction.Transactions._correlate")
    @patch("dkb_robo.transaction.Transactions._filter")
    @patch("dkb_robo.transaction.Transactions._fetch")
    def test_018_get(
        self,
        mock_fetch,
        mock_filter,
        mock_correlate,
        mock_aformat,
        mock_creditformat,
        mock_depotformat,
    ):
        "" " test get() for depot transactions " ""
        mock_aformat.return_value = "mock_aformat"
        mock_creditformat.return_value = "mock_creditformat"
        mock_depotformat.return_value = "mock_depotformat"
        mock_filter.return_value = [
            {"id": "id", "attributes": {"mock_filter": "mock_filter"}}
        ]
        mock_correlate.return_value = [
            {"id": "id", "attributes": {"mock_correlate": "mock_correlate"}}
        ]
        self.assertEqual(
            ["mock_depotformat"],
            self.transaction.get("transaction_url", "depot", "from_date", "to_date"),
        )
        self.assertTrue(mock_fetch.called)
        self.assertFalse(mock_filter.called)
        self.assertTrue(mock_correlate.called)
        self.assertFalse(mock_aformat.called)
        self.assertFalse(mock_creditformat.called)
        self.assertTrue(mock_depotformat.called)

    def test_019_map(self):
        """test _details() - add instrument information"""
        included_list = [
            {
                "id": "inid",
                "attributes": {
                    "identifiers": [
                        {"identifier": "isin", "value": "value"},
                        {"identifier": "isin", "value": "value2"},
                    ],
                    "name": {"short": "short"},
                },
            }
        ]
        data_dic = {
            "attributes": {
                "performance": {"currentValue": {"value": 1000}},
                "lastOrderDate": "2020-01-01",
                "quantity": {"value": 1000, "unit": "unit"},
            },
            "relationships": {
                "instrument": {"data": {"id": "inid"}},
                "quote": {"data": {"id": "inid", "value": "value"}},
            },
        }
        result = {
            "attributes": {
                "performance": {"currentValue": {"value": 1000}},
                "lastOrderDate": "2020-01-01",
                "quantity": {"value": 1000, "unit": "unit"},
                "instrument": {
                    "identifiers": [
                        {"identifier": "isin", "value": "value"},
                        {"identifier": "isin", "value": "value2"},
                    ],
                    "name": {"short": "short"},
                    "id": "inid",
                },
                "quote": {
                    "identifiers": [
                        {"identifier": "isin", "value": "value"},
                        {"identifier": "isin", "value": "value2"},
                    ],
                    "name": {"short": "short"},
                    "id": "inid",
                },
            },
            "relationships": {
                "instrument": {"data": {"id": "inid"}},
                "quote": {"data": {"id": "inid", "value": "value"}},
            },
        }
        self.assertEqual(result, self.transaction._map(data_dic, included_list))

    def test_020_map(self):
        """test _details() - add instrument information"""
        included_list = [
            {
                "id": "inid",
                "attributes": {
                    "identifiers": [
                        {"identifier": "isin", "value": "value"},
                        {"identifier": "isin", "value": "value2"},
                    ],
                    "name": {"short": "short"},
                },
            }
        ]
        data_dic = {
            "attributes": {
                "performance": {"currentValue": {"value": 1000}},
                "lastOrderDate": "2020-01-01",
                "quantity": {"value": 1000, "unit": "unit"},
            },
            "relationships": {
                "instrument": {"data": {"id": "inid"}},
                "quote": {"data": {"id": "quoteid", "value": "value"}},
            },
        }
        result = {
            "attributes": {
                "performance": {"currentValue": {"value": 1000}},
                "lastOrderDate": "2020-01-01",
                "quantity": {"value": 1000, "unit": "unit"},
                "instrument": {
                    "identifiers": [
                        {"identifier": "isin", "value": "value"},
                        {"identifier": "isin", "value": "value2"},
                    ],
                    "name": {"short": "short"},
                    "id": "inid",
                },
            },
            "relationships": {
                "instrument": {"data": {"id": "inid"}},
                "quote": {"data": {"id": "quoteid", "value": "value"}},
            },
        }
        self.assertEqual(result, self.transaction._map(data_dic, included_list))

    def test_021_map(self):
        """test _details() - add instrument information"""
        included_list = [
            {
                "id": "inid",
                "attributes": {
                    "identifiers": [
                        {"identifier": "isin", "value": "value"},
                        {"identifier": "isin", "value": "value2"},
                    ],
                    "name": {"short": "short"},
                },
            }
        ]
        data_dic = {
            "attributes": {
                "performance": {"currentValue": {"value": 1000}},
                "lastOrderDate": "2020-01-01",
                "quantity": {"value": 1000, "unit": "unit"},
            },
            "relationships": {
                "instrument": {"data": {"id": "inid1"}},
                "quote": {"data": {"id": "inid", "value": "value"}},
            },
        }
        result = {
            "attributes": {
                "performance": {"currentValue": {"value": 1000}},
                "lastOrderDate": "2020-01-01",
                "quantity": {"value": 1000, "unit": "unit"},
                "quote": {
                    "identifiers": [
                        {"identifier": "isin", "value": "value"},
                        {"identifier": "isin", "value": "value2"},
                    ],
                    "name": {"short": "short"},
                    "id": "inid",
                },
            },
            "relationships": {
                "instrument": {"data": {"id": "inid1"}},
                "quote": {"data": {"id": "inid", "value": "value"}},
            },
        }
        self.assertEqual(result, self.transaction._map(data_dic, included_list))

    @patch("dkb_robo.transaction.Transactions._map")
    def test_022__correlate(self, mock_map):
        """test _correlate()"""
        mock_map.return_value = "mock_map"
        transaction_dic = {"data": [{"foo": "bar"}]}
        self.assertEqual(["mock_map"], self.transaction._correlate(transaction_dic))
        self.assertTrue(mock_map.called)

    @patch("dkb_robo.transaction.Transactions._map")
    def test_023__correlate(self, mock_map):
        """test _correlate()"""
        mock_map.return_value = "mock_map"
        transaction_dic = {"included": "included", "data": [{"foo": "bar"}]}
        self.assertEqual(["mock_map"], self.transaction._correlate(transaction_dic))
        self.assertTrue(mock_map.called)

    @patch("dkb_robo.transaction.Transactions._map")
    def test_024__correlate(self, mock_map):
        """test _correlate()"""
        mock_map.return_value = None
        transaction_dic = {"included": "included", "data": [{"foo": "bar"}]}
        self.assertFalse(self.transaction._correlate(transaction_dic))
        self.assertTrue(mock_map.called)

    @patch("dkb_robo.transaction.Transactions._map")
    def test_025__correlate(self, mock_map):
        """test _correlate()"""
        mock_map.return_value = "mock_map"
        transaction_dic = {"included": "included", "data1": [{"foo": "bar"}]}
        self.assertFalse(self.transaction._correlate(transaction_dic))
        self.assertFalse(mock_map.called)


class TestAccountTransactionItem(unittest.TestCase):
    def setUp(self):
        self.amount_data = {"value": 100, "currencyCode": "USD"}
        self.creditor_data = {
            "creditorAccount": {
                "iban": "DE1234567890",
                "bic": "BICCODE",
                "id": "creditor_id",
                "name": "Creditor Name",
                "intermediaryName": "credintermediaryName",
            },
            "agent": {"bic": "BICCODE"},
            "id": "creditor_id",
            "name": "Creditor Name",
        }
        self.debtor_data = {
            "debtorAccount": {
                "iban": "DE0987654321",
                "bic": "BICCODE1",
                "id": "debtor_id",
                "name": "Debtor Name",
                "intermediaryName": "debintermediaryName",
            },
            "agent": {"bic": "BICCODE1"},
            "id": "debtor_id",
            "name": "Debtor Name",
        }
        self.transaction_data = {
            "status": "completed",
            "bookingDate": "2022-01-15",
            "valueDate": "2022-01-16",
            "description": "Payment for services",
            "mandateId": "mandate123",
            "endToEndId": "endToEnd123",
            "transactionType": "credit",
            "purposeCode": "purpose123",
            "businessTransactionCode": "business123",
            "amount": self.amount_data,
            "creditor": self.creditor_data,
            "debtor": self.debtor_data,
            "isRevocable": False,
        }
        self.maxDiff = None

    @patch("dkb_robo.transaction.Amount", autospec=True)
    @patch("dkb_robo.transaction.Account", autospec=True)
    def test_026_post_init(self, MockAccount, MockAmount):
        MockAmount.return_value = MagicMock()
        MockAccount.return_value = MagicMock()

        transaction = AccountTransactionItem(**self.transaction_data)

        MockAmount.assert_called_once_with(**self.amount_data)
        MockAccount.assert_any_call(**self.creditor_data["creditorAccount"])
        MockAccount.assert_any_call(**self.debtor_data["debtorAccount"])
        self.assertEqual(transaction.description, "Payment for services")

    @patch("dkb_robo.transaction.logger")
    def test_027_peer_information(self, mock_logger):
        transaction = AccountTransactionItem(**self.transaction_data)
        self.assertEqual("BICCODE", transaction.creditor.bic)
        self.assertEqual("creditor_id", transaction.creditor.id)
        self.assertEqual("Creditor Name", transaction.creditor.name)
        self.assertEqual("credintermediaryName", transaction.creditor.intermediaryName)
        self.assertEqual("BICCODE1", transaction.debtor.bic)
        self.assertEqual("BICCODE1", transaction.debtor.bic)
        self.assertEqual("debtor_id", transaction.debtor.id)
        self.assertEqual("Debtor Name", transaction.debtor.name)
        self.assertEqual("DE0987654321", transaction.debtor.iban)
        self.assertEqual("debintermediaryName", transaction.debtor.intermediaryName)

    @patch("dkb_robo.transaction.logger")
    def test_028_peer_information(self, mock_logger):

        self.amount_data = {"value": 100, "currencyCode": "USD"}
        self.creditor_data = {
            "creditorAccount": {
                "iban": "DE1234567890",
                "bic": "BICCODE",
                "id": "creditor_id",
                "name": "Creditor Name",
            },
            "agent": {"bic": "BICCODE"},
            "id": "creditor_id",
            "name": "Creditor Name",
        }
        self.debtor_data = {
            "debtorAccount": {
                "iban": "DE0987654321",
                "bic": "BICCODE1",
                "id": "debtor_id",
                "name": "Debtor Name",
            },
            "agent": {"bic": "BICCODE1"},
            "id": "debtor_id",
            "name": "Debtor Name",
            "intermediaryName": "debintermediaryName",
        }
        self.transaction_data1 = {
            "amount": self.amount_data,
            "creditor": self.creditor_data,
            "debtor": self.debtor_data,
            "description": "Payment for services",
        }
        result = {
            "debtorAccount": {
                "iban": "DE0987654321",
                "bic": "BICCODE1",
                "id": "debtor_id",
                "name": "Debtor Name",
                "intermediaryName": "debintermediaryName",
            },
            "agent": {"bic": "BICCODE1"},
            "id": None,
            "bic": None,
            "name": None,
            "intermediaryName": "debintermediaryName",
        }
        transaction = AccountTransactionItem(
            **self.transaction_data1
        )._peer_information(peer_dic={"debtor": self.debtor_data}, peer_type="debtor")
        self.assertEqual(result, transaction)

    @patch("dkb_robo.transaction.logger")
    def test_029_format(self, mock_logger):
        transaction = AccountTransactionItem(**self.transaction_data)
        formatted_transaction = transaction.format()

        expected_transaction = {
            "amount": 100,
            "currencycode": "USD",
            "date": "2022-01-15",
            "bdate": "2022-01-15",
            "vdate": "2022-01-16",
            "customerreference": "endToEnd123",
            "mandatereference": "mandate123",
            "postingtext": "credit",
            "reasonforpayment": "Payment for services",
            "peeraccount": "DE0987654321",
            "peerbic": "BICCODE1",
            "peerid": "debtor_id",
            "peer": "debintermediaryName",
            "text": "credit debintermediaryName Payment for services",
        }
        self.assertEqual(expected_transaction, formatted_transaction)

    @patch("dkb_robo.transaction.logger")
    def test_030_format(self, mock_logger):
        self.transaction_data["debtor"]["debtorAccount"]["intermediaryName"] = None
        transaction = AccountTransactionItem(**self.transaction_data)
        formatted_transaction = transaction.format()

        expected_transaction = {
            "amount": 100,
            "currencycode": "USD",
            "date": "2022-01-15",
            "bdate": "2022-01-15",
            "vdate": "2022-01-16",
            "customerreference": "endToEnd123",
            "mandatereference": "mandate123",
            "postingtext": "credit",
            "reasonforpayment": "Payment for services",
            "peeraccount": "DE0987654321",
            "peerbic": "BICCODE1",
            "peerid": "debtor_id",
            "peer": "Debtor Name",
            "text": "credit Debtor Name Payment for services",
        }
        self.assertEqual(expected_transaction, formatted_transaction)

    @patch("dkb_robo.transaction.logger")
    def test_031_format(self, mock_logger):
        self.transaction_data["amount"] = {"value": -100, "currencyCode": "EUR"}
        transaction = AccountTransactionItem(**self.transaction_data)
        formatted_transaction = transaction.format()

        expected_transaction = {
            "amount": -100,
            "currencycode": "EUR",
            "date": "2022-01-15",
            "bdate": "2022-01-15",
            "vdate": "2022-01-16",
            "customerreference": "endToEnd123",
            "mandatereference": "mandate123",
            "postingtext": "credit",
            "reasonforpayment": "Payment for services",
            "peeraccount": "DE1234567890",
            "peerbic": "BICCODE",
            "peerid": "creditor_id",
            "peer": "credintermediaryName",
            "text": "credit credintermediaryName Payment for services",
        }
        self.assertEqual(expected_transaction, formatted_transaction)

    @patch("dkb_robo.transaction.logger")
    def test_032_format(self, mock_logger):
        self.transaction_data["amount"] = {"value": -100, "currencyCode": "EUR"}
        self.transaction_data["creditor"]["creditorAccount"]["intermediaryName"] = None

        transaction = AccountTransactionItem(**self.transaction_data)
        formatted_transaction = transaction.format()

        expected_transaction = {
            "amount": -100,
            "currencycode": "EUR",
            "date": "2022-01-15",
            "bdate": "2022-01-15",
            "vdate": "2022-01-16",
            "customerreference": "endToEnd123",
            "mandatereference": "mandate123",
            "postingtext": "credit",
            "reasonforpayment": "Payment for services",
            "peeraccount": "DE1234567890",
            "peerbic": "BICCODE",
            "peerid": "creditor_id",
            "peer": "Creditor Name",
            "text": "credit Creditor Name Payment for services",
        }
        self.assertEqual(expected_transaction, formatted_transaction)

    @patch("dkb_robo.transaction.logger")
    def test_033_format(self, mock_logger):
        """do not use intermediaryName name for via debit"""
        self.transaction_data["amount"] = {"value": -100, "currencyCode": "EUR"}
        self.transaction_data["description"] = "VISA Debitkartenumsatz"
        transaction = AccountTransactionItem(**self.transaction_data)
        formatted_transaction = transaction.format()

        expected_transaction = {
            "amount": -100.0,
            "currencycode": "EUR",
            "date": "2022-01-15",
            "bdate": "2022-01-15",
            "vdate": "2022-01-16",
            "customerreference": "endToEnd123",
            "mandatereference": "mandate123",
            "postingtext": "credit",
            "reasonforpayment": "VISA Debitkartenumsatz",
            "peeraccount": "DE1234567890",
            "peerbic": "BICCODE",
            "peerid": "creditor_id",
            "peer": "Creditor Name",
            "text": "credit Creditor Name VISA Debitkartenumsatz",
        }
        self.assertEqual(expected_transaction, formatted_transaction)


class TestCreditCardTransactionItem(unittest.TestCase):
    def setUp(self):
        self.amount_data = {"value": 100, "currencyCode": "USD"}
        self.merchant_amount_data = {"value": 90, "currencyCode": "USD"}
        self.merchant_category_data = {"code": "1234"}
        self.transaction_data = {
            "amount": self.amount_data,
            "id": "trans123",
            "authorizationDate": "2022-01-15",
            "bonuses": [],
            "bookingDate": "2022-01-16",
            "cardId": "card123",
            "description": "Payment at merchant",
            "merchantAmount": self.merchant_amount_data,
            "merchantCategory": self.merchant_category_data,
            "status": "completed",
            "transactionType": "purchase",
        }

    @patch("dkb_robo.transaction.Amount", autospec=True)
    @patch(
        "dkb_robo.transaction.CreditCardTransactionItem.MerchantCategory", autospec=True
    )
    def test_033_post_init(self, MockMerchantCategory, MockAmount):
        MockAmount.side_effect = [MagicMock(), MagicMock()]
        MockMerchantCategory.return_value = MagicMock()

        transaction = CreditCardTransactionItem(**self.transaction_data)

        MockAmount.assert_any_call(**self.amount_data)
        MockAmount.assert_any_call(**self.merchant_amount_data)
        MockMerchantCategory.assert_called_once_with(**self.merchant_category_data)

    def test_034_post_init(self):

        transaction = CreditCardTransactionItem(**self.transaction_data)

        self.assertEqual(transaction.amount.value, 100)
        self.assertEqual(transaction.amount.currencyCode, "USD")
        self.assertEqual(transaction.id, "trans123")
        self.assertEqual(transaction.authorizationDate, "2022-01-15")
        self.assertEqual(transaction.bookingDate, "2022-01-16")
        self.assertEqual(transaction.cardId, "card123")
        self.assertEqual(transaction.description, "Payment at merchant")
        self.assertEqual(transaction.merchantAmount.value, 90)
        self.assertEqual(transaction.merchantAmount.currencyCode, "USD")
        self.assertEqual(transaction.merchantCategory.code, "1234")
        self.assertEqual(transaction.status, "completed")

    @patch("dkb_robo.transaction.logger")
    def test_035_format(self, mock_logger):
        transaction = CreditCardTransactionItem(**self.transaction_data)
        formatted_transaction = transaction.format()

        expected_transaction = {
            "amount": 100,
            "bdate": "2022-01-16",
            "currencycode": "USD",
            "text": "Payment at merchant",
            "vdate": "2022-01-15",
        }

        self.assertEqual(formatted_transaction, expected_transaction)


class TestDepotTransactionItem(unittest.TestCase):
    def setUp(self):
        self.quantity_data = {"unit": "shares", "value": 100}
        self.custody_data = {
            "block": {"blockType": "type1"},
            "certificateType": "certType",
            "characteristic": {"characteristicType": "charType"},
            "custodyType": "custType",
            "custodyTypeId": "custTypeId",
        }
        self.instrument_data = {
            "id": "instr123",
            "identifiers": [{"identifier": "ISIN", "value": "US1234567890"}],
            "name": {"long": "Long Name", "short": "Short Name"},
            "unit": "unit1",
        }
        self.performance_data = {
            "currentValue": {"value": 150.0, "currencyCode": "EUR"},
            "isOutdated": False,
        }
        self.quote_data = {
            "id": "quote123",
            "market": "market1",
            "price": {"value": 150.0, "currencyCode": "EUR"},
            "timestamp": "2022-01-15",
        }
        self.transaction_data = {
            "id": "trans123",
            "availableQuantity": self.quantity_data,
            "custody": self.custody_data,
            "instrument": self.instrument_data,
            "lastOrderDate": "2022-01-15",
            "performance": self.performance_data,
            "quantity": self.quantity_data,
            "quote": self.quote_data,
        }

    @patch("dkb_robo.transaction.PerformanceValue", autospec=True)
    @patch("dkb_robo.transaction.DepotTransactionItem.Quantity", autospec=True)
    @patch("dkb_robo.transaction.DepotTransactionItem.Custody", autospec=True)
    @patch("dkb_robo.transaction.DepotTransactionItem.Instrument", autospec=True)
    @patch("dkb_robo.transaction.DepotTransactionItem.Performance", autospec=True)
    @patch("dkb_robo.transaction.DepotTransactionItem.Quote", autospec=True)
    def test_036_post_init(
        self,
        MockQuote,
        MockPerformance,
        MockInstrument,
        MockCustody,
        MockQuantity,
        MockPerformanceValue,
    ):
        MockQuantity.side_effect = [MagicMock(), MagicMock()]
        MockCustody.return_value = MagicMock()
        MockInstrument.return_value = MagicMock()
        MockPerformance.return_value = MagicMock()
        MockQuote.return_value = MagicMock()

        transaction = DepotTransactionItem(**self.transaction_data)

        MockQuantity.assert_any_call(**self.quantity_data)
        MockCustody.assert_called_once_with(**self.custody_data)
        MockInstrument.assert_called_once_with(**self.instrument_data)
        MockPerformance.assert_called_once_with(**self.performance_data)
        MockQuote.assert_called_once_with(**self.quote_data)

    def test_037_post_init(self):
        transaction = DepotTransactionItem(**self.transaction_data)
        self.assertEqual(transaction.id, "trans123")
        self.assertEqual(transaction.availableQuantity.unit, "shares")
        self.assertEqual(transaction.availableQuantity.value, 100)
        self.assertEqual(transaction.custody.block.blockType, "type1")
        self.assertEqual(transaction.custody.certificateType, "certType")
        self.assertEqual(
            transaction.custody.characteristic.characteristicType, "charType"
        )
        self.assertEqual(transaction.custody.custodyType, "custType")
        self.assertEqual(transaction.custody.custodyTypeId, "custTypeId")
        self.assertEqual(transaction.instrument.id, "instr123")
        self.assertEqual(transaction.instrument.identifiers[0].identifier, "ISIN")
        self.assertEqual(transaction.instrument.identifiers[0].value, "US1234567890")
        self.assertEqual(transaction.instrument.name.long, "Long Name")
        self.assertEqual(transaction.instrument.name.short, "Short Name")
        self.assertEqual(transaction.instrument.unit, "unit1")
        self.assertEqual(transaction.lastOrderDate, "2022-01-15")
        self.assertEqual(transaction.performance.currentValue.value, 150.0)
        self.assertEqual(transaction.performance.currentValue.currencyCode, "EUR")
        self.assertEqual(transaction.performance.isOutdated, False)
        self.assertEqual(transaction.quantity.unit, "shares")
        self.assertEqual(transaction.quantity.value, 100)
        self.assertEqual(transaction.quote.id, "quote123")
        self.assertEqual(transaction.quote.market, "market1")
        self.assertEqual(transaction.quote.price.value, 150.0)
        self.assertEqual(transaction.quote.price.currencyCode, "EUR")
        self.assertEqual(transaction.quote.timestamp, "2022-01-15")

    @patch("dkb_robo.transaction.logger")
    def test_038_format(self, mock_logger):
        transaction = DepotTransactionItem(**self.transaction_data)
        formatted_transaction = transaction.format()

        expected_transaction = {
            "isin_wkn": "US1234567890",
            "lastorderdate": "2022-01-15",
            "price_euro": 150.0,
            "quantity": 100.0,
            "shares": 100.0,
            "shares_unit": "shares",
            "text": "Short Name",
            "text_long": "Long Name",
            "currencyCode": "EUR",
            "market": "market1",
            "price": 150.0,
        }

        self.assertEqual(formatted_transaction, expected_transaction)

    @patch("dkb_robo.transaction.logger")
    def test_039_format(self, mock_logger):
        self.transaction_data["availableQuantity"]["value"] = "aa"
        transaction = DepotTransactionItem(**self.transaction_data)
        formatted_transaction = transaction.format()

        expected_transaction = {
            "isin_wkn": "US1234567890",
            "lastorderdate": "2022-01-15",
            "price_euro": 150.0,
            "quantity": None,
            "shares": None,
            "shares_unit": "shares",
            "text": "Short Name",
            "text_long": "Long Name",
            "currencyCode": "EUR",
            "market": "market1",
            "price": 150.0,
        }
        self.assertEqual(formatted_transaction, expected_transaction)


if __name__ == "__main__":

    unittest.main()
