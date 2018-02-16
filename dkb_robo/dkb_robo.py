#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" dkb internet banking automation library """

from __future__ import print_function
import sys

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
    dkb_user=None
    dkb_password=None
    dkb_br = None
    last_login = None
    account_dic = None
    
    def __init__(self, dkb_user=None, dkb_password=None):
        self.dkb_user = dkb_user # TODO additional checks (Fail on config, not fail on first use)
        self.dkb_password = dkb_password # TODO additional checks
        
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

        tr_list = []
        # enter a loop to check all following pages
        tr_lines = self.dkb_br.get_current_page()
        tr_list.append(tr_lines)

        # loop into the differnt pages
        loop_cnt = 1

        # we need to set more_pages to true to enter loop
        more_pages = True
        while more_pages:
            # for the moment we assume that there is no further page
            more_pages = False
            loop_cnt += 1
            more_tr = tr_lines.findAll('a', attrs={'class':'gotoPage'})
            for page in more_tr:
                # check if there are more pages to download
                if page.contents[0] == str(loop_cnt):
                    # more pages available fetch/parse the page and enter
                    # while loop again
                    new_link = self.base_url + page['href']
                    self.dkb_br.open(new_link)
                    tr_list.append(self.dkb_br.get_current_page())
                    more_pages = True
                    break


        transactions_dic = self.parse_account_transactions(tr_list)
        return transactions_dic

    def get_creditcard_transactions(self, transaction_url, date_from, date_to):
        """ get transactions from an regular account for a certain amount of time
        args:
            self.dkb_br          - browser object
            transaction_url - link to collect the transactions
            date_from       - transactions starting form
            date_to         - end date
        """

        # get credit card transaction form yesterday
        kk_list = []

        more_kktr = None
        self.dkb_br.open(transaction_url)
        self.dkb_br.select_form('#form1579108072_1')

        self.dkb_br["slSearchPeriod"] = 0
        self.dkb_br["filterType"] = 'DATE_RANGE'
        self.dkb_br["postingDate"] = str(date_from)
        self.dkb_br["toPostingDate"] = str(date_to)
        self.dkb_br.submit_selected()

        # parse the lines to get transactions from the day
        kk_resp = self.dkb_br.get_current_page()
        kk_list.append(kk_resp)

        # check if there is a another page
        more_kktr = kk_resp.findAll('a', attrs={'class':'icons butNext0'})

        while more_kktr:
            # if so get link/transactions from 2nd page
            link = self.base_url + more_kktr[0]['href']
            self.dkb_br.open(link)
            mkk_lines = self.dkb_br.get_current_page()
            kk_list.append(mkk_lines)
            more_kktr = mkk_lines.findAll('a', attrs={'class':'icons butNext0'})

        transaction_list = self.parse_cc_transactions(kk_list)
        return transaction_list

    def get_credit_limits(self):
        """ create a dictionary of credit limites of the different accounts

        args:
            self.dkb_br - browser object

        returns:
            dictionary of the accounts and limits
        """
        limit_url = self.base_url + '/DkbTransactionBanking/content/service/CreditcardLimit.xhtml'
        self.dkb_br.open(limit_url)

        soup = self.dkb_br.get_current_page()
        form = soup.find('form', attrs={'id':'form597962073_1'})

        # checking account limits
        table = form.find('table', attrs={'class':'dropdownAnchor'})
        rows = table.findAll("tr")
        limit_dic = {}
        for row in rows:
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

    def get_excemption_order(self):
        """ returns a dictionary of the stored excemption orders

        args:
            self.dkb_br - browser object
            url - folder url

        returns:
            dictionary of excemption orders
        """
        exo_url = self.base_url + '/DkbTransactionBanking/content/personaldata/ExemptionOrder/ExemptionOrderOverview.xhtml'
        self.dkb_br.open(exo_url)

        soup = self.dkb_br.get_current_page()

        for lbr in soup.findAll("br"):
            lbr.replace_with("")
            # br.replace('<br />', ' ')


        table = soup.find('table', attrs={'class':'expandableTable'})

        rows = table.findAll("tr")
        exo_dic = {}
        count = 0
        for row in rows:
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
            list of transactions; each transaction gets represented as a dictionalry containing the following information
            - date   - booking date
            - amount - amount
            - text   - test
        """
        transaction_list = []
        if atype == 'account':
            transaction_list = self.get_account_transactions(self.dkb_br, transaction_url, date_from, date_to)
        elif atype == 'creditcard':
            transaction_list = self.get_creditcard_transactions(self.dkb_br, transaction_url, date_from, date_to)

        return transaction_list

    def login(self):
        """ login into DKB banking area

        args:
            dkb_user = dkb username
            dkb_password  = dkb_password

        returns:
            self.dkb_br - handle to browser object for further processing
            last_login - last login date (german date format)
            account_dic - dictionary containig account information
            - name
            - account numner
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

        # filter last login date
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

        # initilize some cookies to fool dkb
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
            list of transactions captured. Each transaction gets respresented by a hash containing the follwoing values
            - date - booking date
            - amount - amount
            - text - text
        """
        # parse the lines to get all account infos
        # soup = BeautifulSoup(transactions, "html5lib")

        # create empty list
        transaction_list = []

        for chunk in transactions:
            tr_lists = chunk.findAll('table', attrs={'id':'umsatzTabelle'})
            for tr_list in tr_lists:
                rows = tr_list.findAll("tr", attrs={'class':'mainRow'})
                for row in rows:
                    cols = row.findAll("td")
                    date = cols[0].find('span', attrs={'class':'valueDate'}).text.strip()
                    if date == '':
                        date = 'vorgem.'
                    amount = cols[3].text.strip()
                    f_amount = amount.replace('.', '')
                    f_amount = f_amount.replace(',', '.')

                    text = ''
                    divs = cols[1].findAll('div')
                    if len(divs) > 2:
                        if 'DATUM ' in  str(divs[2].text.strip()):
                            text = divs[0].text.strip() + ' ' + divs[1].text.strip()
                        else:
                            text = divs[0].text.strip() + ' ' + divs[1].text.strip() + divs[2].text.strip()
                    else:
                        text = divs[0].text.strip() + ' ' + divs[1].text.strip()

                    text = text.replace('  ', ' ')
                    text = text.replace('  ', ' ')
                    text = text.replace('  ', ' ')
                    text = text.replace('  ', ' ')

                    # store entry
                    tmp_dic = {}
                    tmp_dic['amount'] = f_amount
                    tmp_dic['date'] = date
                    tmp_dic['text'] = text
                    transaction_list.append(tmp_dic)

        return transaction_list

    def parse_cc_transactions(self, transactions):
        """ parses html code and creates a list of transactions included

        args:
            transactions - html page including transactions

        returns:
            list of transactions captured. Each transaction gets respresented by a hash containing the follwoing values
            - bdate - booking date
            - vdate - valuta date
            - amount - amount
            - text - text
        """
        # parse the lines to get all account infos
        # soup = BeautifulSoup(transactions, "html5lib")

        # create empty dic
        transaction_list = []

        for chunk in transactions:
            # get kk transactions
            table_lists = chunk.findAll("table", attrs={'class':'expandableTable dateHandling '})

            for tr_line in table_lists:

                rows = tr_line.findAll("tr", attrs={'class':'mainRow'})
                for row in rows:
                    cols = row.findAll("td")
                    vdate = cols[1].find("span", attrs={'class':'valueDate'}).text.strip()
                    # reformat date
                    vdate = datetime.strptime(vdate, '%d.%m.%y').strftime("%d.%m.%Y")

                    try:
                        bdate = cols[1].findAll(text=True)[3].strip()
                        # reformat date
                        bdate = datetime.strptime(bdate, '%d.%m.%y').strftime("%d.%m.%Y")
                    except IndexError:
                        bdate = vdate
                    except AttributeError:
                        bdate = vdate

                    text = cols[2].text.strip()
                    amount = cols[3].find("span").text.strip()
                    f_amount = amount.replace('.', '')
                    f_amount = f_amount.replace(',', '.')

                    tmp_dic = {}
                    tmp_dic['bdate'] = bdate
                    tmp_dic['show_date'] = bdate
                    tmp_dic['vdate'] = vdate
                    tmp_dic['store_date'] = vdate
                    tmp_dic['text'] = text
                    tmp_dic['amount'] = f_amount
                    transaction_list.append(tmp_dic)

        return transaction_list

    def parse_overview(self, soup):
        """ creates a dictionary including account information

        args:
            soup - BautifulSoup object

        returns:
            overview_dic - dictionary containg following account information
            - name
            - account numner
            - type (account, creditcard, depot)
            - account balance
            - date of balance
            - link to details
            - link to transactions
        """
        # get account information
        overview_dic = {}
        # to_remove = 0
        counter = 0
        for row in soup.findAll("tr", attrs={'class':'mainRow'}):
            overview_dic[counter] = {}
            cols = row.findAll("td")

            # account name
            overview_dic[counter]['name'] = cols[0].find('div').text.strip()

            # account number
            overview_dic[counter]['account'] = cols[1].text.strip()
            # date
            overview_dic[counter]['date'] = cols[2].text.strip()
            # amount (to be reformated)
            amount = cols[3].text.strip().replace('.', '')
            overview_dic[counter]['amount'] = float(amount.replace(',', '.'))

            # get link for transactions
            link = cols[4].find('a', attrs={'class':'evt-paymentTransaction'})
            if link:
                # thats a cash account or a credit card
                if 'cash' in cols[4].text.strip().lower():
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
                    link = cols[4].find('a', attrs={'class':'evt-depot'})
                    overview_dic[counter]['transactions'] = self.base_url + link['href']
                except IndexError:
                    pass

            # get link for details
            try:
                link = cols[4].find('a', attrs={'class':'evt-details'})
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
            pb_dic[link_name]['documents'] = self.get_document_links(self.dkb_br, pb_dic[link_name]['details'])

        return pb_dic

    

        