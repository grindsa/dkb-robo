#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" dkb internet banking automation library """

from __future__ import print_function
import sys
import cookielib
import mechanize
from BeautifulSoup import BeautifulSoup

reload(sys)
sys.setdefaultencoding('utf8')


class DKBRobo(object):
    """ dkb_robo class """

    base_url = 'https://www.dkb.de'

    def login(self, dkb_user, dkb_password):
        """ login into DKB banking area

        args:
            dkb_user = dkb username
            dkb_password  = dkb_password

        returns:
            dkb_br - handle to browser object for further processing
            last_login - last login date (german date format)
            account_dic - dictionary containig the account information
        """
        # login url
        login_url = self.base_url + '/' + 'banking'

        # create browser and login
        dkb_br = self.new_instance()
        dkb_br.open(login_url)

        dkb_br.select_form(name="login")
        dkb_br["j_username"] = str(dkb_user)
        dkb_br["j_password"] = str(dkb_password)

        response = dkb_br.submit()

        # parse the lines to get all account infos
        soup = BeautifulSoup(response.read())

        # filter last login date
        last_login = soup.find("div", attrs={'id':'lastLoginContainer'}).text.strip()
        # remove crlf
        last_login = last_login.replace('\n', '')
        # format string in a way we need it
        last_login = last_login.replace('  ', '')
        last_login = last_login.replace('Letzte Anmeldung:', '')

        # parse account date
        overview_dic = self.parse_overview(soup)

        return(dkb_br, last_login, overview_dic)

    def logout(self, dkb_br):
        """ logout from DKB banking area

        args:
            dkb_br = browser object

        returns:
            None
        """
        logout_url = self.base_url + '/' + 'DkbTransactionBanking/banner.xhtml?$event=logout'
        dkb_br.open(logout_url)

    def new_instance(self):
        """ creates a new browser instance

        args:
           None

        returns:
           dkb_br - instance
        """
        # create browser and cookiestore objects
        dkb_br = mechanize.Browser()
        dkb_cj = cookielib.LWPCookieJar()
        dkb_br.set_cookiejar = dkb_cj

        # configure browser
        dkb_br.set_handle_equiv = True
        dkb_br.set_handle_redirect = True
        dkb_br.set_handle_referer = True
        dkb_br.set_handle_robots = False
        dkb_br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)'), ('Accept-Language', 'en-US,en;q=0.5'), ('Connection', 'keep-alive')]

        # initilize some cookies to fool dkb
        dkb_ck = cookielib.Cookie(version=0, name='javascript', value='enabled', port=None, port_specified=False, domain='www.dkb.de', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)
        dkb_ck = cookielib.Cookie(version=0, name='BRSINFO_browserPlugins', value='NPSWF32_25_0_0_127.dll%3B', port=None, port_specified=False, domain='www.dkb.de', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)
        dkb_ck = cookielib.Cookie(version=0, name='BRSINFO_screen', value='width%3D1600%3Bheight%3D900%3BcolorDepth%3D24', port=None, port_specified=False, domain='www.dkb.de', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        dkb_cj.set_cookie(dkb_ck)

        return dkb_br

    def parse_overview(self, soup):
        """ creates a dictionary including account information

        args:
           soup - BautifulSoup object

        returns:
           overview_dic - dictionary containg the account information
        """

        # get account information
        overview_dic = {}
        # to_remove = 0
        counter = 0
        for row in soup.findAll("tr", attrs={'class':'mainRow'}):
            counter += 1
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

            # get link for details
            link = cols[4].find('a', attrs={'class':'evt-details'})
            overview_dic[counter]['details'] = self.base_url + link['href']

        return overview_dic

    def scan_postbox(self, dkb_br):
        """ scans the DKB postbox and creates a dictionary out of the
            different documents

        args:
            dkb_br = browser object

        returns:
           dictionaly of the document per section
        """
        pb_url = self.base_url + '/banking/postfach'
        pb_result = dkb_br.open(pb_url)
        soup = BeautifulSoup(pb_result.read())
        table = soup.find('table', attrs={'id':'welcomeMboTable'})
        tbody = table.find('tbody')

        pb_dic = {}
        for row in tbody.findAll('tr'):
            link = row.find('a')
            link_name = link.contents[0]
            pb_dic[link_name] = {}
            pb_dic[link_name]['name'] = link_name
            pb_dic[link_name]['details'] = self.base_url + link['href']
            pb_dic[link_name]['documents'] = self.get_document_links(dkb_br, pb_dic[link_name]['details'])

        return pb_dic

    def get_document_links(self, dkb_br, url):
        """ create a dictionary of the documents stored in a pbost folder

        args:
            dkb_br - browser object
            url - folder url

        returns:
            dictionary of the documents
        """
        document_dic = {}

        category_result = dkb_br.open(url)
        soup = BeautifulSoup(category_result.read())
        table = soup.find('table', attrs={'class':'widget widget abaxx-table expandableTable expandableTable-with-sort'})
        if table:
            tbody = table.find('tbody')
            for row in tbody.findAll('tr'):
                link = row.find('a')
                # link_name = link.contents[0]
                # url  = self.base_url + link['href']
                document_dic[link.contents[0]] = self.base_url + link['href']

        return document_dic
