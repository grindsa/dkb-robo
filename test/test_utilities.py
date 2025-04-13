# -*- coding: utf-8 -*-
# pylint: disable=r0904, c0415
""" unittests for dkb_robo """
import sys
import os
import unittest
import logging
from unittest.mock import patch, Mock, MagicMock
from dataclasses import dataclass, asdict

sys.path.insert(0, ".")
sys.path.insert(0, "..")


@dataclass
class DataclassObject:
    Attr1: str
    attr2: int
    attr3: dict
    attr4: list


class TestDKBRobo(unittest.TestCase):
    """test class"""

    maxDiff = None

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        from dkb_robo.utilities import (
            validate_dates,
            generate_random_string,
            logger_setup,
            string2float,
            _convert_date_format,
            get_dateformat,
            get_valid_filename,
            object2dictionary,
            logger_setup,
            ulal,
        )

        self.validate_dates = validate_dates
        self.string2float = string2float
        self.generate_random_string = generate_random_string
        self.logger_setup = logger_setup
        self._convert_date_format = _convert_date_format
        self.get_dateformat = get_dateformat
        self.get_valid_filename = get_valid_filename
        self.object2dictionary = object2dictionary
        self.logger = logging.getLogger("dkb_robo")
        self.logger_setup = logger_setup
        self.ulal = ulal

    @patch("time.time")
    def test_001_validate_dates(self, mock_time):
        """test validate dates with correct data"""
        date_from = "01.01.2024"
        date_to = "10.01.2024"
        mock_time.return_value = 1726309859
        self.assertEqual(
            ("2024-01-01", "2024-01-10"), self.validate_dates(date_from, date_to)
        )

    @patch("time.time")
    def test_002_validate_dates(self, mock_time):
        """test validate dates dates to be corrected"""
        date_from = "12.12.2021"
        date_to = "11.12.2021"
        mock_time.return_value = 1726309859
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(
                ("2022-01-01", "2022-01-01"), self.validate_dates(date_from, date_to)
            )
        self.assertIn(
            "INFO:dkb_robo.utilities:validate_dates(): adjust date_from to 2022-01-01",
            lcm.output,
        )
        self.assertIn(
            "INFO:dkb_robo.utilities:validate_dates(): adjust date_to to 2022-01-01",
            lcm.output,
        )

    @patch("time.time")
    def test_003_validate_dates(self, mock_time):
        """test validate dates with correct data"""
        date_from = "2024-01-01"
        date_to = "2024-01-10"
        mock_time.return_value = 1726309859
        self.assertEqual(
            ("2024-01-01", "2024-01-10"), self.validate_dates(date_from, date_to)
        )

    @patch("time.time")
    def test_004_validate_dates(self, mock_time):
        """test validate dates dates to be corrected"""
        date_from = "2021-12-01"
        date_to = "2021-12-11"
        mock_time.return_value = 1726309859
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(
                ("2022-01-01", "2022-01-01"), self.validate_dates(date_from, date_to)
            )
        self.assertIn(
            "INFO:dkb_robo.utilities:validate_dates(): adjust date_from to 2022-01-01",
            lcm.output,
        )
        self.assertIn(
            "INFO:dkb_robo.utilities:validate_dates(): adjust date_to to 2022-01-01",
            lcm.output,
        )

    @patch("time.time")
    def test_005_validate_dates(self, mock_time):
        """test validate dates dates to be corrected"""
        date_from = "01.12.2024"
        date_to = "11.12.2024"
        mock_time.return_value = 1726309859
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(
                ("2024-09-14", "2024-09-14"), self.validate_dates(date_from, date_to)
            )
        self.assertIn(
            "INFO:dkb_robo.utilities:validate_dates(): adjust date_from to 2024-09-14",
            lcm.output,
        )
        self.assertIn(
            "INFO:dkb_robo.utilities:validate_dates(): adjust date_to to 2024-09-14",
            lcm.output,
        )

    @patch("time.time")
    def test_006_validate_dates(self, mock_time):
        """test validate dates dates to be corrected"""
        date_from = "2024-12-01"
        date_to = "2024-12-11"
        mock_time.return_value = 1726309859
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(
                ("2024-09-14", "2024-09-14"), self.validate_dates(date_from, date_to)
            )
        self.assertIn(
            "INFO:dkb_robo.utilities:validate_dates(): adjust date_from to 2024-09-14",
            lcm.output,
        )
        self.assertIn(
            "INFO:dkb_robo.utilities:validate_dates(): adjust date_to to 2024-09-14",
            lcm.output,
        )

    @patch("time.time")
    def test_007_validate_dates(self, mock_time):
        """test validate dates with correct data"""
        date_from = "15.01.2024"
        date_to = "10.01.2024"
        mock_time.return_value = 1726309859
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(
                ("2024-01-10", "2024-01-10"), self.validate_dates(date_from, date_to)
            )
        self.assertIn(
            "INFO:dkb_robo.utilities:validate_dates(): adjust date_from to date_to",
            lcm.output,
        )

    @patch("time.time")
    def test_008_validate_dates(self, mock_time):
        """test validate dates with correct data"""
        date_from = "2024-01-15"
        date_to = "2024-01-10"
        mock_time.return_value = 1726309859
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(
                ("2024-01-10", "2024-01-10"), self.validate_dates(date_from, date_to)
            )
        self.assertIn(
            "INFO:dkb_robo.utilities:validate_dates(): adjust date_from to date_to",
            lcm.output,
        )

    @patch("time.time")
    def test_009_validate_dates(self, mock_time):
        """test validate dates with correct data"""
        date_from = "15.01.2024"
        date_to = "10.01.2024"
        mock_time.return_value = 1726309859
        with self.assertLogs("dkb_robo", level="INFO") as lcm:
            self.assertEqual(
                ("2024-01-10", "2024-01-10"), self.validate_dates(date_from, date_to)
            )
        self.assertIn(
            "INFO:dkb_robo.utilities:validate_dates(): adjust date_from to date_to",
            lcm.output,
        )

    @patch("random.choice")
    def test_010_generate_random_string(self, mock_rc):
        """test generate_random_string"""
        mock_rc.return_value = "1a"
        length = 5
        self.assertEqual("1a1a1a1a1a", self.generate_random_string(length))

    @patch("random.choice")
    def test_011_generate_random_string(self, mock_rc):
        """generate_random_string"""
        mock_rc.return_value = "1a"
        length = 10
        self.assertEqual("1a1a1a1a1a1a1a1a1a1a", self.generate_random_string(length))

    def test_012_string2float(self):
        """test string2float"""
        value = 1000
        self.assertEqual(1000.0, self.string2float(value))

    def test_013_string2float(self):
        """test string2float"""
        value = 1000.0
        self.assertEqual(1000.0, self.string2float(value))

    def test_014_string2float(self):
        """test string2float"""
        value = "1.000,00"
        self.assertEqual(1000.0, self.string2float(value))

    def test_015_string2float(self):
        """test string2float"""
        value = "1000,00"
        self.assertEqual(1000.0, self.string2float(value))

    def test_016_string2float(self):
        """test string2float"""
        value = "1.000"
        self.assertEqual(1000.0, self.string2float(value))

    def test_017_string2float(self):
        """test string2float"""
        value = "1.000,23"
        self.assertEqual(1000.23, self.string2float(value))

    def test_018_string2float(self):
        """test string2float"""
        value = "1000,23"
        self.assertEqual(1000.23, self.string2float(value))

    def test_019_string2float(self):
        """test string2float"""
        value = 1000.23
        self.assertEqual(1000.23, self.string2float(value))

    def test_020_string2float(self):
        """test string2float"""
        value = "-1.000"
        self.assertEqual(-1000.0, self.string2float(value))

    def test_021_string2float(self):
        """test string2float"""
        value = "-1.000,23"
        self.assertEqual(-1000.23, self.string2float(value))

    def test_022_string2float(self):
        """test string2float"""
        value = "-1000,23"
        self.assertEqual(-1000.23, self.string2float(value))

    def test_023_string2float(self):
        """test string2float"""
        value = -1000.23
        self.assertEqual(-1000.23, self.string2float(value))

    def test_024__convert_date_format(self):
        """test _convert_date_format()"""
        self.assertEqual(
            "01.01.2023",
            self._convert_date_format("2023/01/01", ["%Y/%m/%d"], "%d.%m.%Y"),
        )

    def test_025__convert_date_format(self):
        """test _convert_date_format()"""
        self.assertEqual(
            "wrong date",
            self._convert_date_format("wrong date", ["%Y/%m/%d"], "%d.%m.%Y"),
        )

    def test_026__convert_date_format(self):
        """test _convert_date_format() first match"""
        self.assertEqual(
            "01.01.2023",
            self._convert_date_format(
                "2023/01/01", ["%Y/%m/%d", "%d.%m.%Y"], "%d.%m.%Y"
            ),
        )

    def test_027__convert_date_format(self):
        """test _convert_date_format() last match"""
        self.assertEqual(
            "01.01.2023",
            self._convert_date_format(
                "2023/01/01", ["%d.%m.%Y", "%Y/%m/%d"], "%d.%m.%Y"
            ),
        )

    def test_028__convert_date_format(self):
        """test _convert_date_format() last match"""
        self.assertEqual(
            "2023/01/01",
            self._convert_date_format(
                "2023/01/01", ["%Y/%m/%d", "%d.%m.%Y"], "%Y/%m/%d"
            ),
        )

    def test_029__convert_date_format(self):
        """test _convert_date_format() first match"""
        self.assertEqual(
            "2023/01/01",
            self._convert_date_format(
                "2023/01/01", ["%d.%m.%Y", "%Y/%m/%d"], "%Y/%m/%d"
            ),
        )

    def test_030__convert_date_format(self):
        """test _convert_date_format() no match"""
        self.assertEqual(
            "wrong date",
            self._convert_date_format(
                "wrong date", ["%Y/%m/%d", "%Y-%m-%d"], "%d.%m.%Y"
            ),
        )

    def test_039__get_valid_filename(self):
        """test get_valid_filename"""
        filename = "test.pdf"
        self.assertEqual("test.pdf", self.get_valid_filename(filename))

    def test_040__get_valid_filename(self):
        """test get_valid_filename"""
        filename = "test test.pdf"
        self.assertEqual("test_test.pdf", self.get_valid_filename(filename))

    def test_041__get_valid_filename(self):
        """test get_valid_filename"""
        filename = "testötest.pdf"
        self.assertEqual("testötest.pdf", self.get_valid_filename(filename))

    def test_042__get_valid_filename(self):
        """test get_valid_filename"""
        filename = "test/test.pdf"
        self.assertEqual("test_test.pdf", self.get_valid_filename(filename))

    def test_043_get_valid_filename(self):
        """test get_valid_filename"""
        filename = "test\\test.pdf"
        self.assertEqual("test_test.pdf", self.get_valid_filename(filename))

    def test_044_get_valid_filename(self):
        """test get_valid_filename"""
        filename = ".\test.pdf"
        self.assertEqual("._est.pdf", self.get_valid_filename(filename))

    def test_045_get_valid_filename(self):
        """test get_valid_filename"""
        filename = "../test.pdf"
        self.assertEqual(".._test.pdf", self.get_valid_filename(filename))

    @patch("dkb_robo.utilities.generate_random_string")
    def test_046_get_valid_filename(self, mock_rand):
        """test get_valid_filename"""
        filename = ".."
        mock_rand.return_value = "random"
        self.assertEqual("random.pdf", self.get_valid_filename(filename))

    def test_047_object2dictionary(self):
        """test object2dictionary"""

        nested_obj = DataclassObject(
            Attr1="nested_value1", attr2=3, attr3="nested_value1", attr4="nested_value2"
        )

        test_obj = DataclassObject(
            Attr1="value1", attr2=2, attr3=nested_obj, attr4="foo"
        )

        expected_output = {
            "Attr1": "value1",
            "attr2": 2,
            "attr3": {
                "Attr1": "nested_value1",
                "attr2": 3,
                "attr3": "nested_value1",
                "attr4": "nested_value2",
            },
            "attr4": "foo",
        }

        result = self.object2dictionary(test_obj)
        self.assertEqual(result, expected_output)

    def test_048_object2dictionary(self):
        """test object2dictionary"""
        test_obj = DataclassObject(
            Attr1="value1", attr2=2, attr3="attr3", attr4="attr4"
        )
        expected_output = {"attr1": "value1", "attr3": "attr3", "attr4": "attr4"}
        result = self.object2dictionary(test_obj, key_lc=True, skip_list=["attr2"])
        self.assertEqual(result, expected_output)

    def test_049_logger_setup(self):
        """logger setup"""
        self.assertTrue(self.logger_setup(False))

    def test_050_logger_setup(self):
        """logger setup"""
        self.assertTrue(self.logger_setup(True))

    def test_051_ulal(self):
        """test ulal() with_valid_parameter"""
        mapclass = Mock()
        parameter = {"key1": "value1", "key2": "value2"}
        result = self.ulal(mapclass, parameter)
        mapclass.assert_called_once_with(**parameter)
        self.assertEqual(result, mapclass.return_value)

    def test_052_ulal(self):
        """test ulal() with none parameter"""
        mapclass = MagicMock()
        parameter = None
        result = self.ulal(mapclass, parameter)
        mapclass.assert_not_called()
        self.assertIsNone(result)


class TestAmount(unittest.TestCase):
    """test class"""

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        from dkb_robo.utilities import Amount

        self.Amount = Amount

    @patch("dkb_robo.utilities.logger", autospec=True)
    def test_047_amount(self, mock_logger):
        """test Amount"""
        amount_data = {
            "value": "1000",
            "currencyCode": "USD",
            "conversionRate": "1.2",
            "date": "2022-01-01",
            "unit": "unit",
        }
        amount = self.Amount(**amount_data)
        self.assertEqual(amount.value, 1000.0)
        self.assertEqual(amount.currencyCode, "USD")
        self.assertEqual(amount.conversionRate, 1.2)
        self.assertEqual(amount.date, "2022-01-01")
        self.assertEqual(amount.unit, "unit")
        mock_logger.error.assert_not_called()

    @patch("dkb_robo.utilities.logger", autospec=True)
    def test_049_amount(self, mock_logger):
        """test Amount with wrong value"""
        amount_data = {
            "value": "invalid",
            "currencyCode": "USD",
            "conversionRate": "1.2",
            "date": "2022-01-01",
            "unit": "unit",
        }
        amount = self.Amount(**amount_data)
        self.assertFalse(amount.value)
        self.assertEqual(amount.currencyCode, "USD")
        self.assertEqual(amount.conversionRate, 1.2)
        self.assertEqual(amount.date, "2022-01-01")
        self.assertEqual(amount.unit, "unit")
        mock_logger.error.assert_called_with(
            "Account.__post_init: value conversion error:  %s",
            "could not convert string to float: 'invalid'",
        )

    @patch("dkb_robo.utilities.logger", autospec=True)
    def test_050_amount(self, mock_logger):
        """test Amount with wrong conversation rate"""
        amount_data = {
            "value": "1000",
            "currencyCode": "USD",
            "conversionRate": "invalid",
            "date": "2022-01-01",
            "unit": "unit",
        }
        amount = self.Amount(**amount_data)
        self.assertEqual(amount.value, 1000)
        self.assertEqual(amount.currencyCode, "USD")
        self.assertFalse(amount.conversionRate)
        self.assertEqual(amount.date, "2022-01-01")
        self.assertEqual(amount.unit, "unit")
        mock_logger.error.assert_called_with(
            "Account.__post_init: converstionRate conversion error:  %s",
            "could not convert string to float: 'invalid'",
        )


class TestPerformanceValue(unittest.TestCase):
    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        from dkb_robo.utilities import PerformanceValue

        self.PerformanceValue = PerformanceValue

    @patch("dkb_robo.utilities.logger", autospec=True)
    def test_051_performancevalue(self, mock_logger):
        performance_value_data = {
            "currencyCode": "USD",
            "value": "1000",
            "unit": "unit",
        }

        performance_value = self.PerformanceValue(**performance_value_data)

        self.assertEqual(performance_value.currencyCode, "USD")
        self.assertEqual(performance_value.value, 1000.0)
        self.assertEqual(performance_value.unit, "unit")
        mock_logger.error.assert_not_called()

    @patch("dkb_robo.utilities.logger", autospec=True)
    def test_052_performancevalue(self, mock_logger):
        performance_value_data = {
            "currencyCode": "USD",
            "value": "invalid",
            "unit": "unit",
        }

        performance_value = self.PerformanceValue(**performance_value_data)

        self.assertEqual(performance_value.currencyCode, "USD")
        self.assertIsNone(performance_value.value)
        self.assertEqual(performance_value.unit, "unit")
        mock_logger.error.assert_called_with(
            "PerformanceValue.__post_init: conversion error:  %s",
            "could not convert string to float: 'invalid'",
        )


if __name__ == "__main__":

    unittest.main()
