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
        from dkb_robo.utilities import validate_dates, generate_random_string, logger_setup, string2float, _convert_date_format, get_dateformat
        self.validate_dates = validate_dates
        self.string2float = string2float
        self.generate_random_string = generate_random_string
        self.logger_setup = logger_setup
        self._convert_date_format = _convert_date_format
        self.get_dateformat = get_dateformat
        self.logger = logging.getLogger('dkb_robo')

    @patch('time.time')
    def test_001_validate_dates(self, mock_time):
        """ test validate dates with correct data """
        date_from = '01.01.2024'
        date_to = '10.01.2024'
        mock_time.return_value = 1726309859
        self.assertEqual(('2024-01-01', '2024-01-10'), self.validate_dates(self.logger, date_from, date_to))

    @patch('time.time')
    def test_002_validate_dates(self, mock_time):
        """ test validate dates dates to be corrected """
        date_from = '12.12.2021'
        date_to = '11.12.2021'
        mock_time.return_value = 1726309859
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('2022-01-01', '2022-01-01'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 2022-01-01', lcm.output)
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_to to 2022-01-01', lcm.output)

    @patch('time.time')
    def test_003_validate_dates(self, mock_time):
        """ test validate dates with correct data """
        date_from = '2024-01-01'
        date_to = '2024-01-10'
        mock_time.return_value = 1726309859
        self.assertEqual(('2024-01-01', '2024-01-10'), self.validate_dates(self.logger, date_from, date_to))

    @patch('time.time')
    def test_004_validate_dates(self, mock_time):
        """ test validate dates dates to be corrected """
        date_from = '2021-12-01'
        date_to = '2021-12-11'
        mock_time.return_value = 1726309859
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('2022-01-01', '2022-01-01'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 2022-01-01', lcm.output)
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_to to 2022-01-01', lcm.output)

    @patch('time.time')
    def test_005_validate_dates(self, mock_time):
        """ test validate dates dates to be corrected """
        date_from = '01.12.2024'
        date_to = '11.12.2024'
        mock_time.return_value = 1726309859
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('2024-09-14', '2024-09-14'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 2024-09-14', lcm.output)
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_to to 2024-09-14', lcm.output)

    @patch('time.time')
    def test_006_validate_dates(self, mock_time):
        """ test validate dates dates to be corrected """
        date_from = '2024-12-01'
        date_to = '2024-12-11'
        mock_time.return_value = 1726309859
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('2024-09-14', '2024-09-14'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to 2024-09-14', lcm.output)
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_to to 2024-09-14', lcm.output)

    @patch('time.time')
    def test_007_validate_dates(self, mock_time):
        """ test validate dates with correct data """
        date_from = '15.01.2024'
        date_to = '10.01.2024'
        mock_time.return_value = 1726309859
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('2024-01-10', '2024-01-10'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to date_to', lcm.output)

    @patch('time.time')
    def test_008_validate_dates(self, mock_time):
        """ test validate dates with correct data """
        date_from = '2024-01-15'
        date_to = '2024-01-10'
        mock_time.return_value = 1726309859
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('2024-01-10', '2024-01-10'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to date_to', lcm.output)

    @patch('time.time')
    def test_009_validate_dates(self, mock_time):
        """ test validate dates with correct data """
        date_from = '15.01.2024'
        date_to = '10.01.2024'
        mock_time.return_value = 1726309859
        with self.assertLogs('dkb_robo', level='INFO') as lcm:
            self.assertEqual(('2024-01-10', '2024-01-10'), self.validate_dates(self.logger, date_from, date_to))
        self.assertIn('INFO:dkb_robo:validate_dates(): adjust date_from to date_to', lcm.output)

    @patch('random.choice')
    def test_010_generate_random_string(self, mock_rc):
        """ test generate_random_string """
        mock_rc.return_value = '1a'
        length = 5
        self.assertEqual('1a1a1a1a1a', self.generate_random_string(length))

    @patch('random.choice')
    def test_011_generate_random_string(self, mock_rc):
        """ generate_random_string """
        mock_rc.return_value = '1a'
        length = 10
        self.assertEqual('1a1a1a1a1a1a1a1a1a1a', self.generate_random_string(length))

    def test_012_string2float(self):
        """ test string2float """
        value = 1000
        self.assertEqual(1000.0, self.string2float(value))

    def test_013_string2float(self):
        """ test string2float """
        value = 1000.0
        self.assertEqual(1000.0, self.string2float(value))

    def test_014_string2float(self):
        """ test string2float """
        value = '1.000,00'
        self.assertEqual(1000.0, self.string2float(value))

    def test_015_string2float(self):
        """ test string2float """
        value = '1000,00'
        self.assertEqual(1000.0, self.string2float(value))

    def test_016_string2float(self):
        """ test string2float """
        value = '1.000'
        self.assertEqual(1000.0, self.string2float(value))

    def test_017_string2float(self):
        """ test string2float """
        value = '1.000,23'
        self.assertEqual(1000.23, self.string2float(value))

    def test_018_string2float(self):
        """ test string2float """
        value = '1000,23'
        self.assertEqual(1000.23, self.string2float(value))

    def test_019_string2float(self):
        """ test string2float """
        value = 1000.23
        self.assertEqual(1000.23, self.string2float(value))

    def test_020_string2float(self):
        """ test string2float """
        value = '-1.000'
        self.assertEqual(-1000.0, self.string2float(value))

    def test_021_string2float(self):
        """ test string2float """
        value = '-1.000,23'
        self.assertEqual(-1000.23, self.string2float(value))

    def test_022_string2float(self):
        """ test string2float """
        value = '-1000,23'
        self.assertEqual(-1000.23, self.string2float(value))

    def test_023_string2float(self):
        """ test string2float """
        value = -1000.23
        self.assertEqual(-1000.23, self.string2float(value))

    def test_024__convert_date_format(self):
        """ test _convert_date_format() """
        self.assertEqual('01.01.2023', self._convert_date_format(self.logger, '2023/01/01', ['%Y/%m/%d'], '%d.%m.%Y'))

    def test_025__convert_date_format(self):
        """ test _convert_date_format() """
        self.assertEqual('wrong date', self._convert_date_format(self.logger, 'wrong date', ['%Y/%m/%d'], '%d.%m.%Y'))

    def test_026__convert_date_format(self):
        """ test _convert_date_format() first match """
        self.assertEqual('01.01.2023', self._convert_date_format(self.logger, '2023/01/01', ['%Y/%m/%d', '%d.%m.%Y'], '%d.%m.%Y'))

    def test_027__convert_date_format(self):
        """ test _convert_date_format() last match """
        self.assertEqual('01.01.2023', self._convert_date_format(self.logger, '2023/01/01', ['%d.%m.%Y', '%Y/%m/%d'], '%d.%m.%Y'))

    def test_028__convert_date_format(self):
        """ test _convert_date_format() last match """
        self.assertEqual('2023/01/01', self._convert_date_format(self.logger, '2023/01/01', ['%Y/%m/%d', '%d.%m.%Y'], '%Y/%m/%d'))

    def test_029__convert_date_format(self):
        """ test _convert_date_format() first match """
        self.assertEqual('2023/01/01', self._convert_date_format(self.logger, '2023/01/01', ['%d.%m.%Y', '%Y/%m/%d'], '%Y/%m/%d'))

    def test_030__convert_date_format(self):
        """ test _convert_date_format() no match """
        self.assertEqual('wrong date', self._convert_date_format(self.logger, 'wrong date', ['%Y/%m/%d', '%Y-%m-%d'], '%d.%m.%Y'))



if __name__ == '__main__':

    unittest.main()
