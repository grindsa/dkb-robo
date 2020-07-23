#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" dkb internet banking automation library """

from __future__ import print_function
import sys
import os
import csv
import random
import time
from datetime import datetime
import re
from string import digits, ascii_letters
try:
    from urllib import parse
except BaseException:
    import urlparse as parse
import mechanicalsoup

if sys.version_info > (3, 0):
    import http.cookiejar as cookielib
    import importlib
    importlib.reload(sys)
else:
    import cookielib # pylint: disable=E0401
    # pylint: disable=E0602, E1101
    reload(sys)
    sys.setdefaultencoding('utf8')

def generate_random_string(length):
    """ generate random string to be used as name """
    char_set = digits + ascii_letters
    return ''.join(random.choice(char_set) for _ in range(length))

def print_debug(debug, text):
    """ little helper to print debug messages """
    if debug:
        print('{0}: {1}'.format(datetime.now(), text))

class DKBRobo(object):
    """ dkb_robo class """

    base_url = 'https://www.dkb.de'
    dkb_user = None
    dkb_password = None
    dkb_br = None
    last_login = None
    account_dic = {}
    tan_insert = False
    debug = False

    def __init__(self, dkb_user=None, dkb_password=None, tan_insert=False, debug=False):
        self.dkb_user = dkb_user
        self.dkb_password = dkb_password
        self.tan_insert = tan_insert
        self.debug = debug

    def __enter__(self):
        """
        Makes DKBRobo a Context Manager

        with DKBRobo("user","pwd") as dkb:
            print (dkb.lastlogin)
        """
        if not self.dkb_br:
            self.login()
        return self

    def __exit__(self, *args):
        """
        Close the connection at the end of the context
        """
        self.logout()

    def get_account_transactions(self, transaction_url, date_from, date_to):
        """ get transactions from an regular account for a certain amount of time
        args:
            self.dkb_br          - browser object
            transaction_url - link to collect the transactions
            date_from       - transactions starting form
            date_to         - end date
        """
        print_debug(self.debug, 'DKBRobo.get_account_transactions({0}: {1}/{2})\n'.format(transaction_url, date_from, date_to))
        self.dkb_br.open(transaction_url)
        self.dkb_br.select_form('#form1615473160_1')

        self.dkb_br["slTransactionStatus"] = 0
        self.dkb_br["searchPeriodRadio"] = 1
        self.dkb_br["slSearchPeriod"] = 1
        self.dkb_br["transactionDate"] = str(date_from)
        self.dkb_br["toTransactionDate"] = str(date_to)
        self.dkb_br.submit_selected()
        self.dkb_br.get_current_page()
        response = self.dkb_br.follow_link('csvExport')
        return self.parse_account_transactions(response.content)

    def get_creditcard_transactions(self, transaction_url, date_from, date_to):
        """ get transactions from an regular account for a certain amount of time
        args:
            self.dkb_br          - browser object
            transaction_url - link to collect the transactions
            date_from       - transactions starting form
            date_to         - end date
        """
        print_debug(self.debug, 'DKBRobo.get_creditcard_transactions({0}: {1}/{2})\n'.format(transaction_url, date_from, date_to))
        # get credit card transaction form yesterday
        self.dkb_br.open(transaction_url)
        self.dkb_br.select_form('#form1579108072_1')

        self.dkb_br["slSearchPeriod"] = 0
        self.dkb_br["filterType"] = 'DATE_RANGE'
        self.dkb_br["postingDate"] = str(date_from)
        self.dkb_br["toPostingDate"] = str(date_to)
        self.dkb_br.submit_selected()

        response = self.dkb_br.follow_link('csvExport')
        return self.parse_cc_transactions(response.content)

    def get_credit_limits(self):
        """ create a dictionary of credit limits of the different accounts

        args:
            self.dkb_br - browser object

        returns:
            dictionary of the accounts and limits
        """
        print_debug(self.debug, 'DKBRobo.get_credit_limits()\n')
        limit_url = self.base_url + '/DkbTransactionBanking/content/service/CreditcardLimit.xhtml'
        self.dkb_br.open(limit_url)

        soup = self.dkb_br.get_current_page()
        form = soup.find('form', attrs={'id':'form597962073_1'})

        limit_dic = {}
        if form:
            # checking account limits
            table = form.find('table', attrs={'class':'dropdownAnchor'})
            if table:
                for row in table.findAll("tr"):
                    cols = row.findAll("td")
                    tmp = row.find("th")
                    if cols:
                        limit = tmp.find('span').text.strip()
                        limit = limit.replace('.', '')
                        limit = limit.replace(',', '.')
                        account = cols[0].find('div', attrs={'class':'minorLine'}).text.strip()
                        limit_dic[account] = limit

            # credit card  limits
            table = form.find('table', attrs={'class':'multiColumn'})
            if table:
                rows = table.findAll("tr")
                for row in rows:
                    cols = row.findAll("td")
                    tmp = row.find("th")
                    if cols:
                        try:
                            limit = tmp.find('span').text.strip()
                            limit = limit.replace('.', '')
                            limit = limit.replace(',', '.')
                            account = cols[0].find('div', attrs={'class':'minorLine'}).text.strip()
                            limit_dic[account] = limit
                        except IndexError:
                            pass
                        except AttributeError:
                            pass

        return limit_dic

    def get_document_links(self, url, path=None, link_name=None, download_all=False):
        """ create a dictionary of the documents stored in a pbost folder

        args:
            self.dkb_br - browser object
            url - folder url
            path - path for document download

        returns:
            dictionary of the documents
        """
        print_debug(self.debug, 'DKBRobo.get_document_links({0})\n'.format(url))
        document_dic = {}

        # set download filter if there is a need to do so
        if path and not download_all:
            class_filter = {'class': 'mbo-messageState-unread'}
        else:
            class_filter = {}

        self.dkb_br.open(url)
        while True:
            soup = self.dkb_br.get_current_page()
            table = soup.find('table', attrs={'class':'widget widget abaxx-table expandableTable expandableTable-with-sort'})
            if table:
                tbody = table.find('tbody')
                for row in tbody.findAll('tr', class_filter):
                    link = row.find('a')
                    # download file
                    if path:
                        fname = '{0}/{1}'.format(path, link_name)
                        rcode = self.get_document(fname, self.base_url + link['href'])
                        if rcode == 200:
                            # mark url as read
                            self.update_downloadstate(link_name, self.base_url + link['href'])
                        if rcode:
                            document_dic[link.contents[0]] = {'rcode': rcode, 'link':  self.base_url + link['href']}
                        else:
                            document_dic[link.contents[0]] = self.base_url + link['href']
                    else:
                        document_dic[link.contents[0]] = self.base_url + link['href']

            next_site = soup.find('span', attrs={'class':'pager-navigator-next'})
            if next_site:
                next_url = self.base_url + next_site.find('a')['href']
                self.dkb_br.open(next_url)
            else:
                break

        return document_dic

    def get_document(self, path, url):
        """ get download document from postbox

        args:
            self.dkb_br - browser object
            path - path to store the document
            url - download url
        returns:
            http response code
        """
        print_debug(self.debug, 'DKBRobo.get_document({0})\n'.format(url))

        # create directory if not existing
        if not os.path.exists(path):
            print_debug(self.debug, 'create directory {0}\n'.format(path))
            os.makedirs(path)

        # fetch file
        response = self.dkb_br.open(url)

        # gt filename from response header
        fname = ''
        if "Content-Disposition" in response.headers.keys():
            fname = re.findall("filename=(.+)", response.headers["Content-Disposition"])[0]
            # dump content to file
            print_debug(self.debug, 'writing to {0}/{1}\n'.format(path, fname))
            pdf_file = open('{0}/{1}'.format(path, fname), 'wb')
            pdf_file.write(response.content)
            pdf_file.close()
            result = response.status_code
        else:
            fname = '{0}.pdf'.format(generate_random_string(20))
            result = None

        return result

    def get_exemption_order(self):
        """ returns a dictionary of the stored exemption orders

        args:
            self.dkb_br - browser object
            url - folder url

        returns:
            dictionary of exemption orders
        """
        print_debug(self.debug, 'DKBRobo.get_exemption_order()\n')
        exo_url = self.base_url + '/DkbTransactionBanking/content/personaldata/ExemptionOrder/ExemptionOrderOverview.xhtml'
        self.dkb_br.open(exo_url)

        soup = self.dkb_br.get_current_page()

        for lbr in soup.findAll("br"):
            lbr.replace_with("")
            # br.replace('<br />', ' ')


        table = soup.find('table', attrs={'class':'expandableTable'})

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
                        exo_dic[count]['amount'] = float(cols[3].text.strip().replace('.', '').replace('EUR', ''))
                        exo_dic[count]['used'] = float(cols[4].text.strip().replace('.', '').replace('EUR', ''))
                        exo_dic[count]['available'] = float(cols[5].text.strip().replace('.', '').replace('EUR', ''))
                    except IndexError:
                        pass
                    except AttributeError:
                        pass

        return exo_dic

    def get_financial_statement(self):
        """ get finanical statement """
        print_debug(self.debug, 'DKBRobo.get_financial_statement()\n')

        if self.tan_insert:
            statement_url = self.base_url + '/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=init'
        else:
            statement_url = self.base_url + '/DkbTransactionBanking/content/LoginWithBoundDevice/LoginWithBoundDeviceProcess/confirmLogin.xhtml'

        self.dkb_br.open(statement_url)
        soup = self.dkb_br.get_current_page()
        return soup

    def get_points(self):
        """ returns the DKB points

        args:
            self.dkb_br - browser object

        returns:
            points - dkb points
        """
        print_debug(self.debug, 'DKBRobo.get_points()\n')
        point_url = self.base_url + '/DkbTransactionBanking/content/FavorableWorld/Overview.xhtml?$event=init'
        self.dkb_br.open(point_url)

        p_dic = {}
        soup = self.dkb_br.get_current_page()
        table = soup.find('table', attrs={'class':'expandableTable'})
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
        print_debug(self.debug, 'DKBRobo.get_standing_orders()\n')
        so_url = self.base_url + '/banking/finanzstatus/dauerauftraege?$event=infoStandingOrder'
        self.dkb_br.open(so_url)

        so_list = []
        soup = self.dkb_br.get_current_page()
        table = soup.find('table', attrs={'class':'expandableTable'})
        if table:
            tbody = table.find('tbody')
            rows = tbody.findAll('tr')
            for row in rows:
                tmp_dic = {}
                cols = row.findAll("td")
                tmp_dic['recipient'] = cols[0].text.strip()
                amount = cols[1].text.strip()
                amount = amount.replace('\n', '')
                amount = amount.replace('.', '')
                amount = amount.replace(',', '.')
                amount = float(amount.replace('EUR', ''))
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

    def get_transactions(self, transaction_url, atype, date_from, date_to):
        """ get transactions for a certain amount of time
        args:
            self.dkb_br          - browser object
            transaction_url - link to collect the transactions
            atype           - account type (cash, creditcard, depot)
            date_from       - transactions starting form
            date_to         - end date

        returns:
            list of transactions; each transaction gets represented as a dictionary containing the following information
            - date   - booking date
            - amount - amount
            - text   - test
        """
        print_debug(self.debug, 'DKBRobo.get_account_transactions({0}/{1}: {2}/{3})\n'.format(transaction_url, atype, date_from, date_to))
        transaction_list = []
        if atype == 'account':
            transaction_list = self.get_account_transactions(transaction_url, date_from, date_to)
        elif atype == 'creditcard':
            transaction_list = self.get_creditcard_transactions(transaction_url, date_from, date_to)

        return transaction_list

    def login(self):
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
        print_debug(self.debug, 'DKBRobo.login()\n')

        # login url
        login_url = self.base_url + '/' + 'banking'

        # create browser and login
        self.dkb_br = self.new_instance()

        self.dkb_br.open(login_url)
        try:
            self.dkb_br.select_form('#login')
            self.dkb_br["j_username"] = str(self.dkb_user)
            self.dkb_br["j_password"] = str(self.dkb_password)

            # submit form and check response
            self.dkb_br.submit_selected()
            soup = self.dkb_br.get_current_page()

            # catch login error
            if soup.find("div", attrs={'class':'clearfix module text errorMessage'}):
                print('Login failed! Aborting...')
                sys.exit(0)

            # catch generic notices
            if soup.find("form", attrs={'id':'genericNoticeForm'}):
                self.dkb_br.open(login_url)
                soup = self.dkb_br.get_current_page()

            # filter last login date
            if soup.find("div", attrs={'id':'lastLoginContainer'}):
                last_login = soup.find("div", attrs={'id':'lastLoginContainer'}).text.strip()
                # remove crlf
                last_login = last_login.replace('\n', '')
                # format string in a way we need it
                last_login = last_login.replace('  ', '')
                last_login = last_login.replace('Letzte Anmeldung:', '')
                self.last_login = last_login

                if soup.find('h1').text.strip() == 'Anmeldung bestätigen':
                    if self.tan_insert:
                        # chiptan input
                        login_confirmed = self.ctan_check(soup)
                    else:
                        # app confirmation needed to continue
                        login_confirmed = self.login_confirm()

                    if login_confirmed:
                        # login got confirmed get overview and parse data
                        soup_new = self.get_financial_statement()
                        self.account_dic = self.parse_overview(soup_new)
        except mechanicalsoup.utils.LinkNotFoundError:
            print('login failed: LinkNotFoundError')

    def ctan_check(self, _soup):
        """ input of chiptan during login """
        print_debug(self.debug, 'DKBRobo.ctan_check()\n')

        try:
            self.dkb_br.select_form('form[name="confirmForm"]')
            self.dkb_br["$event"] = 'tanVerification'
        except BaseException as err_:
            print_debug(self.debug, 'confirmForm not found\n')

        try:
            self.dkb_br.select_form('form[name="next"]')
            self.dkb_br["$event"] = 'next'
        except BaseException:
            print_debug(self.debug, 'nextForm not found\n')

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
        if soup.find("div", attrs={'class':'clearfix module text errorMessage'}):
            print('Login failed due to wrong tan! Aborting...')
            sys.exit(0)
        else:
            print_debug(self.debug, 'TAN is correct...\n')
            login_confirm = True

        print_debug(self.debug, 'DKBRobo.ctan_check() ended with :{0}\n'.format(login_confirm))
        return login_confirm

    def login_confirm(self):
        """ confirm login to dkb via app

        returns:
            true/false - depending if login has been confirmed
        """
        print_debug(self.debug, 'DKBRobo.login_confirm()\n')
        print('check your banking app and confirm login...')

        try:
            # get xsrf token
            soup = self.dkb_br.get_current_page()
            xsrf_token = soup.find('input', attrs={'name':'XSRFPreventionToken'}).get('value')
        except BaseException:
            # fallback
            xsrf_token = generate_random_string(25)

        # timestamp in miliseconds for py3 and py2
        try:
            poll_id = int(datetime.utcnow().timestamp()*1e3)
        except BaseException:
            poll_id = int(round(time.time() * 1000))

        # poll url
        poll_url = self.base_url + '/DkbTransactionBanking/content/LoginWithBoundDevice/LoginWithBoundDeviceProcess/confirmLogin.xhtml'
        login_confirmed = False
        while not login_confirmed:
            poll_id += 1
            # add id to pollurl
            url = poll_url + '?$event=pollingVerification&_=' + str(poll_id)
            result = self.dkb_br.open(url).json()
            if 'guiState' in result:
                print_debug(self.debug, 'poll(id: {0} status: {1}\n'.format(poll_id, result['guiState']))
                if result['guiState'] == 'MAP_TO_EXIT':
                    print_debug(self.debug, 'session got confirmed...\n')
                    login_confirmed = True
                elif result['guiState'] == 'EXPIRED':
                    print('Session got expired. Aborting...')
                    sys.exit(0)
            else:
                print('Timeout during session confirmation. Aborting...')
                sys.exit(0)
            time.sleep(2)

        post_data = {'$event': 'next', 'XSRFPreventionToken': xsrf_token}
        self.dkb_br.post(url=poll_url, data=post_data)

        return login_confirmed

    def logout(self):
        """ logout from DKB banking area

        args:
            self.dkb_br = browser object

        returns:
            None
        """
        print_debug(self.debug, 'DKBRobo.logout()\n')
        logout_url = self.base_url + '/' + 'DkbTransactionBanking/banner.xhtml?$event=logout'
        self.dkb_br.open(logout_url)

    def new_instance(self):
        """ creates a new browser instance

        args:
           None

        returns:
           self.dkb_br - instance
        """
        print_debug(self.debug, 'DKBRobo.new_instance()\n')
        # create browser and cookiestore objects
        self.dkb_br = mechanicalsoup.StatefulBrowser()
        dkb_cj = cookielib.LWPCookieJar()
        self.dkb_br.set_cookiejar = dkb_cj

        # configure browser
        self.dkb_br.set_handle_equiv = True
        self.dkb_br.set_handle_redirect = True
        self.dkb_br.set_handle_referer = True
        self.dkb_br.set_handle_robots = False
        self.dkb_br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)'), ('Accept-Language', 'en-US,en;q=0.5'), ('Connection', 'keep-alive')]

        # initialize some cookies to fool dkb
        dkb_ck = cookielib.Cookie(version=0, name='javascript', value='enabled', port=None, port_specified=False, domain='www.dkb.de', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)
        dkb_ck = cookielib.Cookie(version=0, name='BRSINFO_browserPlugins', value='NPSWF32_25_0_0_127.dll%3B', port=None, port_specified=False, domain='www.dkb.de', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)
        dkb_ck = cookielib.Cookie(version=0, name='BRSINFO_screen', value='width%3D1600%3Bheight%3D900%3BcolorDepth%3D24', port=None, port_specified=False, domain='www.dkb.de', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)

        return self.dkb_br

    def parse_account_transactions(self, transactions):
        """ parses html code and creates a list of transactions included

        args:
            transactions - html page including transactions

        returns:
            list of transactions captured. Each transaction gets represented by a hash containing the following values
            - date - booking date
            - amount - amount
            - text - text
        """
        print_debug(self.debug, 'DKBRobo.parse_account_transactions()\n')
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
                    amount = row[7]
                    amount = amount.replace('.', '')
                    tmp_dic['amount'] = amount.replace(',', '.')

                    #  date is only for backwards compatibility
                    tmp_dic['date'] = row[0]
                    tmp_dic['text'] = '{0} {1} {2}'.format(tmp_dic['postingtext'], tmp_dic['peer'], tmp_dic['reasonforpayment'])

                    # append dic to list
                    transaction_list.append(tmp_dic)
        return transaction_list

    def parse_cc_transactions(self, transactions):
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
        print_debug(self.debug, 'DKBRobo.parse_cc_transactions()\n')
        # parse the lines to get all account infos
        # soup = BeautifulSoup(transactions, "html5lib")

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
                    amount = row[4].replace('.', '')
                    tmp_dic['amount'] = amount.replace(',', '.')

                    # append dic to list
                    transaction_list.append(tmp_dic)
        return transaction_list

    def parse_overview(self, soup):
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
        print_debug(self.debug, 'DKBRobo.parse_overview()\n')
        # get account information
        overview_dic = {}
        # to_remove = 0
        counter = 0
        ontop = 0
        for row in soup.findAll("tr", attrs={'class':'mainRow'}):
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
            except ValueError:
                pass

            # get link for transactions
            link = cols[4 + ontop].find('a', attrs={'class':'evt-paymentTransaction'})
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
                    link = cols[4 + ontop].find('a', attrs={'class':'evt-depot'})
                    overview_dic[counter]['transactions'] = self.base_url + link['href']
                except (IndexError, TypeError):
                    pass

            # get link for details
            try:
                link = cols[4 + ontop].find('a', attrs={'class':'evt-details'})
                overview_dic[counter]['details'] = self.base_url + link['href']
            except (IndexError, TypeError):
                pass

            # increase counter
            counter += 1
        return overview_dic

    def scan_postbox(self, path=None, download_all=False):
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
        print_debug(self.debug, 'DKBRobo.scan_postbox()\n')
        pb_url = self.base_url + '/banking/postfach'
        self.dkb_br.open(pb_url)
        soup = self.dkb_br.get_current_page()
        table = soup.find('table', attrs={'id':'welcomeMboTable'})
        tbody = table.find('tbody')

        pb_dic = {}
        for row in tbody.findAll('tr'):
            link = row.find('a')
            link_name = link.contents[0]
            pb_dic[link_name] = {}
            pb_dic[link_name]['name'] = link_name
            pb_dic[link_name]['details'] = self.base_url + link['href']
            if path:
                pb_dic[link_name]['documents'] = self.get_document_links(pb_dic[link_name]['details'], path, link_name, download_all)
            else:
                pb_dic[link_name]['documents'] = self.get_document_links(pb_dic[link_name]['details'])

        return pb_dic

    def update_downloadstate(self, link_name, url):
        """ mark document and read

            args:
            self.dkb_br - browser object
            link_name - link_name
            url - download url
        """
        print_debug(self.debug, 'DKBRobo.update_downloadstate({0}, {1})\n'.format(link_name, url))

        # get row number to be marked as read
        row_num = parse.parse_qs(parse.urlparse(url).query)['row'][0]
        # construct url
        if link_name == 'Kontoauszüge':
            mark_link = 'kontoauszuege'
        else:
            mark_link = link_name.lower()
        mark_url = '{0}/DkbTransactionBanking/content/mailbox/MessageList/%24{1}.xhtml?$event=updateDownloadState&row={2}'.format(self.base_url, mark_link, row_num)
        # fetch file
        _response = self.dkb_br.open(mark_url)
        # return response.status_code
