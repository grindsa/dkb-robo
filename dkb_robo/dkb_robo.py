# pylint: disable=c0302, r0913, w2301
""" dkb internet banking automation library """
# -*- coding: utf-8 -*-
import os
import csv
import random
import time
from datetime import datetime
import re
import json
from string import digits, ascii_letters
from urllib import parse
from http import cookiejar
import logging
import mechanicalsoup
import requests


LEGACY_DATE_FORMAT = '%d.%m.%Y'
API_DATE_FORMAT = '%Y-%m-%d'


def convert_date_format(logger, input_date, input_format_list, output_format):
    """ convert date to a specified output format """
    logger.debug('convert_date_format(%s)', input_date)

    output_date = None
    for input_format in input_format_list:
        try:
            parsed_date = datetime.strptime(input_date, input_format)
            # convert date
            output_date = parsed_date.strftime(output_format)
            break
        except Exception:
            logger.debug('convert_date_format(): cannot convert date: %s', input_date)
            # something went wrong. we return the date we got as input
            continue

    if not output_date:
        output_date = input_date

    logger.debug('convert_date_format() ended with: %s', output_date)
    return output_date


def generate_random_string(length):
    """ generate random string to be used as name """
    char_set = digits + ascii_letters
    return ''.join(random.choice(char_set) for _ in range(length))


def string2float(value):
    """ convert string to float value """
    try:
        result = float(value.replace('.', '').replace(',', '.'))
    except Exception:
        result = value

    return result


def logger_setup(debug):
    """ setup logger """
    if debug:
        log_mode = logging.DEBUG
    else:
        log_mode = logging.INFO

    # define standard log format
    log_format = '%(message)s'
    logging.basicConfig(
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        level=log_mode)
    logger = logging.getLogger('dkb_robo')
    return logger


def enforce_date_format(logger, date_from, date_to, min_year):
    """ enforce a certain date format """
    logger.debug('enforce_date_format(): %s, %s %s', date_from, date_to, min_year)

    if min_year == 1:
        # this is the new api we need to ensure %Y-%m-%d
        date_from = convert_date_format(logger, date_from, [API_DATE_FORMAT, LEGACY_DATE_FORMAT], API_DATE_FORMAT)
        date_to = convert_date_format(logger, date_to, [API_DATE_FORMAT, LEGACY_DATE_FORMAT], API_DATE_FORMAT)
    else:
        # this is the old  api we need to ensure $d.%m,%Y
        date_from = convert_date_format(logger, date_from, [API_DATE_FORMAT, LEGACY_DATE_FORMAT], LEGACY_DATE_FORMAT)
        date_to = convert_date_format(logger, date_to, [API_DATE_FORMAT, LEGACY_DATE_FORMAT], LEGACY_DATE_FORMAT)

    logger.debug('enforce_date_format() ended with: %s, %s', date_from, date_to)
    return date_from, date_to


def validate_dates(logger, date_from, date_to, min_year=3):
    """ correct dates if needed """
    logger.debug('validate_dates()')
    try:
        date_from_uts = int(time.mktime(datetime.strptime(date_from, "%d.%m.%Y").timetuple()))
    except ValueError:
        date_from_uts = int(time.mktime(datetime.strptime(date_from, API_DATE_FORMAT).timetuple()))
    try:
        date_to_uts = int(time.mktime(datetime.strptime(date_to, "%d.%m.%Y").timetuple()))
    except ValueError:
        date_to_uts = int(time.mktime(datetime.strptime(date_to, API_DATE_FORMAT).timetuple()))
    now_uts = int(time.time())

    # minimal date (3 years back)
    minimal_date_uts = now_uts - min_year * 365 * 86400

    if date_from_uts < minimal_date_uts:
        logger.info('validate_dates(): adjust date_from to %s', datetime.utcfromtimestamp(minimal_date_uts).strftime('%d.%m.%Y'))
        date_from = datetime.utcfromtimestamp(minimal_date_uts).strftime('%d.%m.%Y')
    if date_to_uts < minimal_date_uts:
        logger.info('validate_dates(): adjust date_to to %s', datetime.utcfromtimestamp(minimal_date_uts).strftime('%d.%m.%Y'))
        date_to = datetime.utcfromtimestamp(minimal_date_uts).strftime('%d.%m.%Y')

    if date_from_uts > now_uts:
        logger.info('validate_dates(): adjust date_from to %s', datetime.utcfromtimestamp(now_uts).strftime('%d.%m.%Y'))
        date_from = datetime.utcfromtimestamp(now_uts).strftime('%d.%m.%Y')
    if date_to_uts > now_uts:
        logger.info('validate_dates(): adjust date_to to %s', datetime.utcfromtimestamp(now_uts).strftime('%d.%m.%Y'))
        date_to = datetime.utcfromtimestamp(now_uts).strftime('%d.%m.%Y')

    date_from, date_to = enforce_date_format(logger, date_from, date_to, min_year)

    logger.debug('validate_dates() returned: %s, %s', date_from, date_to)
    return (date_from, date_to)


class DKBRoboError(Exception):
    """ dkb-robo exception class """
    ...


class DKBRobo(object):
    """ dkb_robo class """
    # pylint: disable=R0904
    base_url = 'https://www.ib.dkb.de'
    banking_url = 'https://banking.dkb.de'
    api_prefix = '/api'
    mfa_method = 'seal_one'
    legacy_login = False
    proxies = {}
    dkb_user = None
    dkb_password = None
    dkb_br = None
    client = None
    token_dic = None
    last_login = None
    account_dic = {}
    tan_insert = False
    logger = None

    def __init__(self, dkb_user=None, dkb_password=None, tan_insert=False, legacy_login=False, debug=False):
        self.dkb_user = dkb_user
        self.dkb_password = dkb_password
        self.tan_insert = tan_insert
        self.legacy_login = legacy_login
        self.logger = logger_setup(debug)

    def __enter__(self):
        """ Makes DKBRobo a Context Manager """
        # tan usage requires legacy login
        if self.tan_insert:
            self.legacy_login = True

        if self.legacy_login and not self.dkb_br:
            self._legacy_login()
        elif not self.legacy_login and not self.client:
            self._login()
        return self

    def __exit__(self, *args):
        """
        Close the connection at the end of the context
        """
        self._logout()

    #
    # public objects
    #

    def get_credit_limits(self):
        """ create a dictionary of credit limits of the different accounts
        args:
            self.dkb_br - browser object
        returns:
            dictionary of the accounts and limits
        """
        self.logger.debug('DKBRobo.get_credit_limits()\n')
        limit_url = self.base_url + '/DkbTransactionBanking/content/service/CreditcardLimit.xhtml'
        self.dkb_br.open(limit_url)

        soup = self.dkb_br.get_current_page()
        form = soup.find('form', attrs={'id': 'form597962073_1'})

        if form:
            # get checking account limits
            limit_dic = self._get_checking_account_limit(form)

            # get credit cards limits
            limit_dic.update(self._get_cc_limits(form))
        else:
            limit_dic = {}

        return limit_dic

    def get_exemption_order(self):
        """ returns a dictionary of the stored exemption orders """
        self.logger.debug('DKBRobo.get_exemption_order()\n')
        exo_url = self.base_url + '/DkbTransactionBanking/content/personaldata/ExemptionOrderOverview.xhtml'

        self.dkb_br.open(exo_url)

        soup = self.dkb_br.get_current_page()

        for lbr in soup.findAll("br"):
            lbr.replace_with("")
            # br.replace('<br />', ' ')

        table = soup.find('table', attrs={'class': 'expandableTable'})

        exo_dic = {}
        if table:
            count = 0
            for row in table.findAll("tr"):
                cols = row.findAll("td")
                if cols:
                    try:
                        count += 1
                        exo_dic[count] = {}
                        # description
                        description = re.sub(' +', ' ', cols[1].text.strip())
                        description = description.replace('\n', '')
                        description = description.replace('\r', '')
                        description = description.replace('  ', ' ')
                        exo_dic[count]['description'] = description

                        # validity
                        validity = re.sub(' +', ' ', cols[2].text.strip())
                        validity = validity.replace('\n', '')
                        validity = validity.replace('\r', '')
                        validity = validity.replace('  ', ' ')
                        exo_dic[count]['validity'] = validity
                        exo_dic[count]['amount'] = string2float(cols[3].text.strip().replace('EUR', ''))
                        exo_dic[count]['used'] = string2float(cols[4].text.strip().replace('EUR', ''))
                        exo_dic[count]['available'] = string2float(cols[5].text.strip().replace('EUR', ''))
                    except Exception as _err:
                        self.logger.error('DKBRobo.get_exemption_order(): %s\n', _err)

        return exo_dic

    def get_points(self):
        """ returns the DKB points
        args:
            self.dkb_br - browser object
        returns:
            points - dkb points
        """
        self.logger.debug('DKBRobo.get_points()\n')
        point_url = self.base_url + '/DkbTransactionBanking/content/FavorableWorld/Overview.xhtml?$event=init'
        self.dkb_br.open(point_url)

        p_dic = {}
        soup = self.dkb_br.get_current_page()
        table = soup.find('table', attrs={'class': 'expandableTable'})
        if table:
            tbody = table.find('tbody')
            row = tbody.findAll('tr')[0]
            cols = row.findAll("td")
            # points
            points = re.sub(' +', ' ', cols[1].text.strip())
            points = points.replace('\n', '')
            (pointsamount, pointsex) = points.replace('  ', ' ').split(' ', 1)
            pointsamount = int(pointsamount.replace('.', ''))
            pointsex = int(pointsex.replace('.', ''))

            # text
            ptext = cols[0].text.strip()
            (tlist) = ptext.split('\n', 1)
            ptext = tlist[0].lstrip()
            ptext = ptext.rstrip()
            etext = tlist[1].lstrip()
            etext = etext.rstrip()

            # store data
            p_dic[ptext] = pointsamount
            p_dic[etext] = pointsex

        return p_dic

    def get_standing_orders(self):
        """ get standing orders
        args:
            self.dkb_br          - browser object
        returns:
            so_dic = standing order dic
        """
        self.logger.debug('DKBRobo.get_standing_orders()\n')
        so_url = self.base_url + '/banking/finanzstatus/dauerauftraege?$event=infoStandingOrder'
        self.dkb_br.open(so_url)

        so_list = []
        soup = self.dkb_br.get_current_page()
        table = soup.find('table', attrs={'class': 'expandableTable'})
        if table:
            tbody = table.find('tbody')
            rows = tbody.findAll('tr')
            for row in rows:
                tmp_dic = {}
                cols = row.findAll("td")
                tmp_dic['recipient'] = cols[0].text.strip()
                amount = cols[1].text.strip()
                amount = amount.replace('\n', '')
                amount = string2float(amount.replace('EUR', ''))
                tmp_dic['amount'] = amount

                interval = cols[2]
                for brt in interval.findAll('br'):
                    brt.unwrap()

                interval = re.sub('\t+', ' ', interval.text.strip())
                interval = interval.replace('\n', '')
                interval = re.sub(' +', ' ', interval)
                tmp_dic['interval'] = interval
                tmp_dic['purpose'] = cols[3].text.strip()

                # store dict in list
                so_list.append(tmp_dic)

        return so_list

    def get_transactions(self, transaction_url, atype, date_from, date_to, transaction_type='booked'):
        """ exported method to get transactions """
        self.logger.debug('DKBRobo.get_transactions(%s/%s: %s/%s)\n', transaction_url, atype, date_from, date_to)

        if self.legacy_login:
            (date_from, date_to) = validate_dates(self.logger, date_from, date_to, 3)
            transaction_list = self._legacy_get_transactions(transaction_url, atype, date_from, date_to, transaction_type)
        else:
            (date_from, date_to) = validate_dates(self.logger, date_from, date_to, 1)
            transaction_list = self._get_transactions(transaction_url, atype, date_from, date_to, transaction_type)

        self.logger.debug('DKBRobo.get_transactions(): %s transactions returned\n', len(transaction_list))
        return transaction_list

    def scan_postbox(self, path=None, download_all=False, archive=False, prepend_date=False):
        """ scans the DKB postbox and creates a dictionary out of the
            different documents
        args:
            self.dkb_br = browser object
            path = directory to store the downloaded data
            download_all = download all documents instead just the new ones
        returns:
           dictionary in the following format

           - folder name in postbox
                - details -> link to document overview
                - documents
                    - name of document -> document link
        """
        self.logger.debug('DKBRobo.scan_postbox() path: %s, download_all: %s, archive: %s, prepend_date: %s\n', path, download_all, archive, prepend_date)
        if archive:
            pb_url = self.base_url + '/banking/postfach/ordner?$event=gotoFolder&folderNameOrId=archiv'
        else:
            pb_url = self.base_url + '/banking/postfach'
        self.dkb_br.open(pb_url)
        soup = self.dkb_br.get_current_page()
        if archive:
            table = soup.find('table', attrs={'id': re.compile('mbo-message-list*')})
        else:
            table = soup.find('table', attrs={'id': 'welcomeMboTable'})
        tbody = table.find('tbody')

        if archive:
            select_all = True
        else:
            select_all = download_all

        pb_dic = {}
        for row in tbody.findAll('tr'):
            link = row.find('a')
            link_name = link.contents[0]
            pb_dic[link_name] = {}
            pb_dic[link_name]['name'] = link_name
            pb_dic[link_name]['details'] = self.base_url + link['href']
            if path:
                pb_dic[link_name]['documents'] = self._get_document_links(pb_dic[link_name]['details'], path, link_name, select_all, prepend_date)
            else:
                pb_dic[link_name]['documents'] = self._get_document_links(pb_dic[link_name]['details'], select_all=select_all, prepend_date=prepend_date)
        return pb_dic

    #
    # private objects using the new api
    #

    def _add_account_transactionamount(self, transaction):
        """ add amount from accont transaction """
        self.logger.debug('DKBRobo._add_account_transactionamount()\n')

        output_dic = {}
        if 'amount' in transaction['attributes']:
            if 'value' in transaction['attributes']['amount']:
                output_dic['amount'] = float(transaction['attributes']['amount']['value'])
            if 'currencyCode' in transaction['attributes']['amount']:
                output_dic['currencycode'] = transaction['attributes']['amount']['currencyCode']

        return output_dic

    def _add_account_transaction_creditorinfo(self, transaction):
        """ we need creditor information for outgoing payments"""
        self.logger.debug('DKBRobo._add_account_transaction_creditorinfo()\n')

        output_dic = {}
        if 'creditor' in transaction['attributes']:
            if 'creditorAccount' in transaction['attributes']['creditor'] and 'iban' in transaction['attributes']['creditor']['creditorAccount']:
                output_dic['peeraccount'] = transaction['attributes']['creditor']['creditorAccount']['iban']
            if 'agent' in transaction['attributes']['creditor'] and 'bic' in transaction['attributes']['creditor']['agent']:
                output_dic['peerbic'] = transaction['attributes']['creditor']['agent']['bic']
            if 'name' in transaction['attributes']['creditor']:
                output_dic['peer'] = transaction['attributes']['creditor']['name']
            if 'id' in transaction['attributes']['creditor']:
                output_dic['peerid'] = transaction['attributes']['creditor']['id']
            else:
                output_dic['peerid'] = ''

        return output_dic

    def _add_account_transaction_debtorinfo(self, transaction):
        """we need debitor information for incoming payments """
        self.logger.debug('DKBRobo._add_account_transaction_debtorinfo()\n')

        output_dic = {}
        if 'debtor' in transaction['attributes']:
            if 'debtorAccount' in transaction['attributes']['debtor'] and 'iban' in transaction['attributes']['debtor']['debtorAccount']:
                output_dic['peeraccount'] = transaction['attributes']['debtor']['debtorAccount']['iban']
            if 'agent' in transaction['attributes']['debtor'] and 'bic' in transaction['attributes']['debtor']['agent']:
                output_dic['peerbic'] = transaction['attributes']['debtor']['agent']['bic']
            if 'intermediaryName' in transaction['attributes']['debtor'] and transaction['attributes']['debtor']['intermediaryName']:
                output_dic['peer'] = transaction['attributes']['debtor']['intermediaryName']
            else:
                if 'name' in transaction['attributes']['debtor']:
                    output_dic['peer'] = transaction['attributes']['debtor']['name']

            # add perrid
            output_dic['peerid'] = self._add_account_transaction_debtorpeerid(transaction)

        return output_dic

    def _add_account_transaction_debtorpeerid(self, transaction):
        """ lookup peerid """
        self.logger.debug('DKBRobo._add_account_transaction_debtorpeerid()\n')
        peer_id = ''
        if 'id' in transaction['attributes']['debtor']:
            peer_id = transaction['attributes']['debtor']['id']

        return peer_id

    def _add_account_transactioninformation(self, transaction):
        """ add infromation from accont transaction """
        self.logger.debug('DKBRobo._add_account_transactioninformation()\n')

        output_dic = {}
        if 'bookingDate' in transaction['attributes']:
            output_dic['date'] = transaction['attributes']['bookingDate']
            output_dic['bdate'] = transaction['attributes']['bookingDate']
        if 'valueDate' in transaction['attributes']:
            output_dic['vdate'] = transaction['attributes']['valueDate']
        if 'endToEndId' in transaction['attributes']:
            output_dic['customerreferenz'] = transaction['attributes']['endToEndId']
        if 'transactionType' in transaction['attributes']:
            output_dic['postingtext'] = transaction['attributes']['transactionType']
        if 'description' in transaction['attributes']:
            output_dic['reasonforpayment'] = transaction['attributes']['description']

        return output_dic

    def _get_account_details(self, aid, accounts_dic, group_name, product_settings_dic):
        """ get credit account details from cc json """
        self.logger.debug('DKBRobo._get_account_details(%s)\n', aid)

        output_dic = {}
        if 'data' in accounts_dic:
            for account in accounts_dic['data']:
                if account['id'] == aid and 'attributes' in account:
                    # build dictionary with account information
                    output_dic = {**self._add_accountinformation(account, aid, group_name), **self._add_accountdetails(account), **self._add_accountbalance(account), **self._add_accountname(account, product_settings_dic, aid)}
                    break

        return output_dic

    def _add_accountbalance(self, account):
        """ add balance to dictionary """
        self.logger.debug('DKBRobo._add_accountbalance()\n')

        output_dic = {}
        if 'balance' in account['attributes']:
            mapping_dic = {'amount': 'value', 'currencycode': 'currencyCode'}
            for my_field, dkb_field in mapping_dic.items():
                if dkb_field in account['attributes']['balance']:
                    output_dic[my_field] = account['attributes']['balance'][dkb_field]

        return output_dic

    def _add_accountdetails(self, account):
        """ add several details to dictionaries """
        self.logger.debug('DKBRobo._add_accountdetails()\n')

        output_dic = {}
        mapping_dic = {'iban': 'iban', 'account': 'iban', 'holdername': 'holderName', 'limit': 'overdraftLimit'}
        for my_field, dkb_field in mapping_dic.items():
            if dkb_field in account['attributes']:
                output_dic[my_field] = account['attributes'][dkb_field]

        return output_dic

    def _add_accountinformation(self, account, aid, group_name):
        """ add general account information """
        self.logger.debug('DKBRobo._add_accountinformation()\n')

        output_dic = {}
        output_dic['type'] = 'account'
        output_dic['id'] = aid
        output_dic['productgroup'] = group_name
        output_dic['transactions'] = self.banking_url + self.api_prefix + f"/accounts/accounts/{aid}/transactions"
        if 'updatedAt' in account['attributes']:
            output_dic['date'] = account['attributes']['updatedAt']
        return output_dic

    def _add_accountname(self, account, product_settings_dic, aid):
        """ add card name """
        self.logger.debug('DKBRobo._add_accountname()\n')

        output_dic = {}
        # overwrite display name set in ui
        if 'accounts' in product_settings_dic:
            output_dic['name'] = self._display_name_lookup(aid, product_settings_dic['accounts'], account['attributes']['product']['displayName'])
        else:
            output_dic['name'] = account['attributes']['product']['displayName']

        return output_dic

    def _add_brokerage_informationy(self, position):
        """ add lastorder date and value """
        self.logger.debug('DKBRobo._add_brokerage_informationy()\n')

        output_dic = {}
        if 'lastOrderDate' in position['attributes']:
            output_dic['lastorderdate'] = position['attributes']['lastOrderDate']

        if 'performance' in position['attributes'] and 'currentValue' in position['attributes']['performance'] and 'value' in position['attributes']['performance']['currentValue']:
            output_dic['price_euro'] = position['attributes']['performance']['currentValue']['value']

        return output_dic

    def _add_brokerage_instrumentinformation(self, ele):
        """ add instrument information """
        self.logger.debug('DKBRobo._add_brokerage_instrumentinformation()\n')

        output_dic = {}
        if 'attributes' in ele:
            if 'name' in ele['attributes'] and 'short' in ele['attributes']['name']:
                output_dic['text'] = ele['attributes']['name']['short']
            if 'identifiers' in ele['attributes']:
                for identifier in ele['attributes']['identifiers']:
                    if identifier['identifier'] == 'isin':
                        output_dic['isin_wkn'] = identifier['value']
                        break
        return output_dic

    def _add_brokerage_quoteinformation(self, ele):
        """ add quote information """
        self.logger.debug('DKBRobo._add_brokerage_quoteinformation()\n')

        output_dic = {}
        if 'attributes' in ele and 'price' in ele['attributes']:
            if 'value' in ele['attributes']['price']:
                output_dic['price'] = float(ele['attributes']['price']['value'])
            if 'currencyCode' in ele['attributes']['price']:
                output_dic['currencycode'] = ele['attributes']['price']['currencyCode']
        if 'market' in ele['attributes']:
            output_dic['market'] = ele['attributes']['market']

        return output_dic

    def _add_brokerage_quantity(self, position):
        """ add quantity information """
        self.logger.debug('DKBRobo._add_brokerage_quantity()\n')
        output_dic = {}
        if 'quantity' in position['attributes']:
            output_dic['shares'] = position['attributes']['quantity']['value']
            output_dic['quantity'] = float(position['attributes']['quantity']['value'])
            output_dic['shares_unit'] = position['attributes']['quantity']['unit']

        return output_dic

    def _add_brokerageholder(self, depot, bid, product_settings_dic):
        """ add card holder information """
        self.logger.debug('DKBRobo._add_brokerageholder()\n')

        output_dic = {}
        # set display name
        if 'brokerageAccounts' in product_settings_dic:
            output_dic['name'] = self._display_name_lookup(bid, product_settings_dic['brokerageAccounts'], depot['attributes']['holderName'])
        else:
            output_dic['name'] = depot['attributes']['holderName']

        return output_dic

    def _add_brokerageinformation(self, depot, bid, group_name):
        """ add depot information """
        self.logger.debug('DKBRobo._add_brokerageinformation()\n')

        output_dic = {}
        output_dic['type'] = 'depot'
        output_dic['id'] = bid
        output_dic['productgroup'] = group_name
        output_dic['transactions'] = self.banking_url + self.api_prefix + f"/broker/brokerage-accounts/{bid}/positions?include=instrument%2Cquote"
        if 'holderName' in depot['attributes']:
            output_dic['holdername'] = depot['attributes']['holderName']
        if 'depositAccountId' in depot['attributes']:
            output_dic['account'] = depot['attributes']['depositAccountId']

        return output_dic

    def _add_brokerageperformance(self, depot):
        """ add depot value and currentcy """
        self.logger.debug('DKBRobo._add_brokerage_performance()\n')

        output_dic = {}
        if 'brokerageAccountPerformance' in depot['attributes']:
            if 'currentValue' in depot['attributes']['brokerageAccountPerformance']:
                if 'currencyCode' in depot['attributes']['brokerageAccountPerformance']['currentValue']:
                    output_dic['currencycode'] = depot['attributes']['brokerageAccountPerformance']['currentValue']['currencyCode']
                if 'value' in depot['attributes']['brokerageAccountPerformance']['currentValue']:
                    output_dic['amount'] = depot['attributes']['brokerageAccountPerformance']['currentValue']['value']

        return output_dic

    def _add_card_transactionamount(self, transaction):
        """ add amount from card transaction """
        self.logger.debug('DKBRobo._add_card_transactionamount()\n')
        output_dic = {}
        if 'amount' in transaction['attributes']:
            if 'value' in transaction['attributes']['amount']:
                output_dic['amount'] = float(transaction['attributes']['amount']['value'])
            if 'currencyCode' in transaction['attributes']['amount']:
                output_dic['currencycode'] = transaction['attributes']['amount']['currencyCode']

        return output_dic

    def _add_cardbalance(self, card):
        """ add card balance to dictionary """
        self.logger.debug('DKBRobo._add_cardbalance()\n')

        output_dic = {}
        if 'balance' in card['attributes']:
            # DKB show it in a weired way
            if 'value' in card['attributes']['balance']:
                output_dic['amount'] = float(card['attributes']['balance']['value']) * -1
            if 'currencyCode' in card['attributes']['balance']:
                output_dic['currencycode'] = card['attributes']['balance']['currencyCode']
            if 'date' in card['attributes']['balance']:
                output_dic['date'] = card['attributes']['balance']['date']

        return output_dic

    def _add_cardholder(self, card):
        """ add card holder information """
        self.logger.debug('DKBRobo._add_cardholder()\n')

        output_dic = {}
        if 'holder' in card['attributes'] and 'person' in card['attributes']['holder']:
            if 'firstName' in card['attributes']['holder']['person'] and 'lastName' in card['attributes']['holder']['person']:
                output_dic['holdername'] = f"{card['attributes']['holder']['person']['firstName']} {card['attributes']['holder']['person']['lastName']}"

        return output_dic

    def _add_cardinformation(self, card, cid, group_name):
        """ add general information of card """
        self.logger.debug('DKBRobo._add_cardinformation()\n')

        output_dic = {}
        output_dic['type'] = 'creditcard'
        output_dic['id'] = cid
        output_dic['productgroup'] = group_name
        output_dic['transactions'] = self.banking_url + self.api_prefix + f"/credit-card/cards/{cid}/transactions"
        if 'maskedPan' in card['attributes']:
            output_dic['maskedpan'] = card['attributes']['maskedPan']
            output_dic['account'] = card['attributes']['maskedPan']

        return output_dic

    def _add_cardlimit(self, card):
        """ add cardlimit """
        self.logger.debug('DKBRobo._add_cardlimit()\n')

        output_dic = {}
        if 'limit' in card['attributes'] and 'value' in card['attributes']['limit']:
            output_dic['limit'] = card['attributes']['limit']['value']

        return output_dic

    def _add_card_transactioninformation(self, transaction):
        """ add card transaction infromatoin """
        self.logger.debug('DKBRobo._add_card_transactioninformation()\n')
        output_dic = {}
        if 'bookingDate' in transaction['attributes']:
            output_dic['bdate'] = transaction['attributes']['bookingDate']
            output_dic['vdate'] = transaction['attributes']['bookingDate']
        if 'description' in transaction['attributes']:
            output_dic['text'] = transaction['attributes']['description']
        return output_dic

    def _add_cardname(self, card, product_settings_dic, cid):
        """ add card name """
        self.logger.debug('DKBRobo._add_cardname()\n')

        output_dic = {}
        if 'creditCards' in product_settings_dic:
            output_dic['name'] = self._display_name_lookup(cid, product_settings_dic['creditCards'], card['attributes']['product']['displayName'])
        else:
            output_dic['name'] = card['attributes']['product']['displayName']

        return output_dic

    def _build_account_dic(self, portfolio_dic):
        """ create overview """
        self.logger.debug('DKBRobo._build_account_list()\n')

        account_dic = {}
        account_cnt = 0
        if 'product_display' in portfolio_dic and 'data' in portfolio_dic['product_display']:
            for data_ele in portfolio_dic['product_display']['data']:

                # build product settings dictioary needed to sort the productgroup
                product_settings_dic = self._build_product_settings_dic(data_ele)

                if 'attributes' in data_ele and 'productGroups' in data_ele['attributes']:
                    # sorting should be similar to frontend
                    for product_group in sorted(data_ele['attributes']['productGroups'].values(), key=lambda x: x['index']):
                        product_group_name = product_group['name']
                        product_group_dic, account_cnt = self._sort_product_group(account_cnt, product_settings_dic, product_group_name, product_group, portfolio_dic['accounts'], portfolio_dic['cards'], portfolio_dic['brokerage_accounts'])
                        account_dic = {**account_dic, **product_group_dic}

        return account_dic

    def _build_product_settings_dic(self, data_ele):
        """ build products settings dictionary """
        self.logger.debug('DKBRobo._build_product_settings_dic()\n')

        if 'attributes' in data_ele and 'productSettings' in data_ele['attributes']:
            product_settings_dic = data_ele['attributes']['productSettings']
        else:
            product_settings_dic = {}

        return product_settings_dic

    def _check_processing_status(self, polling_dic, cnt):
        self.logger.debug('DKBRobo._check_processing_status()\n')
        self.logger.debug('DKBRobo._login: cnt %s got %s flag', cnt, polling_dic['data']['attributes']['verificationStatus'])

        mfa_completed = False
        if (polling_dic['data']['attributes']['verificationStatus']) == 'processed':
            mfa_completed = True
        elif (polling_dic['data']['attributes']['verificationStatus']) == 'canceled':
            raise DKBRoboError('2fa chanceled by user')
        return mfa_completed

    def _complete_2fa(self, challenge_id, devicename):
        """ wait for confirmation for the 2nd factor """
        self.logger.debug('DKBRobo._complete_2fa()\n')

        self._print_2fa_confirmation(devicename)

        cnt = 0
        mfa_completed = False
        # we give us 50 seconds to press a button on the phone
        while cnt <= 10:
            response = self.client.get(self.banking_url + self.api_prefix + f"/mfa/mfa/challenges/{challenge_id}")
            cnt += 1
            if response.status_code == 200:
                polling_dic = response.json()
                if 'data' in polling_dic and 'attributes' in polling_dic['data'] and 'verificationStatus' in polling_dic['data']['attributes']:
                    # check processing status
                    mfa_completed = self._check_processing_status(polling_dic, cnt)
                    if mfa_completed:
                        break
                else:
                    self.logger.error('DKBRobo._complete_2fa(): error parsing polling response: %s', polling_dic)
            else:
                self.logger.error('DKBRobo._complete_2fa(): polling request failed. RC: %s', response.status_code)
            time.sleep(5)

        return mfa_completed

    def _display_name_lookup(self, oid, display_settings, product_name):
        """ replace product name with name displayed in UI """
        self.logger.debug('DKBRobo._diplay_name_lookup(%s)\n', product_name)
        if oid in display_settings and 'name' in display_settings[oid]:
            product_name = display_settings[oid]['name']

        return product_name

    def _do_sso_redirect(self):
        """  redirect to access legacy page """
        self.logger.debug('DKBRobo._do_sso_redirect()\n')

        data_dic = {'data': {'cookieDomain': '.dkb.de'}}
        self.client.headers['Content-Type'] = 'application/json'
        self.client.headers['Sec-Fetch-Dest'] = 'empty'
        self.client.headers['Sec-Fetch-Mode'] = 'cors'
        self.client.headers['Sec-Fetch-Site'] = 'same-origin'

        response = self.client.post(self.banking_url + self.api_prefix + '/sso-redirect', data=json.dumps(data_dic))

        if response.status_code != 200 or response.text != 'OK':
            self.logger.error('SSO redirect failed. RC: %s text: %s', response.status_code, response.text)

        clientcookies = self.client.cookies
        self.dkb_br = self._new_instance(clientcookies)

    def _format_account_transactions(self, transaction_list):
        """ format transactions """
        self.logger.debug('DKBRobo._format_transactions()\n')

        format_transaction_list = []
        for transaction in transaction_list:
            if 'attributes' in transaction:
                transaction_dic = {**self._add_account_transactionamount(transaction), **self._add_account_transactioninformation(transaction)}

                if transaction_dic['amount'] > 0:
                    # incoming payment - collect debitor information
                    transaction_dic = {**transaction_dic, **self._add_account_transaction_debtorinfo(transaction)}
                else:
                    # outgoing payment - collect creditor information
                    transaction_dic = {**transaction_dic, **self._add_account_transaction_creditorinfo(transaction)}

                # add posting test for backwards compability
                if 'postingtext' in transaction_dic and 'peer' in transaction_dic and 'reasonforpayment' in transaction_dic:
                    transaction_dic['text'] = f'{transaction_dic["postingtext"]} {transaction_dic["peer"]} {transaction_dic["reasonforpayment"]}'

                format_transaction_list.append(transaction_dic)

        return format_transaction_list

    def _format_brokerage_account(self, brokerage_dic):
        """ format brokerage dictionary """
        self.logger.debug('DKBRobo._format_brokerage_account(%s)\n', len(brokerage_dic))

        position_list = []
        included_list = self._get_brokerage_includedlist(brokerage_dic)
        if 'data' in brokerage_dic:
            for position in brokerage_dic['data']:
                position_dic = self._get_brokerage_position(position, included_list)
                if position_dic:
                    position_list.append(position_dic)

        return position_list

    def _format_card_transactions(self, transaction_list):
        """ format credit card transactions """
        self.logger.debug('DKBRobo._format_card_transactions(%s)\n', len(transaction_list))

        format_transaction_list = []
        for transaction in transaction_list:
            if 'attributes' in transaction:
                transaction_dic = {**self._add_card_transactionamount(transaction), **self._add_card_transactioninformation(transaction)}
                format_transaction_list.append(transaction_dic)

        return format_transaction_list

    def _get_accounts(self):
        """ get accounts via API """
        self.logger.debug('DKBRobo._get_accounts()\n')

        response = self.client.get(self.banking_url + self.api_prefix + '/accounts/accounts')
        if response.status_code == 200:
            account_dic = response.json()
        else:
            self.logger.error('DKBRobo._get_accounts(): RC is not 200 but %s', response.status_code)
            account_dic = {}

        return account_dic

    def _get_brokerage_accounts(self):
        """ get brokerage_accounts via API """
        self.logger.debug('DKBRobo._get_brokerage_accounts()\n')

        response = self.client.get(self.banking_url + self.api_prefix + '/broker/brokerage-accounts')
        if response.status_code == 200:
            account_dic = response.json()
        else:
            self.logger.error('DKBRobo._get_brokerage_accounts(): RC is not 200 but %s', response.status_code)
            account_dic = {}

        return account_dic

    def _get_brokerage_details(self, bid, brokerage_dic, group_name, product_settings_dic):
        """ get depod details from brokerage json """
        self.logger.debug('DKBRobo._get_brokerage_details(%s)\n', bid)

        output_dic = {}
        if 'data' in brokerage_dic:
            for depot in brokerage_dic['data']:
                if depot['id'] == bid and 'attributes' in depot:
                    output_dic = {**self._add_brokerageinformation(depot, bid, group_name), **self._add_brokerageperformance(depot), **self._add_brokerageholder(depot, bid, product_settings_dic)}
                    break

        return output_dic

    def _get_brokerage_includedlist(self, brokerage_dic):
        """ get include list from brokerage_account dictionary"""
        self.logger.debug('DKBRobo._get_brokerage_includedlist()\n')

        included_list = []
        if 'included' in brokerage_dic:
            included_list = brokerage_dic['included']

        return included_list

    def _get_cards(self):
        """ get cards via API """
        self.logger.debug('DKBRobo._get_cards()\n')

        response = self.client.get(self.banking_url + self.api_prefix + '/credit-card/cards?filter%5Btype%5D=creditCard&filter%5Bportfolio%5D=dkb&filter%5Btype%5D=debitCard')
        if response.status_code == 200:
            card_dic = response.json()
        else:
            self.logger.error('DKBRobo._get_cards(): RC is not 200 but %s', response.status_code)
            card_dic = {}

        return card_dic

    def _get_card_details(self, cid, cards_dic, group_name, product_settings_dic):
        """ get credit card details from cc json """
        self.logger.debug('DKBRobo._get_cc_details(%s)\n', cid)

        output_dic = {}
        if 'data' in cards_dic:
            for card in cards_dic['data']:
                if card['id'] == cid and 'attributes' in card:
                    # build dictionary with card information
                    output_dic = {**self._add_cardinformation(card, cid, group_name), **self._add_cardholder(card), **self._add_cardlimit(card), **self._add_cardbalance(card), **self._add_cardname(card, product_settings_dic, cid)}
                    break

        return output_dic

    def _get_loans(self):
        """ get loands via API """
        self.logger.debug('DKBRobo._get_loans()\n')
        response = self.client.get(self.banking_url + self.api_prefix + '/loans/loans')
        if response.status_code == 200:
            loans_dic = response.json()
        else:
            self.logger.error('DKBRobo._get_loans(): RC is not 200 but %s', response.status_code)
            loans_dic = {}

        return loans_dic

    def _get_mfa_challenge_id(self, mfa_dic, device_num=0):
        """ get challenge dict with information on the 2nd factor """
        self.logger.debug('DKBRobo._get_mfa_challenge_id() login with device_num: %s\n', device_num)

        challenge_id = None
        device_name = None

        if 'data' in mfa_dic and 'id' in mfa_dic['data'][device_num]:
            try:
                device_name = mfa_dic['data'][device_num]['attributes']['deviceName']
                self.logger.debug('DKBRobo._get_mfa_challenge_id(): devicename: %s\n', device_name)
            except Exception as _err:
                self.logger.error('DKBRobo._get_mfa_challenge_id(): unable to get deviceName')
                device_name = None

            # additional headers needed as this call requires it
            self.client.headers['Content-Type'] = 'application/vnd.api+json'
            self.client.headers["Accept"] = "application/vnd.api+json"

            # we are expecting the first method from mfa_dic to be used
            data_dic = {'data': {'type': 'mfa-challenge', 'attributes': {'mfaId': self.token_dic['mfa_id'], 'methodId': mfa_dic['data'][device_num]['id'], 'methodType': self.mfa_method}}}
            response = self.client.post(self.banking_url + self.api_prefix + '/mfa/mfa/challenges', data=json.dumps(data_dic))

            # process response
            challenge_id = self._process_challenge_response(response)

            # we rmove the headers we added earlier
            self.client.headers.pop('Content-Type')
            self.client.headers.pop('Accept')

        else:
            self.logger.error('DKBRobo._get_mfa_challenge_id(): mfa_dic has an unexpected data structure')

        return challenge_id, device_name

    def _get_mfa_methods(self):
        """ get mfa methods """
        self.logger.debug('DKBRobo._get_mfa_methods()\n')
        mfa_dic = {}

        # check for access_token and get mfa_methods
        if 'access_token' in self.token_dic:
            response = self.client.get(self.banking_url + self.api_prefix + f'/mfa/mfa/methods?filter%5BmethodType%5D={self.mfa_method}')
            if response.status_code == 200:
                mfa_dic = response.json()
            else:
                raise DKBRoboError(f'Login failed: getting mfa_methods failed. RC: {response.status_code}')
        else:
            raise DKBRoboError('Login failed: no 1fa access token.')

        return mfa_dic

    def _get_brokerage_position(self, position, included_list):
        """ get information on a single position witin a brokerage account """
        self.logger.debug('DKBRobo._get_brokerage_position()\n')
        (_instrument_id, _quote_id) = self._get_relationship_ids(position)

        position_dic = {}
        if 'attributes' in position:
            position_dic = {**self._add_brokerage_quantity(position), **self._add_brokerage_informationy(position)}
            for ele in included_list:
                if 'id' in ele and ele['id'] == _instrument_id:
                    position_dic = {**position_dic, **self._add_brokerage_instrumentinformation(ele)}
                if 'id' in ele and ele['id'] == _quote_id:
                    position_dic = {**position_dic, **self._add_brokerage_quoteinformation(ele)}

        return position_dic

    def _get_overview(self):
        """ get portfolio via api """
        self.logger.debug('DKBRobo.get_portfolio()\n')

        # we calm the IDS system of DKB with two calls without sense
        self.client.get(self.banking_url + self.api_prefix + '/terms-consent/consent-requests??filter%5Bportfolio%5D=DKB')
        response = self.client.get(self.banking_url + self.api_prefix + '/config/users/me/product-display-settings')

        portfolio_dic = {}
        if response.status_code == 200:
            portfolio_dic['product_display'] = response.json()
            portfolio_dic['accounts'] = self._get_accounts()
            portfolio_dic['cards'] = self._get_cards()
            portfolio_dic['brokerage_accounts'] = self._get_brokerage_accounts()
            portfolio_dic['loands'] = self._get_loans()

        self.account_dic = self._build_account_dic(portfolio_dic)

    def _get_relationship_ids(self, position):
        """ get relationship ids from depot position """
        self.logger.debug('DKBRobo._get_relationship_ids()\n')

        instrument_id = None
        quote_id = None
        if 'relationships' in position:
            if 'instrument' in position['relationships'] and 'data' in position['relationships']['instrument'] and 'id' in position['relationships']['instrument']['data']:
                instrument_id = position['relationships']['instrument']['data']['id']
            if 'quote' in position['relationships'] and 'data' in position['relationships']['quote'] and 'id' in position['relationships']['quote']['data']:
                quote_id = position['relationships']['quote']['data']['id']

        return instrument_id, quote_id

    def _get_token(self):
        """ get access token """
        self.logger.debug('DKBRobo._get_token()\n')

        # login via API
        data_dic = {'grant_type': 'banking_user_sca', 'username': self.dkb_user, 'password': self.dkb_password, 'sca_type': 'web-login'}
        response = self.client.post(self.banking_url + self.api_prefix + '/token', data=data_dic)
        if response.status_code == 200:
            self.token_dic = response.json()
        else:
            raise DKBRoboError(f'Login failed: 1st factor authentication failed. RC: {response.status_code}')

    def _get_transactions(self, transaction_url, atype, date_from, date_to, transaction_type):
        """ get transactions via API """
        self.logger.debug('DKBRobo._get_transactions(%s, %s)\n', atype, transaction_type)

        transaction_list = []

        response = self.client.get(transaction_url)
        if response.status_code == 200:
            transaction_dic = response.json()
        else:
            self.logger.error('DKBRobo._get_transactions(): RC is not 200 but %s', response.status_code)
            transaction_dic = {}

        if transaction_dic and 'data' in transaction_dic:
            if atype == 'account':
                transaction_list = self._filter_transactions(transaction_dic['data'], date_from, date_to, transaction_type)
                transaction_list = self._format_account_transactions(transaction_list)
            elif atype == 'creditcard':
                transaction_list = self._filter_transactions(transaction_dic['data'], date_from, date_to, transaction_type)
                transaction_list = self._format_card_transactions(transaction_list)
            elif atype == 'depot':
                transaction_list = self._format_brokerage_account(transaction_dic)

        return transaction_list

    def _filter_transactions(self, transaction_list, date_from, date_to, transaction_type):
        """ filter transaction by date """
        self.logger.debug('DKBRobo._filter_transactions()\n')

        try:
            date_from_uts = int(time.mktime(datetime.strptime(date_from, LEGACY_DATE_FORMAT).timetuple()))
        except ValueError:
            date_from_uts = int(time.mktime(datetime.strptime(date_from, API_DATE_FORMAT).timetuple()))

        try:
            date_to_uts = int(time.mktime(datetime.strptime(date_to, LEGACY_DATE_FORMAT).timetuple()))
        except ValueError:
            date_to_uts = int(time.mktime(datetime.strptime(date_to, API_DATE_FORMAT).timetuple()))

        filtered_transaction_list = []
        for transaction in transaction_list:
            if 'attributes' in transaction and 'status' in transaction['attributes'] and 'bookingDate' in transaction['attributes']:
                if transaction['attributes']['status'] == transaction_type:
                    bookingdate_uts = int(time.mktime(datetime.strptime(transaction['attributes']['bookingDate'], API_DATE_FORMAT).timetuple()))
                    if date_from_uts <= bookingdate_uts <= date_to_uts:
                        filtered_transaction_list.append(transaction)

        return filtered_transaction_list

    def _login(self):
        """ login into DKB banking area and perform an sso redirect """
        self.logger.debug('DKBRobo._login()\n')

        mfa_dic = {}

        # create new session
        self.client = self._new_session()

        # get token for 1fa
        self._get_token()

        # get mfa methods
        mfa_dic = self._get_mfa_methods()

        # pick mfa device from list
        device_number = self._select_mfa_device(mfa_dic)

        # we need a challege-id for polling so lets try to get it
        mfa_challenge_id = None
        if 'mfa_id' in self.token_dic and 'data' in mfa_dic:
            mfa_challenge_id, device_name = self._get_mfa_challenge_id(mfa_dic, device_number)
        else:
            raise DKBRoboError('Login failed: no 1fa access token.')

        # lets complete 2fa
        mfa_completed = False
        if mfa_challenge_id:
            mfa_completed = self._complete_2fa(mfa_challenge_id, device_name)
        else:
            raise DKBRoboError('Login failed: No challenge id.')

        # update token dictionary
        if mfa_completed and 'access_token' in self.token_dic:
            self._update_token()
        else:
            raise DKBRoboError('Login failed: mfa did not complete')

        if 'token_factor_type' not in self.token_dic:
            raise DKBRoboError('Login failed: token_factor_type is missing')

        if 'token_factor_type' in self.token_dic and self.token_dic['token_factor_type'] != '2fa':

            raise DKBRoboError('Login failed: 2nd factor authentication did not complete')

        # get account overview
        self._get_overview()

        # redirect to legacy page
        self._do_sso_redirect()

    def _new_session(self):
        """ new request session for the api calls """
        self.logger.debug('DKBRobo._new_session()\n')

        headers = {
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0'}
        client = requests.session()
        client.headers = headers
        if self.proxies:
            client.proxies = self.proxies
            client.verify = False

        # get cookies
        client.get(self.banking_url + '/login')

        # add csrf token
        if '__Host-xsrf' in client.cookies:
            headers['x-xsrf-token'] = client.cookies['__Host-xsrf']
            client.headers = headers

        return client

    def _print_2fa_confirmation(self, devicename):
        """ 2fa confirmation message """
        self.logger.debug('DKBRobo._print_2fa_confirmation()\n')
        if devicename:
            print(f'check your banking app on "{devicename}" and confirm login...')
        else:
            print('check your banking app and confirm login...')

    def _process_challenge_response(self, response):
        """ get challenge dict with information on the 2nd factor """
        self.logger.debug('DKBRobo._process_challenge_response()\n')
        challenge_id = None
        if response.status_code in (200, 201):
            challenge_dic = response.json()
            if 'data' in challenge_dic and 'id' in challenge_dic['data'] and 'type' in challenge_dic['data']:
                if challenge_dic['data']['type'] == 'mfa-challenge':
                    challenge_id = challenge_dic['data']['id']
                else:
                    raise DKBRoboError(f'Login failed:: wrong challenge type: {challenge_dic}')

            else:
                raise DKBRoboError(f'Login failed: challenge response format is other than expected: {challenge_dic}')
        else:
            raise DKBRoboError(f'Login failed: post request to get the mfa challenges failed. RC: {response.status_code}')

        return challenge_id

    def _process_userinput(self, device_num, device_list, _tmp_device_num, deviceselection_completed):
        self.logger.debug('DKBRobo._process_userinput(%s)', _tmp_device_num)
        try:
            if int(_tmp_device_num) in device_list:
                deviceselection_completed = True
                device_num = int(_tmp_device_num)
            else:
                print('\nWrong input!')
        except Exception:
            print('\nInvalid input!')

        return device_num, deviceselection_completed

    def _update_token(self):
        """ update token information with 2fa iformation """
        self.logger.debug('DKBRobo._update_token()\n')

        data_dic = {'grant_type': 'banking_user_mfa', 'mfa_id': self.token_dic['mfa_id'], 'access_token': self.token_dic['access_token']}
        response = self.client.post(self.banking_url + self.api_prefix + '/token', data=data_dic)
        if response.status_code == 200:
            self.token_dic = response.json()
        else:
            raise DKBRoboError(f'Login failed: token update failed. RC: {response.status_code}')

    def _select_mfa_device(self, mfa_dic):
        """ pick mfa_device from dictionary """
        self.logger.debug('_select_mfa_device()')
        device_num = 0

        if 'data' in mfa_dic and len(mfa_dic['data']) > 1:
            device_list = []
            deviceselection_completed = False
            while not deviceselection_completed:
                print('\nPick an authentication device from the below list:')
                # we have multiple devices to select
                for idx, device_dic in enumerate(mfa_dic['data']):
                    device_list.append(idx)
                    if 'attributes' in device_dic and 'deviceName' in device_dic['attributes']:
                        print(f"[{idx}] - {device_dic['attributes']['deviceName']}")
                _tmp_device_num = input(':')

                device_num, deviceselection_completed = self._process_userinput(device_num, device_list, _tmp_device_num, deviceselection_completed)

        self.logger.debug('_select_mfa_device() ended with: %s', device_num)
        return device_num

    def _sort_product_group(self, account_cnt, product_settings_dic, group_name, product_group, accounts_dic, cards_dic, brokerage_dic):
        """ sort products and productsgroup as shown in ui and get details """
        self.logger.debug('DKBRobo._sort_product_group()\n')
        product_dic = {}
        if 'products' in product_group:
            for product, data_dic in product_group['products'].items():
                for pid, _product_data in sorted(data_dic.items(), key=lambda x: x[1]['index']):
                    if product == 'accounts':
                        product_dic[account_cnt] = self._get_account_details(pid, accounts_dic, group_name, product_settings_dic)
                    elif product == 'creditCards':
                        product_dic[account_cnt] = self._get_card_details(pid, cards_dic, group_name, product_settings_dic)
                    elif product == 'brokerageAccounts':
                        product_dic[account_cnt] = self._get_brokerage_details(pid, brokerage_dic, group_name, product_settings_dic)
                    else:
                        self.logger.error('DKBRobo._sort_product_group(): product %s not implemented yet.', product)
                    account_cnt += 1

        return product_dic, account_cnt

    #
    # private objects using the legacy api
    #

    def _check_confirmation(self, result, poll_id):
        """ check if login has been confirmed via app
            args:
                result - result of polling request
            returns:
                login_confirmed - confirmation status True/False
        """
        self.logger.debug('DKBRobo._check_confirmation()\n')
        login_confirmed = False
        if 'state' in result:
            # new dkb mfa app
            self.logger.debug('mfa poll(id: %s status: %s)\n', poll_id, result['state'])
            # pylint: disable=R1723
            if result['state'] == 'PROCESSED':
                self.logger.debug('Session got confirmed...\n')
                login_confirmed = True
            elif result['state'] == 'EXPIRED':
                raise DKBRoboError('Session expired')
        elif 'guiState' in result:
            # legacy dkb app
            self.logger.debug('legacy poll(id: %s status: %s)\n', poll_id, result['guiState'])
            # pylint: disable=R1723
            if result['guiState'] == 'MAP_TO_EXIT':
                self.logger.debug('Session got confirmed...\n')
                login_confirmed = True
            elif result['guiState'] == 'EXPIRED':
                raise DKBRoboError('Session expired')
        else:
            raise DKBRoboError('Error during session confirmation')

        self.logger.debug('DKBRobo._check_confirmation() ended with %s\n', login_confirmed)
        return login_confirmed

    def _ctan_check(self, _soup):
        """ input of chiptan during login """
        self.logger.debug('DKBRobo._ctan_check()\n')

        event_field = '$event'

        try:
            self.dkb_br.select_form('form[name="confirmForm"]')
            self.dkb_br[event_field] = 'tanVerification'
        except Exception as _err:
            self.logger.debug('confirmForm not found\n')

        try:
            self.dkb_br.select_form('form[name="next"]')
            self.dkb_br[event_field] = 'next'
        except Exception:
            self.logger.debug('nextForm not found\n')

        # open page to insert tan
        self.dkb_br.submit_selected()
        soup = self.dkb_br.get_current_page()

        login_confirm = False

        # select tan form
        self.dkb_br.select_form('#next')
        # print steps to be done
        olist = soup.find("ol")
        if olist:
            for li_ in olist.findAll('li'):
                print(li_.text.strip())
        else:
            print('Please open the TAN2GO app to get a TAN to be inserted below.')

        # ask for TAN
        self.dkb_br["tan"] = input("TAN: ")
        self.dkb_br[event_field] = 'next'

        # submit form and check response
        self.dkb_br.submit_selected()
        soup = self.dkb_br.get_current_page()

        # catch tan error
        # pylint: disable=R1720
        if soup.find("div", attrs={'class': 'clearfix module text errorMessage'}):
            raise DKBRoboError('Login failed due to wrong TAN')
        else:
            self.logger.debug('TAN is correct...\n')
            login_confirm = True

        self.logger.debug('DKBRobo._ctan_check() ended with :%s\n', login_confirm)
        return login_confirm

    def _download_document(self, folder_url, path, class_filter, folder, table, prepend_date):
        """ document download """
        self.logger.debug('_download_document()\n')
        document_dic = {}
        document_name_list = []

        tbody = table.find('tbody')
        for row in tbody.findAll('tr', class_filter):
            link = row.find('a')

            # get formatted date
            formatted_date = self._get_formatted_date(prepend_date, row)

            # download file
            if path:
                folder_path = f'{path}/{folder}'
                rcode, fname, document_name_list = self._get_document(folder_url, folder_path, self.base_url + link['href'], document_name_list, formatted_date)
                if rcode == 200:
                    # mark url as read
                    self._update_downloadstate(folder, self.base_url + link['href'])
                if rcode:
                    document_dic[link.contents[0]] = {'rcode': rcode, 'link': self.base_url + link['href'], 'fname': fname}
                else:
                    document_dic[link.contents[0]] = self.base_url + link['href']
            else:
                document_dic[link.contents[0]] = self.base_url + link['href']
        return (document_dic, document_name_list)

    def _get_amount(self, cols, ontop):
        """ get link for transactions """
        self.logger.debug('_get_amount()')

        amount = cols[3 + ontop].text.strip().replace('.', '')
        try:
            result = float(amount.replace(',', '.'))
        except Exception as _err:
            self.logger.error('DKBRobo._parse_overview() convert amount: %s\n', _err)
            result = None

        return result

    def _get_cc_limits(self, form):
        """ get credit card limits """
        self.logger.debug('DKBRobo._get_cc_limits()\n')

        limit_dic = {}
        table = form.find('table', attrs={'class': 'multiColumn'})
        if table:
            rows = table.findAll("tr")
            for row in rows:
                cols = row.findAll("td")
                tmp = row.find("th")
                if cols:
                    try:
                        limit = tmp.find('span').text.strip()
                        account = cols[0].find('div', attrs={'class': 'minorLine'}).text.strip()
                        limit_dic[account] = string2float(limit)
                    except Exception as _err:
                        self.logger.error('DKBRobo.get_credit_limits() get credit card limits: %s\n', _err)

        return limit_dic

    def _get_checking_account_limit(self, form):
        """ get checking account limits """
        self.logger.debug('DKBRobo._get_checking_account_limit()\n')

        limit_dic = {}
        table = form.find('table', attrs={'class': 'dropdownAnchor'})
        if table:
            for row in table.findAll("tr"):
                cols = row.findAll("td")
                tmp = row.find("th")
                if cols:
                    limit = tmp.find('span').text.strip()
                    account = cols[0].find('div', attrs={'class': 'minorLine'}).text.strip()
                    limit_dic[account] = string2float(limit)

        return limit_dic

    def _get_document(self, folder_url, path, url, document_name_list, formatted_date):
        """ get download document from postbox
        args:
            self.dkb_br - browser object
            path - path to store the document
            url - download url
        returns:
            http response code
        """
        self.logger.debug('DKBRobo._get_document(%s)\n', url)

        # create directory if not existing
        if not os.path.exists(path):
            self.logger.debug('create directory %s\n', path)
            os.makedirs(path)

        # fetch file
        response = self.dkb_br.open(folder_url)
        response = self.dkb_br.open(url)

        # gt filename from response header
        fname = ''
        if "Content-Disposition" in response.headers.keys():
            self.logger.debug('DKBRobo._get_document(): response.header: %s\n', response.headers)
            # unquote filename to cover german umlaut including a fallback
            try:
                fname = parse.unquote(re.findall("filename=(.+)", response.headers["Content-Disposition"])[0])
            except Exception as _err:
                self.logger.debug('DKBRobo._get_document(): error during filename conversion: %s\n', _err)
                fname = re.findall("filename=(.+)", response.headers["Content-Disposition"])[0]

            if fname in document_name_list:
                # rename to avoid overrides
                self.logger.debug('DKBRobo._get_document(): adding datetime to avoid overrides.\n')
                now = datetime.now()
                fname = f'{now.strftime("%Y-%m-%d-%H-%M-%S")}_{fname}'

            if formatted_date:
                fname = f'{formatted_date}{fname}'

            # log filename
            self.logger.debug('DKBRobo._get_document(): filename: %s\n', fname)

            # dump content to file
            self.logger.debug('DKBRobo._get_document() content-length: %s\n', len(response.content))
            with open(f'{path}/{fname}', 'wb') as pdf_file:
                pdf_file.write(response.content)
            result = response.status_code
            document_name_list.append(fname)
        else:
            fname = f'{generate_random_string(20)}.pdf'
            result = None

        return result, f'{path}/{fname}', document_name_list

    def _get_document_links(self, url, path=None, link_name=None, select_all=False, prepend_date=False):
        """ create a dictionary of the documents stored in a pbost folder
        args:
            self.dkb_br - browser object
            url - folder url
            path - path for document download
        returns:
            dictionary of documents
        """
        # pylint: disable=R0914
        self.logger.debug('DKBRobo._get_document_links(%s)\n', url)
        document_dic = {}

        # set download filter if there is a need to do so
        if path and not select_all:
            class_filter = {'class': 'mbo-messageState-unread'}
        else:
            class_filter = {}

        self.dkb_br.open(url)
        # create a list of documents to avoid overrides
        document_name_list = []

        next_url = url

        while True:
            soup = self.dkb_br.get_current_page()
            if soup:
                table = soup.find('table', attrs={'class': 'widget widget abaxx-table expandableTable expandableTable-with-sort'})
                if table:
                    (tmp_dic, tmp_list, ) = self._download_document(next_url, path, class_filter, link_name, table, prepend_date)
                    document_name_list.extend(tmp_list)
                    document_dic.update(tmp_dic)

                next_site = soup.find('span', attrs={'class': 'pager-navigator-next'})
                if next_site:
                    next_url = self.base_url + next_site.find('a')['href']
                    self.dkb_br.open(next_url)
                else:
                    break  # pragma: no cover
            else:
                break  # pragma: no cover

        return document_dic

    def _get_evtdetails_link(self, cols, ontop):
        """ get link for details """
        self.logger.debug('get_evt_details()')

        try:
            link = cols[4 + ontop].find('a', attrs={'class': 'evt-details'})
            details_link = self.base_url + link['href']
        except Exception as _err:
            self.logger.error('DKBRobo._parse_overview() get link: %s\n', _err)
            details_link = None

        return details_link

    def _get_financial_statement(self):
        """ get finanical statement """
        self.logger.debug('DKBRobo._get_financial_statement()\n')

        statement_url = self.base_url + '/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=init'

        self.dkb_br.open(statement_url)
        soup = self.dkb_br.get_current_page()
        return soup

    def _get_formatted_date(self, prepend_date, row):
        """ get document date for prepending """
        self.logger.debug('_get_formatted_date()\n')
        formatted_date = ""
        if prepend_date:
            try:
                creation_date = row.find('td', attrs={'class': 'abaxx-aspect-messageWithState-mailboxMessage-created'}).text
                creation_date_components = creation_date.split(".")
                formatted_date = f'{creation_date_components[2]}-{creation_date_components[1]}-{creation_date_components[0]}_'
            except Exception:
                self.logger.error("Can't parse date, this could i.e. be for archived documents.")

        return formatted_date

    def _get_transaction_link(self, cols, ontop, account_number):
        """ get link for transactions """
        self.logger.debug('_get_transaction_link()')

        account_type = None
        transaction_link = None

        link = cols[4 + ontop].find('a', attrs={'class': 'evt-paymentTransaction'})
        if link:
            # thats a cash account or a credit card
            if 'cash' in cols[4 + ontop].text.strip().lower() or account_number.startswith('DE'):
                # this is a cash account
                account_type = 'account'
            else:
                # this is a credit card
                account_type = 'creditcard'
            transaction_link = self.base_url + link['href']
        else:
            try:
                # thats a depot
                account_type = 'depot'
                link = cols[4 + ontop].find('a', attrs={'class': 'evt-depot'})
                transaction_link = self.base_url + link['href']
            except Exception as _err:
                self.logger.error('DKBRobo._parse_overview() parse depot: %s\n', _err)

        return (account_type, transaction_link)

    def _legacy_get_account_transactions(self, transaction_url, date_from, date_to, transaction_type="booked"):
        """ get transactions from an regular account for a certain amount of time """
        self.logger.debug('DKBRobo._legacy_get_account_transactions(%s: %s/%s, %s)\n', transaction_url, date_from, date_to, transaction_type)
        self.dkb_br.open(transaction_url)
        self.dkb_br.select_form('#form1615473160_1')
        if transaction_type == 'reserved':
            self.dkb_br["slTransactionStatus"] = 1
        else:
            self.dkb_br["slTransactionStatus"] = 0
        self.dkb_br["searchPeriodRadio"] = 1
        self.dkb_br["slSearchPeriod"] = 1
        self.dkb_br["transactionDate"] = str(date_from)
        self.dkb_br["toTransactionDate"] = str(date_to)
        self.dkb_br.submit_selected()
        self.dkb_br.get_current_page()
        response = self.dkb_br.follow_link('csvExport')
        return self._parse_account_transactions(response.content)

    def _legacy_get_creditcard_transactions(self, transaction_url, date_from, date_to, transaction_type="booked"):
        """ get transactions from an regular account for a certain amount of time """
        self.logger.debug('DKBRobo._legacy_get_creditcard_transactions(%s: %s/%s, %s)\n', transaction_url, date_from, date_to, transaction_type)
        # get credit card transaction form yesterday
        self.dkb_br.open(transaction_url)
        self.dkb_br.select_form('#form1579108072_1')
        if transaction_type == 'reserved':
            self.dkb_br["slTransactionStatus"] = 1
        else:
            self.dkb_br["slTransactionStatus"] = 0
        self.dkb_br["slSearchPeriod"] = 0
        self.dkb_br["filterType"] = 'DATE_RANGE'
        self.dkb_br["postingDate"] = str(date_from)
        self.dkb_br["toPostingDate"] = str(date_to)
        self.dkb_br.submit_selected()

        response = self.dkb_br.follow_link('csvExport')
        return self._parse_cc_transactions(response.content)

    def _legacy_get_depot_status(self, transaction_url, date_from, date_to, transaction_type="booked"):
        """ get depoot status """
        self.logger.debug('DKBRobo.get_depot_transactions(%s: %s/%s, %s)\n', transaction_url, date_from, date_to,
                          transaction_type)

        self.dkb_br.open(transaction_url)
        response = self.dkb_br.follow_link('csvExport')
        return self._parse_depot_status(response.content)

    def _legacy_get_transactions(self, transaction_url, atype, date_from, date_to, transaction_type='booked'):
        """ get transactions for a certain amount of time       """
        self.logger.debug('DKBRobo._legacy_get_transactions(%s/%s: %s/%s, %s)\n', transaction_url, atype, date_from, date_to, transaction_type)

        transaction_list = []
        if atype == 'account':
            transaction_list = self._legacy_get_account_transactions(transaction_url, date_from, date_to, transaction_type)
        elif atype == 'creditcard':
            transaction_list = self._legacy_get_creditcard_transactions(transaction_url, date_from, date_to, transaction_type)
        elif atype == 'depot':
            transaction_list = self._legacy_get_depot_status(transaction_url, date_from, date_to, transaction_type)

        return transaction_list

    def _legacy_login(self):
        """ login into DKB banking area via the legacy frontend """
        self.logger.debug('DKBRobo._login()\n')

        # login url
        login_url = self.base_url + '/' + 'banking'

        # create browser and login
        self.dkb_br = self._new_instance()

        self.dkb_br.open(login_url)
        try:
            self.dkb_br.select_form('#login')
            self.dkb_br["j_username"] = str(self.dkb_user)
            self.dkb_br["j_password"] = str(self.dkb_password)

            # submit form and check response
            self.dkb_br.submit_selected()
            soup = self.dkb_br.get_current_page()

            # catch login error
            if soup.find("div", attrs={'class': 'clearfix module text errorMessage'}):
                raise DKBRoboError('Login failed')

            # catch generic notices
            if soup.find("form", attrs={'id': 'genericNoticeForm'}):
                self.dkb_br.open(login_url)
                soup = self.dkb_br.get_current_page()

            # filter last login date
            if soup.find("div", attrs={'id': 'lastLoginContainer'}):
                last_login = soup.find("div", attrs={'id': 'lastLoginContainer'}).text.strip()
                # remove crlf
                last_login = last_login.replace('\n', '')
                # format string in a way we need it
                last_login = last_login.replace('  ', '')
                last_login = last_login.replace('Letzte Anmeldung:', '')
                self.last_login = last_login
                if soup.find('h1').text.strip() == 'Anmeldung bestätigen':
                    if self.tan_insert:
                        # chiptan input
                        login_confirmed = self._ctan_check(soup)
                    else:
                        # app confirmation needed to continue
                        login_confirmed = self._login_confirm()
                    if login_confirmed:
                        # login got confirmed get overview and parse data
                        soup_new = self._get_financial_statement()
                        self.account_dic = self._parse_overview(soup_new)
        except mechanicalsoup.utils.LinkNotFoundError as err:
            raise DKBRoboError('Login failed: LinkNotFoundError') from err

    def _login_confirm(self):
        """ confirm login to dkb via app
        returns:
            true/false - depending if login has been confirmed
        """
        self.logger.debug('DKBRobo._login_confirm()\n')
        print('check your banking app and confirm login...')

        try:
            # get xsrf token
            soup = self.dkb_br.get_current_page()
            xsrf_token = soup.find('input', attrs={'name': 'XSRFPreventionToken'}).get('value')
        except Exception:
            # fallback
            soup = None

        # not confirmed by default
        login_confirmed = False

        if soup:
            # poll url
            poll_id = int(datetime.utcnow().timestamp() * 1e3)
            poll_url = self.base_url + soup.find("form", attrs={'id': 'confirmForm'}).get('action')
            for _cnt in range(120):
                # add id to pollurl
                poll_id += 1
                url = poll_url + '?$event=pollingVerification&$ignore.request=true&_=' + str(poll_id)
                result = self.dkb_br.open(url).json()
                login_confirmed = self._check_confirmation(result, poll_id)
                if login_confirmed:
                    break
                time.sleep(1.5)
            else:
                raise DKBRoboError("No session confirmation after 120 polls")

            post_data = {'$event': 'next', 'XSRFPreventionToken': xsrf_token}
            self.dkb_br.post(url=poll_url, data=post_data)
        else:
            raise DKBRoboError("Error while getting the confirmation page")

        return login_confirmed

    def _logout(self):
        """ logout from DKB banking area
        args:
            self.dkb_br = browser object
        returns:
            None
        """
        self.logger.debug('DKBRobo._logout()\n')
        logout_url = self.base_url + '/' + 'DkbTransactionBanking/banner.xhtml?$event=logout'
        if self.dkb_br:
            self.dkb_br.open(logout_url)

    def _new_instance(self, clientcookies=None):
        """ creates a new browser instance
        args:
           None
        returns:
           self.dkb_br - instance
        """
        self.logger.debug('DKBRobo._new_instance()\n')
        # create browser and cookiestore objects
        self.dkb_br = mechanicalsoup.StatefulBrowser()

        # set proxies
        if self.proxies:
            self.dkb_br.session.proxies = self.proxies
            self.dkb_br.session.verify = False

        dkb_cj = cookiejar.LWPCookieJar()
        self.dkb_br.set_cookiejar = dkb_cj

        # configure browser
        self.dkb_br.set_handle_equiv = True
        self.dkb_br.set_handle_redirect = True
        self.dkb_br.set_handle_referer = True
        self.dkb_br.set_handle_robots = False
        self.dkb_br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)'), ('Accept-Language', 'en-US,en;q=0.5'), ('Connection', 'keep-alive')]

        # initialize some cookies to fool dkb
        dkb_ck = cookiejar.Cookie(version=0, name='javascript', value='enabled', port=None, port_specified=False, domain=self.base_url, domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)
        dkb_ck = cookiejar.Cookie(version=0, name='BRSINFO_browserPlugins', value='NPSWF32_25_0_0_127.dll%3B', port=None, port_specified=False, domain=self.base_url, domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)
        dkb_ck = cookiejar.Cookie(version=0, name='BRSINFO_screen', value='width%3D1600%3Bheight%3D900%3BcolorDepth%3D24', port=None, port_specified=False, domain=self.base_url, domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)

        if clientcookies:
            self.logger.debug('_new_instance(): adding clientcookies.')
            for cookie in clientcookies:
                self.dkb_br.session.cookies.set_cookie(cookie)
        return self.dkb_br

    def _parse_account_transactions(self, transactions):
        """ parses html code and creates a list of transactions included
        args:
            transactions - html page including transactions
        returns:
            list of transactions captured. Each transaction gets represented by a hash containing the following values
            - date - booking date
            - amount - amount
            - text - text
        """
        self.logger.debug('DKBRobo._parse_account_transactions()\n')
        # create empty list
        transaction_list = []

        # parse CSV
        for row in csv.reader(transactions.decode('latin-1').splitlines(), delimiter=';'):
            if len(row) == 12:
                # skip first line
                if row[0] != 'Buchungstag':
                    tmp_dic = {}

                    # data from CSV
                    tmp_dic['bdate'] = row[0]
                    tmp_dic['vdate'] = row[1]
                    # remove double spaces
                    tmp_dic['postingtext'] = ' '.join(row[2].split())
                    tmp_dic['peer'] = ' '.join(row[3].split())
                    tmp_dic['reasonforpayment'] = ' '.join(row[4].split())
                    tmp_dic['mandatereference'] = ' '.join(row[9].split())
                    tmp_dic['customerreferenz'] = ' '.join(row[10].split())

                    tmp_dic['peeraccount'] = row[5]
                    tmp_dic['peerbic'] = row[6]
                    tmp_dic['peerid'] = row[8]

                    # reformat amount
                    tmp_dic['amount'] = string2float(row[7])

                    #  date is only for backwards compatibility
                    tmp_dic['date'] = row[0]
                    tmp_dic['text'] = f"{tmp_dic['postingtext']} {tmp_dic['peer']} {tmp_dic['reasonforpayment']}"

                    # append dic to list
                    transaction_list.append(tmp_dic)
        return transaction_list

    def _parse_cc_transactions(self, transactions):
        """ parses html code and creates a list of transactions included """
        self.logger.debug('DKBRobo._parse_cc_transactions()\n')

        # create empty list
        transaction_list = []

        # parse CSV
        for row in csv.reader(transactions.decode('latin-1').splitlines(), delimiter=';'):
            if len(row) == 7:
                # skip first line
                if row[1] != 'Wertstellung':
                    tmp_dic = {}
                    tmp_dic['vdate'] = row[1]
                    tmp_dic['show_date'] = row[1]
                    tmp_dic['bdate'] = row[2]
                    tmp_dic['store_date'] = row[2]
                    tmp_dic['text'] = row[3]
                    tmp_dic['amount'] = string2float(row[4])
                    tmp_dic['amount_original'] = row[5].replace('.', '').replace(',', '.')
                    # append dic to list
                    transaction_list.append(tmp_dic)
        return transaction_list

    def _parse_depot_status(self, transactions):
        """ parses html code and creates a list of stocks included  """
        self.logger.debug('DKBRobo._parse_depot_status()\n')

        # create empty list
        stocks_list = []

        # parse CSV
        entry_row_length = 13
        for row in csv.reader(transactions.decode('latin-1').splitlines(), delimiter=';'):
            if len(row) == entry_row_length:
                # skip header line
                if row[0] != 'Bestand':
                    tmp_dic = {}
                    tmp_dic['shares'] = string2float(row[0])
                    tmp_dic['shares_unit'] = row[1]
                    tmp_dic['isin_wkn'] = row[2]
                    tmp_dic['text'] = row[3]
                    tmp_dic['price'] = string2float(row[4])
                    tmp_dic['win_loss'] = row[5]
                    tmp_dic['win_loss_currency'] = row[6]
                    tmp_dic['aquisition_cost'] = row[7]
                    tmp_dic['aquisition_cost_currency'] = row[8]
                    tmp_dic['dev_price'] = row[9]
                    tmp_dic['price_euro'] = string2float(row[10])
                    tmp_dic['availability'] = row[11]

                    # append dic to list
                    stocks_list.append(tmp_dic)
        return stocks_list

    def _parse_overview(self, soup):
        """ creates a dictionary including account information """
        self.logger.debug('DKBRobo._parse_overview()\n')
        overview_dic = {}
        counter = 0
        ontop = 0
        for row in soup.findAll("tr", attrs={'class': 'mainRow'}):
            overview_dic[counter] = {}
            cols = row.findAll("td")

            # check if we have accounts from other banks in overview
            # in this case we need to shift columns by one
            if cols[0].find("img"):
                ontop = 1

            # account name
            overview_dic[counter]['name'] = cols[0 + ontop].find('div').text.strip()

            # account number
            overview_dic[counter]['account'] = cols[1 + ontop].text.strip()
            # date
            overview_dic[counter]['date'] = cols[2 + ontop].text.strip()

            # amount
            amount = self._get_amount(cols, ontop)
            if amount:
                overview_dic[counter]['amount'] = amount

            # get link for transactions
            (account_type, transaction_link) = self._get_transaction_link(cols, ontop, overview_dic[counter]['account'])
            if account_type:
                overview_dic[counter]['type'] = account_type
            if transaction_link:
                overview_dic[counter]['transactions'] = transaction_link

            # get link for details
            details_link = self._get_evtdetails_link(cols, ontop)
            if details_link:
                overview_dic[counter]['details'] = details_link

            # increase counter
            counter += 1
        return overview_dic

    def _update_downloadstate(self, link_name, url):
        """ mark document and read
            args:
            self.dkb_br - browser object
            link_name - link_name
            url - download url
        """
        self.logger.debug('DKBRobo._update_downloadstate(%s, %s)\n', link_name, url)

        # get row number to be marked as read
        row_num = parse.parse_qs(parse.urlparse(url).query)['row'][0]
        # construct url
        if link_name == 'Kontoauszüge':
            mark_link = 'kontoauszuege'
        else:
            mark_link = link_name.lower()
        mark_url = f'{self.base_url}/DkbTransactionBanking/content/mailbox/MessageList/%24{mark_link}.xhtml?$event=updateDownloadState&row={row_num}'
        # mark document by fetch url
        _response = self.dkb_br.open(mark_url)  # lgtm [py/unused-local-variable]
