"""miscellaneous functions"""

# -*- coding: utf-8 -*-
import logging
from pathlib import Path
import random
from string import digits, ascii_letters
from typing import Any, Dict, List, Tuple, Optional, Union
from datetime import datetime, timezone, date
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

SCREEN_RESOLUTION_POOL = {
    "Windows": [
        ((1920, 1080), 45),
        ((1366, 768), 20),
        ((1536, 864), 10),
        ((1600, 900), 8),
        ((2560, 1440), 8),
        ((1280, 720), 5),
        ((3840, 2160), 4),
    ],
    "Mac OS": [
        ((2560, 1600), 28),
        ((1440, 900), 22),
        ((1680, 1050), 16),
        ((1728, 1117), 12),
        ((1792, 1120), 10),
        ((1920, 1080), 7),
        ((2560, 1440), 5),
    ],
    "Linux": [
        ((1920, 1080), 40),
        ((1366, 768), 18),
        ((2560, 1440), 14),
        ((1600, 900), 10),
        ((1280, 720), 8),
        ((3440, 1440), 6),
        ((3840, 2160), 4),
    ],
    "Unknown": [
        ((1920, 1080), 50),
        ((1366, 768), 20),
        ((1536, 864), 10),
        ((1600, 900), 10),
        ((2560, 1440), 10),
    ],
}


def filter_unexpected_fields(cls):
    """filter undefined fields (not defined as class variable) before import to dataclass"""
    original_init = cls.__init__
    expected_fields = {field.name for field in fields(cls)}

    def new_init(self, *args, **kwargs):
        dropped_fields = [key for key in kwargs if key not in expected_fields]
        if dropped_fields:
            logger.debug(
                "filter_unexpected_fields(%s): dropped unexpected fields: %s",
                cls.__name__,
                dropped_fields,
            )
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


def get_valid_screen_resolution(operating_system: str = "Unknown") -> dict:
    """Get a plausible desktop screen resolution for the given OS. we also weight the resolutions to favor more common ones."""
    pool = SCREEN_RESOLUTION_POOL.get(
        operating_system, SCREEN_RESOLUTION_POOL["Unknown"]
    )
    values = [item[0] for item in pool]
    weights = [item[1] for item in pool]
    width, height = random.choices(values, weights=weights, k=1)[0]
    return {"width": width, "height": height}


def get_valid_filename(name):
    """sanitize filenames"""
    s = re.sub(r"(?u)[^-\w.]", " ", str(name))
    p = Path(s.strip())
    s = "_".join(p.stem.split())

    if s in {"", ".", ".."}:
        s = f"{generate_random_string(8)}.pdf"
    return s + p.suffix


def string2float(value: Union[str, float, int]) -> Union[float, str, int]:
    """convert string to float value"""
    try:
        result = float(value.replace(".", "").replace(",", "."))
    except Exception:
        result = value

    return result


def logger_setup(debug: bool) -> logging.Logger:
    """setup logger"""
    log_mode = logging.DEBUG if debug else logging.INFO
    log_format = "%(module)s: %(message)s" if debug else "%(message)s"

    mylogger = logging.getLogger("dkb_robo")
    mylogger.setLevel(log_mode)

    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Keep setup idempotent: update existing stream handlers, otherwise add one.
    stream_handlers = [
        handler
        for handler in mylogger.handlers
        if isinstance(handler, logging.StreamHandler)
    ]
    if stream_handlers:
        for handler in stream_handlers:
            handler.setLevel(log_mode)
            handler.setFormatter(formatter)
    else:
        handler = logging.StreamHandler()
        handler.setLevel(log_mode)
        handler.setFormatter(formatter)
        mylogger.addHandler(handler)

    return mylogger


def validate_dates(date_from: str, date_to: str) -> Tuple[str, str]:
    """correct dates if needed"""
    logger.debug("validate_dates()")

    def _parse_date(value: str) -> date:
        for date_format in (LEGACY_DATE_FORMAT, API_DATE_FORMAT):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        raise DKBRoboError(
            f"invalid date '{value}'; expected formats: {LEGACY_DATE_FORMAT} or {API_DATE_FORMAT}"
        )

    date_from_obj = _parse_date(date_from)
    date_to_obj = _parse_date(date_to)
    now_date = datetime.fromtimestamp(int(time.time()), timezone.utc).date()
    minimal_date = datetime(2022, 1, 1, tzinfo=timezone.utc).date()

    # adjust valid_from to valid_to
    if date_to_obj <= date_from_obj:
        logger.info("validate_dates(): adjust date_from to date_to")
        date_from_obj = date_to_obj

    if date_from_obj < minimal_date:
        logger.info(
            "validate_dates(): adjust date_from to %s",
            minimal_date.strftime(API_DATE_FORMAT),
        )
        date_from_obj = minimal_date
    if date_to_obj < minimal_date:
        logger.info(
            "validate_dates(): adjust date_to to %s",
            minimal_date.strftime(API_DATE_FORMAT),
        )
        date_to_obj = minimal_date

    if date_from_obj > now_date:
        logger.info(
            "validate_dates(): adjust date_from to %s",
            now_date.strftime(API_DATE_FORMAT),
        )
        date_from_obj = now_date
    if date_to_obj > now_date:
        logger.info(
            "validate_dates(): adjust date_to to %s",
            now_date.strftime(API_DATE_FORMAT),
        )
        date_to_obj = now_date

    date_from = date_from_obj.strftime(API_DATE_FORMAT)
    date_to = date_to_obj.strftime(API_DATE_FORMAT)

    logger.debug("validate_dates() returned: %s, %s", date_from, date_to)
    return date_from, date_to


def ulal(mapclass, parameter):
    """map parameter"""
    if not parameter:
        return None
    if not isinstance(parameter, dict):
        logger.debug(
            "ulal(%s): skip non-dict parameter of type %s",
            getattr(mapclass, "__name__", str(mapclass)),
            type(parameter).__name__,
        )
        return None
    try:
        return mapclass(**parameter)
    except TypeError as err:
        raise DKBRoboError(
            f"ulal: cannot map parameter to {getattr(mapclass, '__name__', str(mapclass))}: {err}"
        ) from err
    return None


def _object2dictionary_input(obj: Any) -> Optional[Dict[str, Any]]:
    """Normalize supported input types for object2dictionary."""
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return obj

    logger.debug("object2dictionary(): unsupported input type %s", type(obj).__name__)
    return None


def _object2dictionary_convert_value(value: Any, key_lc: bool) -> Any:
    """Recursively convert nested values to serializable dict/list structures."""
    if is_dataclass(value):
        return object2dictionary(value, key_lc=key_lc)
    if isinstance(value, dict):
        return {
            (sub_key.lower() if key_lc else sub_key): _object2dictionary_convert_value(
                sub_value, key_lc
            )
            for sub_key, sub_value in value.items()
        }
    if isinstance(value, list):
        return [_object2dictionary_convert_value(item, key_lc) for item in value]
    return value


def object2dictionary(obj, key_lc: bool = False, skip_list: Optional[List[str]] = None):
    """convert dataclass-like object to dict"""

    raw = _object2dictionary_input(obj)
    if raw is None:
        return {}

    skip_keys = set(skip_list) if isinstance(skip_list, list) else set()
    output_dict: Dict[str, Any] = {}
    for key, value in raw.items():
        if key in skip_keys:
            continue
        target_key = key.lower() if key_lc else key
        output_dict[target_key] = _object2dictionary_convert_value(value, key_lc)
    return output_dict
