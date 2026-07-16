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

        unfiltered_exo_list = (
            full_list.get("data", {}).get("attributes", {}).get("exemptionOrders", [])
        )
        exo_list = []
        for exo in unfiltered_exo_list:

            exemptionorder_obj = ExemptionOrderItem(**exo)
            if self.unfiltered:
                exo_list.append(exemptionorder_obj)
            else:
                exemption_amount = exemptionorder_obj.exemptionAmount
                utilized_amount = exemptionorder_obj.utilizedAmount
                partner = exemptionorder_obj.partner
                exo_list.append(
                    {
                        "amount": exemption_amount.value if exemption_amount else None,
                        "used": utilized_amount.value if utilized_amount else None,
                        "currencycode": (
                            exemption_amount.currencyCode if exemption_amount else None
                        ),
                        "validfrom": exemptionorder_obj.validFrom,
                        "validto": exemptionorder_obj.validUntil,
                        "receivedat": exemptionorder_obj.receivedAt,
                        "type": exemptionorder_obj.exemptionOrderType,
                        "partner": (
                            object2dictionary(partner, key_lc=True, skip_list=["title"])
                            if partner
                            else {}
                        ),
                    }
                )

        logger.debug("ExemptionOrders._filter() ended with: %s entries.", len(exo_list))
        return exo_list

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
