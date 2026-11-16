# -*- coding: utf-8 -*-
# pylint: disable=r0904, c0415, c0413, r0913, w0212
"""unittests for dkb_robo"""

import sys
import os
from datetime import date
import unittest
import logging
import json
import requests
from unittest.mock import patch, Mock, MagicMock, mock_open
import io

sys.path.insert(0, ".")
sys.path.insert(0, "..")
from dkb_robo.standingorder import StandingOrders


def json_load(fname):
    """simple json load"""

    with open(fname, "r", encoding="utf8") as myfile:
        data_dic = json.load(myfile)

    return data_dic


class TestDKBRobo(unittest.TestCase):
    """test class"""

    @patch("requests.Session")
    def setUp(self, mock_session):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger("dkb_robo")
        self.dkb = StandingOrders(client=mock_session)
        self.maxDiff = None

    @patch("dkb_robo.standingorder.StandingOrders._filter")
    def test_001_fetch(self, mock_filter):
        """test StandingOrders.fetch() without uid"""
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {"foo": "bar"}

        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb.fetch(None))
        self.assertEqual(
            "account-id is required to fetch standing orders", str(err.exception)
        )
        self.assertFalse(mock_filter.called)

    @patch("dkb_robo.standingorder.StandingOrders._filter")
    def test_002_fetch(self, mock_filter):
        """test StandingOrders.fetch() with uid but http error"""
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 400
        self.dkb.client.get.return_value.text = "bad request"
        self.dkb.client.get.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("400 Client Error")
        )
        with self.assertRaises(Exception) as err:
            self.assertFalse(self.dkb.fetch(uid="uid"))
        self.assertEqual(
            "fetch standing orders: http status code is 400; response=bad request",
            str(err.exception),
        )
        self.assertFalse(mock_filter.called)

    @patch("dkb_robo.standingorder.StandingOrders._filter")
    def test_003_fetch(self, mock_filter):
        """test StandingOrders.fetch() with uid no error"""
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {"foo": "bar"}
        mock_filter.return_value = "mock_filter"
        self.assertEqual("mock_filter", self.dkb.fetch(uid="uid"))
        self.assertTrue(mock_filter.called)
        self.dkb.client.get.assert_called_once_with(
            "https://banking.dkb.de/api/accounts/payments/recurring-credit-transfers",
            params={"accountId": "uid"},
            timeout=10.0,
        )

    @patch("dkb_robo.standingorder.StandingOrders._filter")
    def test_004_fetch_request_exception(self, mock_filter):
        """test StandingOrders.fetch() with request exception"""
        self.dkb.client = Mock()
        self.dkb.client.get.side_effect = requests.exceptions.Timeout("timeout")
        with self.assertRaises(Exception) as err:
            self.dkb.fetch(uid="uid")
        self.assertIn("fetch standing orders: request failed:", str(err.exception))
        self.assertFalse(mock_filter.called)

    @patch("dkb_robo.standingorder.StandingOrders._filter")
    def test_005_fetch_invalid_json(self, mock_filter):
        """test StandingOrders.fetch() with invalid json response"""
        self.dkb.client = Mock()
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.side_effect = ValueError("invalid json")
        with self.assertRaises(Exception) as err:
            self.dkb.fetch(uid="uid")
        self.assertEqual(
            "fetch standing orders: invalid json in response", str(err.exception)
        )
        self.assertFalse(mock_filter.called)

    @patch("dkb_robo.standingorder.StandingOrders._filter")
    def test_006_fetch_base_url_trailing_slash(self, mock_filter):
        """test StandingOrders.fetch() with trailing slash in base_url"""
        self.dkb = StandingOrders(client=Mock(), base_url="https://banking.dkb.de/api/")
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {"foo": "bar"}
        mock_filter.return_value = "mock_filter"

        self.assertEqual("mock_filter", self.dkb.fetch(uid="uid"))
        self.dkb.client.get.assert_called_once_with(
            "https://banking.dkb.de/api/accounts/payments/recurring-credit-transfers",
            params={"accountId": "uid"},
            timeout=10.0,
        )

    @patch("dkb_robo.standingorder.StandingOrders._filter")
    def test_007_fetch_custom_timeout(self, mock_filter):
        """test StandingOrders.fetch() with custom timeout"""
        self.dkb = StandingOrders(client=Mock(), timeout=3.5)
        self.dkb.client.get.return_value.status_code = 200
        self.dkb.client.get.return_value.json.return_value = {"foo": "bar"}
        mock_filter.return_value = "mock_filter"

        self.assertEqual("mock_filter", self.dkb.fetch(uid="uid"))
        self.dkb.client.get.assert_called_once_with(
            "https://banking.dkb.de/api/accounts/payments/recurring-credit-transfers",
            params={"accountId": "uid"},
            timeout=3.5,
        )

    def test_008__filter(self):
        """test StandingOrders._filter() with empty list"""
        full_list = {}
        self.assertFalse(self.dkb._filter(full_list))

    def test_009__filter(self):
        """test StandingOrders._filter() with list"""
        full_list = {
            "data": [
                {
                    "attributes": {
                        "description": "description",
                        "amount": {"currencyCode": "EUR", "value": "100.00"},
                        "creditor": {
                            "name": "cardname",
                            "creditorAccount": {"iban": "crediban", "bic": "credbic"},
                        },
                        "recurrence": {
                            "from": "2020-01-01",
                            "until": "2025-12-01",
                            "frequency": "monthly",
                            "nextExecutionAt": "2020-02-01",
                        },
                    }
                }
            ]
        }
        result = [
            {
                "amount": 100.0,
                "currencycode": "EUR",
                "purpose": "description",
                "recipient": "cardname",
                "creditoraccount": {"iban": "crediban", "bic": "credbic"},
                "interval": {
                    "from": "2020-01-01",
                    "until": "2025-12-01",
                    "frequency": "monthly",
                    "nextExecutionAt": "2020-02-01",
                    "holidayExecutionStrategy": None,
                },
            }
        ]
        self.assertEqual(result, self.dkb._filter(full_list))

    def test_010__filter(self):
        """test StandingOrders._filter() with list from file"""
        so_list = json_load(self.dir_path + "/mocks/so.json")
        self.dkb.unfiltered = False
        result = [
            {
                "amount": 100.0,
                "currencycode": "EUR",
                "purpose": "description1",
                "recipient": "name1",
                "creditoraccount": {"iban": "iban1", "bic": "bic1"},
                "interval": {
                    "from": "2022-01-01",
                    "until": "2025-12-01",
                    "frequency": "monthly",
                    "holidayExecutionStrategy": "following",
                    "nextExecutionAt": "2022-11-01",
                },
            },
            {
                "amount": 200.0,
                "currencycode": "EUR",
                "purpose": "description2",
                "recipient": "name2",
                "creditoraccount": {"iban": "iban2", "bic": "bic2"},
                "interval": {
                    "from": "2022-02-01",
                    "until": "2025-12-02",
                    "frequency": "monthly",
                    "holidayExecutionStrategy": "following",
                    "nextExecutionAt": "2022-11-02",
                },
            },
            {
                "amount": 300.0,
                "currencycode": "EUR",
                "purpose": "description3",
                "recipient": "name3",
                "creditoraccount": {"iban": "iban3", "bic": "bic3"},
                "interval": {
                    "from": "2022-03-01",
                    "until": "2025-03-01",
                    "frequency": "monthly",
                    "holidayExecutionStrategy": "following",
                    "nextExecutionAt": "2022-03-01",
                },
            },
        ]
        self.assertEqual(result, self.dkb._filter(so_list))

    def test_011__filter(self):
        """test StandingOrders._filter() with incomplete list/conversion error"""
        full_list = {
            "data": [
                {
                    "attributes": {
                        "description": "description",
                        "amount": {"value": "aa"},
                        "creditor": {
                            "name": "cardname",
                            "creditorAccount": {"iban": "crediban", "bic": "credbic"},
                        },
                        "recurrence": {
                            "from": "2020-01-01",
                            "until": "2025-12-01",
                            "frequency": "monthly",
                            "nextExecutionAt": "2020-02-01",
                        },
                    }
                }
            ]
        }
        result = [
            {
                "amount": None,
                "currencycode": None,
                "purpose": "description",
                "recipient": "cardname",
                "creditoraccount": {"iban": "crediban", "bic": "credbic"},
                "interval": {
                    "from": "2020-01-01",
                    "until": "2025-12-01",
                    "frequency": "monthly",
                    "nextExecutionAt": "2020-02-01",
                    "holidayExecutionStrategy": None,
                },
            }
        ]
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(result, self.dkb._filter(full_list))
        self.assertIn(
            "ERROR:dkb_robo.utilities:Account.__post_init: value conversion error:  could not convert string to float: 'aa'",
            lcm.output,
        )

    def test_012__filter(self):
        """test StandingOrders._filter() with incomplete list/conversion error"""
        full_list = {
            "data": [
                {
                    "attributes": {
                        "description": "description",
                        "amount": {"value": "100"},
                        "creditor": {
                            "name": "cardname",
                            "creditorAccount": {"iban": "crediban", "bic": "credbic"},
                        },
                        "recurrence": {
                            "from": "2020-01-01",
                            "until": "2025-12-01",
                            "frequency": "monthly",
                            "nextExecutionAt": "2020-02-01",
                        },
                    }
                }
            ]
        }
        self.dkb.unfiltered = True
        result = self.dkb._filter(full_list)
        self.assertEqual(100, result[0].amount.value)
        self.assertEqual("description", result[0].description)
        self.assertEqual("cardname", result[0].creditor.name)
        self.assertEqual("crediban", result[0].creditor.iban)
        self.assertEqual("credbic", result[0].creditor.bic)
        self.assertEqual("2020-01-01", result[0].recurrence.frm)
        self.assertEqual("monthly", result[0].recurrence.frequency)
        self.assertEqual("2025-12-01", result[0].recurrence.until)
        self.assertEqual("2020-02-01", result[0].recurrence.nextExecutionAt)
        self.assertIsNone(result[0].recurrence.holidayExecutionStrategy)

    def test_013__filter_missing_nested_fields(self):
        """test StandingOrders._filter() with missing nested fields"""
        full_list = {
            "data": [
                {
                    "attributes": {
                        "description": "description",
                        "amount": {"value": "100"},
                    }
                }
            ]
        }

        result = [
            {
                "amount": 100.0,
                "currencycode": None,
                "purpose": "description",
                "recipient": None,
                "creditoraccount": {},
                "interval": {
                    "from": None,
                    "until": None,
                    "frequency": None,
                    "holidayExecutionStrategy": None,
                    "nextExecutionAt": None,
                },
            }
        ]

        self.assertEqual(result, self.dkb._filter(full_list))

    def test_014__filter_unfiltered_malformed_creditor_debtor_accounts(self):
        """test StandingOrders._filter() handles malformed creditor/debtor accounts"""
        full_list = {
            "data": [
                {
                    "attributes": {
                        "description": "description",
                        "amount": {"value": "100"},
                        "creditor": {
                            "name": "cardname",
                            "creditorAccount": "not-a-dict",
                        },
                        "debtor": {
                            "debtorAccount": "not-a-dict",
                        },
                        "recurrence": {
                            "from": "2020-01-01",
                            "until": "2025-12-01",
                            "frequency": "monthly",
                            "nextExecutionAt": "2020-02-01",
                        },
                    }
                }
            ]
        }

        self.dkb.unfiltered = True
        result = self.dkb._filter(full_list)

        self.assertEqual(100, result[0].amount.value)
        self.assertIsNone(result[0].creditor)
        self.assertIsNone(result[0].debtor)
        self.assertEqual("2020-01-01", result[0].recurrence.frm)


if __name__ == "__main__":

    unittest.main()
