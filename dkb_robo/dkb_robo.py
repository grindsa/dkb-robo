# pylint: disable=c0415, r0913
""" dkb internet banking automation library """
# -*- coding: utf-8 -*-
from pathlib import Path
import time
from dkb_robo.postbox import PostBox
from dkb_robo.authentication import Authentication
from dkb_robo.exemptionorder import ExemptionOrders
from dkb_robo.standingorder import StandingOrders
from dkb_robo.transaction import Transactions
from dkb_robo.utilities import logger_setup, validate_dates, get_dateformat


LEGACY_DATE_FORMAT, API_DATE_FORMAT = get_dateformat()


class DKBRoboError(Exception):
    """dkb-robo exception class"""


class DKBRobo(object):
    """dkb_robo class"""

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
    unfiltered = False

    def __init__(
        self,
        dkb_user=None,
        dkb_password=None,
        tan_insert=False,
        legacy_login=False,
        debug=False,
        mfa_device=None,
        chip_tan=False,
        unfiltered=False,
    ):
        self.dkb_user = dkb_user
        self.dkb_password = dkb_password
        self.chip_tan = chip_tan
        self.tan_insert = tan_insert
        self.legacy_login = legacy_login
        self.logger = logger_setup(debug)
        self.mfa_device = mfa_device
        self.unfiltered = unfiltered

    def __enter__(self):
        """Makes DKBRobo a Context Manager"""
        # tan usage requires legacy login
        if self.tan_insert:
            self.logger.info(
                "tan_insert is a legacy login option and will be disabled soon. Please use chip_tan instead"
            )
            self.chip_tan = True

        if self.legacy_login:
            raise DKBRoboError(
                "Legacy Login got deprecated. Please do not use this option anymore"
            )

        if self.mfa_device == "m":
            self.mfa_device = 1

        self.wrapper = Authentication(
            dkb_user=self.dkb_user,
            dkb_password=self.dkb_password,
            proxies=self.proxies,
            chip_tan=self.chip_tan,
            mfa_device=self.mfa_device,
            unfiltered=self.unfiltered,
        )

        # login and get the account overview
        (self.account_dic, self.last_login) = self.wrapper.login()

        return self

    def __exit__(self, *args):
        """Close the connection at the end of the context"""
        self.wrapper.logout()

    def _accounts_by_id(self):
        self.logger.debug("DKBRobo._accounts_by_id()\n")

        if self.unfiltered:
            accounts_by_id = {}
            for acc in self.wrapper.account_dic.values():
                uid = getattr(acc, "id", None)
                if getattr(acc, "iban", None):
                    accounts_by_id[uid] = acc.iban
                elif getattr(acc, "maskedPan", None):
                    accounts_by_id[uid] = acc.maskedPan
                elif getattr(acc, "depositAccountId", None):
                    accounts_by_id[uid] = acc.depositAccountId
        else:
            accounts_by_id = {
                acc["id"]: acc["account"] for acc in self.wrapper.account_dic.values()
            }

        self.logger.debug(
            "DKBRobo._accounts_by_id(): returned %s elements\n",
            len(accounts_by_id.keys()),
        )
        return accounts_by_id

    def get_credit_limits(self):
        """create a dictionary of credit limits of the different accounts"""
        self.logger.debug("DKBRobo.get_credit_limits()\n")

        limit_dic = {}
        for _aid, account_data in self.account_dic.items():
            if "limit" in account_data:
                if "iban" in account_data:
                    limit_dic[account_data["iban"]] = account_data["limit"]
                elif "maskedpan" in account_data:
                    limit_dic[account_data["maskedpan"]] = account_data["limit"]

        return limit_dic

    def get_exemption_order(self):
        """get get_exemption_order"""
        self.logger.debug("DKBRobo.get_exemption_order()\n")
        exemptionorder = ExemptionOrders(
            client=self.wrapper.client, unfiltered=self.unfiltered
        )
        return exemptionorder.fetch()

    def get_points(self):
        """returns the DKB points"""
        self.logger.debug("DKBRobo.get_points()\n")
        raise DKBRoboError("Method not supported...")

    def get_standing_orders(self, uid=None):
        """get standing orders"""
        self.logger.debug("DKBRobo.get_standing_orders()\n")
        standingorder = StandingOrders(
            client=self.wrapper.client, unfiltered=self.unfiltered
        )
        return standingorder.fetch(uid)

    def get_transactions(
        self, transaction_url, atype, date_from, date_to, transaction_type="booked"
    ):
        """exported method to get transactions"""
        self.logger.debug(
            "DKBRobo.get_transactions(%s/%s: %s/%s)\n",
            transaction_url,
            atype,
            date_from,
            date_to,
        )

        (date_from, date_to) = validate_dates(date_from, date_to)
        transaction = Transactions(
            client=self.wrapper.client, unfiltered=self.unfiltered
        )
        transaction_list = transaction.get(
            transaction_url, atype, date_from, date_to, transaction_type
        )

        self.logger.debug(
            "DKBRobo.get_transactions(): %s transactions returned\n",
            len(transaction_list),
        )
        return transaction_list

    def scan_postbox(
        self, path=None, download_all=False, _archive=False, prepend_date=False
    ):
        """scan posbox and return document dictionary"""
        self.logger.debug("DKBRobo.scan_postbox()\n")
        return self.download(
            Path(path) if path is not None else None, download_all, prepend_date
        )

    def download_doc(
        self,
        path: Path,
        doc,
        prepend_date: bool = False,
        mark_read: bool = True,
        use_account_folders: bool = False,
        list_only: bool = False,
        accounts_by_id: dict = None,
    ):
        """download a single document"""
        target = path / doc.category()

        if use_account_folders:
            target = target / doc.account(card_lookup=accounts_by_id)

        filename = f"{doc.date()}_{doc.filename()}" if prepend_date else doc.filename()

        if not list_only:
            self.logger.info('Downloading "%s" to %s...', doc.subject(), target)

            download_rcode = doc.download(self.wrapper.client, target / filename)
            if download_rcode:
                if mark_read:
                    doc.mark_read(self.wrapper.client, True)
                time.sleep(0.5)
                doc.rcode = download_rcode
            else:
                self.logger.info("File already exists. Skipping %s.", filename)
                doc.rcode = "skipped"

    def format_doc(
        self,
        path,
        documents,
        use_account_folders: bool = False,
        prepend_date: bool = False,
        accounts_by_id: dict = None,
    ):
        """format documents"""

        document_dic = {}
        for doc in documents.values():
            category = doc.category()

            if category not in document_dic:
                document_dic[category] = {"documents": {}, "count": 0}

            target = path / category
            if use_account_folders:
                target = target / doc.account(card_lookup=accounts_by_id)
            filename = (
                f"{doc.date()}_{doc.filename()}" if prepend_date else doc.filename()
            )

            document_dic[category]["documents"][doc.message.subject] = {
                "id": doc.id,
                "date": doc.document.creationDate,
                "link": doc.document.link,
                "fname": str(target / filename),
                "rcode": doc.rcode,
            }
            document_dic[category]["count"] += 1
        return document_dic

    def download(
        self,
        path: Path,
        download_all: bool,
        prepend_date: bool = False,
        mark_read: bool = True,
        use_account_folders: bool = False,
        list_only: bool = False,
    ):
        """download postbox documents"""
        if path is None:
            list_only = True
        postbox = PostBox(client=self.wrapper.client)
        documents = postbox.fetch_items()
        if not download_all:
            # only unread documents
            documents = {
                id: item
                for id, item in documents.items()
                if item.message and item.message.read is False
            }

        # create dictionary to map accounts to their respective iban/maskedpan
        accounts_by_id = self._accounts_by_id()
        if not list_only:
            # download the documents if required
            for doc in documents.values():
                self.download_doc(
                    path=path,
                    doc=doc,
                    prepend_date=prepend_date,
                    mark_read=mark_read,
                    use_account_folders=use_account_folders,
                    list_only=list_only,
                    accounts_by_id=accounts_by_id,
                )

        # format the documents
        if not self.unfiltered:
            documents = self.format_doc(
                path=path,
                documents=documents,
                use_account_folders=use_account_folders,
                prepend_date=prepend_date,
                accounts_by_id=accounts_by_id,
            )

        return documents
