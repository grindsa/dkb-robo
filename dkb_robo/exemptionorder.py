""" Module for handling dkb standing orders """
from typing import Dict, List
from dataclasses import dataclass, field
import logging
import requests
from dkb_robo.utilities import Amount, DKBRoboError, filter_unexpected_fields, object2dictionary


logger = logging.getLogger(__name__)


@filter_unexpected_fields
@dataclass
class PartnerItem:
    """ class for a single partner """
    dateOfBirth: str = None
    firstName: str = None
    lastName: str = None
    salutation: str = None
    taxId: str = None


@filter_unexpected_fields
@dataclass
class ExemptionOrderItem:
    """ class for a single exemption order """
    exemptionAmount: str = None
    exemptionOrderType: str = None
    partner: str = None
    receivedAt: str = None
    utilizedAmount: str = None
    remainingAmount: str = None
    validFrom: str = None
    validUntil: str = None
    def __post_init__(self):
        self.exemptionAmount = Amount(**self.exemptionAmount)
        self.remainingAmount = Amount(**self.remainingAmount)
        self.utilizedAmount = Amount(**self.utilizedAmount)
        self.partner = PartnerItem(**self.partner)


class ExemptionOrders:
    """ exemption order class """
    def __init__(self, client: requests.Session, unprocessed: bool = False, base_url: str = 'https://banking.dkb.de/api'):
        self.client = client
        self.base_url = base_url
        self.unprocessed = unprocessed

    def _filter(self, full_list: Dict[str, str]) -> List[Dict[str, str]]:
        """ filter standing orders """
        logger.debug('ExemptionOrders._filter()\n')

        unfiltered_exo_list = full_list.get('data', {}).get('attributes', {}).get('exemptionOrders', [])
        exo_list = []
        for exo in unfiltered_exo_list:

            exemptionorder_obj = ExemptionOrderItem(**exo)
            if self.unprocessed:
                exo_list.append(exemptionorder_obj)
            else:
                exo_list.append({
                    'amount': exemptionorder_obj.exemptionAmount.value,
                    'used': exemptionorder_obj.utilizedAmount.value,
                    'currencycode': exemptionorder_obj.exemptionAmount.currencyCode,
                    'validfrom': exemptionorder_obj.validFrom,
                    'validto': exemptionorder_obj.validUntil,
                    'receivedat': exemptionorder_obj.receivedAt,
                    'type': exemptionorder_obj.exemptionOrderType,
                    'partner': object2dictionary(exemptionorder_obj.partner, key_lc=True)
                })

        logger.debug('ExemptionOrders._filter() ended with: %s entries.', len(exo_list))
        return exo_list

    def fetch(self) -> Dict:
        """ fetcg exemption orders from api  """
        logger.debug('ExemptionOrders.fetch()\n')

        exo_list = []

        response = self.client.get(self.base_url + '/customers/me/tax-exemptions')
        if response.status_code == 200:
            _exo_list = response.json()
            exo_list = self._filter(_exo_list)
        else:
            raise DKBRoboError(f'fetch exemption orders: http status code is not 200 but {response.status_code}')

        logger.debug('ExemptionOrders.fetch() ended\n')
        return exo_list
