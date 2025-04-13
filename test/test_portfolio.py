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
from dkb_robo.portfolio import (
    ProductGroup,
    AccountItem,
    CardItem,
    DepotItem,
    Overview,
    Amount,
    CardItem,
    Person,
    DepotItem,
)


def json_load(fname):
    """simple json load"""

    with open(fname, "r", encoding="utf8") as myfile:
        data_dic = json.load(myfile)

    return data_dic


class TestProductGroup(unittest.TestCase):
    """test class"""

    def setUp(self):
        """setup"""
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.productgroup = ProductGroup()

    def test_001__uid2names(self):
        """test uid2names one item"""
        data_ele = {
            "attributes": {"productSettings": {"product": {"uid": {"name": "name"}}}}
        }
        self.assertEqual({"uid": "name"}, self.productgroup._uid2names(data_ele))

    def test_002__uid2names(self):
        """test uid2names two items"""
        data_ele = {
            "attributes": {
                "productSettings": {
                    "product1": {"uid1": {"name": "name1"}},
                    "product2": {"uid2": {"name": "name2"}},
                }
            }
        }
        self.assertEqual(
            {"uid1": "name1", "uid2": "name2"}, self.productgroup._uid2names(data_ele)
        )

    def test_003__uid2names(self):
        """test uid2names malformed input"""
        data_ele = {"attributes": {"foo": "bar"}}
        self.assertFalse({}, self.productgroup._uid2names(data_ele))

    def test_004__uid2names(self):
        """test uid2names malformed input"""
        data_ele = {"attributes": {"productSettings": {"foo": "bar"}}}
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertFalse({}, self.productgroup._uid2names(data_ele))
        self.assertIn(
            "WARNING:dkb_robo.portfolio:uid2name mapping failed. product data are not in dictionary format",
            lcm.output,
        )

    def test_005__uid2names(self):
        """test uid2names malformed input"""
        data_ele = {"foo": "bar"}
        self.assertFalse({}, self.productgroup._uid2names(data_ele))

    def test_006__group(self):
        """test _group() malformed input"""
        data_ele = {}
        self.assertFalse(self.productgroup._group(data_ele))

    def test_007__group(self):
        """test _group()"""
        data_ele = {
            "attributes": {
                "productGroups": {
                    "foo": {
                        "index": 0,
                        "name": "foo",
                        "products": {
                            "product1": {"uid1": {"index": 1}, "uid2": {"index": 0}}
                        },
                    }
                }
            }
        }
        self.assertEqual(
            [{"name": "foo", "product_list": {1: "uid1", 0: "uid2"}}],
            self.productgroup._group(data_ele),
        )

    def test_008__group(self):
        """test _group()"""
        data_ele = {
            "attributes": {
                "productGroups": {
                    "foo": {
                        "index": 0,
                        "name": "foo",
                        "products": {
                            "product1": {"uid1": {"index": 1}, "uid2": {"index": 2}},
                            "product2": {"uid3": {"index": 0}, "uid4": {"index": 3}},
                        },
                    }
                }
            }
        }
        self.assertEqual(
            [
                {
                    "name": "foo",
                    "product_list": {0: "uid3", 1: "uid1", 2: "uid2", 3: "uid4"},
                }
            ],
            self.productgroup._group(data_ele),
        )

    def test_009__group(self):
        """test _group()"""
        data_ele = {
            "attributes": {
                "productGroups": {
                    "foo": {
                        "index": 1,
                        "name": "foo",
                        "products": {
                            "product1": {"uid1": {"index": 1}, "uid2": {"index": 2}},
                            "product2": {"uid3": {"index": 0}, "uid4": {"index": 3}},
                        },
                    },
                    "bar": {
                        "index": 0,
                        "name": "bar",
                        "products": {
                            "product1": {"uid4": {"index": 1}, "uid5": {"index": 2}},
                            "product2": {"uid6": {"index": 0}, "uid7": {"index": 3}},
                        },
                    },
                }
            }
        }
        result = [
            {
                "name": "bar",
                "product_list": {1: "uid4", 2: "uid5", 0: "uid6", 3: "uid7"},
            },
            {
                "name": "foo",
                "product_list": {1: "uid1", 2: "uid2", 0: "uid3", 3: "uid4"},
            },
        ]
        self.assertEqual(result, self.productgroup._group(data_ele))

    @patch("dkb_robo.portfolio.ProductGroup._group")
    @patch("dkb_robo.portfolio.ProductGroup._uid2names")
    def test_010_map(self, mock_uid2names, mock_group):
        """test map()"""
        data = {"data": {"foo": "bar"}}
        mock_uid2names.return_value = "mock_uid2names"
        mock_group.return_value = "mock_group"
        self.assertEqual(("mock_uid2names", "mock_group"), self.productgroup.map(data))
        self.assertTrue(mock_uid2names.called)
        self.assertTrue(mock_group.called)


class TestOverview(unittest.TestCase):
    """test class"""

    @patch("requests.Session")
    def setUp(self, mock_session):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.overview = Overview(client=mock_session)
        self.maxDiff = None

    def test_011__fetch(self):
        """test _fetch()"""
        self.overview.client = Mock()
        self.overview.client.get.return_value.status_code = 200
        self.overview.client.get.return_value.json.return_value = {"foo": "bar"}
        self.assertEqual({"foo": "bar"}, self.overview._fetch("url"))
        self.assertTrue(self.overview.client.get.called)

    def test_012__fetch(self):
        """test _fetch()"""
        self.overview.client = Mock()
        self.overview.client.get.return_value.status_code = 400
        self.overview.client.get.return_value.json.return_value = {"foo": "bar"}
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertFalse(self.overview._fetch("url"))
        self.assertIn(
            "ERROR:dkb_robo.portfolio:fetch url: RC is not 200 but 400", lcm.output
        )
        self.assertTrue(self.overview.client.get.called)

    @patch("dkb_robo.portfolio.Overview._sort")
    @patch("dkb_robo.portfolio.Overview._fetch")
    def test_013_get(self, mock_fetch, mock_sort):
        """test get()"""
        mock_fetch.return_value = {"data": "data"}
        mock_sort.return_value = "mock_sort"
        self.assertEqual("mock_sort", self.overview.get())
        self.assertTrue(mock_fetch.called)
        self.assertTrue(mock_sort.called)

    @patch("dkb_robo.portfolio.Overview._sort")
    @patch("dkb_robo.portfolio.Overview._fetch")
    def test_014_get(self, mock_fetch, mock_sort):
        """test get()"""
        mock_fetch.return_value = None
        mock_sort.return_value = "mock_sort"
        self.assertEqual("mock_sort", self.overview.get())
        self.assertTrue(mock_fetch.called)
        self.assertTrue(mock_sort.called)

    @patch("dkb_robo.portfolio.AccountItem", autospec=True)
    @patch("dkb_robo.portfolio.CardItem", autospec=True)
    @patch("dkb_robo.portfolio.DepotItem", autospec=True)
    def test_015_itemize(self, mock_depot, mock_card, mock_account):
        """test _itemize() formatted"""
        portfolio_dic = {
            "accounts": {"data": [{"id": "acc1", "attributes": {"amount": 100}}]},
            "cards": {"data": [{"id": "card1", "attributes": {"limit": 500}}]},
            "depots": {"data": [{"id": "depot1", "attributes": {"value": 1000}}]},
        }

        mock_account.return_value.format.return_value = "formatted_account"
        mock_card.return_value.format.return_value = "formatted_card"
        mock_depot.return_value.format.return_value = "formatted_depot"

        result = self.overview._itemize(portfolio_dic)

        self.assertEqual(
            result,
            {
                "acc1": "formatted_account",
                "card1": "formatted_card",
                "depot1": "formatted_depot",
            },
        )

    @patch("dkb_robo.portfolio.AccountItem", autospec=True)
    @patch("dkb_robo.portfolio.CardItem", autospec=True)
    @patch("dkb_robo.portfolio.DepotItem", autospec=True)
    def test_016_itemize(self, mock_depot, mock_card, mock_account):
        """test _itemize() unfiltered"""
        portfolio_dic = {
            "accounts": {"data": [{"id": "acc1", "attributes": {"amount": 100}}]},
            "cards": {"data": [{"id": "card1", "attributes": {"limit": 500}}]},
            "depots": {"data": [{"id": "depot1", "attributes": {"value": 1000}}]},
        }

        mock_account.return_value = "unfiltered_account"
        mock_card.return_value = "unfiltered_card"
        mock_depot.return_value = "unfiltered_depot"
        self.overview.unfiltered = True
        result = self.overview._itemize(portfolio_dic)

        self.assertEqual(
            result,
            {
                "acc1": "unfiltered_account",
                "card1": "unfiltered_card",
                "depot1": "unfiltered_depot",
            },
        )

    @patch("dkb_robo.portfolio.ProductGroup", autospec=True)
    @patch("dkb_robo.portfolio.Overview._itemize", autospec=True)
    @patch("dkb_robo.portfolio.Overview._add_remaining", autospec=True)
    def test_017_sort(self, mock_add, mock_itemize, mock_pgrp):
        """test _sort() formatted"""
        portfolio_dic = {
            "product_display": {"data": [{"id": "display1"}]},
            "accounts": {"data": [{"id": "acc1", "attributes": {"amount": 100}}]},
            "cards": {"data": [{"id": "card1", "attributes": {"limit": 500}}]},
            "depots": {"data": [{"id": "depot1", "attributes": {"value": 1000}}]},
        }

        mock_itemize.return_value = {
            "acc1": {"amount": 100},
            "card1": {"limit": 500},
            "depot1": {"value": 1000},
        }

        mock_product_group = MagicMock()
        mock_product_group.map.return_value = (
            {"acc1": "Account"},
            [{"name": "Group1", "product_list": {"acc1": "acc1"}}],
        )
        mock_pgrp.return_value = mock_product_group

        mock_add.return_value = {0: {"amount": 100, "productgroup": "Group1"}}

        result = self.overview._sort(portfolio_dic)

        self.assertEqual(result, {0: {"amount": 100, "productgroup": "Group1"}})

    @patch("dkb_robo.portfolio.ProductGroup", autospec=True)
    @patch("dkb_robo.portfolio.Overview._itemize", autospec=True)
    @patch("dkb_robo.portfolio.Overview._add_remaining", autospec=True)
    def test_018_sort(self, mock_add, mock_itemize, mock_pgrp):
        """test _sort() unfiltered"""
        portfolio_dic = {
            "product_display": {"data": [{"id": "display1"}]},
            "accounts": {"data": [{"id": "acc1", "attributes": {"amount": 100}}]},
            "cards": {"data": [{"id": "card1", "attributes": {"limit": 500}}]},
            "depots": {"data": [{"id": "depot1", "attributes": {"value": 1000}}]},
        }

        mock_itemize.return_value = {
            "acc1": MagicMock(),
            "card1": MagicMock(),
            "depot1": MagicMock(),
        }

        mock_product_group = MagicMock()
        mock_product_group.map.return_value = (
            {"acc1": "Account"},
            [{"name": "Group1", "product_list": {"acc1": "acc1"}}],
        )
        mock_pgrp.return_value = mock_product_group

        mock_add.return_value = {0: {"amount": 100, "productgroup": "Group1"}}

        self.overview.unfiltered = True
        result = self.overview._sort(portfolio_dic)

        self.assertEqual(result, {0: {"amount": 100, "productgroup": "Group1"}})

    def test_019_add_remaining(self):
        """test _add_remaining() formatted"""
        data_dic = {
            "product1": {"name": "Product 1"},
            "product2": {"name": "Product 2"},
        }
        account_dic = {}
        account_cnt = 0

        result = self.overview._add_remaining(data_dic, account_dic, account_cnt)

        expected_result = {
            0: {"name": "Product 1", "productgroup": None},
            1: {"name": "Product 2", "productgroup": None},
        }

        self.assertEqual(result, expected_result)

    def test_020_add_remaining(self):
        """test _add_remaining() unfiltered"""
        self.overview.unfiltered = True
        data_dic = {"product1": MagicMock(), "product2": MagicMock()}
        account_dic = {}
        account_cnt = 0

        result = self.overview._add_remaining(data_dic, account_dic, account_cnt)

        data_dic["product1"].productGroup = None
        data_dic["product2"].productGroup = None

        expected_result = {0: data_dic["product1"], 1: data_dic["product2"]}

        self.assertEqual(result, expected_result)

    @patch("dkb_robo.portfolio.Overview._fetch")
    def test_021_get(self, mock_fetch):
        """test get() e2e"""
        pd_dic = json_load(self.dir_path + "/mocks/pd.json")
        account_dic = json_load(self.dir_path + "/mocks/accounts.json")
        card_dic = json_load(self.dir_path + "/mocks/cards.json")
        depot_dic = json_load(self.dir_path + "/mocks/brokerage.json")
        mock_fetch.side_effect = [
            pd_dic,
            account_dic,
            card_dic,
            depot_dic,
            {"foo": "bar"},
        ]

        result = {
            0: {
                "account": "987654321",
                "amount": 1234.56,
                "currencyCode": "EUR",
                "holderName": "HolderName1",
                "id": "baccountid1",
                "name": "pdsettings brokeraage baccountid1",
                "productgroup": "productGroup name 1",
                "transactions": "https://banking.dkb.de/api/broker/brokerage-accounts/baccountid1/positions?include=instrument%2Cquote",
                "type": "depot",
            },
            1: {
                "account": "AccountIBAN3",
                "amount": -1000.22,
                "currencyCode": "EUR",
                "date": "2020-03-01",
                "holderName": "Account HolderName 3",
                "iban": "AccountIBAN3",
                "id": "accountid3",
                "limit": 2500.0,
                "name": "pdsettings accoutname accountid3",
                "productgroup": "productGroup name 1",
                "transactions": "https://banking.dkb.de/api/accounts/accounts/accountid3/transactions",
                "type": "account",
            },
            2: {
                "account": "maskedPan1",
                "amount": -1234.56,
                "currencycode": "EUR",
                "date": "2020-01-03",
                "expirydate": "2020-01-02",
                "holdername:": "holderfirstName holderlastName",
                "id": "cardid1",
                "limit": 1000.0,
                "maskedpan": "maskedPan1",
                "name": "pdsettings cardname cardid1",
                "productgroup": "productGroup name 1",
                "status": {
                    "category": "active",
                    "final": None,
                    "limitationsFor": [],
                    "reason": None,
                    "since": None,
                },
                "transactions": "https://banking.dkb.de/api/card-transactions/creditcard-transactions?cardId=cardid1",
                "type": "creditcard",
            },
            3: {
                "account": "maskedPan2",
                "amount": 12345.67,
                "currencycode": "EUR",
                "date": "2020-02-07",
                "expirydate": "2020-02-02",
                "holdername:": "holderfirstName2 holderlastName2",
                "id": "cardid2",
                "limit": 0.0,
                "maskedpan": "maskedPan2",
                "name": "displayName2",
                "productgroup": "productGroup name 1",
                "status": {
                    "category": "active",
                    "final": None,
                    "limitationsFor": [],
                    "reason": None,
                    "since": None,
                },
                "transactions": "https://banking.dkb.de/api/card-transactions/creditcard-transactions?cardId=cardid2",
                "type": "creditcard",
            },
            4: {
                "account": "AccountIBAN2",
                "amount": 1284.56,
                "currencyCode": "EUR",
                "date": "2020-02-01",
                "holderName": "Account HolderName 2",
                "iban": "AccountIBAN2",
                "id": "accountid2",
                "limit": 0.0,
                "name": "pdsettings accoutname accountid2",
                "productgroup": "productGroup name 2",
                "transactions": "https://banking.dkb.de/api/accounts/accounts/accountid2/transactions",
                "type": "account",
            },
            5: {
                "account": "AccountIBAN1",
                "amount": 12345.67,
                "currencyCode": "EUR",
                "date": "2020-01-01",
                "holderName": "Account HolderName 1",
                "iban": "AccountIBAN1",
                "id": "accountid1",
                "limit": 1000.0,
                "name": "Account DisplayName 1",
                "productgroup": None,
                "transactions": "https://banking.dkb.de/api/accounts/accounts/accountid1/transactions",
                "type": "account",
            },
            6: {
                "account": "maskedPan3",
                "expirydate": "2020-04-04",
                "holdername:": "holderfirstName3 holderlastName3",
                "id": "cardid3",
                "limit": None,
                "maskedpan": "maskedPan3",
                "name": "Visa Debitkarte",
                "productgroup": None,
                "status": {
                    "category": "blocked",
                    "final": True,
                    "limitationsFor": None,
                    "reason": "cancellation-of-product-by-customer",
                    "since": "2020-03-01",
                },
                "transactions": None,
                "type": "debitcard",
            },
            7: {
                "account": "maskedPan4",
                "expirydate": "2020-04-03",
                "holdername:": "holderfirstName4 holderlastName4",
                "id": "cardid4",
                "limit": None,
                "maskedpan": "maskedPan4",
                "name": "Visa Debitkarte",
                "productgroup": None,
                "status": {
                    "category": "active",
                    "final": None,
                    "limitationsFor": None,
                    "reason": None,
                    "since": None,
                },
                "transactions": None,
                "type": "debitcard",
            },
        }

        self.assertEqual(result, self.overview.get())


class TestAccountItem(unittest.TestCase):
    """test class"""

    def setUp(self):
        """setup"""
        self.amount_data = {"value": 1000, "currencyCode": "USD"}
        self.interests_data = [
            {
                "details": [
                    {
                        "condition": {
                            "currency": "USD",
                            "maximumAmount": 5000,
                            "minimumAmount": 1000,
                        },
                        "interestRate": 1.5,
                    }
                ],
                "method": "simple",
                "type": "savings",
            }
        ]
        self.product_data = {
            "id": "prod123",
            "type": "savings",
            "displayName": "Savings Account",
        }
        self.account_data = {
            "availableBalance": self.amount_data,
            "balance": self.amount_data,
            "currencyCode": "USD",
            "displayName": "My Account",
            "holderName": "John Doe",
            "id": "acc123",
            "iban": "DE1234567890",
            "interestRate": {"value": 1.5, "currencyCode": "USD"},
            "interests": self.interests_data,
            "lastAccountStatementDate": "2022-01-01",
            "nearTimeBalance": self.amount_data,
            "openingDate": "2020-01-01",
            "overdraftLimit": 500.0,
            "permissions": ["view", "edit"],
            "product": self.product_data,
            "productGroup": "group1",
            "state": "active",
            "type": "checking",
            "unauthorizedOverdraftInterestRate": {"value": 2.5, "currencyCode": "USD"},
            "updatedAt": "2022-01-15",
        }

    def test_022_post_init(self):
        """test post init"""
        self.maxDiff = None
        account = AccountItem(**self.account_data)
        self.assertEqual(account.id, "acc123")
        self.assertEqual(account.displayName, "My Account")
        self.assertEqual(account.holderName, "John Doe")
        self.assertEqual(account.iban, "DE1234567890")
        self.assertEqual(account.currencyCode, "USD")
        self.assertEqual(account.type, "checking")
        self.assertEqual(account.state, "active")
        self.assertEqual(account.permissions, ["view", "edit"])
        self.assertEqual(account.productGroup, "group1")
        self.assertEqual(account.openingDate, "2020-01-01")
        self.assertEqual(account.lastAccountStatementDate, "2022-01-01")
        self.assertEqual(account.updatedAt, "2022-01-15")
        self.assertEqual(account.balance.value, 1000)
        self.assertEqual(account.balance.currencyCode, "USD")
        self.assertEqual(account.availableBalance.value, 1000)
        self.assertEqual(account.availableBalance.currencyCode, "USD")
        self.assertEqual(account.nearTimeBalance.value, 1000)
        self.assertEqual(account.nearTimeBalance.currencyCode, "USD")
        self.assertEqual(account.overdraftLimit, 500.0)
        self.assertEqual(account.interestRate["value"], 1.5)
        self.assertEqual(account.interestRate["currencyCode"], "USD")
        self.assertEqual(account.interests[0].type, "savings")
        self.assertEqual(account.interests[0].method, "simple")
        self.assertEqual(account.interests[0].details[0].condition.currency, "USD")
        self.assertEqual(account.interests[0].details[0].interestRate, 1.5)
        self.assertEqual(account.interests[0].details[0].condition.maximumAmount, 5000)
        self.assertEqual(account.interests[0].details[0].condition.minimumAmount, 1000)
        self.assertEqual(account.unauthorizedOverdraftInterestRate["value"], 2.5)
        self.assertEqual(account.product.id, "prod123")
        self.assertEqual(account.product.type, "savings")
        self.assertEqual(account.product.displayName, "Savings Account")

    def test_023_post_init(self):
        """test post init with invalid data"""
        self.maxDiff = None
        self.account_data["overdraftLimit"] = "aa"
        self.account_data["interests"][0]["details"][0]["condition"][
            "maximumAmount"
        ] = "aa"
        self.account_data["interests"][0]["details"][0]["condition"][
            "minimumAmount"
        ] = "aa"
        account = AccountItem(**self.account_data)
        self.assertEqual(account.id, "acc123")
        self.assertEqual(account.displayName, "My Account")
        self.assertEqual(account.holderName, "John Doe")
        self.assertEqual(account.iban, "DE1234567890")
        self.assertEqual(account.currencyCode, "USD")
        self.assertEqual(account.type, "checking")
        self.assertEqual(account.state, "active")
        self.assertEqual(account.permissions, ["view", "edit"])
        self.assertEqual(account.productGroup, "group1")
        self.assertEqual(account.openingDate, "2020-01-01")
        self.assertEqual(account.lastAccountStatementDate, "2022-01-01")
        self.assertEqual(account.updatedAt, "2022-01-15")
        self.assertEqual(account.balance.value, 1000)
        self.assertEqual(account.balance.currencyCode, "USD")
        self.assertEqual(account.availableBalance.value, 1000)
        self.assertEqual(account.availableBalance.currencyCode, "USD")
        self.assertEqual(account.nearTimeBalance.value, 1000)
        self.assertEqual(account.nearTimeBalance.currencyCode, "USD")
        self.assertEqual(account.overdraftLimit, None)
        self.assertEqual(account.interestRate["value"], 1.5)
        self.assertEqual(account.interestRate["currencyCode"], "USD")
        self.assertEqual(account.interests[0].type, "savings")
        self.assertEqual(account.interests[0].method, "simple")
        self.assertEqual(account.interests[0].details[0].condition.currency, "USD")
        self.assertEqual(account.interests[0].details[0].interestRate, 1.5)
        self.assertEqual(account.interests[0].details[0].condition.maximumAmount, None)
        self.assertEqual(account.interests[0].details[0].condition.minimumAmount, None)
        self.assertEqual(account.unauthorizedOverdraftInterestRate["value"], 2.5)
        self.assertEqual(account.product.id, "prod123")
        self.assertEqual(account.product.type, "savings")
        self.assertEqual(account.product.displayName, "Savings Account")

    def test_024_post_init(self):
        """test post init"""
        self.maxDiff = None
        self.account_data["nearTimeBalance"] = None
        account = AccountItem(**self.account_data)
        self.assertEqual(account.id, "acc123")
        self.assertEqual(account.displayName, "My Account")
        self.assertEqual(account.holderName, "John Doe")
        self.assertEqual(account.iban, "DE1234567890")
        self.assertEqual(account.currencyCode, "USD")
        self.assertEqual(account.type, "checking")
        self.assertEqual(account.state, "active")
        self.assertEqual(account.permissions, ["view", "edit"])
        self.assertEqual(account.productGroup, "group1")
        self.assertEqual(account.openingDate, "2020-01-01")
        self.assertEqual(account.lastAccountStatementDate, "2022-01-01")
        self.assertEqual(account.updatedAt, "2022-01-15")
        self.assertEqual(account.balance.value, 1000)
        self.assertEqual(account.balance.currencyCode, "USD")
        self.assertEqual(account.availableBalance.value, 1000)
        self.assertEqual(account.availableBalance.currencyCode, "USD")
        self.assertFalse(account.nearTimeBalance)
        self.assertEqual(account.overdraftLimit, 500.0)
        self.assertEqual(account.interestRate["value"], 1.5)
        self.assertEqual(account.interestRate["currencyCode"], "USD")
        self.assertEqual(account.interests[0].type, "savings")
        self.assertEqual(account.interests[0].method, "simple")
        self.assertEqual(account.interests[0].details[0].condition.currency, "USD")
        self.assertEqual(account.interests[0].details[0].interestRate, 1.5)
        self.assertEqual(account.interests[0].details[0].condition.maximumAmount, 5000)
        self.assertEqual(account.interests[0].details[0].condition.minimumAmount, 1000)
        self.assertEqual(account.unauthorizedOverdraftInterestRate["value"], 2.5)
        self.assertEqual(account.product.id, "prod123")
        self.assertEqual(account.product.type, "savings")
        self.assertEqual(account.product.displayName, "Savings Account")

    @patch("dkb_robo.portfolio.logger")
    def test_024_format(self, mock_logger):
        """test format()"""
        account = AccountItem(**self.account_data)
        formatted_account = account.format()

        expected_output = {
            "account": "DE1234567890",
            "amount": 1000,
            "currencyCode": "USD",
            "date": "2022-01-15",
            "holderName": "John Doe",
            "iban": "DE1234567890",
            "id": "acc123",
            "limit": 500.0,
            "name": "Savings Account",
            "transactions": "https://banking.dkb.de/api/accounts/accounts/acc123/transactions",
            "type": "checking",
        }
        self.assertEqual(formatted_account, expected_output)


class TestCardItem(unittest.TestCase):
    """test class"""

    def setUp(self):
        """setup"""
        self.maxDiff = None
        self.amount_data = {"value": 1000, "currencyCode": "USD"}
        self.person_data = {"firstName": "John", "lastName": "Doe"}
        self.limit_data = {
            "value": 5000,
            "currencyCode": "USD",
            "identifier": "limit1",
            "categories": [{"amount": self.amount_data, "name": "category1"}],
        }
        self.product_data = {
            "superProductId": "prod123",
            "displayName": "Credit Card",
            "institute": "Bank",
            "productType": "credit",
            "ownerType": "individual",
            "id": "prod123",
            "type": "creditCard",
        }
        self.status_data = {
            "category": "active",
            "since": "2022-01-01",
            "reason": "none",
            "final": True,
            "limitationsFor": [],
        }
        self.card_data = {
            "activationDate": "2022-01-01",
            "authorizedAmount": {"value": 1000, "currencyCode": "USD"},
            "availableLimit": {"value": 1000, "currencyCode": "USD"},
            "balance": self.amount_data,
            "billingDetails": {
                "days": [1, 15],
                "calendarType": "monthly",
                "cycle": "monthly",
            },
            "blockedSince": "2022-01-01",
            "creationDate": "2022-01-01",
            "engravedLine1": "John Doe",
            "engravedLine2": "Credit Card",
            "expiryDate": "2025-01-01",
            "failedPinAttempts": 0,
            "followUpCardId": "card123",
            "holder": {"person": self.person_data},
            "id": "card123",
            "limit": self.limit_data,
            "maskedPan": "1234********5678",
            "network": "Visa",
            "owner": self.person_data,
            "product": self.product_data,
            "referenceAccount": {"iban": "DE1234567890", "bic": "BICCODE"},
            "state": "active",
            "status": self.status_data,
            "type": "creditCard",
        }

    def test_025_post_init(self):
        """test post init"""
        card = CardItem(**self.card_data)
        self.assertEqual(card.id, "card123")
        self.assertEqual(card.activationDate, "2022-01-01")
        self.assertEqual(card.authorizedAmount.value, 1000)
        self.assertEqual(card.authorizedAmount.currencyCode, "USD")
        self.assertEqual(card.availableLimit.value, 1000)
        self.assertEqual(card.availableLimit.currencyCode, "USD")
        self.assertEqual(card.balance.value, 1000)
        self.assertEqual(card.balance.currencyCode, "USD")
        self.assertEqual(card.billingDetails.days, [1, 15])
        self.assertEqual(card.billingDetails.calendarType, "monthly")
        self.assertEqual(card.billingDetails.cycle, "monthly")
        self.assertEqual(card.blockedSince, "2022-01-01")
        self.assertEqual(card.creationDate, "2022-01-01")
        self.assertEqual(card.engravedLine1, "John Doe")
        self.assertEqual(card.engravedLine2, "Credit Card")
        self.assertEqual(card.expiryDate, "2025-01-01")
        self.assertEqual(card.failedPinAttempts, 0)
        self.assertEqual(card.followUpCardId, "card123")
        self.assertEqual(card.holder.person.firstName, "John")
        self.assertEqual(card.holder.person.lastName, "Doe")
        self.assertEqual(card.limit.value, 5000)
        self.assertEqual(card.limit.currencyCode, "USD")
        self.assertEqual(card.limit.identifier, "limit1")
        self.assertEqual(card.limit.categories[0].amount.value, 1000)
        self.assertEqual(card.limit.categories[0].amount.currencyCode, "USD")
        self.assertEqual(card.limit.categories[0].name, "category1")
        self.assertEqual(card.maskedPan, "1234********5678")
        self.assertEqual(card.network, "Visa")
        self.assertEqual(card.owner.firstName, "John")
        self.assertEqual(card.owner.lastName, "Doe")
        self.assertEqual(card.product.superProductId, "prod123")
        self.assertEqual(card.product.displayName, "Credit Card")
        self.assertEqual(card.product.institute, "Bank")
        self.assertEqual(card.product.productType, "credit")
        self.assertEqual(card.product.ownerType, "individual")
        self.assertEqual(card.product.id, "prod123")
        self.assertEqual(card.product.type, "creditCard")
        self.assertEqual(card.referenceAccount.iban, "DE1234567890")
        self.assertEqual(card.referenceAccount.bic, "BICCODE")
        self.assertEqual(card.state, "active")
        self.assertEqual(card.status.category, "active")
        self.assertEqual(card.status.since, "2022-01-01")
        self.assertEqual(card.status.reason, "none")
        self.assertEqual(card.status.final, True)
        self.assertEqual(card.status.limitationsFor, [])
        self.assertEqual(card.type, "creditCard")

    def test_026_post_init(self):
        """test post init with invalid data"""
        self.card_data["limit"]["value"] = "aa"
        self.card_data["limit"]["categories"][0]["amount"]["value"] = "aa"
        card = CardItem(**self.card_data)
        self.assertEqual(card.limit.value, None)
        self.assertEqual(card.availableLimit.value, 1000)
        self.assertEqual(card.authorizedAmount.value, 1000)
        self.assertEqual(card.limit.categories[0].amount.value, None)
        self.assertEqual(card.id, "card123")
        self.assertEqual(card.activationDate, "2022-01-01")
        self.assertEqual(card.authorizedAmount.currencyCode, "USD")
        self.assertEqual(card.availableLimit.currencyCode, "USD")
        # self.assertEqual(card.balance.value, 1000)
        self.assertEqual(card.balance.currencyCode, "USD")
        self.assertEqual(card.billingDetails.days, [1, 15])
        self.assertEqual(card.billingDetails.calendarType, "monthly")
        self.assertEqual(card.billingDetails.cycle, "monthly")
        self.assertEqual(card.blockedSince, "2022-01-01")
        self.assertEqual(card.creationDate, "2022-01-01")
        self.assertEqual(card.engravedLine1, "John Doe")
        self.assertEqual(card.engravedLine2, "Credit Card")
        self.assertEqual(card.expiryDate, "2025-01-01")
        self.assertEqual(card.failedPinAttempts, 0)
        self.assertEqual(card.followUpCardId, "card123")
        self.assertEqual(card.holder.person.firstName, "John")
        self.assertEqual(card.holder.person.lastName, "Doe")

        self.assertEqual(card.limit.currencyCode, "USD")
        self.assertEqual(card.limit.identifier, "limit1")
        self.assertEqual(card.limit.categories[0].amount.currencyCode, "USD")
        self.assertEqual(card.limit.categories[0].name, "category1")
        self.assertEqual(card.maskedPan, "1234********5678")
        self.assertEqual(card.network, "Visa")
        self.assertEqual(card.owner.firstName, "John")
        self.assertEqual(card.owner.lastName, "Doe")
        self.assertEqual(card.product.superProductId, "prod123")
        self.assertEqual(card.product.displayName, "Credit Card")
        self.assertEqual(card.product.institute, "Bank")
        self.assertEqual(card.product.productType, "credit")
        self.assertEqual(card.product.ownerType, "individual")
        self.assertEqual(card.product.id, "prod123")
        self.assertEqual(card.product.type, "creditCard")
        self.assertEqual(card.referenceAccount.iban, "DE1234567890")
        self.assertEqual(card.referenceAccount.bic, "BICCODE")
        self.assertEqual(card.state, "active")
        self.assertEqual(card.status.category, "active")
        self.assertEqual(card.status.since, "2022-01-01")
        self.assertEqual(card.status.reason, "none")
        self.assertEqual(card.status.final, True)
        self.assertEqual(card.status.limitationsFor, [])
        self.assertEqual(card.type, "creditCard")

    @patch("dkb_robo.portfolio.logger")
    def test_027_format(self, mock_logger):
        """test format() for creditcard"""
        card = CardItem(**self.card_data)
        formatted_card = card.format()

        expected_output = {
            "account": "1234********5678",
            "expirydate": "2025-01-01",
            "holdername:": "John Doe",
            "id": "card123",
            "name": "Credit Card",
            "limit": 5000,
            "maskedpan": "1234********5678",
            "status": {
                "category": "active",
                "since": "2022-01-01",
                "reason": "none",
                "final": True,
                "limitationsFor": [],
            },
            "type": "creditcard",
            "transactions": "https://banking.dkb.de/api/card-transactions/creditcard-transactions?cardId=card123",
            "amount": -1000,
            "currencycode": "USD",
            "date": None,  # Assuming balance.date is None
        }

        self.assertEqual(formatted_card, expected_output)

    @patch("dkb_robo.portfolio.logger")
    def test_028_format(self, mock_logger):
        """test format() for debitcard"""
        self.card_data["type"] = "debitCard"
        card = CardItem(**self.card_data)
        formatted_card = card.format()

        expected_output = {
            "account": "1234********5678",
            "expirydate": "2025-01-01",
            "holdername:": "John Doe",
            "id": "card123",
            "name": "Credit Card",
            "limit": 5000.0,
            "maskedpan": "1234********5678",
            "status": {
                "category": "active",
                "since": "2022-01-01",
                "reason": "none",
                "final": True,
                "limitationsFor": [],
            },
            "type": "debitcard",
            "transactions": None,
        }

        self.assertEqual(formatted_card, expected_output)


class TestDepotItem(unittest.TestCase):
    """test class"""

    def setUp(self):
        """setup"""
        self.amount_data = {"value": 1000, "currencyCode": "USD"}
        self.person_data = {"firstName": "John", "lastName": "Doe"}
        self.brokerage_account_performance_data = {
            "currentValue": self.amount_data,
            "averagePrice": self.amount_data,
            "overallAbsolute": self.amount_data,
            "overallRelative": "10%",
            "isOutdated": False,
        }
        self.reference_account_data = [
            {
                "internalReferenceAccounts": False,
                "accountType": "savings",
                "accountNumber": "123456",
                "bankCode": "BANK123",
                "holderName": "John Doe",
            }
        ]
        self.depot_data = {
            "brokerageAccountPerformance": self.brokerage_account_performance_data,
            "depositAccountId": "acc123",
            "holder": self.person_data,
            "holderName": "John Doe",
            "id": "depot123",
            "referenceAccounts": self.reference_account_data,
            "riskClasses": ["low", "medium"],
            "tradingEnabled": True,
            "type": "depot",
        }

    def test_029_post_init(self):
        """test post init"""
        depot = DepotItem(**self.depot_data)
        self.assertEqual(depot.id, "depot123")
        self.assertEqual(depot.depositAccountId, "acc123")
        self.assertEqual(depot.holder.firstName, "John")
        self.assertEqual(depot.holder.lastName, "Doe")
        self.assertEqual(depot.holderName, "John Doe")
        self.assertEqual(depot.type, "depot")
        self.assertEqual(depot.tradingEnabled, True)
        self.assertEqual(depot.brokerageAccountPerformance.currentValue.value, 1000)
        self.assertEqual(
            depot.brokerageAccountPerformance.currentValue.currencyCode, "USD"
        )
        self.assertEqual(depot.brokerageAccountPerformance.averagePrice.value, 1000)
        self.assertEqual(
            depot.brokerageAccountPerformance.averagePrice.currencyCode, "USD"
        )
        self.assertEqual(depot.brokerageAccountPerformance.overallAbsolute.value, 1000)
        self.assertEqual(
            depot.brokerageAccountPerformance.overallAbsolute.currencyCode, "USD"
        )
        self.assertEqual(depot.brokerageAccountPerformance.overallRelative, "10%")
        self.assertEqual(depot.brokerageAccountPerformance.isOutdated, False)
        self.assertEqual(depot.referenceAccounts[0].internalReferenceAccounts, False)
        self.assertEqual(depot.referenceAccounts[0].accountType, "savings")
        self.assertEqual(depot.referenceAccounts[0].accountNumber, "123456")
        self.assertEqual(depot.referenceAccounts[0].bankCode, "BANK123")
        self.assertEqual(depot.referenceAccounts[0].holderName, "John Doe")
        self.assertEqual(depot.riskClasses, ["low", "medium"])

    @patch("dkb_robo.portfolio.logger")
    def test_030_format(self, mock_logger):
        """test format()"""
        depot = DepotItem(**self.depot_data)
        formatted_depot = depot.format()

        expected_output = {
            "account": "acc123",
            "amount": 1000,
            "currencyCode": "USD",
            "holderName": "John Doe",
            "id": "depot123",
            "name": "John Doe",
            "type": "depot",
            "transactions": "https://banking.dkb.de/api/broker/brokerage-accounts/depot123/positions?include=instrument%2Cquote",
        }

        self.assertEqual(formatted_depot, expected_output)


if __name__ == "__main__":

    unittest.main()
