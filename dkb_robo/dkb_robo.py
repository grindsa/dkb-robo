# pylint: disable=c0415, r0913
""" dkb internet banking automation library """
# -*- coding: utf-8 -*-
from pathlib import Path
import time
from dkb_robo.postbox import PostBox
from dkb_robo.standingorder import StandingOrder
from dkb_robo.transaction import Transaction
from dkb_robo.utilities import logger_setup, validate_dates, get_dateformat
from dkb_robo.api import Wrapper

LEGACY_DATE_FORMAT, API_DATE_FORMAT = get_dateformat()


class DKBRoboError(Exception):
    """ dkb-robo exception class """


class DKBRobo(object):
    """ dkb_robo class """
    # pylint: disable=R0904
    legacy_login = False
    dkb_user = None
    dkb_password = None
    proxies = {}
    last_login = None
    mfa_device = 0
    account_dic = {}
    tan_insert = False
    chip_tan = False
    logger = None
    wrapper = None

    def __init__(self, dkb_user=None, dkb_password=None, tan_insert=False, legacy_login=False, debug=False, mfa_device=None, chip_tan=False):
        self.dkb_user = dkb_user
        self.dkb_password = dkb_password
        self.chip_tan = chip_tan
        self.tan_insert = tan_insert
        self.legacy_login = legacy_login
        self.logger = logger_setup(debug)
        self.mfa_device = mfa_device

    def __enter__(self):
        """ Makes DKBRobo a Context Manager """
        # tan usage requires legacy login
        if self.tan_insert:
            self.logger.info('tan_insert is a legacy login option and will be disabled soon. Please use chip_tan instead')
            self.chip_tan = True

        if self.legacy_login:
            raise DKBRoboError('Legacy Login got deprecated. Please do not use this option anymore')

        if self.mfa_device == 'm':
            self.mfa_device = 1

        self.wrapper = Wrapper(dkb_user=self.dkb_user, dkb_password=self.dkb_password, proxies=self.proxies, chip_tan=self.chip_tan, mfa_device=self.mfa_device, logger=self.logger)

        # login and get the account overview
        (self.account_dic, self.last_login) = self.wrapper.login()

        return self

    def __exit__(self, *args):
        """ Close the connection at the end of the context """
        self.wrapper.logout()

    def get_credit_limits(self):
        """ create a dictionary of credit limits of the different accounts """
        self.logger.debug('DKBRobo.get_credit_limits()\n')
        return self.wrapper.get_credit_limits()

    def get_exemption_order(self):
        """ get get_exemption_order """
        self.logger.debug('DKBRobo.get_exemption_order()\n')
        return self.wrapper.get_exemption_order()

    def get_points(self):
        """ returns the DKB points """
        self.logger.debug('DKBRobo.get_points()\n')
        raise DKBRoboError('Method not supported...')

    def get_standing_orders(self, uid=None):
        """ get standing orders """
        self.logger.debug('DKBRobo.get_standing_orders()\n')
        standingorder = StandingOrder(client=self.wrapper.client, logger=self.logger)
        return standingorder.fetch(uid)

    def get_transactions(self, transaction_url, atype, date_from, date_to, transaction_type='booked'):
        """ exported method to get transactions """
        self.logger.debug('DKBRobo.get_transactions(%s/%s: %s/%s)\n', transaction_url, atype, date_from, date_to)

        (date_from, date_to) = validate_dates(self.logger, date_from, date_to)
        transaction = Transaction(client=self.wrapper.client, logger=self.logger)
        transaction_list = transaction.get(transaction_url, atype, date_from, date_to, transaction_type)

        self.logger.debug('DKBRobo.get_transactions(): %s transactions returned\n', len(transaction_list))
        return transaction_list

    def scan_postbox(self, path=None, download_all=False, archive=False, prepend_date=False):
        """ scan posbox and return document dictionary """
        self.logger.debug('DKBRobo.scan_postbox()\n')
        return self.download(Path(path) if path is not None else None, download_all, prepend_date)

    def download(self, path: Path, download_all: bool, prepend_date: bool = False, mark_read: bool = True, use_account_folders: bool = False, list_only: bool = False):
        """ download postbox documents """
        if path is None:
            list_only = True
        postbox = PostBox(client=self.wrapper.client, logger=self.logger)
        documents = postbox.fetch_items()

        if not download_all:
            # only unread documents
            documents = {id: item for id, item in documents.items()
                         if item.message and item.message.read is False}

        accounts_by_id = {acc['id']: acc['account'] for acc in self.wrapper.account_dic.values()}
        for doc in documents.values():
            target = path / doc.category()

            if use_account_folders:
                target = target / doc.account(card_lookup=accounts_by_id)

            filename = f"{doc.date()}_{doc.filename()}" if prepend_date else doc.filename()

            if not list_only:
                self.logger.info("Downloading %s to %s...", doc.subject(), target)
                if doc.download(self.wrapper.client, target / filename):
                    if mark_read:
                        doc.mark_read(self.wrapper.client, True)
                    time.sleep(.5)
                else:
                    self.logger.info("File already exists. Skipping %s.", filename)
        return documents
