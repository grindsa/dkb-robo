"""Module for handling dkb transactions"""

# pylint: disable=c0415, r0913, c0103
import datetime
from typing import Any, Dict, List, Optional, Union, Type
from dataclasses import dataclass, field
import logging
import requests
from dkb_robo.utilities import (
    Account,
    Amount,
    DKBRoboError,
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
        timeout: float = 10.0,
    ):
        self.client = client
        self.base_url = base_url
        self.uid = None
        self.unfiltered = unfiltered
        self.timeout = timeout

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

    def _fetch(self, transaction_url: str) -> Dict[str, Any]:
        """get transaction list"""
        logger.debug("Transactions.fetch(%s)\n", transaction_url)

        transaction_dic = {"data": [], "included": []}
        visited_urls = set()
        while transaction_url:
            if transaction_url in visited_urls:
                raise DKBRoboError(
                    f"fetch transactions: pagination loop detected for url {transaction_url}"
                )
            visited_urls.add(transaction_url)

            try:
                response = self.client.get(transaction_url, timeout=self.timeout)
            except requests.RequestException as err:
                raise DKBRoboError(
                    f"fetch transactions: request failed for {transaction_url}: {err}"
                ) from err

            try:
                response.raise_for_status()
            except requests.HTTPError as err:
                response_text = response.text if response.text else ""
                response_detail = (
                    f"; response={response_text[:200]}" if response_text else ""
                )
                raise DKBRoboError(
                    f"fetch transactions: http status code is {response.status_code}{response_detail}"
                ) from err

            try:
                _transaction_dic = response.json()
            except ValueError as err:
                raise DKBRoboError(
                    f"fetch transactions: invalid json in response for {transaction_url}"
                ) from err

            if not isinstance(_transaction_dic, dict):
                raise DKBRoboError(
                    f"fetch transactions: invalid payload type {type(_transaction_dic).__name__}"
                )

            if "data" in _transaction_dic:
                transaction_dic["data"].extend(_transaction_dic["data"])
                transaction_url = self._nextpage_url(_transaction_dic)  # get next page
            else:
                logger.debug("fetch transactions: no data in response")
                transaction_url = None

            if "included" in _transaction_dic:
                transaction_dic["included"].extend(_transaction_dic["included"])

        logger.debug(
            "Transactions.fetch() ended with %s entries\n", len(transaction_dic["data"])
        )
        return transaction_dic

    def _filter(
        self,
        transaction_list: List[Dict[str, Any]],
        date_from: str,
        date_to: str,
        transaction_type: str,
    ) -> List[Dict[str, Any]]:
        """filter transactions"""
        logger.debug("Transactions._filter()\n")

        def _parse_date(value: str) -> datetime.date:
            for date_format in (LEGACY_DATE_FORMAT, API_DATE_FORMAT):
                try:
                    return datetime.datetime.strptime(value, date_format).date()
                except ValueError:
                    continue
            raise DKBRoboError(
                f"filter transactions: invalid date '{value}'; expected formats {LEGACY_DATE_FORMAT} or {API_DATE_FORMAT}"
            )

        # support transation type 'reserved' for backwards compatibility
        transaction_type = (
            "pending" if transaction_type == "reserved" else transaction_type
        )

        date_from_obj = _parse_date(date_from)
        date_to_obj = _parse_date(date_to)

        filtered_transaction_list = []
        for transaction in transaction_list:
            attributes = transaction.get("attributes", {})
            if not isinstance(attributes, dict):
                continue
            if attributes.get("status") != transaction_type:
                continue
            booking_date = attributes.get("bookingDate")
            if not booking_date:
                continue

            try:
                booking_date_obj = datetime.datetime.strptime(
                    booking_date, API_DATE_FORMAT
                ).date()
            except ValueError:
                logger.debug("Transactions._filter(): skip invalid bookingDate %s", booking_date)
                continue

            if date_from_obj <= booking_date_obj <= date_to_obj:
                filtered_transaction_list.append(transaction)

        logger.debug(
            "Transactions._filter() ended with %s entries\n",
            len(filtered_transaction_list),
        )
        return filtered_transaction_list

    def _format(
        self, raw_transaction_list: List[Dict[str, Any]], atype: str
    ) -> List[Dict[str, Any]]:
        """format transaction list"""
        logger.debug("Transactions._format()\n")

        mapping_dic: Dict[str, Type] = {
            "account": AccountTransactionItem,
            "creditcard": CreditCardTransactionItem,
            "creditCard": CreditCardTransactionItem,
            "brokerageAccount": DepotTransactionItem,
            "depot": DepotTransactionItem,
        }

        if atype not in mapping_dic:
            allowed_types = ", ".join(sorted(mapping_dic.keys()))
            raise DKBRoboError(
                f"format transactions: unsupported account type '{atype}'. Allowed: {allowed_types}"
            )

        mapping_cls = mapping_dic[atype]

        transaction_list = []
        if raw_transaction_list:
            for ele in raw_transaction_list:
                if "attributes" not in ele or "id" not in ele:
                    continue
                attributes = ele.get("attributes", {})
                if not isinstance(attributes, dict):
                    continue
                transaction_data = {**attributes, "id": ele["id"]}
                transaction = mapping_cls(**transaction_data)
                if self.unfiltered:
                    transaction_list.append(transaction)
                else:
                    transaction_list.append(transaction.format())

        logger.debug(
            "Transactions._format() ended with %s entries\n", len(transaction_list)
        )
        return transaction_list

    def _map(self, position: Dict[str, Any], included_list: List[Dict[str, Any]]):
        """add details from depot transaction"""
        logger.debug("DepotTransaction._map()\n")

        if not isinstance(position, dict):
            logger.debug("DepotTransaction._map(): skip non-dict position")
            return None

        mapped_position = {**position}
        attributes = mapped_position.get("attributes", {})
        if not isinstance(attributes, dict):
            attributes = {}
        mapped_attributes = {**attributes}
        mapped_position["attributes"] = mapped_attributes

        instrument_id = (
            mapped_position.get("relationships", {})
            .get("instrument", {})
            .get("data", {})
            .get("id", None)
        )
        quote_id = (
            mapped_position.get("relationships", {})
            .get("quote", {})
            .get("data", {})
            .get("id", None)
        )
        for ele in included_list:
            if not isinstance(ele, dict):
                continue
            if "id" in ele and ele["id"] == instrument_id and isinstance(
                ele.get("attributes"), dict
            ):
                mapped_attributes["instrument"] = {**ele["attributes"], "id": ele["id"]}
            if "id" in ele and ele["id"] == quote_id and isinstance(
                ele.get("attributes"), dict
            ):
                mapped_attributes["quote"] = {**ele["attributes"], "id": ele["id"]}

        logger.debug("DepotTransaction._map() ended\n")
        return mapped_position

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

    id: Optional[str] = None
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

        if not isinstance(peer_dic, dict) or not peer_type:
            return {}
        if not isinstance(peer_dic.get(peer_type), dict):
            return {}

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

    def _build_text(self, posting_text: str, peer: Optional[str], reason: str) -> str:
        """Build backwards-compatible text field."""
        return f"{posting_text or ''} {peer or ''} {reason or ''}".strip()

    def _incoming_peer(self) -> Dict[str, Optional[str]]:
        """Peer details for incoming transactions (debtor side)."""
        return {
            "peeraccount": self.debtor.iban if self.debtor else None,
            "peerbic": self.debtor.bic if self.debtor else None,
            "peerid": self.debtor.id if self.debtor else None,
            "peer": (
                self.debtor.intermediaryName
                if self.debtor and self.debtor.intermediaryName
                else (self.debtor.name if self.debtor else None)
            ),
        }

    def _outgoing_peer(self, reason_for_payment: str) -> Dict[str, Optional[str]]:
        """Peer details for outgoing transactions (creditor side)."""
        use_intermediary = (
            self.creditor
            and self.creditor.intermediaryName
            and "visa debitkartenumsatz" not in reason_for_payment.lower()
        )
        return {
            "peeraccount": self.creditor.iban if self.creditor else None,
            "peerbic": self.creditor.bic if self.creditor else None,
            "peerid": self.creditor.id if self.creditor else None,
            "peer": (
                self.creditor.intermediaryName
                if use_intermediary
                else (self.creditor.name if self.creditor else None)
            ),
        }

    def format(self):
        """format format transaction list ot a useful output"""
        logger.debug("AccountTransaction.format()\n")

        amount_value = self.amount.value if self.amount else None
        amount_currency = self.amount.currencyCode if self.amount else None
        reason_for_payment = self.description if self.description else ""
        posting_text = self.transactionType if self.transactionType else ""

        transaction_dic = {
            "amount": amount_value,
            "currencycode": amount_currency,
            "date": self.bookingDate,
            # for backwards compatibility
            "bdate": self.bookingDate,
            "vdate": self.valueDate,
            "customerreference": self.endToEndId,
            "mandatereference": self.mandateId,
            "postingtext": posting_text,
            "reasonforpayment": reason_for_payment,
        }

        if amount_value is not None and amount_value > 0:
            transaction_dic.update(self._incoming_peer())
        else:
            transaction_dic.update(self._outgoing_peer(reason_for_payment))

        # this is for backwards compatibility
        transaction_dic["text"] = self._build_text(
            transaction_dic["postingtext"],
            transaction_dic["peer"],
            transaction_dic["reasonforpayment"],
        )

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
            "amount": self.amount.value if self.amount else None,  # * -1,
            "bdate": self.bookingDate,
            "currencycode": self.amount.currencyCode if self.amount else None,
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
            identifiers = self.identifiers if isinstance(self.identifiers, list) else []
            self.identifiers = [
                self.IdentifierItem(**identifier)
                for identifier in identifiers
                if isinstance(identifier, dict)
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

        identifier_value = None
        if self.instrument and self.instrument.identifiers:
            identifier_value = self.instrument.identifiers[0].value

        performance_value = None
        if self.performance and self.performance.currentValue:
            performance_value = self.performance.currentValue.value

        quantity_value = self.quantity.value if self.quantity else None
        shares_value = self.availableQuantity.value if self.availableQuantity else None
        shares_unit = self.quantity.unit if self.quantity else None
        text_short = self.instrument.name.short if self.instrument and self.instrument.name else None
        text_long = self.instrument.name.long if self.instrument and self.instrument.name else None

        transaction_dic = {
            "isin_wkn": identifier_value,
            "lastorderdate": self.lastOrderDate,
            "price_euro": performance_value,
            "quantity": quantity_value,
            # for backwards compatibility
            "shares": shares_value,
            "shares_unit": shares_unit,
            "text": text_short,
            "text_long": text_long,
        }

        if self.quote and self.quote.price:
            transaction_dic["currencyCode"] = self.quote.price.currencyCode
            transaction_dic["market"] = self.quote.market
            transaction_dic["price"] = self.quote.price.value

        return transaction_dic
