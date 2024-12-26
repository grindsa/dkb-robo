""" Module for handling dkb standing orders """
from typing import Dict, List
import logging
import requests
from dkb_robo.api import DKBRoboError


class StandingOrder:
    """ StandingOrder class """
    def __init__(self, client: requests.Session, logger: logging.Logger, base_url: str = 'https://banking.dkb.de/api'):
        self.client = client
        self.logger = logger
        self.base_url = base_url
        self.uid = None

    def _filter(self, full_list: Dict[str, str]) -> List[Dict[str, str]]:
        """ filter standing orders """
        self.logger.debug('standing.StandingOrder._filter()\n')

        so_list = []
        if 'data' in full_list:
            for ele in full_list['data']:

                try:
                    amount = float(ele.get('attributes', {}).get('amount', {}).get('value', None))
                except Exception as err:
                    self.logger.error('api.StandingOrder._filter() error: %s', err)
                    amount = None

                _tmp_dic = {
                    'amount': amount,
                    'currencycode': ele.get('attributes', {}).get('amount', {}).get('currencyCode', None),
                    'purpose': ele.get('attributes', {}).get('description', None),
                    'recpipient': ele.get('attributes', {}).get('creditor', {}).get('name', None),
                    'creditoraccount': ele.get('attributes', {}).get('creditor', {}).get('creditorAccount', None),
                    'interval': ele.get('attributes', {}).get('recurrence', None)}
                so_list.append(_tmp_dic)

        self.logger.debug('standing.StandingOrder._filter() ended with: %s entries.', len(so_list))
        return so_list

    def fetch(self, uid) -> Dict:
        """ fetch standing orders """
        self.logger.debug('standing.StandingOrder.fetch()\n')

        so_list = []
        if uid:
            response = self.client.get(self.base_url + '/accounts/payments/recurring-credit-transfers' + '?accountId=' + uid)
            if response.status_code == 200:
                _so_list = response.json()
                so_list = self._filter(_so_list)
        else:
            raise DKBRoboError('account-id is required to fetch standing orders')

        self.logger.debug('standing.StandingOrder.fetch() ended\n')
        return so_list
