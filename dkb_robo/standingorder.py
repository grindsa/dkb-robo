""" Module for handling dkb standing orders """
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging
import requests
from dkb_robo.utilities import DKBRoboError, Amount, filter_unexpected_fields, object2dictionary


logger = logging.getLogger(__name__)


@filter_unexpected_fields
@dataclass
class CreditorAccount:
    """ class for a single creditor account """
    iban: Optional[str] = None
    bic: Optional[str] = None
    name: Optional[str] = None


@filter_unexpected_fields
@dataclass
class DebtorAccount:
    """ class for a single debitor account """
    iban: Optional[str] = None
    accountId: Optional[str] = None  # pylint: disable=C0103 # NOSONAR


@filter_unexpected_fields
@dataclass
class Recurrence:
    """ class for frequency account """
    frm: Optional[str] = None
    frequency: Optional[str] = None
    holidayExecutionStrategy: Optional[str] = None  # pylint: disable=C0103 # NOSONAR
    nextExecutionAt: Optional[str] = None  # pylint: disable=C0103 # NOSONAR
    until: Optional[str] = None


@filter_unexpected_fields
@dataclass
class StandingOrderItem:
    """ class for a single standing order """
    amount: Optional[Amount] = None
    creditor: Optional[CreditorAccount] = None
    debtor: Optional[DebtorAccount] = None
    description: Optional[str] = None
    messages: List[str] = field(default_factory=list)
    recurrence: Optional[Recurrence] = None
    status: Optional[str] = None

    def __post_init__(self):
        self.amount = Amount(**self.amount)
        self.creditor['creditorAccount']['name'] = self.creditor.get('name', {})
        self.creditor = CreditorAccount(**self.creditor['creditorAccount'])
        if self.debtor and 'debtorAccount' in self.debtor:
            self.debtor = DebtorAccount(**self.debtor['debtorAccount'])
        # rewrite from - field to frm
        self.recurrence['frm'] = self.recurrence.get('from', None)
        self.recurrence = Recurrence(**self.recurrence)


class StandingOrders:
    """ StandingOrders class """
    def __init__(self, client: requests.Session, unprocessed: bool = False, base_url: str = 'https://banking.dkb.de/api'):
        self.client = client
        self.base_url = base_url
        self.unprocessed = unprocessed
        self.uid = None

    def _filter(self, full_list: Dict[str, str]) -> List[Dict[str, str]]:
        """ filter standing orders """
        logger.debug('StandingOrders._filter()\n')

        so_list = []
        if 'data' in full_list:
            for ele in full_list['data']:

                standingorder_obj = StandingOrderItem(**ele['attributes'])

                if self.unprocessed:
                    so_list.append(standingorder_obj)
                else:
                    so_list.append({
                        'amount': standingorder_obj.amount.value,
                        'currencycode': standingorder_obj.amount.currencyCode,
                        'purpose': standingorder_obj.description,
                        'recipient': standingorder_obj.creditor.name,
                        'creditoraccount': object2dictionary(standingorder_obj.creditor, skip_list=['name']),
                        # from got rewritten in dataclase - we need to rewrite it back
                        'interval': {**object2dictionary(standingorder_obj.recurrence, skip_list=['frm']), 'from': standingorder_obj.recurrence.frm},
                    })

        logger.debug('StandingOrders._filter() ended with: %s entries.', len(so_list))
        return so_list

    def fetch(self, uid) -> Dict:
        """ fetch standing orders """
        logger.debug('StandingOrders.fetch()\n')

        so_list = []
        if uid:
            response = self.client.get(self.base_url + '/accounts/payments/recurring-credit-transfers' + '?accountId=' + uid)
            if response.status_code == 200:
                _so_list = response.json()
                so_list = self._filter(_so_list)
        else:
            raise DKBRoboError('account-id is required to fetch standing orders')

        logger.debug('StandingOrders.fetch() ended\n')
        return so_list
