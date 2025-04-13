""" Module for handling dkb transactions """
# pylint: disable=c0415, r0913, c0103
import datetime
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging
import requests
from dkb_robo.utilities import (
    Account,
    Amount,
    PerformanceValue,
    get_dateformat,
    filter_unexpected_fields,
    ulal,
)


LEGACY_DATE_FORMAT, API_DATE_FORMAT = get_dateformat()
logger = logging.getLogger(__name__)


class Transactions:
    """Transactions class"""

    def __init__(
        self,
        client: requests.Session,
        unfiltered: bool = False,
        base_url: str = "https://banking.dkb.de/api",
    ):
        self.client = client
        self.base_url = base_url
        self.uid = None
        self.unfiltered = unfiltered

    def _correlate(self, transaction_dic: Dict[str, str]) -> List[Dict[str, str]]:
        """correlate transactions"""
        logger.debug("Transactions._correlate()\n")

        if "included" in transaction_dic:
            included_list = transaction_dic["included"]
        else:
            included_list = []

        position_list = []
        if "data" in transaction_dic:
            for position in transaction_dic["data"]:
                position_dic = self._map(position, included_list)
                if position_dic:
                    position_list.append(position_dic)

        logger.debug(
            "Transactions._correlate() ended with %s entries\n", len(position_list)
        )
        return position_list

    def _fetch(self, transaction_url: str) -> Dict[str, str]:
        """get transaction list"""
        logger.debug("Transactions.fetch(%s)\n", transaction_url)

        transaction_dic = {"data": [], "included": []}
        while transaction_url:
            response = self.client.get(transaction_url)
            if response.status_code == 200:
                _transaction_dic = response.json()
                if "data" in _transaction_dic:
                    transaction_dic["data"].extend(_transaction_dic["data"])
                    transaction_url = self._nextpage_url(
                        _transaction_dic
                    )  # get next page
                else:
                    logger.debug("fetch transactions: no data in response")
                    transaction_url = None

                if "included" in _transaction_dic:
                    transaction_dic["included"].extend(_transaction_dic["included"])
            else:
                logger.error(
                    "fetch transactions: http status code is not 200 but %s",
                    response.status_code,
                )
                break

        logger.debug(
            "Transactions.fetch() ended with %s entries\n", len(transaction_dic["data"])
        )
        return transaction_dic

    def _filter(
        self,
        transaction_list: List[Dict[str, str]],
        date_from: str,
        date_to: str,
        transaction_type: str,
    ) -> List[Dict[str, str]]:
        """filter transactions"""
        logger.debug("Transactions._filter()\n")

        # support transation type 'reserved' for backwards compatibility
        transaction_type = (
            "pending" if transaction_type == "reserved" else transaction_type
        )

        try:
            date_from_uts = int(
                time.mktime(
                    datetime.datetime.strptime(
                        date_from, LEGACY_DATE_FORMAT
                    ).timetuple()
                )
            )
        except ValueError:
            date_from_uts = int(
                time.mktime(
                    datetime.datetime.strptime(date_from, API_DATE_FORMAT).timetuple()
                )
            )

        try:
            date_to_uts = int(
                time.mktime(
                    datetime.datetime.strptime(date_to, LEGACY_DATE_FORMAT).timetuple()
                )
            )
        except ValueError:
            date_to_uts = int(
                time.mktime(
                    datetime.datetime.strptime(date_to, API_DATE_FORMAT).timetuple()
                )
            )

        filtered_transaction_list = []
        for transaction in transaction_list:
            if (
                "attributes" in transaction
                and "status" in transaction["attributes"]
                and "bookingDate" in transaction["attributes"]
            ):
                if transaction["attributes"]["status"] == transaction_type:
                    bookingdate_uts = int(
                        time.mktime(
                            datetime.datetime.strptime(
                                transaction["attributes"]["bookingDate"],
                                API_DATE_FORMAT,
                            ).timetuple()
                        )
                    )
                    if date_from_uts <= bookingdate_uts <= date_to_uts:
                        filtered_transaction_list.append(transaction)

        logger.debug(
            "Transactions._filter() ended with %s entries\n",
            len(filtered_transaction_list),
        )
        return filtered_transaction_list

    def _format(
        self, raw_transaction_list: List[Dict[str, str]], atype: str
    ) -> List[Dict[str, str]]:
        """format transaction list"""
        logger.debug("Transactions._format()\n")

        mapping_dic = {
            "account": "AccountTransactionItem",
            "creditcard": "CreditCardTransactionItem",
            "creditCard": "CreditCardTransactionItem",
            "brokerageAccount": "DepotTransactionItem",
            "depot": "DepotTransactionItem",
        }

        transaction_list = []
        if raw_transaction_list:
            for ele in raw_transaction_list:
                if "attributes" not in ele or "id" not in ele:
                    continue
                # add id to attributes tree
                ele["attributes"]["id"] = ele["id"]
                transaction = globals()[mapping_dic[atype]](**ele["attributes"])
                if self.unfiltered:
                    transaction_list.append(transaction)
                else:
                    transaction_list.append(transaction.format())

        logger.debug(
            "Transactions._format() ended with %s entries\n", len(transaction_list)
        )
        return transaction_list

    def _map(self, position: Dict[str, str], included_list: List[Dict[str, str]]):
        """add details from depot transaction"""
        logger.debug("DepotTransaction._map()\n")

        instrument_id = (
            position.get("relationships", {})
            .get("instrument", {})
            .get("data", {})
            .get("id", None)
        )
        quote_id = (
            position.get("relationships", {})
            .get("quote", {})
            .get("data", {})
            .get("id", None)
        )
        for ele in included_list:
            if "id" in ele and ele["id"] == instrument_id:
                position["attributes"]["instrument"] = ele["attributes"]
                position["attributes"]["instrument"]["id"] = ele["id"]
            if "id" in ele and ele["id"] == quote_id:
                position["attributes"]["quote"] = ele["attributes"]
                position["attributes"]["quote"]["id"] = ele["id"]

        logger.debug("DepotTransaction._map() ended\n")
        return position

    def _nextpage_url(self, tr_dic):
        """get transaction url"""
        logger.debug("Transactions._nextpage_url()\n")

        transaction_url = None
        if "links" in tr_dic and "next" in tr_dic["links"]:
            logger.debug(
                "Transactions._nextpage_url(): next page: %s", tr_dic["links"]["next"]
            )
            transaction_url = self.base_url + "/accounts" + tr_dic["links"]["next"]
        else:
            logger.debug("Transactions._nextpage_url(): no next page")
            transaction_url = None

        logger.debug("Transactions._nextpage_url() ended\n")
        return transaction_url

    def get(
        self,
        transaction_url: str,
        atype: str,
        date_from: str,
        date_to: str,
        transaction_type: str = "booked",
    ):
        """fetch transactions"""
        logger.debug("Transactions.get()\n")

        if transaction_url:
            if atype == "account":
                logger.info("fetching account transactions")
                transaction_url = (
                    transaction_url
                    + "?filter[bookingDate][GE]="
                    + date_from
                    + "&filter[bookingDate][LE]="
                    + date_to
                    + "&expand=Merchant&page[size]=400"
                )
            elif atype in ["creditcard", "creditCard"]:
                logger.info("fetching card transactions")
                transaction_url = (
                    transaction_url
                    + "&filter[date][GE]="
                    + date_from
                    + "&filter[date][LE]="
                    + date_to
                    + "&expand=Merchant&page[size]=400"
                )
        transaction_dic = self._fetch(transaction_url)

        if atype in ["account", "creditcard", "creditCard"]:
            raw_transaction_list = self._filter(
                transaction_list=transaction_dic["data"],
                date_from=date_from,
                date_to=date_to,
                transaction_type=transaction_type,
            )
        else:
            raw_transaction_list = self._correlate(transaction_dic)

        # format output
        transaction_list = self._format(raw_transaction_list, atype)

        logger.debug("Transactions.get() ended\n")
        return transaction_list


@filter_unexpected_fields
@dataclass
class AccountTransactionItem:
    """dataclass for a single AccountTransaction"""

    status: Optional[str] = None
    bookingDate: Optional[str] = None
    valueDate: Optional[str] = None
    description: Optional[str] = None
    mandateId: Optional[str] = None
    endToEndId: Optional[str] = None
    transactionType: Optional[str] = None
    purposeCode: Optional[str] = None
    businessTransactionCode: Optional[str] = None
    amount: Optional[Dict] = None
    creditor: Optional[Union[Dict, str]] = None
    debtor: Optional[Union[Dict, str]] = None
    isRevocable: bool = False

    def __post_init__(self):
        self.amount = ulal(Amount, self.amount)
        # regroup creditor information allowing simpler access
        self.creditor = ulal(
            Account, self._peer_information(self.creditor, "creditorAccount")
        )
        # regroup debtor for the same reason
        self.debtor = ulal(
            Account, self._peer_information(self.debtor, "debtorAccount")
        )
        if self.description:
            self.description = " ".join(self.description.split())

    def _peer_information(
        self, peer_dic: Dict[str, str], peer_type: str = None
    ) -> Dict[str, str]:
        """add peer information"""
        logger.debug("AccountTransaction._peer_information(%s)\n", peer_type)

        peer_dic[peer_type]["bic"] = peer_dic.get("agent", {}).get("bic", None)
        peer_dic[peer_type]["id"] = peer_dic.get("id", None)

        try:
            peer_dic[peer_type]["name"] = " ".join(peer_dic.pop("name", None).split())
        except Exception:
            peer_dic[peer_type]["name"] = peer_dic.pop("name", None)

        if peer_dic.get("intermediaryName", None):
            peer_dic[peer_type]["intermediaryName"] = " ".join(
                peer_dic.get("intermediaryName", None).split()
            )

        logger.debug("AccountTransaction._peer_information() ended\n")
        return peer_dic[peer_type]

    def format(self):
        """format format transaction list ot a useful output"""
        logger.debug("AccountTransaction.format()\n")

        transaction_dic = {
            "amount": self.amount.value,
            "currencycode": self.amount.currencyCode,
            "date": self.bookingDate,
            # for backwards compatibility
            "bdate": self.bookingDate,
            "vdate": self.valueDate,
            "customerreference": self.endToEndId,
            "mandatereference": self.mandateId,
            "postingtext": self.transactionType,
            "reasonforpayment": self.description,
        }

        if self.amount.value > 0:
            # incoming transaction
            transaction_dic["peeraccount"] = self.debtor.iban
            transaction_dic["peerbic"] = self.debtor.bic
            transaction_dic["peerid"] = self.debtor.id
            if self.debtor.intermediaryName:
                transaction_dic["peer"] = self.debtor.intermediaryName
            else:
                transaction_dic["peer"] = self.debtor.name
        else:
            # outgoing transaction
            transaction_dic["peeraccount"] = self.creditor.iban
            transaction_dic["peerbic"] = self.creditor.bic
            transaction_dic["peerid"] = self.creditor.id
            if (
                self.creditor.intermediaryName
                and self.description.lower() != "visa debitkartenumsatz"
            ):
                transaction_dic["peer"] = self.creditor.intermediaryName
            else:
                transaction_dic["peer"] = self.creditor.name

        # this is for backwards compatibility
        transaction_dic[
            "text"
        ] = f"{transaction_dic['postingtext']} {transaction_dic['peer']} {transaction_dic['reasonforpayment']}"

        logger.debug("AccountTransaction.format() ended\n")
        return transaction_dic


@filter_unexpected_fields
@dataclass
class CreditCardTransactionItem:
    """dataclass for a single CreditCardTransaction"""

    amount: Optional[Dict] = None
    id: Optional[str] = None
    authorizationDate: Optional[str] = None
    bonuses: Optional[List] = None
    bookingDate: Optional[str] = None
    cardId: Optional[str] = None
    description: Optional[str] = None
    merchantAmount: Optional[Dict] = None
    merchantCategory: Optional[Dict] = field(default_factory=dict)
    status: Optional[str] = None
    transactionType: Optional[str] = None

    def __post_init__(self):
        self.amount = ulal(Amount, self.amount)
        self.merchantAmount = ulal(Amount, self.merchantAmount)
        self.merchantCategory = ulal(self.MerchantCategory, self.merchantCategory)

    @filter_unexpected_fields
    @dataclass
    class MerchantCategory:
        """dataclass for a single merchantCategory"""

        code: Optional[str] = None

    def format(self):
        """format format transaction list ot a useful output"""
        logger.debug("CreditCardTransaction.format()\n")

        transaction_dic = {
            # fixing strange behaviour of DKB API
            "amount": self.amount.value,  # * -1,
            "bdate": self.bookingDate,
            "currencycode": self.amount.currencyCode,
            "text": self.description,
            "vdate": self.authorizationDate,
        }

        logger.debug("CreditCardTransaction.format() ended\n")
        return transaction_dic


@filter_unexpected_fields
@dataclass
class DepotTransactionItem:
    """DepotTransaction class"""

    id: Optional[str] = None
    availableQuantity: Optional[Union[Dict, str]] = None
    custody: Optional[Union[Dict, str]] = None
    instrument: Optional[Union[Dict, str]] = None
    lastOrderDate: Optional[str] = None
    performance: Optional[Union[Dict, str]] = None
    quantity: Optional[Union[Dict, str]] = None
    quote: Optional[Union[Dict, str]] = None

    def __post_init__(self):
        self.availableQuantity = ulal(self.Quantity, self.availableQuantity)
        self.custody = ulal(self.Custody, self.custody)
        self.performance = ulal(self.Performance, self.performance)
        self.quantity = ulal(self.Quantity, self.quantity)
        self.instrument = ulal(self.Instrument, self.instrument)
        self.quote = ulal(self.Quote, self.quote)

    @filter_unexpected_fields
    @dataclass
    class Custody:
        """dataclass for custody"""

        block: Optional[Union[Dict, str]] = None
        certificateType: Optional[str] = None
        characteristic: Optional[Union[Dict, str]] = None
        custodyType: Optional[str] = None
        custodyTypeId: Optional[str] = None

        @filter_unexpected_fields
        @dataclass
        class Block:
            """dataclass for block"""

            blockType: Optional[str] = None

        @filter_unexpected_fields
        @dataclass
        class Characteristic:
            """dataclass for characteristic"""

            characteristicType: Optional[str] = None

        def __post_init__(self):
            self.block = ulal(self.Block, self.block)
            self.characteristic = ulal(self.Characteristic, self.characteristic)

    @filter_unexpected_fields
    @dataclass
    class Instrument:
        """dataclass for instrument"""

        id: Optional[str] = None
        identifiers: Optional[List] = field(default_factory=list)
        name: Optional[Union[Dict, str]] = None
        unit: Optional[str] = None

        def __post_init__(self):
            self.name = ulal(self.Name, self.name)
            self.identifiers = [
                self.IdentifierItem(**identifier) for identifier in self.identifiers
            ]

        @filter_unexpected_fields
        @dataclass
        class IdentifierItem:
            """dataclass for identifier"""

            identifier: Optional[str] = None
            value: Optional[str] = None

        @filter_unexpected_fields
        @dataclass
        class Name:
            """dataclass for name"""

            long: Optional[str] = None
            short: Optional[str] = None

    @filter_unexpected_fields
    @dataclass
    class Performance:
        """dataclass for performance"""

        currentValue: Optional[Union[Dict, str]] = None
        isOutdated: Optional[bool] = False

        def __post_init__(self):
            self.currentValue = ulal(PerformanceValue, self.currentValue)

    @filter_unexpected_fields
    @dataclass
    class Quantity:
        """dataclass for quantity"""

        unit: Optional[str] = None
        value: Optional[float] = None

        def __post_init__(self):
            try:
                self.value = float(self.value)
            except Exception:
                self.value = None

    @filter_unexpected_fields
    @dataclass
    class Quote:
        """dataclass for quote"""

        id: Optional[str] = None
        market: Optional[str] = None
        price: Optional[Union[Dict, str]] = None
        timestamp: Optional[str] = None

        def __post_init__(self):
            self.price = ulal(PerformanceValue, self.price)

    def format(self) -> Dict[str, str]:
        """format  transaction list ot a useful output"""
        logger.debug("DepotTransaction.format()\n")

        transaction_dic = {
            "isin_wkn": self.instrument.identifiers[0].value,
            "lastorderdate": self.lastOrderDate,
            "price_euro": self.performance.currentValue.value,
            "quantity": self.quantity.value,
            # for backwards compatibility
            "shares": self.availableQuantity.value,
            "shares_unit": self.quantity.unit,
            "text": self.instrument.name.short,
            "text_long": self.instrument.name.long,
        }

        if self.quote:
            transaction_dic["currencyCode"] = self.quote.price.currencyCode
            transaction_dic["market"] = self.quote.market
            transaction_dic["price"] = self.quote.price.value

        return transaction_dic
