# -*- coding: utf-8 -*-
# pylint: disable=r0904, c0415
""" unittests for dkb_robo """
import sys
import os
import unittest
import logging
from unittest.mock import patch
sys.path.insert(0, '.')
sys.path.insert(0, '..')


class TestDKBRobo(unittest.TestCase):
    """ test class """

    maxDiff = None

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        from dkb_robo.utilities import validate_dates, generate_random_string, logger_setup, string2float, _convert_date_format, _enforce_date_format
        self.validate_dates = validate_dates
        self.string2float = string2float
        self.generate_random_string = generate_random_string
        self.logger_setup = logger_setup
        self._convert_date_format = _convert_date_format
        self._enforce_date_format = _enforce_date_format
        self.logger = logging.getLogger('dkb_robo')

    @patch('time.time')
    def test_001_validate_dates(self, mock_time):
        """ test validate dates with correct data """
        date_from = '01.12.2021'
        date_to = '10.12.2021'
        mock_time.return_value = 1639232579
        self.assertEqual(('01.12.2021', '10.12.2021'), self.validate_dates(self.logger, date_from, date_to))

    @patch('time.time')
    def test_002_validate_dates(self, mock_time):
        """ test validate dates date_from to be corrected """
        date_from = '12.12.2021'
        date_to = '11.12.2021'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('11.12.2021', '11.12.2021'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 11.12.2021', lcm.output)

    @patch('time.time')
    def test_003_validate_dates(self, mock_time):
        """ test validate dates date_to to be corrected """
        date_from = '01.12.2021'
        date_to = '12.12.2021'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('01.12.2021', '11.12.2021'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_to to 11.12.2021', lcm.output)

    @patch('time.time')
    def test_004_validate_dates(self, mock_time):
        """ test validate dates date_to to be corrected """
        date_from = '01.12.2021'
        date_to = '12.12.2021'
        mock_time.return_value = 1639232579
        self.assertEqual(('01.12.2021', '12.12.2021'), self.validate_dates(self.logger, date_from, date_to, legacy_login=False))

    @patch('time.time')
    def test_005_validate_dates(self, mock_time):
        """ test validate dates date_from to be corrected past past > 3 years """
        date_from = '01.01.1980'
        date_to = '12.12.2021'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('12.12.2018', '11.12.2021'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 12.12.2018', lcm.output)

    @patch('time.time')
    def test_006_validate_dates(self, mock_time):
        """ test validate dates date_from to be corrected past past > 3 years """
        date_from = '01.01.1980'
        date_to = '02.01.1980'
        mock_time.return_value = 1639232579
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('12.12.2018', '12.12.2018'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 12.12.2018', lcm.output)
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_to to 12.12.2018', lcm.output)

    @patch('time.time')
    def test_007_validate_dates(self, mock_time):
        """ test validate dates with correct data """
        date_from = '2021-12-01'
        date_to = '2021-12-10'
        mock_time.return_value = 1639232579
        self.assertEqual(('2021-12-01', '2021-12-10'), self.validate_dates(self.logger, date_from, date_to, 1))

    @patch('time.time')
    def test_008_validate_dates(self, mock_time):
        """ test validate dates with correct data """
        date_from = '2021-12-01'
        date_to = '2021-12-10'
        mock_time.return_value = 1639232579
        self.assertEqual(('01.12.2021', '10.12.2021'), self.validate_dates(self.logger, date_from, date_to, 3))

    @patch('random.choice')
    def test_009_generate_random_string(self, mock_rc):
        """ test generate_random_string """
        mock_rc.return_value = '1a'
        length = 5
        self.assertEqual('1a1a1a1a1a', self.generate_random_string(length))

    @patch('random.choice')
    def test_010_generate_random_string(self, mock_rc):
        """ generate_random_string """
        mock_rc.return_value = '1a'
        length = 10
        self.assertEqual('1a1a1a1a1a1a1a1a1a1a', self.generate_random_string(length))

    def test_011_string2float(self):
        """ test string2float """
        value = 1000
        self.assertEqual(1000.0, self.string2float(value))

    def test_012_string2float(self):
        """ test string2float """
        value = 1000.0
        self.assertEqual(1000.0, self.string2float(value))

    def test_013_string2float(self):
        """ test string2float """
        value = '1.000,00'
        self.assertEqual(1000.0, self.string2float(value))

    def test_014_string2float(self):
        """ test string2float """
        value = '1000,00'
        self.assertEqual(1000.0, self.string2float(value))

    def test_015_string2float(self):
        """ test string2float """
        value = '1.000'
        self.assertEqual(1000.0, self.string2float(value))

    def test_016_string2float(self):
        """ test string2float """
        value = '1.000,23'
        self.assertEqual(1000.23, self.string2float(value))

    def test_017_string2float(self):
        """ test string2float """
        value = '1000,23'
        self.assertEqual(1000.23, self.string2float(value))

    def test_018_string2float(self):
        """ test string2float """
        value = 1000.23
        self.assertEqual(1000.23, self.string2float(value))

    def test_019_string2float(self):
        """ test string2float """
        value = '-1.000'
        self.assertEqual(-1000.0, self.string2float(value))

    def test_020_string2float(self):
        """ test string2float """
        value = '-1.000,23'
        self.assertEqual(-1000.23, self.string2float(value))

    def test_021_string2float(self):
        """ test string2float """
        value = '-1000,23'
        self.assertEqual(-1000.23, self.string2float(value))

    def test_022_string2float(self):
        """ test string2float """
        value = -1000.23
        self.assertEqual(-1000.23, self.string2float(value))

    def test_023__convert_date_format(self):
        """ test _convert_date_format() """
        self.assertEqual('01.01.2023', self._convert_date_format(self.logger, '2023/01/01', ['%Y/%m/%d'], '%d.%m.%Y'))

    def test_024__convert_date_format(self):
        """ test _convert_date_format() """
        self.assertEqual('wrong date', self._convert_date_format(self.logger, 'wrong date', ['%Y/%m/%d'], '%d.%m.%Y'))

    def test_025__convert_date_format(self):
        """ test _convert_date_format() first match """
        self.assertEqual('01.01.2023', self._convert_date_format(self.logger, '2023/01/01', ['%Y/%m/%d', '%d.%m.%Y'], '%d.%m.%Y'))

    def test_026__convert_date_format(self):
        """ test _convert_date_format() last match """
        self.assertEqual('01.01.2023', self._convert_date_format(self.logger, '2023/01/01', ['%d.%m.%Y', '%Y/%m/%d'], '%d.%m.%Y'))

    def test_027__convert_date_format(self):
        """ test _convert_date_format() last match """
        self.assertEqual('2023/01/01', self._convert_date_format(self.logger, '2023/01/01', ['%Y/%m/%d', '%d.%m.%Y'], '%Y/%m/%d'))

    def test_028__convert_date_format(self):
        """ test _convert_date_format() first match """
        self.assertEqual('2023/01/01', self._convert_date_format(self.logger, '2023/01/01', ['%d.%m.%Y', '%Y/%m/%d'], '%Y/%m/%d'))

    def test_029__convert_date_format(self):
        """ test _convert_date_format() no match """
        self.assertEqual('wrong date', self._convert_date_format(self.logger, 'wrong date', ['%Y/%m/%d', '%Y-%m-%d'], '%d.%m.%Y'))

    def test_030__enforce_date_format(self):
        """ test _enforce_date_format() - old frontend - old date format """
        self.assertEqual(('01.01.2023', '02.01.2023'), self._enforce_date_format(self.logger, '01.01.2023', '02.01.2023', 3))

    def test_031__enforce_date_format(self):
        """ test _enforce_date_format() - old frontend - new date format """
        self.assertEqual(('01.04.2023', '02.04.2023'), self._enforce_date_format(self.logger, '2023-04-01', '2023-04-02', 3))

    def test_032__enforce_date_format(self):
        """ test _enforce_date_format() - new frontend - new date format """
        self.assertEqual(('2023-01-01', '2023-01-02'), self._enforce_date_format(self.logger, '2023-01-01', '2023-01-02', 1))

    def test_033__enforce_date_format(self):
        """ test _enforce_date_format() - new frontend - old date format """
        self.assertEqual(('2023-01-01', '2023-01-02'), self._enforce_date_format(self.logger, '01.01.2023', '02.01.2023', 1))


if __name__ == '__main__':

    unittest.main()
