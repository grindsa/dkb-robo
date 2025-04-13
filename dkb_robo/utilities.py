""" miscellaneous functions """
# -*- coding: utf-8 -*-
import logging
from pathlib import Path
import random
from string import digits, ascii_letters
from typing import List, Tuple, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, fields, asdict, is_dataclass
import time
import re


logger = logging.getLogger(__name__)


def get_dateformat():
    """get date format"""
    return "%d.%m.%Y", "%Y-%m-%d"


LEGACY_DATE_FORMAT, API_DATE_FORMAT = get_dateformat()
JSON_CONTENT_TYPE = "application/vnd.api+json"
BASE_URL = "https://banking.dkb.de/api"


def filter_unexpected_fields(cls):
    """filter undefined fields (not defined as class variable) before import to dataclass"""
    original_init = cls.__init__

    def new_init(self, *args, **kwargs):
        expected_fields = {field.name for field in fields(cls)}
        cleaned_kwargs = {
            key: value for key, value in kwargs.items() if key in expected_fields
        }
        original_init(self, *args, **cleaned_kwargs)

    cls.__init__ = new_init
    return cls


@filter_unexpected_fields
@dataclass
class Account:
    """dataclass to build peer account structure"""

    # pylint: disable=c0103
    accountNr: Optional[str] = None
    accountId: Optional[str] = None
    bic: Optional[str] = None
    blz: Optional[str] = None
    iban: Optional[str] = None
    id: Optional[str] = None
    intermediaryName: Optional[str] = None
    name: Optional[str] = None


@filter_unexpected_fields
@dataclass
class Amount:
    """Amount data class, roughly based on the JSON API response."""

    # pylint: disable=c0103
    value: Optional[float] = None
    currencyCode: Optional[str] = None
    conversionRate: Optional[float] = None
    date: Optional[str] = None
    unit: Optional[str] = None

    def __post_init__(self):
        # convert value to float
        try:
            self.value = float(self.value)
        except Exception as err:
            logger.error("Account.__post_init: value conversion error:  %s", str(err))
            self.value = None
        if self.conversionRate:
            try:
                self.conversionRate = float(self.conversionRate)
            except Exception as err:
                logger.error(
                    "Account.__post_init: converstionRate conversion error:  %s",
                    str(err),
                )
                self.conversionRate = None


@filter_unexpected_fields
@dataclass
class PerformanceValue:
    """PerformanceValue data class, roughly based on the JSON API response."""

    # pylint: disable=c0103
    currencyCode: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None

    def __post_init__(self):
        # convert value to float
        try:
            self.value = float(self.value)
        except Exception as err:
            logger.error(
                "PerformanceValue.__post_init: conversion error:  %s", str(err)
            )
            self.value = None


@filter_unexpected_fields
@dataclass
class Person:
    """Person class"""

    # pylint: disable=c0103
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    title: Optional[str] = None
    salutation: Optional[str] = None
    dateOfBirth: Optional[str] = None
    taxId: Optional[str] = None


class DKBRoboError(Exception):
    """dkb-robo exception class"""


def _convert_date_format(
    input_date: str, input_format_list: List[str], output_format: str
) -> str:
    """convert date to a specified output format"""
    logger.debug("_convert_date_format(%s)", input_date)

    output_date = None
    for input_format in input_format_list:
        try:
            parsed_date = datetime.strptime(input_date, input_format)
            # convert date
            output_date = parsed_date.strftime(output_format)
            break
        except Exception:
            logger.debug("_convert_date_format(): cannot convert date: %s", input_date)
            # something went wrong. we return the date we got as input
            continue

    if not output_date:
        output_date = input_date

    logger.debug("_convert_date_format() ended with: %s", output_date)
    return output_date


def generate_random_string(length: int) -> str:
    """generate random string to be used as name"""
    char_set = digits + ascii_letters
    return "".join(random.choice(char_set) for _ in range(length))


def get_valid_filename(name):
    """sanitize filenames"""
    s = re.sub(r"(?u)[^-\w.]", " ", str(name))
    p = Path(s.strip())
    s = "_".join(p.stem.split())

    if s in {"", ".", ".."}:
        s = f"{generate_random_string(8)}.pdf"
    return s + p.suffix


def object2dictionary(obj, key_lc=False, skip_list=None):
    """convert object to dict"""

    output_dict = {}
    for k, v in asdict(obj).items():
        if isinstance(skip_list, list) and k in skip_list:
            continue
        if is_dataclass(v):
            output_dict[k] = object2dictionary(v, key_lc=key_lc)
        else:
            if key_lc:
                output_dict[k.lower()] = v
            else:
                output_dict[k] = v
    return output_dict


def string2float(value: str) -> float:
    """convert string to float value"""
    try:
        result = float(value.replace(".", "").replace(",", "."))
    except Exception:
        result = value

    return result


def logger_setup(debug: bool) -> logging.Logger:
    """setup logger"""
    if debug:
        log_mode = logging.DEBUG
    else:
        log_mode = logging.INFO

    # define standard log format
    log_format = None
    if debug:
        log_format = "%(module)s: %(message)s"
    else:
        log_format = "%(message)s"

    logging.basicConfig(format=log_format, datefmt="%Y-%m-%d %H:%M:%S", level=log_mode)
    mylogger = logging.getLogger("dkb_robo")
    return mylogger


def validate_dates(date_from: str, date_to: str) -> Tuple[str, str]:
    """correct dates if needed"""
    logger.debug("validate_dates()")

    try:
        date_from_uts = int(
            time.mktime(datetime.strptime(date_from, "%d.%m.%Y").timetuple())
        )
    except ValueError:
        date_from_uts = int(
            time.mktime(datetime.strptime(date_from, API_DATE_FORMAT).timetuple())
        )
    try:
        date_to_uts = int(
            time.mktime(datetime.strptime(date_to, "%d.%m.%Y").timetuple())
        )
    except ValueError:
        date_to_uts = int(
            time.mktime(datetime.strptime(date_to, API_DATE_FORMAT).timetuple())
        )

    now_uts = int(time.time())

    # ajust valid_from to valid_to
    if date_to_uts <= date_from_uts:
        logger.info("validate_dates(): adjust date_from to date_to")
        date_from = date_to

    # minimal date uts (01.01.2022)
    minimal_date_uts = 1640995200

    if date_from_uts < minimal_date_uts:
        logger.info(
            "validate_dates(): adjust date_from to %s",
            datetime.fromtimestamp(minimal_date_uts, timezone.utc).strftime(
                API_DATE_FORMAT
            ),
        )
        date_from = datetime.fromtimestamp(minimal_date_uts, timezone.utc).strftime(
            "%d.%m.%Y"
        )
    if date_to_uts < minimal_date_uts:
        logger.info(
            "validate_dates(): adjust date_to to %s",
            datetime.fromtimestamp(minimal_date_uts, timezone.utc).strftime(
                API_DATE_FORMAT
            ),
        )
        date_to = datetime.fromtimestamp(minimal_date_uts, timezone.utc).strftime(
            "%d.%m.%Y"
        )

    if date_from_uts > now_uts:
        logger.info(
            "validate_dates(): adjust date_from to %s",
            datetime.fromtimestamp(now_uts, timezone.utc).strftime(API_DATE_FORMAT),
        )
        date_from = datetime.fromtimestamp(now_uts).strftime("%d.%m.%Y")
    if date_to_uts > now_uts:
        logger.info(
            "validate_dates(): adjust date_to to %s",
            datetime.fromtimestamp(now_uts, timezone.utc).strftime(API_DATE_FORMAT),
        )
        date_to = datetime.fromtimestamp(now_uts, timezone.utc).strftime("%d.%m.%Y")

    # this is the new api we need to ensure %Y-%m-%d
    date_from = _convert_date_format(
        date_from, [API_DATE_FORMAT, LEGACY_DATE_FORMAT], API_DATE_FORMAT
    )
    date_to = _convert_date_format(
        date_to, [API_DATE_FORMAT, LEGACY_DATE_FORMAT], API_DATE_FORMAT
    )

    logger.debug("validate_dates() returned: %s, %s", date_from, date_to)
    return date_from, date_to


def ulal(mapclass, parameter):
    """map parameter"""
    if parameter:
        return mapclass(**parameter)
    return None
