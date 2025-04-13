""" Module for handling dkb standing orders """
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
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


@filter_unexpected_fields
@dataclass
class ExemptionOrderItem:
    """class for a single exemption order"""

    # pylint: disable=C0103
    exemptionAmount: Optional[str] = None
    exemptionOrderType: Optional[str] = None
    partner: Optional[str] = None
    receivedAt: Optional[str] = None
    utilizedAmount: Optional[str] = None
    remainingAmount: Optional[str] = None
    validFrom: Optional[str] = None
    validUntil: Optional[str] = None

    def __post_init__(self):
        self.exemptionAmount = ulal(Amount, self.exemptionAmount)
        self.remainingAmount = ulal(Amount, self.remainingAmount)
        self.utilizedAmount = ulal(Amount, self.utilizedAmount)
        self.partner = ulal(Person, self.partner)


class ExemptionOrders:
    """exemption order class"""

    def __init__(
        self,
        client: requests.Session,
        unfiltered: bool = False,
        base_url: str = "https://banking.dkb.de/api",
    ):
        self.client = client
        self.base_url = base_url
        self.unfiltered = unfiltered

    def _filter(self, full_list: Dict[str, str]) -> List[Dict[str, str]]:
        """filter standing orders"""
        logger.debug("ExemptionOrders._filter()\n")

        unfiltered_exo_list = (
            full_list.get("data", {}).get("attributes", {}).get("exemptionOrders", [])
        )
        exo_list = []
        for exo in unfiltered_exo_list:

            exemptionorder_obj = ExemptionOrderItem(**exo)
            if self.unfiltered:
                exo_list.append(exemptionorder_obj)
            else:
                exo_list.append(
                    {
                        "amount": exemptionorder_obj.exemptionAmount.value,
                        "used": exemptionorder_obj.utilizedAmount.value,
                        "currencycode": exemptionorder_obj.exemptionAmount.currencyCode,
                        "validfrom": exemptionorder_obj.validFrom,
                        "validto": exemptionorder_obj.validUntil,
                        "receivedat": exemptionorder_obj.receivedAt,
                        "type": exemptionorder_obj.exemptionOrderType,
                        "partner": object2dictionary(
                            exemptionorder_obj.partner, key_lc=True, skip_list=["title"]
                        ),
                    }
                )

        logger.debug("ExemptionOrders._filter() ended with: %s entries.", len(exo_list))
        return exo_list

    def fetch(self) -> Dict:
        """fetcg exemption orders from api"""
        logger.debug("ExemptionOrders.fetch()\n")

        exo_list = []

        response = self.client.get(self.base_url + "/customers/me/tax-exemptions")
        if response.status_code == 200:
            _exo_list = response.json()
            exo_list = self._filter(_exo_list)
        else:
            raise DKBRoboError(
                f"fetch exemption orders: http status code is not 200 but {response.status_code}"
            )

        logger.debug("ExemptionOrders.fetch() ended\n")
        return exo_list
