""" Module for handling dkb standing orders """
from typing import Dict, List
import logging
import requests
from dkb_robo.api import DKBRoboError


class ExemptionOrder:
    """ exemption order class """
    def __init__(self, client: requests.Session, logger: logging.Logger, base_url: str = 'https://banking.dkb.de/api'):
        self.client = client
        self.logger = logger
        self.base_url = base_url

    def _filter(self, full_list: Dict[str, str]) -> List[Dict[str, str]]:
        """ filter standing orders """
        self.logger.debug('exemptionorder.ExemptionOrder._filter()\n')

        unfiltered_exo_list = full_list.get('data', {}).get('attributes', {}).get('exemptionOrders', [])
        exo_list = []
        for exo in unfiltered_exo_list:
            try:
                amount = float(exo.get('exemptionAmount', {}).get('value', None))
            except Exception as err:
                self.logger.error('amount conversion error: %s', err)
                amount = None
            try:
                used = float(exo.get('utilizedAmount', {}).get('value', None))
            except Exception as err:
                self.logger.error('used conversion error: %s', err)
                used = None

            partner = {k.lower(): v for k, v in exo.get('partner', {}).items()}
            exo_list.append({
                'amount': amount,
                'used': used,
                'currencycode': exo.get('exemptionAmount', {}).get('currencyCode', None),
                'validfrom': exo.get('validFrom', None),
                'validto': exo.get('validUntil', None),
                'receivedat': exo.get('receivedAt', None),
                'type': exo.get('exemptionOrderType', None),
                'partner': partner
            })

        self.logger.debug('exemptionorder.ExemptionOrder._filter() ended with: %s entries.', len(exo_list))
        return exo_list

    def fetch(self) -> Dict:
        """ fetcg exemption orders from api  """
        self.logger.debug('exemptionorder.ExemptionOrder.fetch()\n')

        exo_list = []

        response = self.client.get(self.base_url + '/customers/me/tax-exemptions')
        if response.status_code == 200:
            _exo_list = response.json()
            exo_list = self._filter(_exo_list)
        else:
            raise DKBRoboError(f'fetch exemption orders: http status code is not 200 but {response.status_code}')

        self.logger.debug('exemptionorder.ExemptionOrder.fetch() ended\n')
        return exo_list
