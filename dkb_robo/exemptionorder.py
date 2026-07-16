"""Module for handling DKB exemption orders."""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import logging
from urllib.parse import urljoin
import requests
from dkb_robo.utilities import (
    Amount,
    DKBRoboError,
    Person,
    filter_unexpected_fields,
    object2dictionary,
    ulal,
)

logger = logging.getLogger(__name__)


ExemptionField = Optional[Union[Dict[str, Any], Amount]]
PartnerField = Optional[Union[Dict[str, Any], Person]]
FilteredExemptionOrder = Dict[str, Any]
ExemptionOrderList = List[Union["ExemptionOrderItem", FilteredExemptionOrder]]


@filter_unexpected_fields
@dataclass
class ExemptionOrderItem:
    """Represents a single exemption order."""

    # pylint: disable=C0103
    exemptionAmount: ExemptionField = None
    exemptionOrderType: Optional[str] = None
    partner: PartnerField = None
    receivedAt: Optional[str] = None
    utilizedAmount: ExemptionField = None
    remainingAmount: ExemptionField = None
    validFrom: Optional[str] = None
    validUntil: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.exemptionAmount, dict):
            self.exemptionAmount = ulal(Amount, self.exemptionAmount)
        if isinstance(self.remainingAmount, dict):
            self.remainingAmount = ulal(Amount, self.remainingAmount)
        if isinstance(self.utilizedAmount, dict):
            self.utilizedAmount = ulal(Amount, self.utilizedAmount)
        if isinstance(self.partner, dict):
            self.partner = ulal(Person, self.partner)


class ExemptionOrders:
    """Fetches and filters exemption orders from the DKB API."""

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

    def _filter(self, full_list: Dict[str, Any]) -> ExemptionOrderList:
        """Filter exemption orders from the API payload."""
        logger.debug("ExemptionOrders._filter()")

        exo_list = []
        for exo in self._extract_exemption_orders(full_list):
            exemptionorder_obj = ExemptionOrderItem(**exo)
            if self.unfiltered:
                exo_list.append(exemptionorder_obj)
                continue
            exo_list.append(self._build_filtered_exemption_order(exemptionorder_obj))

        logger.debug("ExemptionOrders._filter() ended with: %s entries.", len(exo_list))
        return exo_list

    def _extract_exemption_orders(self, full_list: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract exemption order entries from the API payload."""
        data = full_list.get("data", {}) if isinstance(full_list, dict) else {}
        attributes = data.get("attributes", {}) if isinstance(data, dict) else {}
        exemption_orders = (
            attributes.get("exemptionOrders", []) if isinstance(attributes, dict) else []
        )
        return [item for item in exemption_orders if isinstance(item, dict)]

    def _build_filtered_exemption_order(
        self, exemptionorder_obj: ExemptionOrderItem
    ) -> FilteredExemptionOrder:
        """Build filtered output for a single exemption order."""
        exemption_amount = exemptionorder_obj.exemptionAmount
        utilized_amount = exemptionorder_obj.utilizedAmount
        return {
            "amount": exemption_amount.value if exemption_amount else None,
            "used": utilized_amount.value if utilized_amount else None,
            "currencycode": (
                exemption_amount.currencyCode if exemption_amount else None
            ),
            "validfrom": exemptionorder_obj.validFrom,
            "validto": exemptionorder_obj.validUntil,
            "receivedat": exemptionorder_obj.receivedAt,
            "type": exemptionorder_obj.exemptionOrderType,
            "partner": self._build_partner(exemptionorder_obj.partner),
        }

    def _build_partner(self, partner: Optional[Person]) -> Dict[str, Any]:
        """Build partner output shape for filtered responses."""
        if not partner:
            return {}
        return object2dictionary(partner, key_lc=True, skip_list=["title"])

    def fetch(self) -> ExemptionOrderList:
        """Fetch exemption orders from the API."""
        logger.debug("ExemptionOrders.fetch()")

        exo_list = []
        endpoint = urljoin(
            self.base_url.rstrip("/") + "/", "customers/me/tax-exemptions"
        )

        try:
            response = self.client.get(endpoint, timeout=self.timeout)
        except requests.RequestException as err:
            raise DKBRoboError(f"fetch exemption orders: request failed: {err}") from err

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            status_code = response.status_code
            response_text = response.text if response.text else ""
            response_detail = (
                f"; response={response_text[:200]}" if response_text else ""
            )
            raise DKBRoboError(
                f"fetch exemption orders: http status code is {status_code}{response_detail}"
            ) from err

        try:
            _exo_list = response.json()
        except ValueError as err:
            raise DKBRoboError("fetch exemption orders: invalid json in response") from err
        exo_list = self._filter(_exo_list)

        logger.debug("ExemptionOrders.fetch() ended")
        return exo_list
