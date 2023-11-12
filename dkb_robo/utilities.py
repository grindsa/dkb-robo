""" miscellaneous functions """
# -*- coding: utf-8 -*-
import logging
import random
from string import digits, ascii_letters
import datetime
import time


LEGACY_DATE_FORMAT = '%d.%m.%Y'
API_DATE_FORMAT = '%Y-%m-%d'


def convert_date_format(logger, input_date, input_format_list, output_format):
    """ convert date to a specified output format """
    logger.debug('convert_date_format(%s)', input_date)

    output_date = None
    for input_format in input_format_list:
        try:
            parsed_date = datetime.datetime.strptime(input_date, input_format)
            # convert date
            output_date = parsed_date.strftime(output_format)
            break
        except Exception:
            logger.debug('convert_date_format(): cannot convert date: %s', input_date)
            # something went wrong. we return the date we got as input
            continue

    if not output_date:
        output_date = input_date

    logger.debug('convert_date_format() ended with: %s', output_date)
    return output_date


def generate_random_string(length):
    """ generate random string to be used as name """
    char_set = digits + ascii_letters
    return ''.join(random.choice(char_set) for _ in range(length))


def string2float(value):
    """ convert string to float value """
    try:
        result = float(value.replace('.', '').replace(',', '.'))
    except Exception:
        result = value

    return result


def logger_setup(debug):
    """ setup logger """
    if debug:
        log_mode = logging.DEBUG
    else:
        log_mode = logging.INFO

    # define standard log format
    log_format = '%(message)s'
    logging.basicConfig(
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        level=log_mode)
    logger = logging.getLogger('dkb_robo')
    return logger


def enforce_date_format(logger, date_from, date_to, min_year):
    """ enforce a certain date format """
    logger.debug('enforce_date_format(): %s, %s %s', date_from, date_to, min_year)

    if min_year == 1:
        # this is the new api we need to ensure %Y-%m-%d
        date_from = convert_date_format(logger, date_from, [API_DATE_FORMAT, LEGACY_DATE_FORMAT], API_DATE_FORMAT)
        date_to = convert_date_format(logger, date_to, [API_DATE_FORMAT, LEGACY_DATE_FORMAT], API_DATE_FORMAT)
    else:
        # this is the old  api we need to ensure $d.%m,%Y
        date_from = convert_date_format(logger, date_from, [API_DATE_FORMAT, LEGACY_DATE_FORMAT], LEGACY_DATE_FORMAT)
        date_to = convert_date_format(logger, date_to, [API_DATE_FORMAT, LEGACY_DATE_FORMAT], LEGACY_DATE_FORMAT)

    logger.debug('enforce_date_format() ended with: %s, %s', date_from, date_to)
    return date_from, date_to


def validate_dates(logger, date_from, date_to, min_year=3, legacy_login=True):
    """ correct dates if needed """
    logger.debug('validate_dates()')
    try:
        date_from_uts = int(time.mktime(datetime.datetime.strptime(date_from, "%d.%m.%Y").timetuple()))
    except ValueError:
        date_from_uts = int(time.mktime(datetime.datetime.strptime(date_from, API_DATE_FORMAT).timetuple()))
    try:
        date_to_uts = int(time.mktime(datetime.datetime.strptime(date_to, "%d.%m.%Y").timetuple()))
    except ValueError:
        date_to_uts = int(time.mktime(datetime.datetime.strptime(date_to, API_DATE_FORMAT).timetuple()))
    now_uts = int(time.time())

    # minimal date (3 years back)
    minimal_date_uts = now_uts - min_year * 365 * 86400

    if date_from_uts < minimal_date_uts:
        logger.info('validate_dates(): adjust date_from to %s', datetime.datetime.utcfromtimestamp(minimal_date_uts).strftime('%d.%m.%Y'))
        date_from = datetime.datetime.utcfromtimestamp(minimal_date_uts).strftime('%d.%m.%Y')
    if date_to_uts < minimal_date_uts:
        logger.info('validate_dates(): adjust date_to to %s', datetime.datetime.utcfromtimestamp(minimal_date_uts).strftime('%d.%m.%Y'))
        date_to = datetime.datetime.utcfromtimestamp(minimal_date_uts).strftime('%d.%m.%Y')

    if date_from_uts > now_uts:
        logger.info('validate_dates(): adjust date_from to %s', datetime.datetime.utcfromtimestamp(now_uts).strftime('%d.%m.%Y'))
        date_from = datetime.datetime.utcfromtimestamp(now_uts).strftime('%d.%m.%Y')
    if date_to_uts > now_uts and legacy_login:
        logger.info('validate_dates(): adjust date_to to %s', datetime.datetime.utcfromtimestamp(now_uts).strftime('%d.%m.%Y'))
        date_to = datetime.datetime.utcfromtimestamp(now_uts).strftime('%d.%m.%Y')

    date_from, date_to = enforce_date_format(logger, date_from, date_to, min_year)

    logger.debug('validate_dates() returned: %s, %s', date_from, date_to)
    return (date_from, date_to)
