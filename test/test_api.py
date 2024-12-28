# -*- coding: utf-8 -*-
# pylint: disable=r0904, c0415, c0413, r0913, w0212
""" unittests for dkb_robo """
import sys
import os
from datetime import date
import unittest
import logging
import json
from unittest.mock import patch, Mock, mock_open
from bs4 import BeautifulSoup
from mechanicalsoup import LinkNotFoundError
import io
sys.path.insert(0, '.')
sys.path.insert(0, '..')
from dkb_robo.api import Wrapper


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


def my_side_effect(*args):
    """ my sideeffect funtion """
    return [200, args[1], [args[4]]]


class TestDKBRobo(unittest.TestCase):
    """ test class """

    maxDiff = None

    def setUp(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('dkb_robo')
        self.dkb = Wrapper(logger=self.logger)

    def test_110_get_credit_limits(self):
        """ teest _get_credit_limits() """
        self.dkb.account_dic = {0: {'limit': 1000, 'iban': 'iban'}, 1: {'limit': 2000, 'maskedpan': 'maskedpan'}}
        result_dic = {'iban': 1000, 'maskedpan': 2000}
        self.assertEqual(result_dic, self.dkb.get_credit_limits())

    def test_111_get_credit_limits(self):
        """ teest get_credit_limits() """
        self.dkb.account_dic = {'foo': 'bar'}
        self.assertFalse(self.dkb.get_credit_limits())

    @patch('dkb_robo.legacy.Wrapper.get_exemption_order')
    def test_130_get_exemption_order(self, mock_exo):
        """ test get_exemption_order() """
        mock_exo.return_value = 'mock_exo'
        self.assertEqual('mock_exo', self.dkb.get_exemption_order())


if __name__ == '__main__':

    unittest.main()
