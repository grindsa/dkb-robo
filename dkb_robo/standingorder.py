"""Module for handling DKB standing orders."""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging
from urllib.parse import urljoin
import requests
from dkb_robo.utilities import (
    DKBRoboError,
    Account,
    Amount,
    filter_unexpected_fields,
    object2dictionary,
    ulal,
)

logger = logging.getLogger(__name__)


AmountField = Optional[Union[Dict[str, Any], Amount]]
AccountField = Optional[Union[Dict[str, Any], Account]]
RecurrenceField = Optional[Union[Dict[str, Any], "StandingOrderItem.Recurrence"]]
FilteredStandingOrder = Dict[str, Any]
StandingOrderList = List[Union["StandingOrderItem", FilteredStandingOrder]]


@filter_unexpected_fields
@dataclass
class StandingOrderItem:
    """Represents a single standing order."""

    amount: AmountField = None
    creditor: AccountField = None
    debtor: AccountField = None
    description: Optional[str] = None
    messages: List[str] = field(default_factory=list)
    recurrence: RecurrenceField = None
    status: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.amount, dict):
            self.amount = ulal(Amount, self.amount)

        if isinstance(self.creditor, dict):
            creditor_account = self.creditor.get("creditorAccount")
            if isinstance(creditor_account, dict):
                creditor_account["name"] = self.creditor.get("name", None)
                self.creditor = ulal(Account, creditor_account)
            else:
                self.creditor = None

        if isinstance(self.debtor, dict):
            debtor_account = self.debtor.get("debtorAccount")
            if isinstance(debtor_account, dict):
                self.debtor = ulal(Account, debtor_account)
            else:
                self.debtor = None

        # rewrite from - field to frm
        if isinstance(self.recurrence, dict):
            self.recurrence["frm"] = self.recurrence.get("from", None)
            self.recurrence = ulal(self.Recurrence, self.recurrence)

    @filter_unexpected_fields
    @dataclass
    class Recurrence:
        """Recurrence information for a standing order."""

        # pylint: disable=C0103
        frm: Optional[str] = None
        frequency: Optional[str] = None
        holidayExecutionStrategy: Optional[str] = None
        nextExecutionAt: Optional[str] = None
        until: Optional[str] = None


class StandingOrders:
    """Fetches and filters standing orders from the DKB API."""

    _DEFAULT_INTERVAL = {
        "from": None,
        "until": None,
        "frequency": None,
        "holidayExecutionStrategy": None,
        "nextExecutionAt": None,
    }

    def __init__(
        self,
        client: requests.Session,
        unfiltered: bool = False,
        base_url: str = "https://banking.dkb.de/api",
        timeout: float = 10.0,
    ):
        self.client = client
        self.base_url = base_url
        self.unfiltered = unfiltered
        self.timeout = timeout

    def _filter(self, full_list: Dict[str, Any]) -> StandingOrderList:
        """Filter standing orders from the API payload."""
        logger.debug("StandingOrders._filter()")

        so_list = []
        for ele in full_list.get("data", []):
            attributes = ele.get("attributes", {}) if isinstance(ele, dict) else {}
            standingorder_obj = StandingOrderItem(**attributes)
            if self.unfiltered:
                so_list.append(standingorder_obj)
                continue
            so_list.append(self._build_filtered_standing_order(standingorder_obj))

        logger.debug("StandingOrders._filter() ended with: %s entries.", len(so_list))
        return so_list

    def _build_filtered_standing_order(
        self, standingorder_obj: StandingOrderItem
    ) -> FilteredStandingOrder:
        """Build output shape for filtered standing order responses."""
        amount = standingorder_obj.amount
        creditor = standingorder_obj.creditor
        recurrence = standingorder_obj.recurrence
        return {
            "amount": amount.value if amount else None,
            "currencycode": amount.currencyCode if amount else None,
            "purpose": standingorder_obj.description,
            "recipient": creditor.name if creditor else None,
            "creditoraccount": self._build_creditor_account(creditor),
            "interval": self._build_interval(recurrence),
        }

    def _build_creditor_account(self, creditor: Optional[Account]) -> Dict[str, Any]:
        """Build creditor account details for filtered responses."""
        if not creditor:
            return {}
        return object2dictionary(
            creditor,
            skip_list=[
                "name",
                "accountId",
                "accountNr",
                "id",
                "intermediaryName",
                "blz",
            ],
        )

    def _build_interval(
        self, recurrence: Optional[StandingOrderItem.Recurrence]
    ) -> Dict[str, Any]:
        """Build recurrence interval while preserving legacy field names."""
        if not recurrence:
            return dict(self._DEFAULT_INTERVAL)
        return {
            **object2dictionary(recurrence, skip_list=["frm"]),
            "from": recurrence.frm,
        }

    def fetch(self, uid: str) -> StandingOrderList:
        """Fetch standing orders for an account id."""
        logger.debug("StandingOrders.fetch()")

        so_list = []
        if not uid:
            raise DKBRoboError("account-id is required to fetch standing orders")

        endpoint = urljoin(
            self.base_url.rstrip("/") + "/",
            "accounts/payments/recurring-credit-transfers",
        )

        try:
            response = self.client.get(
                endpoint,
                params={"accountId": uid},
                timeout=self.timeout,
            )
        except requests.RequestException as err:
            raise DKBRoboError(f"fetch standing orders: request failed: {err}") from err

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            status_code = response.status_code
            response_text = response.text if response.text else ""
            response_detail = (
                f"; response={response_text[:200]}" if response_text else ""
            )
            raise DKBRoboError(
                f"fetch standing orders: http status code is {status_code}{response_detail}"
            ) from err

        try:
            _so_list = response.json()
        except ValueError as err:
            raise DKBRoboError("fetch standing orders: invalid json in response") from err

        so_list = self._filter(_so_list)

        logger.debug("StandingOrders.fetch() ended")
        return so_list
