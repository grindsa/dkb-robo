""" Module for handling dkb transactions """
# pylint: disable=c0415, r0913
import datetime
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging
import requests
from dkb_robo.utilities import Amount, get_dateformat, filter_unexpected_fields, DKBRoboError

LEGACY_DATE_FORMAT, API_DATE_FORMAT = get_dateformat()
logger = logging.getLogger(__name__)


class Transactions:
    """ Transactions class """

    def __init__(self, client: requests.Session, unprocessed: bool = False, base_url: str = 'https://banking.dkb.de/api'):
        self.client = client
        self.base_url = base_url
        self.uid = None
        self.unprocessed = unprocessed

    def _nextpage_url(self, tr_dic):
        """ get transaction url """
        logger.debug('Transactions._nextpage_url()\n')

        transaction_url = None
        if 'links' in tr_dic and 'next' in tr_dic['links']:
            logger.debug('Transactions._nextpage_url(): next page: %s', tr_dic['links']['next'])
            transaction_url = self.base_url + '/accounts' + tr_dic['links']['next']
        else:
            logger.debug('Transactions._nextpage_url(): no next page')
            transaction_url = None

        logger.debug('Transactions._nextpage_url() ended\n')
        return transaction_url

    def _fetch(self, transaction_url: str) -> Dict[str, str]:
        """ get transaction list"""
        logger.debug('Transactions.fetch(%s)\n', transaction_url)

        transaction_dic = {'data': [], 'included': []}
        while transaction_url:
            response = self.client.get(transaction_url)
            if response.status_code == 200:
                _transaction_dic = response.json()
                if 'data' in _transaction_dic:
                    transaction_dic['data'].extend(_transaction_dic['data'])
                    transaction_url = self._nextpage_url(_transaction_dic)    # get next page
                else:
                    logger.debug('fetch transactions: no data in response')
                    transaction_url = None

                if 'included' in _transaction_dic:
                    transaction_dic['included'].extend(_transaction_dic['included'])
            else:
                logger.error('fetch transactions: http status code is not 200 but %s', response.status_code)
                break

        logger.debug('Transactions.fetch() ended with %s entries\n', len(transaction_dic['data']))
        return transaction_dic

    def _filter(self, transaction_list: List[Dict[str, str]], date_from: str, date_to: str, transaction_type: str) -> List[Dict[str, str]]:
        """ filter transactions """
        logger.debug('Transactions._filter()\n')

        # support transation type 'reserved' for backwards compatibility
        transaction_type = 'pending' if transaction_type == 'reserved' else transaction_type

        try:
            date_from_uts = int(time.mktime(datetime.datetime.strptime(date_from, LEGACY_DATE_FORMAT).timetuple()))
        except ValueError:
            date_from_uts = int(time.mktime(datetime.datetime.strptime(date_from, API_DATE_FORMAT).timetuple()))

        try:
            date_to_uts = int(time.mktime(datetime.datetime.strptime(date_to, LEGACY_DATE_FORMAT).timetuple()))
        except ValueError:
            date_to_uts = int(time.mktime(datetime.datetime.strptime(date_to, API_DATE_FORMAT).timetuple()))

        filtered_transaction_list = []
        for transaction in transaction_list:
            # print(transaction)
            if 'attributes' in transaction and 'status' in transaction['attributes'] and 'bookingDate' in transaction['attributes']:
                if transaction['attributes']['status'] == transaction_type:
                    bookingdate_uts = int(time.mktime(datetime.datetime.strptime(transaction['attributes']['bookingDate'], API_DATE_FORMAT).timetuple()))
                    if date_from_uts <= bookingdate_uts <= date_to_uts:
                        filtered_transaction_list.append(transaction)

        logger.debug('Transactions._filter() ended with %s entries\n', len(filtered_transaction_list))
        return filtered_transaction_list

    def get(self, transaction_url: str, atype: str, date_from: str, date_to: str, transaction_type: str = 'booked'):
        """ fetch transactions """
        logger.debug('Transactions.get()\n')

        if transaction_url and atype != 'depot':
            transaction_url = transaction_url + '?filter[bookingDate][GE]=' + date_from + '&filter[bookingDate][LE]=' + date_to + '&expand=Merchant&page[size]=400'

        # transaction_dic = self._fetch(transaction_url)
        import json
        with open('transaction.json', 'r') as f:
            transaction_dic = json.load(f)

        mapping_dic = {
            'account': 'AccountTransaction',
            'creditcard': 'CreditCardTransaction',
            'depot': 'DepotTransaction'
        }

        if atype in ['account', 'creditcard']:
            raw_transaction_list = self._filter(transaction_list=transaction_dic['data'], date_from=date_from, date_to=date_to, transaction_type=transaction_type)
        else:
            raw_transaction_list = transaction_dic

        #    raw_transaction_list = self._filter(transaction_list=transaction_dic['data'], transaction_type=transaction_type, date_from=date_from, date_to=date_to)
        #    transaction = AccountTransaction()
        #elif atype == 'creditcard':
        #    raw_transaction_list = self._filter(transaction_list=transaction_dic['data'], transaction_type=transaction_type, date_from=date_from, date_to=date_to)
        #    transaction = CreditCardTransaction()
        #elif atype == 'depot':
        #    transaction = DepotTransaction()
        #else:
        #    raise DKBRoboError(f'transaction type {atype} is not supported')



        transaction_list = []
        if raw_transaction_list:
            for ele in raw_transaction_list:
                transaction = globals()[mapping_dic[atype]](**ele['attributes'])
                if self.unprocessed:
                    transaction_list.append(transaction)
                else:
                    transaction_list.append(transaction.format())

        #   else:
        #        transaction_list = transaction.format(transaction_dic)

        logger.debug('Transactions.get() ended\n')
        return transaction_list

@filter_unexpected_fields
@dataclass
class AccountTransaction:
    """ dataclass for a single AccountTransaction class """
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
        self.amount = Amount(**self.amount)
        # regroup creditor information allowing simpler access
        self.creditor = PeerAccount(**self._peer_information(self.creditor, 'creditorAccount'))
        # regroup debtor for the same reason
        self.debtor = PeerAccount(**self._peer_information(self.debtor, 'debtorAccount'))

    def _peer_information(self, peer_dic: Dict[str, str], peer_type: str = None) -> Dict[str, str]:
        """ add peer information """
        logger.debug('AccountTransaction._peer_information(%s)\n', peer_type)

        peer_dic['account'] = peer_dic.pop(peer_type, None)
        peer_dic['account'] = {
            'bic': peer_dic.get('agent', {}).get('bic', None),
            'name': " ".join(peer_dic.pop('name', None).split())
        }

        if peer_dic.get('intermediaryName', None):
            peer_dic['account']['intermediaryName'] = " ".join(peer_dic.get('intermediaryName', None).split())

        logger.debug('AccountTransaction._peer_information() ended\n')
        return peer_dic['account']

    def format(self):
        """ format format transaction list ot a useful output """
        logger.debug('AccountTransaction.format()\n')

        transaction_dic = {
            'amount': self.amount.value,
            'currencycode': self.amount.currencyCode,
            'date': self.bookingDate,
            'vdate': self.valueDate,
            'customerreference': self.endToEndId,
            'mandateid': self.mandateId,
            'postingtext': self.transactionType,
            'reasonforpayment': self.description
        }

        if self.amount.value > 0:
            # incoming transaction
            transaction_dic['peeraccount'] = self.debtor.iban
            transaction_dic['peerbic'] = self.debtor.bic
            # transaction_dic['peerid'] = self.debtor.id
            if self.debtor.intermediaryName:
                transaction_dic['peer'] = self.debtor.intermediaryName
            else:
                transaction_dic['peer'] = self.debtor.name
        else:
            # outgoing transaction
            transaction_dic['peeraccount'] = self.creditor.iban
            transaction_dic['peerbic'] = self.creditor.bic
            # transaction_dic['peerid'] = self.creditor.id
            if self.creditor.intermediaryName:
                transaction_dic['peer'] = self.creditor.intermediaryName
            else:
                transaction_dic['peer'] = self.creditor.name

        # this is for backwards compatibility
        if 'postingtext' in transaction_dic and 'peer' in transaction_dic and 'reasonforpayment' in transaction_dic:
            transaction_dic['text'] = f'{transaction_dic["postingtext"]} {transaction_dic["peer"]} {transaction_dic["reasonforpayment"]}'

        logger.debug('AccountTransaction.format() ended\n')
        return transaction_dic

@filter_unexpected_fields
@dataclass
class PeerAccount:
    """ dataclass for a single peer account """
    iban: Optional[str] = None
    bic: Optional[str] = None
    accountNr: Optional[str] = None
    name: Optional[str] = None
    intermediaryName: Optional[str] = None


class CreditCardTransaction:
    """ CreditCardTransaction class """

    def _details(self, transaction):
        """ add details from card transaction """
        logger.debug('CreditCardTransaction._details()\n')

        if 'attributes' in transaction:
            try:
                amount = float(transaction.get('attributes', {}).get('amount', {}).get('value', None))
            except Exception as err:
                logger.error('amount conversion error: %s', err)
                amount = None

            output_dic = {
                'amount': amount,
                'bdate': transaction.get('attributes', {}).get('bookingDate', None),
                'vdate': transaction.get('attributes', {}).get('bookingDate', None),
                'text': transaction.get('attributes', {}).get('description', None),
                'currencycode': transaction.get('attributes', {}).get('amount', {}).get('currencyCode', None),
            }
        else:
            output_dic = {}

        logger.debug('CreditCardTransaction._details() ended\n')
        return output_dic

    def format(self, transaction):
        """ format format transaction list ot a useful output """
        logger.debug('CreditCardTransaction.format()\n')

        if 'attributes' in transaction:
            transaction_dic = self._details(transaction)
        else:
            transaction_dic = {}

        logger.debug('CreditCardTransaction.format() ended\n')
        return transaction_dic


class DepotTransaction:
    """ DepotTransaction class """

    def _details(self, position: Dict[str, str], included_list: List[Dict[str, str]]):
        """ add details from depot transaction """
        logger.debug('DepotTransaction._details()\n')

        instrument_id = position.get('relationships', {}).get('instrument', {}).get('data', {}).get('id', None)
        quote_id = position.get('relationships', {}).get('quote', {}).get('data', {}).get('id', None)

        try:
            quantity = float(position.get('attributes', {}).get('quantity', {}).get('value', None))
        except Exception as err:
            logger.error('quantity conversion error: %s', err)
            quantity = None

        output_dic = {
            'shares': position.get('attributes', {}).get('quantity', {}).get('value', None),
            'quantity': quantity,
            'shares_unit': position.get('attributes', {}).get('quantity', {}).get('unit', None),
            'lastorderdate': position.get('attributes', {}).get('lastOrderDate', None),
            'price_euro': position.get('attributes', {}).get('performance', {}).get('currentValue', {}).get('value', None),
        }

        for ele in included_list:
            if 'id' in ele and ele['id'] == instrument_id:
                output_dic = {**output_dic, **self._instrumentinformation(ele)}
            if 'id' in ele and ele['id'] == quote_id:
                output_dic = {**output_dic, **self._quoteinformation(ele)}

        logger.debug('DepotTransaction._details() ended\n')
        return output_dic

    def _quoteinformation(self, ele: Dict[str, str]) -> Dict[str, str]:
        """ add quote information """
        logger.debug('DepotTransaction._quoteinformation()\n')

        try:
            price = float(ele.get('attributes', {}).get('price', {}).get('value', None))
        except Exception as err:
            logger.error('price conversion error: %s', err)
            price = None

        output_dic = {
            'price': price,
            'market': ele.get('attributes', {}).get('market', None),
            'currencycode': ele.get('attributes', {}).get('price', {}).get('currencyCode', None),
        }

        logger.debug('DepotTransaction._quoteinformation() ended\n')
        return output_dic

    def _instrumentinformation(self, ele: Dict[str, str]) -> Dict[str, str]:
        """ add instrument information """
        logger.debug('DepotTransaction._instrumentinformation()\n')

        output_dic = {
            'text': ele.get('attributes', {}).get('name', {}).get('short', None)
        }
        if 'attributes' in ele and 'identifiers' in ele['attributes']:
            for identifier in ele['attributes']['identifiers']:
                if identifier['identifier'] == 'isin':
                    output_dic['isin_wkn'] = identifier['value']
                    break

        logger.debug('DepotTransaction._instrumentinformation() ended\n')
        return output_dic

    def format(self, transaction_dic: Dict[str, str]) -> List[Dict[str, str]]:
        """ format format transaction list ot a useful output """
        logger.debug('DepotTransaction.format()\n')

        if 'included' in transaction_dic:
            included_list = transaction_dic['included']

        position_list = []
        if 'data' in transaction_dic:
            for position in transaction_dic['data']:
                position_dic = self._details(position, included_list)
                if position_dic:
                    position_list.append(position_dic)

        return position_list
