""" Module for handling dkb transactions """
# pylint: disable=c0415, r0913, c0103
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
import logging
import requests
from dkb_robo.utilities import (
    Amount,
    Person,
    get_dateformat,
    filter_unexpected_fields,
    ulal,
    BASE_URL,
)

LEGACY_DATE_FORMAT, API_DATE_FORMAT = get_dateformat()
logger = logging.getLogger(__name__)


class ProductGroup:
    """ProductGroup class"""

    def _uid2names(self, data_ele: Dict[str, str]) -> Dict[str, str]:
        """create a dictionary containing id to product-name mapping"""
        logger.debug("ProductGroup._uid2names()\n")

        product_settings_dic = {}
        portfolio_dic = data_ele.get("attributes", {}).get("productSettings", {})
        for product_data in portfolio_dic.values():
            if isinstance(product_data, dict):
                for uid, product_value in product_data.items():
                    if "name" in product_value:
                        product_settings_dic[uid] = product_value["name"]
            else:
                logger.warning(
                    "uid2name mapping failed. product data are not in dictionary format"
                )

        logger.debug("ProductGroup._uid2names() ended\n")
        return product_settings_dic

    def _group(self, data_ele: Dict[str, str]) -> List[str]:
        """create a list of products per group"""
        logger.debug("ProductGroup._group()\n")

        product_group_list = []
        portfolio_dic = data_ele.get("attributes", {}).get("productGroups", {})
        for product_group in sorted(portfolio_dic.values(), key=lambda x: x["index"]):
            id_dic = {}
            for _id_dic in product_group["products"].values():
                for uid in _id_dic:
                    id_dic[_id_dic[uid]["index"]] = uid
            product_group_list.append(
                {"name": product_group["name"], "product_list": id_dic}
            )

        logger.debug("ProductGroup._group()\n")
        return product_group_list

    def map(
        self, data_ele: Dict[str, str]
    ) -> Tuple[Dict[str, str], Dict[str, str], int]:
        """fetch data"""
        logger.debug("ProductGroup.map()\n")

        # crate uid-name mapping and items per product group needed to sort the productgroup
        return self._uid2names(data_ele), self._group(data_ele)


class Overview:
    """Overview class"""

    def __init__(
        self,
        client: requests.Session,
        unfiltered: bool = False,
        base_url: str = BASE_URL,
    ):
        self.client = client
        self.base_url = base_url
        self.unfiltered = unfiltered

    def _add(
        self,
        data_dic: Dict[str, str],
        product_group: Dict[str, str],
        dic_id: str,
        product_display_dic: Dict[str, str],
    ) -> Dict[str, str]:
        """add product to account_dic"""
        logger.debug("Overview._add()\n")

        # add product data to account_dic
        acc_dic = data_dic[product_group["product_list"][dic_id]]
        # add productgroup name to account_dic
        if self.unfiltered:
            acc_dic.productGroup = product_group["name"]
        else:
            acc_dic["productgroup"] = product_group["name"]

        if product_group["product_list"][dic_id] in product_display_dic:
            logger.debug(
                'Overview._sort(): found displayname "%s" for product %s',
                product_display_dic[product_group["product_list"][dic_id]],
                product_group["product_list"][dic_id],
            )
            # overwrite product name with display name
            if self.unfiltered:
                acc_dic.displayName = product_display_dic[
                    product_group["product_list"][dic_id]
                ]
            else:
                acc_dic["name"] = product_display_dic[
                    product_group["product_list"][dic_id]
                ]

        logger.debug("Overview._add() ended\n")
        return acc_dic

    def _add_remaining(
        self, data_dic: Dict[str, str], account_dic: Dict[str, str], account_cnt: int
    ) -> Dict[str, str]:
        """add remaining products"""
        logger.debug("Overview._add_remaining()\n")

        for product_data in data_dic.values():
            account_dic[account_cnt] = product_data
            if self.unfiltered:
                account_dic[account_cnt].productGroup = None
            else:
                account_dic[account_cnt]["productgroup"] = None
            account_cnt += 1

        logger.debug("Overview._add_remaining() ended\n")
        return account_dic

    def _fetch(self, url_path) -> Dict[str, str]:
        """fetch data via API"""
        logger.debug("Overview._fetch()\n")

        response = self.client.get(self.base_url + url_path)
        if response.status_code == 200:
            response_dic = response.json()
        else:
            logger.error(
                "fetch %s: RC is not 200 but %s", url_path, response.status_code
            )
            response_dic = {}

        logger.debug("Overview._fetch() ended\n")
        return response_dic

    def _sort(self, portfolio_dic: Dict[str, str]) -> Dict[str, str]:
        """format and sort data"""
        logger.debug("Overview._sort()\n")

        account_dic = {}
        account_cnt = 0

        data_dic = self._itemize(portfolio_dic)

        display_settings_dic = portfolio_dic.get("product_display", {}).get("data", {})
        productgroup = ProductGroup()
        for portfolio in display_settings_dic:
            # get id/name mapping and productlist per group
            product_display_dic, product_group_list = productgroup.map(portfolio)
            for product_group in product_group_list:
                # dic_id is a uid of the product
                for dic_id in sorted(product_group["product_list"]):
                    if product_group["product_list"][dic_id] in data_dic:
                        logger.debug(
                            'Overview._sort(): assign productgroup "%s" to product %s',
                            product_group["name"],
                            product_group["product_list"][dic_id],
                        )
                        # add to dictionary
                        account_dic[account_cnt] = self._add(
                            data_dic, product_group, dic_id, product_display_dic
                        )
                        del data_dic[product_group["product_list"][dic_id]]
                        account_cnt += 1

        # add products without productgroup
        account_dic = self._add_remaining(data_dic, account_dic, account_cnt)

        logger.debug("Overview._sort() ended\n")
        return account_dic

    def _itemize(self, portfolio_dic: Dict[str, str]) -> Dict[str, str]:
        """raw data"""
        logger.debug("Overview._itemize()\n")

        product_dic = {}

        product_group_dic = {
            "accounts": "AccountItem",
            "cards": "CardItem",
            "depots": "DepotItem",
        }
        for product_group in sorted(product_group_dic.keys()):
            if (
                product_group in portfolio_dic
                and "data" in portfolio_dic[product_group]
            ):
                for item in portfolio_dic[product_group]["data"]:
                    item["attributes"]["id"] = item.get("id", None)
                    item["attributes"]["type"] = item.get("type", None)
                    product = globals()[product_group_dic[product_group]](
                        **item["attributes"]
                    )

                    if self.unfiltered:
                        product_dic[item["id"]] = product
                    else:
                        product_dic[item["id"]] = product.format()

        logger.debug("Overview._itemize() ended\n")
        return product_dic

    def get(self):
        """Get overview"""
        logger.debug("Overview.get()")

        # we calm the IDS system of DKB with two calls without sense
        # self._fetch('/terms-consent/consent-requests??filter%5Bportfolio%5D=DKB')
        product_display_dic = self._fetch("/config/users/me/product-display-settings")
        if product_display_dic:
            portfolio_dic = {
                "product_display": product_display_dic,
                "accounts": self._fetch("/accounts/accounts"),
                "cards": self._fetch(
                    "/credit-card/cards?filter%5Btype%5D=creditCard&filter%5Bportfolio%5D=dkb&filter%5Btype%5D=debitCard"
                ),
                "depots": self._fetch("/broker/brokerage-accounts"),
                "loans": self._fetch("/loans/loans"),
            }
        else:
            portfolio_dic = {}

        logger.debug("Overview.get() ended\n")
        return self._sort(portfolio_dic)


@filter_unexpected_fields
@dataclass
class AccountItem:
    """Account dataclass"""

    availableBalance: Optional[Union[Dict, str]] = None
    balance: Optional[Union[Dict, str]] = None
    currencyCode: Optional[str] = None
    displayName: Optional[str] = None
    holderName: Optional[str] = None
    id: Optional[str] = None
    iban: Optional[str] = None
    interestRate: Optional[Union[Dict, str]] = None
    interests: Optional[List] = None
    lastAccountStatementDate: Optional[str] = None
    nearTimeBalance: Optional[Union[Dict, str]] = None
    openingDate: Optional[str] = None
    overdraftLimit: Optional[Union[Dict, str]] = None
    permissions: Optional[List] = None
    product: Optional[Dict] = None
    productGroup: Optional[str] = None
    state: Optional[str] = None
    type: Optional[str] = None
    unauthorizedOverdraftInterestRate: Optional[Union[Dict, str]] = None
    updatedAt: Optional[str] = None
    transactions: Optional[str] = None

    def __post_init__(self):
        self.availableBalance = ulal(Amount, self.availableBalance)
        self.balance = ulal(Amount, self.balance)
        self.interests = [self.InterestsItem(**interest) for interest in self.interests]
        self.nearTimeBalance = ulal(Amount, self.nearTimeBalance)
        self.product = ulal(self.Product, self.product)
        self.transactions = BASE_URL + f"/accounts/accounts/{self.id}/transactions"
        try:
            self.overdraftLimit = float(self.overdraftLimit)
        except Exception:
            self.overdraftLimit = None

    @filter_unexpected_fields
    @dataclass
    class InterestsItem:
        """interests class"""

        details: Optional[List] = None
        method: Optional[str] = None
        type: Optional[str] = None

        def __post_init__(self):
            self.details = [self.DetailsItem(**detail) for detail in self.details]

        @filter_unexpected_fields
        @dataclass
        class DetailsItem:
            """details class"""

            condition: Optional[Union[Dict, str]] = None
            interestRate: Optional[float] = None

            def __post_init__(self):
                self.condition = ulal(self.Condition, self.condition)

            @filter_unexpected_fields
            @dataclass
            class Condition:
                """condition class"""

                currency: Optional[str] = None
                maximumAmount: Optional[float] = None
                minimumAmount: Optional[float] = None

                def __post_init__(self):
                    if self.minimumAmount:
                        try:
                            self.minimumAmount = float(self.minimumAmount)
                        except Exception:
                            self.minimumAmount = None
                    if self.maximumAmount:
                        try:
                            self.maximumAmount = float(self.maximumAmount)
                        except Exception:
                            self.maximumAmount = None

    @filter_unexpected_fields
    @dataclass
    class Product:
        """Product class"""

        id: Optional[str] = None
        type: Optional[str] = None
        displayName: Optional[str] = None

    def format(self) -> Dict[str, str]:
        """format account"""
        logger.debug("Account.format()\n")

        output_dic = {
            # for backward compatibility
            "account": self.iban,
            "amount": self.balance.value,
            "currencyCode": self.currencyCode,
            "date": self.updatedAt,
            "holderName": self.holderName,
            "iban": self.iban,
            "id": self.id,
            "limit": self.overdraftLimit,
            "name": self.product.displayName,
            "transactions": self.transactions,
            "type": self.type,
        }

        logger.debug("Account.format() ended\n")
        return output_dic


@filter_unexpected_fields
@dataclass
class CardItem:
    """Card class"""

    activationDate: Optional[str] = None
    authorizedAmount: Optional[Union[Dict, str]] = None
    availableLimit: Optional[Union[Dict, str]] = None
    balance: Optional[Union[Dict, str]] = None
    billingDetails: Optional[Union[Dict, str]] = None
    blockedSince: Optional[str] = None
    creationDate: Optional[str] = None
    engravedLine1: Optional[str] = None
    engravedLine2: Optional[str] = None
    expiryDate: Optional[str] = None
    failedPinAttempts: Optional[int] = None
    followUpCardId: Optional[str] = None
    holder: Optional[Union[Dict, str]] = None
    id: Optional[str] = None
    limit: Optional[Union[Dict, str]] = None
    maskedPan: Optional[str] = None
    network: Optional[str] = None
    owner: Optional[Union[Dict, str]] = None
    product: Optional[Union[Dict, str]] = None
    referenceAccount: Optional[str] = None
    state: Optional[str] = None
    status: Optional[Union[Dict, str]] = None
    type: Optional[str] = None
    transactions: Optional[str] = None

    def __post_init__(self):
        self.balance = ulal(Amount, self.balance)
        self.owner = ulal(Person, self.owner)
        self.availableLimit = ulal(Amount, self.availableLimit)
        self.authorizedAmount = ulal(Amount, self.authorizedAmount)
        self.referenceAccount = ulal(self.Account, self.referenceAccount)
        self.billingDetails = ulal(self.BillingDetails, self.billingDetails)
        self.limit = self.Limit(**self.limit)
        self.product = ulal(self.Product, self.product)
        self.status = ulal(self.Status, self.status)
        self.holder = ulal(self.Holder, self.holder)
        if self.type:
            self.transactions = (
                BASE_URL
                + f"/card-transactions/creditcard-transactions?cardId={self.id}"
            )

    @filter_unexpected_fields
    @dataclass
    class Account:
        """Account class"""

        iban: Optional[str] = None
        bic: Optional[str] = None

    @filter_unexpected_fields
    @dataclass
    class BillingDetails:
        """BillingDetails class"""

        days: Optional[List] = None
        calendarType: Optional[str] = None
        cycle: Optional[str] = None

    @filter_unexpected_fields
    @dataclass
    class Holder:
        """Holder class"""

        person: Optional[Dict] = None

        def __post_init__(self):
            self.person = ulal(Person, self.person)

    @filter_unexpected_fields
    @dataclass
    class Limit:
        """Limit class"""

        value: Optional[float] = None
        currencyCode: Optional[str] = None
        identifier: Optional[str] = None
        categories: Optional[List] = None

        def __post_init__(self):
            if self.value:
                try:
                    self.value = float(self.value)
                except Exception:
                    self.value = None
            if self.categories:
                self.categories = [
                    self.CategoryItem(**category) for category in self.categories
                ]

        @filter_unexpected_fields
        @dataclass
        class CategoryItem:
            """Category class"""

            amount: Optional[float] = None
            name: Optional[str] = None

            def __post_init__(self):
                self.amount = ulal(Amount, self.amount)

    @filter_unexpected_fields
    @dataclass
    class Product:
        """Product class"""

        superProductId: Optional[str] = None
        displayName: Optional[str] = None
        institute: Optional[str] = None
        productType: Optional[str] = None
        ownerType: Optional[str] = None
        id: Optional[str] = None
        type: Optional[str] = None

    @filter_unexpected_fields
    @dataclass
    class Status:
        """Status class"""

        category: Optional[str] = None
        since: Optional[str] = None
        reason: Optional[str] = None
        final: Optional[bool] = None
        limitationsFor: Optional[List] = None

    def format(self) -> Dict[str, str]:
        """format card"""
        logger.debug("Card.format()\n")

        output_dic = {
            "account": self.maskedPan,
            "expirydate": self.expiryDate,
            "holdername:": self.holder.person.firstName
            + " "
            + self.holder.person.lastName,
            "id": self.id,
            "name": self.product.displayName,
            "limit": self.limit.value,
            "maskedpan": self.maskedPan,
            "status": asdict(self.status),
            "type": self.type.lower(),
        }
        if self.type == "creditCard":
            output_dic["transactions"] = self.transactions
            # dkb does some weird stuff with the balance. we need to flip it
            output_dic["amount"] = self.balance.value * -1
            output_dic["currencycode"] = self.balance.currencyCode
            output_dic["date"] = self.balance.date
        else:
            output_dic["transactions"] = None

        logger.debug("Card.format() ended\n")
        return output_dic


@filter_unexpected_fields
@dataclass
class DepotItem:
    """Depot class"""

    brokerageAccountPerformance: Optional[Union[Dict, str]] = None
    depositAccountId: Optional[str] = None
    holder: Optional[Union[Dict, str]] = None
    holderName: Optional[str] = None
    id: Optional[str] = None
    referenceAccounts: Optional[List] = None
    riskClasses: Optional[List] = None
    tradingEnabled: Optional[bool] = None
    type: Optional[str] = None
    transactions: Optional[str] = None

    def __post_init__(self):
        self.brokerageAccountPerformance = ulal(
            self.BrokerageAccountPerformance, self.brokerageAccountPerformance
        )
        self.holder = ulal(Person, self.holder)
        self.referenceAccounts = [
            self.ReferenceAccountItem(**reference_account)
            for reference_account in self.referenceAccounts
        ]
        self.transactions = (
            BASE_URL
            + f"/broker/brokerage-accounts/{self.id}/positions?include=instrument%2Cquote"
        )

    @filter_unexpected_fields
    @dataclass
    class BrokerageAccountPerformance:
        """BrokerageAccountPerformance class"""

        currentValue: Optional[Union[Dict, str]] = None
        averagePrice: Optional[Union[Dict, str]] = None
        overallAbsolute: Optional[Union[Dict, str]] = None
        overallRelative: Optional[str] = None
        isOutdated: bool = False

        def __post_init__(self):
            self.currentValue = ulal(Amount, self.currentValue)
            self.averagePrice = ulal(Amount, self.averagePrice)
            self.overallAbsolute = ulal(Amount, self.overallAbsolute)

    @filter_unexpected_fields
    @dataclass
    class ReferenceAccountItem:
        """ReferenceAccount class"""

        internalReferenceAccounts: bool = False
        accountType: Optional[str] = None
        accountNumber: Optional[str] = None
        bankCode: Optional[str] = None
        holderName: Optional[str] = None

    def format(self) -> Dict[str, str]:
        """format depot"""
        logger.debug("Depot.format()\n")

        output_dic = {
            "account": self.depositAccountId,
            "amount": self.brokerageAccountPerformance.currentValue.value,
            "currencyCode": self.brokerageAccountPerformance.currentValue.currencyCode,
            "holderName": self.holderName,
            "id": self.id,
            "name": self.holderName,
            "type": "depot",
            "transactions": self.transactions,
        }

        logger.debug("Depot.format() ended\n")
        return output_dic
