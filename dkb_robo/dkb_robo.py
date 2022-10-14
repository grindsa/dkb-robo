#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=c0209, r0913, w2301
""" dkb internet banking automation library """
from __future__ import print_function
import os
import csv
import random
import time
from datetime import datetime
import re
from string import digits, ascii_letters
from urllib import parse
from http import cookiejar
import logging
import urllib
import mechanicalsoup


def generate_random_string(length):
    """ generate random string to be used as name """
    char_set = digits + ascii_letters
    return ''.join(random.choice(char_set) for _ in range(length))


def string2float(value):
    """ convert string to float """
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


def validate_dates(logger, date_from, date_to):
    """ correct dates if needed """
    logger.debug('validate_dates()')
    date_from_uts = int(time.mktime(datetime.strptime(date_from, "%d.%m.%Y").timetuple()))
    date_to_uts = int(time.mktime(datetime.strptime(date_to, "%d.%m.%Y").timetuple()))
    now_uts = int(time.time())

    # minimal date (3 years back)
    minimal_date_uts = now_uts - 3 * 365 * 86400

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

    return (date_from, date_to)


class DKBRoboError(Exception):
    """ dkb-robo exception class """
    ...


class DKBRobo(object):
    """ dkb_robo class """
    # pylint: disable=R0904
    base_url = 'https://www.dkb.de'
    dkb_user = None
    dkb_password = None
    dkb_br = None
    last_login = None
    account_dic = {}
    tan_insert = False
    logger = None

    def __init__(self, dkb_user=None, dkb_password=None, tan_insert=False, debug=False):
        self.dkb_user = dkb_user
        self.dkb_password = dkb_password
        self.tan_insert = tan_insert
        self.logger = logger_setup(debug)

    def __enter__(self):
        """
        Makes DKBRobo a Context Manager

        with DKBRobo("user","pwd") as dkb:
            print (dkb.lastlogin)
        """
        if not self.dkb_br:
            self._login()
        return self

    def __exit__(self, *args):
        """
        Close the connection at the end of the context
        """
        self._logout()

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

        try:
            self.dkb_br.select_form('form[name="confirmForm"]')
            self.dkb_br["$event"] = 'tanVerification'
        except Exception as _err:
            self.logger.debug('confirmForm not found\n')

        try:
            self.dkb_br.select_form('form[name="next"]')
            self.dkb_br["$event"] = 'next'
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
        self.dkb_br["$event"] = 'next'

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

    def _get_document_links(self, url, path=None, link_name=None, select_all=False):
        """ create a dictionary of the documents stored in a pbost folder
        args:
            self.dkb_br - browser object
            url - folder url
            path - path for document download
        returns:
            dictionary of the documents
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
        while True:
            soup = self.dkb_br.get_current_page()
            if soup:
                table = soup.find('table', attrs={'class': 'widget widget abaxx-table expandableTable expandableTable-with-sort'})
                if table:
                    tbody = table.find('tbody')
                    for row in tbody.findAll('tr', class_filter):
                        link = row.find('a')
                        # download file
                        if path:
                            fname = '{0}/{1}'.format(path, link_name)
                            rcode, fname, document_name_list = self._get_document(fname, self.base_url + link['href'], document_name_list)
                            if rcode == 200:
                                # mark url as read
                                self._update_downloadstate(link_name, self.base_url + link['href'])
                            if rcode:
                                document_dic[link.contents[0]] = {'rcode': rcode, 'link': self.base_url + link['href'], 'fname': fname}
                            else:
                                document_dic[link.contents[0]] = self.base_url + link['href']
                        else:
                            document_dic[link.contents[0]] = self.base_url + link['href']

                next_site = soup.find('span', attrs={'class': 'pager-navigator-next'})
                if next_site:
                    next_url = self.base_url + next_site.find('a')['href']
                    self.dkb_br.open(next_url)
                else:
                    break
            else:
                break
        return document_dic

    def _get_document(self, path, url, document_name_list):
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
        response = self.dkb_br.open(url)

        # gt filename from response header
        fname = ''
        if "Content-Disposition" in response.headers.keys():

            self.logger.debug('DKBRobo._get_document(): response.header: %s\n', response.headers)
            # unquote filename to cover german umlaut including a fallback
            try:
                fname = urllib.parse.unquote(re.findall("filename=(.+)", response.headers["Content-Disposition"])[0])
            except Exception as _err:
                self.logger.debug('DKBRobo._get_document(): error during filename conversion: %s\n', _err)
                fname = re.findall("filename=(.+)", response.headers["Content-Disposition"])[0]

            if fname in document_name_list:
                # rename to avoid overrides
                self.logger.debug('DKBRobo._get_document(): adding datetime to avoid overrides.\n')
                now = datetime.now()
                fname = '{0}-{1}'.format(now.strftime("%Y-%m-%d-%H-%M-%S"), fname)

            # log filename
            self.logger.debug('DKBRobo._get_document(): filename: %s\n', fname)

            # dump content to file
            self.logger.debug('DKBRobo._get_document() content-length: %s\n', len(response.content))
            self.logger.debug('writing to %s/%s\n', path, fname)
            with open('{0}/{1}'.format(path, fname), 'wb') as pdf_file:
                pdf_file.write(response.content)
            result = response.status_code
            document_name_list.append(fname)
        else:
            fname = '{0}.pdf'.format(generate_random_string(20))
            result = None

        return result, '{0}/{1}'.format(path, fname), document_name_list

    def _get_financial_statement(self):
        """ get finanical statement """
        self.logger.debug('DKBRobo._get_financial_statement()\n')

        statement_url = self.base_url + '/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=init'

        self.dkb_br.open(statement_url)
        soup = self.dkb_br.get_current_page()
        return soup

    def _login(self):
        """ login into DKB banking area
        args:
            dkb_user = dkb username
            dkb_password  = dkb_password
        returns:
            self.dkb_br - handle to browser object for further processing
            last_login - last login date (German date format)
            account_dic - dictionary containing account information
            - name
            - account number
            - type (account, creditcard, depot)
            - account balance
            - date of balance
            - link to details
            - link to transactions
        """
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
        self.dkb_br.open(logout_url)

    def _new_instance(self):
        """ creates a new browser instance
        args:
           None
        returns:
           self.dkb_br - instance
        """
        self.logger.debug('DKBRobo._new_instance()\n')
        # create browser and cookiestore objects
        self.dkb_br = mechanicalsoup.StatefulBrowser()
        dkb_cj = cookiejar.LWPCookieJar()
        self.dkb_br.set_cookiejar = dkb_cj

        # configure browser
        self.dkb_br.set_handle_equiv = True
        self.dkb_br.set_handle_redirect = True
        self.dkb_br.set_handle_referer = True
        self.dkb_br.set_handle_robots = False
        self.dkb_br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)'), ('Accept-Language', 'en-US,en;q=0.5'), ('Connection', 'keep-alive')]

        # initialize some cookies to fool dkb
        dkb_ck = cookiejar.Cookie(version=0, name='javascript', value='enabled', port=None, port_specified=False, domain='www.dkb.de', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)
        dkb_ck = cookiejar.Cookie(version=0, name='BRSINFO_browserPlugins', value='NPSWF32_25_0_0_127.dll%3B', port=None, port_specified=False, domain='www.dkb.de', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)
        dkb_ck = cookiejar.Cookie(version=0, name='BRSINFO_screen', value='width%3D1600%3Bheight%3D900%3BcolorDepth%3D24', port=None, port_specified=False, domain='www.dkb.de', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)

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
                    tmp_dic['text'] = '{0} {1} {2}'.format(tmp_dic['postingtext'], tmp_dic['peer'], tmp_dic['reasonforpayment'])

                    # append dic to list
                    transaction_list.append(tmp_dic)
        return transaction_list

    def _parse_cc_transactions(self, transactions):
        """ parses html code and creates a list of transactions included
        args:
            transactions - html page including transactions
        returns:
            list of transactions captured. Each transaction gets represented by a hash containing the following values
            - bdate - booking date
            - vdate - valuta date
            - amount - amount
            - text - text
        """
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
        """ parses html code and creates a list of stocks included
        args:
            transactions - html page including transactions
        returns:
            list of stocks in the depot. Each transaction gets represented by a hash containing the following values

        """
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
        """ creates a dictionary including account information
        args:
            soup - BautifulSoup object
        returns:
            overview_dic - dictionary containing following account information
            - name
            - account number
            - type (account, credit-card, depot)
            - account balance
            - date of balance
            - link to details
            - link to transactions
        """
        self.logger.debug('DKBRobo._parse_overview()\n')
        # get account information
        overview_dic = {}
        # to_remove = 0
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
            # amount (to be reformated)
            amount = cols[3 + ontop].text.strip().replace('.', '')
            try:
                overview_dic[counter]['amount'] = float(amount.replace(',', '.'))
            except Exception:
                pass

            # get link for transactions
            link = cols[4 + ontop].find('a', attrs={'class': 'evt-paymentTransaction'})
            if link:
                # thats a cash account or a credit card
                if 'cash' in cols[4 + ontop].text.strip().lower() or overview_dic[counter]['account'].startswith('DE'):
                    # this is a cash account
                    overview_dic[counter]['type'] = 'account'
                else:
                    # this is a credit card
                    overview_dic[counter]['type'] = 'creditcard'
                overview_dic[counter]['transactions'] = self.base_url + link['href']
            else:
                try:
                    # thats a depot
                    overview_dic[counter]['type'] = 'depot'
                    link = cols[4 + ontop].find('a', attrs={'class': 'evt-depot'})
                    overview_dic[counter]['transactions'] = self.base_url + link['href']
                except Exception:
                    pass

            # get link for details
            try:
                link = cols[4 + ontop].find('a', attrs={'class': 'evt-details'})
                overview_dic[counter]['details'] = self.base_url + link['href']
            except Exception:
                pass

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
        mark_url = '{0}/DkbTransactionBanking/content/mailbox/MessageList/%24{1}.xhtml?$event=updateDownloadState&row={2}'.format(self.base_url, mark_link, row_num)
        # mark document by fetch url
        _response = self.dkb_br.open(mark_url)  # lgtm [py/unused-local-variable]

    def get_account_transactions(self, transaction_url, date_from, date_to, transaction_type="booked"):
        """ get transactions from an regular account for a certain amount of time
        args:
            self.dkb_br          - browser object
            transaction_url - link to collect the transactions
            date_from       - transactions starting form
            date_to         - end date
            transaction_type- booked or reserved
        """
        self.logger.debug('DKBRobo.get_account_transactions(%s: %s/%s, %s)\n', transaction_url, date_from, date_to, transaction_type)
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

    def get_creditcard_transactions(self, transaction_url, date_from, date_to, transaction_type="booked"):
        """ get transactions from an regular account for a certain amount of time
        args:
            self.dkb_br          - browser object
            transaction_url - link to collect the transactions
            date_from       - transactions starting form
            date_to         - end date
            transaction_type- booked or reserved
        """
        self.logger.debug('DKBRobo.get_creditcard_transactions(%s: %s/%s, %s)\n', transaction_url, date_from, date_to, transaction_type)
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

    def get_depot_status(self, transaction_url, date_from, date_to, transaction_type="booked"):
        """ get depoot status """
        self.logger.debug('DKBRobo.get_depot_transactions(%s: %s/%s, %s)\n', transaction_url, date_from, date_to,
                          transaction_type)

        self.dkb_br.open(transaction_url)
        response = self.dkb_br.follow_link('csvExport')
        return self._parse_depot_status(response.content)

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

        limit_dic = {}
        if form:
            # checking account limits
            table = form.find('table', attrs={'class': 'dropdownAnchor'})
            if table:
                for row in table.findAll("tr"):
                    cols = row.findAll("td")
                    tmp = row.find("th")
                    if cols:
                        limit = tmp.find('span').text.strip()
                        account = cols[0].find('div', attrs={'class': 'minorLine'}).text.strip()
                        limit_dic[account] = string2float(limit)

            # credit card  limits
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
                        except Exception:
                            pass

        return limit_dic

    def get_exemption_order(self):
        """ returns a dictionary of the stored exemption orders
        args:
            self.dkb_br - browser object
            url - folder url
        returns:
            dictionary of exemption orders
        """
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

                        # exo_dic[count]['validity'] = cols[2].text.strip()
                        exo_dic[count]['amount'] = string2float(cols[3].text.strip().replace('EUR', ''))
                        exo_dic[count]['used'] = string2float(cols[4].text.strip().replace('EUR', ''))
                        exo_dic[count]['available'] = string2float(cols[5].text.strip().replace('EUR', ''))
                    except Exception:
                        pass

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

                interval = re.sub('\t', ' ', interval.text.strip())
                interval = interval.replace('\n', '')
                interval = re.sub(' +', ' ', interval)
                tmp_dic['interval'] = interval
                tmp_dic['purpose'] = cols[3].text.strip()

                # store dict in list
                so_list.append(tmp_dic)

        return so_list

    def get_transactions(self, transaction_url, atype, date_from, date_to, transaction_type='booked'):
        """ get transactions for a certain amount of time
        args:
            self.dkb_br          - browser object
            transaction_url - link to collect the transactions
            atype           - account type (cash, creditcard, depot)
            date_from       - transactions starting form
            date_to         - end date
            transaction_type- booked or reserved
        returns:
            list of transactions; each transaction gets represented as a dictionary containing the following information
            - date   - booking date
            - amount - amount
            - text   - test
        """
        self.logger.debug('DKBRobo.get_account_transactions(%s/%s: %s/%s, %s)\n', transaction_url, atype, date_from, date_to, transaction_type)

        (date_from, date_to) = validate_dates(self.logger, date_from, date_to)

        transaction_list = []
        if atype == 'account':
            transaction_list = self.get_account_transactions(transaction_url, date_from, date_to, transaction_type)
        elif atype == 'creditcard':
            transaction_list = self.get_creditcard_transactions(transaction_url, date_from, date_to, transaction_type)
        elif atype == 'depot':
            transaction_list = self.get_depot_status(transaction_url, date_from, date_to, transaction_type)

        return transaction_list

    def scan_postbox(self, path=None, download_all=False, archive=False):
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
        self.logger.debug('DKBRobo.scan_postbox()\n')
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
                pb_dic[link_name]['documents'] = self._get_document_links(pb_dic[link_name]['details'], path, link_name, select_all)
            else:
                pb_dic[link_name]['documents'] = self._get_document_links(pb_dic[link_name]['details'], select_all=select_all)
        return pb_dic
