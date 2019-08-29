#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" dkb internet banking automation library """

from __future__ import print_function
import sys
import csv
from datetime import datetime
import re
import mechanicalsoup
# from bs4 import BeautifulSoup

if sys.version_info > (3, 0):
    import http.cookiejar as cookielib
    import importlib
    importlib.reload(sys)
else:
    import cookielib
    reload(sys)
    sys.setdefaultencoding('utf8')

class DKBRobo(object):
    """ dkb_robo class """

    base_url = 'https://www.dkb.de'
    dkb_user = None
    dkb_password = None
    dkb_br = None
    last_login = None
    account_dic = {}

    def __init__(self, dkb_user=None, dkb_password=None):
        self.dkb_user = dkb_user
        self.dkb_password = dkb_password

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


    def get_document_links(self, url):
        """ create a dictionary of the documents stored in a pbost folder

        args:
            self.dkb_br - browser object
            url - folder url

        returns:
            dictionary of the documents
        """
        document_dic = {}

        self.dkb_br.open(url)
        soup = self.dkb_br.get_current_page()
        table = soup.find('table', attrs={'class':'widget widget abaxx-table expandableTable expandableTable-with-sort'})
        if table:
            tbody = table.find('tbody')
            for row in tbody.findAll('tr'):
                link = row.find('a')
                document_dic[link.contents[0]] = self.base_url + link['href']

        return document_dic

    def get_exemption_order(self):
        """ returns a dictionary of the stored exemption orders

        args:
            self.dkb_br - browser object
            url - folder url

        returns:
            dictionary of exemption orders
        """
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

    def get_points(self):
        """ returns the DKB points

        args:
            self.dkb_br - browser object

        returns:
            points - dkb points
        """
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
        # login url
        login_url = self.base_url + '/' + 'banking'

        # create browser and login
        self.dkb_br = self.new_instance()

        self.dkb_br.open(login_url)
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

            # parse account date
            self.account_dic = self.parse_overview(soup)

    def logout(self):
        """ logout from DKB banking area

        args:
            self.dkb_br = browser object

        returns:
            None
        """
        logout_url = self.base_url + '/' + 'DkbTransactionBanking/banner.xhtml?$event=logout'
        self.dkb_br.open(logout_url)

    def new_instance(self):
        """ creates a new browser instance

        args:
           None

        returns:
           self.dkb_br - instance
        """
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
                if 'cash' in cols[4 + ontop].text.strip().lower():
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
            except IndexError:
                pass

            # increase counter
            counter += 1
        return overview_dic

    def scan_postbox(self):
        """ scans the DKB postbox and creates a dictionary out of the
            different documents

        args:
            self.dkb_br = browser object

        returns:
           dictionary in the following format

           - folder name in postbox
                - details -> link to document overview
                - documents
                    - name of document -> document link
        """
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
            pb_dic[link_name]['documents'] = self.get_document_links(pb_dic[link_name]['details'])

        return pb_dic
