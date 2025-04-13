# pylint: disable=r0913
""" legacy api """
# -*- coding: utf-8 -*-
import os
from datetime import datetime, timezone
import time
import re
import logging
from http import cookiejar
import csv
from typing import Dict, List, Tuple
from urllib import parse
import mechanicalsoup
import bs4
from dkb_robo.utilities import string2float, generate_random_string


logger = logging.getLogger(__name__)


class DKBRoboError(Exception):
    """dkb-robo exception class"""


class Wrapper(object):
    """this is the wrapper for the legacy api"""

    base_url = "https://www.ib.dkb.de"
    dkb_user = None
    dkb_password = None
    dkb_br = None
    tan_insert = False
    proxies = {}

    def __init__(
        self,
        dkb_user: str = None,
        dkb_password: str = None,
        tan_insert: bool = False,
        proxies: Dict[str, str] = None,
    ):
        self.dkb_user = dkb_user
        self.dkb_password = dkb_password
        self.tan_insert = tan_insert
        self.proxies = proxies

    def _get_amount(self, cols: bs4.element.ResultSet, ontop: int) -> float:
        """get link for transactions"""
        logger.debug("Wrapper._get_amount()")
        amount = cols[3 + ontop].text.strip().replace(".", "")
        try:
            result = float(amount.replace(",", "."))
        except Exception as _err:
            logger.error("Wrapper._parse_overview() convert amount: %s\n", _err)
            result = None

        logger.debug("Wrapper._get_amount() ended")
        return result

    def _check_confirmation(self, result: Dict[str, str], poll_id: int) -> bool:
        """check if login has been confirmed via app"""
        logger.debug("Wrapper._check_confirmation()\n")

        login_confirmed = False
        if "state" in result:
            # new dkb mfa app
            logger.debug("mfa poll(id: %s status: %s)\n", poll_id, result["state"])
            # pylint: disable=R1723
            if result["state"] == "PROCESSED":
                logger.debug("Session got confirmed...\n")
                login_confirmed = True
            elif result["state"] == "EXPIRED":
                raise DKBRoboError("Session expired")
        elif "guiState" in result:
            # legacy dkb app
            logger.debug(
                "legacy poll(id: %s status: %s)\n", poll_id, result["guiState"]
            )
            # pylint: disable=R1723
            if result["guiState"] == "MAP_TO_EXIT":
                logger.debug("Session got confirmed...\n")
                login_confirmed = True
            elif result["guiState"] == "EXPIRED":
                raise DKBRoboError("Session expired")
        else:
            raise DKBRoboError("Error during session confirmation")

        logger.debug("Wrapper._check_confirmation() ended with %s\n", login_confirmed)
        return login_confirmed

    def _ctan_check(self, _soup: str) -> bool:
        """input of chiptan during login"""
        logger.debug("Wrapper._ctan_check()\n")

        event_field = "$event"

        try:
            self.dkb_br.select_form('form[name="confirmForm"]')
            self.dkb_br[event_field] = "tanVerification"
        except Exception as _err:  # pragma: no cover
            logger.debug("confirmForm not found\n")

        # open page to insert tan
        self.dkb_br.submit_selected()
        soup = self.dkb_br.get_current_page()

        login_confirm = False

        # select tan form
        self.dkb_br.select_form("#next")
        # print steps to be done
        olist = soup.find("ol")
        if olist:
            for li_ in olist.find_all("li"):
                print(li_.text.strip())
        else:
            print("Please open the TAN2GO app to get a TAN to be inserted below.")

        # ask for TAN
        self.dkb_br["tan"] = input("TAN: ")
        self.dkb_br[event_field] = "next"

        # submit form and check response
        self.dkb_br.submit_selected()
        soup = self.dkb_br.get_current_page()

        # catch tan error
        # pylint: disable=R1720
        if soup.find("div", attrs={"class": "clearfix module text errorMessage"}):
            raise DKBRoboError("Login failed due to wrong TAN")
        else:
            logger.debug("TAN is correct...\n")
            login_confirm = True

        logger.debug("Wrapper._ctan_check() ended with :%s\n", login_confirm)
        return login_confirm

    def _download_document(
        self,
        folder_url: str,
        path: str,
        class_filter: Dict[str, str],
        folder: str,
        table: "bs4.BeautifulSoup",
        prepend_date: bool,
    ) -> Tuple[Dict, List]:
        """document download"""
        logger.debug("Wrapper._download_document()\n")
        document_dic = {}
        document_name_list = []

        tbody = table.find("tbody")
        for row in tbody.find_all("tr", class_filter):
            link = row.find("a")

            # get formatted date
            formatted_date = self._get_formatted_date(prepend_date, row)

            # download file
            if path:
                folder_path = f"{path}/{folder}"
                rcode, fname, document_name_list = self._get_document(
                    folder_url,
                    folder_path,
                    self.base_url + link["href"],
                    document_name_list,
                    formatted_date,
                )
                if rcode == 200:
                    # mark url as read
                    self._update_downloadstate(folder, self.base_url + link["href"])
                if rcode:
                    document_dic[link.contents[0]] = {
                        "rcode": rcode,
                        "link": self.base_url + link["href"],
                        "fname": fname,
                    }
                else:
                    document_dic[link.contents[0]] = self.base_url + link["href"]
            else:
                document_dic[link.contents[0]] = self.base_url + link["href"]

        logger.debug("Wrapper._download_document()\n")
        return (document_dic, document_name_list)

    def _get_account_transactions(
        self,
        transaction_url: str,
        date_from: str,
        date_to: str,
        transaction_type: str = "booked",
    ) -> Dict:
        """get transactions from an regular account for a certain amount of time"""
        logger.debug(
            "Wrapper._get_account_transactions(%s: %s/%s, %s)\n",
            transaction_url,
            date_from,
            date_to,
            transaction_type,
        )

        self.dkb_br.open(transaction_url)
        self.dkb_br.select_form("#form1615473160_1")
        if transaction_type == "reserved":
            self.dkb_br["slTransactionStatus"] = 1
        else:
            self.dkb_br["slTransactionStatus"] = 0
        self.dkb_br["searchPeriodRadio"] = 1
        self.dkb_br["slSearchPeriod"] = 1
        self.dkb_br["transactionDate"] = str(date_from)
        self.dkb_br["toTransactionDate"] = str(date_to)
        self.dkb_br.submit_selected()
        self.dkb_br.get_current_page()
        response = self.dkb_br.follow_link("csvExport")

        logger.debug("Wrapper._get_account_transactions() ended\n")
        return self._parse_account_transactions(response.content)

    def _get_cc_limits(self, form: bs4.element.Tag) -> Dict[str, str]:
        """get credit card limits"""
        logger.debug("Wrapper._get_cc_limits()\n")

        limit_dic = {}
        table = form.find("table", attrs={"class": "multiColumn"})
        if table:
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                tmp = row.find("th")
                if cols:
                    try:
                        limit = tmp.find("span").text.strip()
                        account = (
                            cols[0]
                            .find("div", attrs={"class": "minorLine"})
                            .text.strip()
                        )
                        limit_dic[account] = string2float(limit)
                    except Exception as _err:
                        logger.error(
                            "Wrapper.get_credit_limits() get credit card limits: %s\n",
                            _err,
                        )

        logger.debug("Wrapper._get_cc_limits() ended\n")
        return limit_dic

    def _get_checking_account_limit(self, form: bs4.element.Tag) -> Dict[str, str]:
        """get checking account limits"""
        logger.debug("Wrapper._get_checking_account_limit()\n")

        limit_dic = {}
        table = form.find("table", attrs={"class": "dropdownAnchor"})
        if table:
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                tmp = row.find("th")
                if cols:
                    limit = tmp.find("span").text.strip()
                    account = (
                        cols[0].find("div", attrs={"class": "minorLine"}).text.strip()
                    )
                    limit_dic[account] = string2float(limit)

        logger.debug("Wrapper._get_checking_account_limit() ended\n")
        return limit_dic

    def _get_creditcard_transactions(
        self,
        transaction_url: str,
        date_from: str,
        date_to: str,
        transaction_type: str = "booked",
    ) -> Dict[str, str]:
        """get transactions from an regular account for a certain amount of time"""
        logger.debug(
            "Wrapper._legacy_get_creditcard_transactions(%s: %s/%s, %s)\n",
            transaction_url,
            date_from,
            date_to,
            transaction_type,
        )
        # get credit card transaction form yesterday
        self.dkb_br.open(transaction_url)
        self.dkb_br.select_form("#form1579108072_1")
        if transaction_type == "reserved":
            self.dkb_br["slTransactionStatus"] = 1
        else:
            self.dkb_br["slTransactionStatus"] = 0
        self.dkb_br["slSearchPeriod"] = 0
        self.dkb_br["filterType"] = "DATE_RANGE"
        self.dkb_br["postingDate"] = str(date_from)
        self.dkb_br["toPostingDate"] = str(date_to)
        self.dkb_br.submit_selected()

        response = self.dkb_br.follow_link("csvExport")

        logger.debug("Wrapper._get_creditcard_transactions() ended")
        return self._parse_cc_transactions(response.content)

    def _get_depot_status(
        self,
        transaction_url: str,
        date_from: str,
        date_to: str,
        transaction_type: str = "booked",
    ) -> Dict[str, str]:
        """get depoot status"""
        logger.debug(
            "Wrapper..get_depot_transactions(%s: %s/%s, %s)\n",
            transaction_url,
            date_from,
            date_to,
            transaction_type,
        )

        self.dkb_br.open(transaction_url)
        response = self.dkb_br.follow_link("csvExport")

        logger.debug("Wrapper._get_creditcard_transactions() ended´\n")
        return self._parse_depot_status(response.content)

    def _get_document(
        self,
        folder_url: str,
        path: str,
        url: str,
        document_name_list: List[str],
        formatted_date: str,
    ) -> Tuple[int, str, List[str]]:
        """get download document from postbox"""
        logger.debug("Wrapper._get_document(%s)\n", url)

        # create directory if not existing
        if not os.path.exists(path):
            logger.info("Wrapper._get_document() Create directory %s\n", path)
            os.makedirs(path)

        # fetch file
        response = self.dkb_br.open(folder_url)
        response = self.dkb_br.open(url)

        # gt filename from response header
        fname = ""
        if "Content-Disposition" in response.headers.keys():
            logger.debug(
                "Wrapper._get_document(): response.header: %s\n", response.headers
            )
            # unquote filename to cover german umlaut including a fallback
            try:
                fname = parse.unquote(
                    re.findall(
                        "filename=(.+)", response.headers["Content-Disposition"]
                    )[0]
                )
            except Exception as _err:
                logger.debug(
                    "Wrapper._get_document(): error during filename conversion: %s\n",
                    _err,
                )
                fname = re.findall(
                    "filename=(.+)", response.headers["Content-Disposition"]
                )[0]

            if fname in document_name_list:
                # rename to avoid overrides
                logger.debug(
                    "Wrapper._get_document(): adding datetime to avoid overrides.\n"
                )
                now = datetime.now()
                fname = f"{now.strftime('%Y-%m-%d-%H-%M-%S')}_{fname}"

            if formatted_date:
                fname = f"{formatted_date}{fname}"

            # log filename
            logger.debug("Wrapper._get_document(): filename: %s\n", fname)

            # dump content to file
            logger.debug(
                "Wrapper._get_document() content-length: %s\n", len(response.content)
            )
            with open(f"{path}/{fname}", "wb") as pdf_file:
                pdf_file.write(response.content)
            result = response.status_code
            document_name_list.append(fname)
        else:
            fname = f"{generate_random_string(20)}.pdf"
            result = None

        logger.debug("Wrapper._get_document() ended")
        return result, f"{path}/{fname}", document_name_list

    def _get_document_links(
        self,
        url: str,
        path: str = None,
        link_name: str = None,
        select_all: bool = False,
        prepend_date: bool = False,
    ) -> Dict[str, str]:
        """create a dictionary of the documents stored in a pbost folder"""
        # pylint: disable=R0914
        logger.debug("Wrapper._get_document_links(%s)\n", url)
        document_dic = {}

        # set download filter if there is a need to do so
        if path and not select_all:
            class_filter = {"class": "mbo-messageState-unread"}
        else:
            class_filter = {}

        self.dkb_br.open(url)
        # create a list of documents to avoid overrides
        document_name_list = []

        next_url = url

        while True:
            soup = self.dkb_br.get_current_page()
            if soup:
                table = soup.find(
                    "table",
                    attrs={
                        "class": "widget widget abaxx-table expandableTable expandableTable-with-sort"
                    },
                )
                if table:
                    (tmp_dic, tmp_list,) = self._download_document(
                        next_url, path, class_filter, link_name, table, prepend_date
                    )
                    document_name_list.extend(tmp_list)
                    document_dic.update(tmp_dic)

                next_site = soup.find("span", attrs={"class": "pager-navigator-next"})
                if next_site:
                    next_url = self.base_url + next_site.find("a")["href"]
                    self.dkb_br.open(next_url)
                else:
                    break  # pragma: no cover
            else:
                break  # pragma: no cover

        logger.debug("Wrapper._get_document_links()")
        return document_dic

    def _get_evtdetails_link(self, cols: bs4.element.ResultSet, ontop: int) -> str:
        """get link for details"""
        logger.debug("Wrapper.get_evt_details()")

        try:
            link = cols[4 + ontop].find("a", attrs={"class": "evt-details"})
            details_link = self.base_url + link["href"]
        except Exception as _err:
            logger.error("Wrapper._parse_overview() get link: %s\n", _err)
            details_link = None

        logger.debug("Wrapper.get_evt_details() ended")
        return details_link

    def _get_financial_statement(self) -> bs4.BeautifulSoup:
        """get finanical statement"""
        logger.debug("Wrapper._get_financial_statement()\n")

        statement_url = (
            self.base_url
            + "/ssohl/DkbTransactionBanking/content/banking/financialstatus/FinancialComposite/FinancialStatus.xhtml?$event=init"
        )

        self.dkb_br.open(statement_url)
        soup = self.dkb_br.get_current_page()

        logger.debug("Wrapper._get_financial_statement() ended\n")
        return soup

    def _get_formatted_date(self, prepend_date: bool, row: bs4.element.Tag) -> str:
        """get document date for prepending"""
        logger.debug("Wrapper._get_formatted_date()\n")

        formatted_date = ""
        if prepend_date:
            try:
                creation_date = row.find(
                    "td",
                    attrs={
                        "class": "abaxx-aspect-messageWithState-mailboxMessage-created"
                    },
                ).text
                creation_date_components = creation_date.split(".")
                formatted_date = f"{creation_date_components[2]}-{creation_date_components[1]}-{creation_date_components[0]}_"
            except Exception:
                logger.error(
                    "Can't parse date, this could i.e. be for archived documents."
                )

        logger.debug("Wrapper._get_formatted_date() ended\n")
        return formatted_date

    def _get_transaction_link(
        self, cols: bs4.element.ResultSet, ontop: int, account_number: str
    ) -> Tuple[str, str]:
        """get link for transactions"""
        logger.debug("Wrapper.get_transaction_link()")

        account_type = None
        transaction_link = None

        link = cols[4 + ontop].find("a", attrs={"class": "evt-paymentTransaction"})
        if link:
            # thats a cash account or a credit card
            if "cash" in cols[
                4 + ontop
            ].text.strip().lower() or account_number.startswith("DE"):
                # this is a cash account
                account_type = "account"
            else:
                # this is a credit card
                account_type = "creditcard"
            transaction_link = self.base_url + link["href"]
        else:
            try:
                # thats a depot
                account_type = "depot"
                link = cols[4 + ontop].find("a", attrs={"class": "evt-depot"})
                transaction_link = self.base_url + link["href"]
            except Exception as _err:
                logger.error("Wrapper._parse_overview() parse depot: %s\n", _err)

        logger.debug("Wrapper._get_transaction_link() ended")
        return account_type, transaction_link

    def _login_confirm(self) -> bool:
        """confirm login to dkb via app"""
        logger.debug("Wrapper._login_confirm()\n")

        print("check your banking app and confirm login...")

        try:
            # get xsrf token
            soup = self.dkb_br.get_current_page()
            xsrf_token = soup.find("input", attrs={"name": "XSRFPreventionToken"}).get(
                "value"
            )
        except Exception:
            # fallback
            soup = None

        # not confirmed by default
        login_confirmed = False

        if soup:
            # poll url
            poll_id = int(datetime.now(timezone.utc).timestamp() * 1e3)
            poll_url = self.base_url + soup.find(
                "form", attrs={"id": "confirmForm"}
            ).get("action")
            for _cnt in range(120):
                # add id to pollurl
                poll_id += 1
                url = (
                    poll_url
                    + "?$event=pollingVerification&$ignore.request=true&_="
                    + str(poll_id)
                )
                result = self.dkb_br.open(url).json()
                login_confirmed = self._check_confirmation(result, poll_id)
                if login_confirmed:
                    break
                time.sleep(1.5)
            else:
                raise DKBRoboError("No session confirmation after 120 polls")

            post_data = {"$event": "next", "XSRFPreventionToken": xsrf_token}
            self.dkb_br.post(url=poll_url, data=post_data)
        else:
            raise DKBRoboError("Error while getting the confirmation page")

        logger.debug("Wrapper._login_confirm() ended\n")
        return login_confirmed

    def _new_instance(
        self, clientcookies=None
    ) -> mechanicalsoup.stateful_browser.StatefulBrowser:
        """creates a new browser instance"""
        logger.debug("Wrapper._new_instance()\n")

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
        self.dkb_br.addheaders = [
            (
                "User-agent",
                "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)",
            ),
            ("Accept-Language", "en-US,en;q=0.5"),
            ("Connection", "keep-alive"),
        ]

        # initialize some cookies to fool dkb
        dkb_ck = cookiejar.Cookie(
            version=0,
            name="javascript",
            value="enabled",
            port=None,
            port_specified=False,
            domain=self.base_url,
            domain_specified=False,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={"HttpOnly": None},
            rfc2109=False,
        )
        dkb_cj.set_cookie(dkb_ck)
        dkb_ck = cookiejar.Cookie(
            version=0,
            name="BRSINFO_browserPlugins",
            value="NPSWF32_25_0_0_127.dll%3B",
            port=None,
            port_specified=False,
            domain=self.base_url,
            domain_specified=False,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={"HttpOnly": None},
            rfc2109=False,
        )
        dkb_cj.set_cookie(dkb_ck)
        dkb_ck = cookiejar.Cookie(
            version=0,
            name="BRSINFO_screen",
            value="width%3D1600%3Bheight%3D900%3BcolorDepth%3D24",
            port=None,
            port_specified=False,
            domain=self.base_url,
            domain_specified=False,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={"HttpOnly": None},
            rfc2109=False,
        )
        dkb_cj.set_cookie(dkb_ck)

        if clientcookies:
            logger.debug("_new_instance(): adding clientcookies.")
            for cookie in clientcookies:
                self.dkb_br.session.cookies.set_cookie(cookie)

        logger.debug("Wrapper._new_instance() ended\n")
        return self.dkb_br

    def _parse_account_transactions(self, transactions: bytes) -> List[str]:
        """parses html code and creates a list of transactions included"""
        logger.debug("Wrapper._parse_account_transactions()\n")

        # create empty list
        transaction_list = []
        # parse CSV
        for row in csv.reader(
            transactions.decode("latin-1").splitlines(), delimiter=";"
        ):
            if len(row) == 12:
                # skip first line
                if row[0] != "Buchungstag":
                    tmp_dic = {}

                    # data from CSV
                    tmp_dic["bdate"] = row[0]
                    tmp_dic["vdate"] = row[1]
                    # remove double spaces
                    tmp_dic["postingtext"] = " ".join(row[2].split())
                    tmp_dic["peer"] = " ".join(row[3].split())
                    tmp_dic["reasonforpayment"] = " ".join(row[4].split())
                    tmp_dic["mandatereference"] = " ".join(row[9].split())
                    tmp_dic["customerreferenz"] = " ".join(row[10].split())
                    tmp_dic["customerreference"] = " ".join(row[10].split())

                    tmp_dic["peeraccount"] = row[5]
                    tmp_dic["peerbic"] = row[6]
                    tmp_dic["peerid"] = row[8]

                    # reformat amount
                    tmp_dic["amount"] = string2float(row[7])

                    #  date is only for backwards compatibility
                    tmp_dic["date"] = row[0]
                    tmp_dic[
                        "text"
                    ] = f"{tmp_dic['postingtext']} {tmp_dic['peer']} {tmp_dic['reasonforpayment']}"

                    # append dic to list
                    transaction_list.append(tmp_dic)

        logger.debug("Wrapper._parse_account_transactions() ended\n")
        return transaction_list

    def _parse_cc_transactions(self, transactions: bytes) -> List[str]:
        """parses html code and creates a list of transactions included"""
        logger.debug("Wrapper._parse_cc_transactions()\n")

        # create empty list
        transaction_list = []

        # parse CSV
        for row in csv.reader(
            transactions.decode("latin-1").splitlines(), delimiter=";"
        ):
            if len(row) == 7:
                # skip first line
                if row[1] != "Wertstellung":
                    tmp_dic = {}
                    tmp_dic["vdate"] = row[1]
                    tmp_dic["show_date"] = row[1]
                    tmp_dic["bdate"] = row[2]
                    tmp_dic["store_date"] = row[2]
                    tmp_dic["text"] = row[3]
                    tmp_dic["amount"] = string2float(row[4])
                    tmp_dic["amount_original"] = (
                        row[5].replace(".", "").replace(",", ".")
                    )
                    # append dic to list
                    transaction_list.append(tmp_dic)

        logger.debug("Wrapper._parse_cc_transactions() ended\n")
        return transaction_list

    def _parse_depot_status(self, transactions: bytes) -> List[str]:
        """parses html code and creates a list of stocks included"""
        logger.debug("Wrapper._parse_depot_status()\n")

        # create empty list
        stocks_list = []

        # parse CSV
        entry_row_length = 13
        for row in csv.reader(
            transactions.decode("latin-1").splitlines(), delimiter=";"
        ):
            if len(row) == entry_row_length:
                # skip header line
                if row[0] != "Bestand":
                    tmp_dic = {}
                    tmp_dic["shares"] = string2float(row[0])
                    tmp_dic["shares_unit"] = row[1]
                    tmp_dic["isin_wkn"] = row[2]
                    tmp_dic["text"] = row[3]
                    tmp_dic["price"] = string2float(row[4])
                    tmp_dic["win_loss"] = row[5]
                    tmp_dic["win_loss_currency"] = row[6]
                    tmp_dic["aquisition_cost"] = row[7]
                    tmp_dic["aquisition_cost_currency"] = row[8]
                    tmp_dic["dev_price"] = row[9]
                    tmp_dic["price_euro"] = string2float(row[10])
                    tmp_dic["availability"] = row[11]

                    # append dic to list
                    stocks_list.append(tmp_dic)

        logger.debug("Wrapper._parse_depot_status() ended\n")
        return stocks_list

    def _parse_overview(self, soup: bs4.BeautifulSoup) -> Dict[str, str]:
        """creates a dictionary including account information"""
        logger.debug("Wrapper._parse_overview()\n")

        overview_dic = {}
        counter = 0
        ontop = 0
        for row in soup.find_all("tr", attrs={"class": "mainRow"}):
            overview_dic[counter] = {}
            cols = row.find_all("td")

            # check if we have accounts from other banks in overview
            # in this case we need to shift columns by one
            if cols[0].find("img"):
                ontop = 1

            # account name
            overview_dic[counter]["name"] = cols[0 + ontop].find("div").text.strip()

            # account number
            overview_dic[counter]["account"] = cols[1 + ontop].text.strip()
            # date
            overview_dic[counter]["date"] = cols[2 + ontop].text.strip()

            # amount
            amount = self._get_amount(cols, ontop)
            if amount:
                overview_dic[counter]["amount"] = amount

            # get link for transactions
            (account_type, transaction_link) = self._get_transaction_link(
                cols, ontop, overview_dic[counter]["account"]
            )
            if account_type:
                overview_dic[counter]["type"] = account_type
            if transaction_link:
                overview_dic[counter]["transactions"] = transaction_link

            # get link for details
            details_link = self._get_evtdetails_link(cols, ontop)
            if details_link:
                overview_dic[counter]["details"] = details_link

            # increase counter
            counter += 1

        logger.debug("Wrapper._parse_overview() ended\n")
        return overview_dic

    def _update_downloadstate(self, link_name: str, url: str) -> Dict[str, str]:
        """mark document as read"""
        logger.debug("Wrapper._update_downloadstate(%s, %s)\n", link_name, url)

        # get row number to be marked as read
        row_num = parse.parse_qs(parse.urlparse(url).query)["row"][0]
        # construct url
        if link_name == "Kontoauszüge":
            mark_link = "kontoauszuege"
        else:
            mark_link = link_name.lower()
        mark_url = f"{self.base_url}/DkbTransactionBanking/content/mailbox/MessageList/%24{mark_link}.xhtml?$event=updateDownloadState&row={row_num}"
        # mark document by fetch url
        _response = self.dkb_br.open(mark_url)  # lgtm [py/unused-local-variable]
        logger.debug("Wrapper._update_downloadstate() ended\n")

    def get_credit_limits(self) -> Dict[str, str]:
        """create a dictionary of credit limits of the different accounts"""
        logger.debug("Wrapper.get_credit_limits()\n")

        limit_url = (
            self.base_url
            + "/ssohl/DkbTransactionBanking/content/service/CreditcardLimit.xhtml"
        )
        self.dkb_br.open(limit_url)

        soup = self.dkb_br.get_current_page()
        form = soup.find("form", attrs={"id": "form597962073_1"})

        if form:
            # get checking account limits
            limit_dic = self._get_checking_account_limit(form)

            # get credit cards limits
            limit_dic.update(self._get_cc_limits(form))
        else:
            limit_dic = {}

        logger.debug("Wrapper.get_credit_limits() ended\n")
        return limit_dic

    def get_exemption_order(self) -> Dict[str, str]:
        """returns a dictionary of the stored exemption orders"""
        logger.debug("Wrapper.get_exemption_order()\n")

        exo_url = (
            self.base_url
            + "/ssohl/DkbTransactionBanking/content/personaldata/ExemptionOrderOverview.xhtml"
        )
        self.dkb_br.open(exo_url)

        soup = self.dkb_br.get_current_page()

        for lbr in soup.find_all("br"):
            lbr.replace_with("")
            # br.replace('<br />', ' ')

        table = soup.find("table", attrs={"class": "expandableTable"})

        exo_dic = {}
        if table:
            count = 0
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if cols:
                    try:
                        count += 1
                        exo_dic[count] = {}
                        # description
                        description = re.sub(" +", " ", cols[1].text.strip())
                        description = description.replace("\n", "")
                        description = description.replace("\r", "")
                        description = description.replace("  ", " ")
                        exo_dic[count]["description"] = description

                        # validity
                        validity = re.sub(" +", " ", cols[2].text.strip())
                        validity = validity.replace("\n", "")
                        validity = validity.replace("\r", "")
                        validity = validity.replace("  ", " ")
                        exo_dic[count]["validity"] = validity
                        exo_dic[count]["amount"] = string2float(
                            cols[3].text.strip().replace("EUR", "")
                        )
                        exo_dic[count]["used"] = string2float(
                            cols[4].text.strip().replace("EUR", "")
                        )
                        exo_dic[count]["available"] = string2float(
                            cols[5].text.strip().replace("EUR", "")
                        )
                    except Exception as _err:
                        logger.error("Wrapper.get_exemption_order(): %s\n", _err)

        logger.debug("Wrapper.get_exemption_order() ended\n")
        return exo_dic

    def get_points(self) -> Dict[str, str]:
        """returns the DKB points"""
        logger.debug("Wrapper..get_points()\n")

        point_url = (
            self.base_url
            + "/DkbTransactionBanking/content/FavorableWorld/Overview.xhtml?$event=init"
        )
        self.dkb_br.open(point_url)

        p_dic = {}
        soup = self.dkb_br.get_current_page()
        table = soup.find("table", attrs={"class": "expandableTable"})
        if table:
            tbody = table.find("tbody")
            row = tbody.find_all("tr")[0]
            cols = row.find_all("td")
            # points
            points = re.sub(" +", " ", cols[1].text.strip())
            points = points.replace("\n", "")
            (pointsamount, pointsex) = points.replace("  ", " ").split(" ", 1)
            pointsamount = int(pointsamount.replace(".", ""))
            pointsex = int(pointsex.replace(".", ""))

            # text
            ptext = cols[0].text.strip()
            (tlist) = ptext.split("\n", 1)
            ptext = tlist[0].lstrip()
            ptext = ptext.rstrip()
            etext = tlist[1].lstrip()
            etext = etext.rstrip()

            # store data
            p_dic[ptext] = pointsamount
            p_dic[etext] = pointsex

        logger.debug("Wrapper..get_points() ended\n")
        return p_dic

    def get_standing_orders(self, _uid: str = None) -> List[str]:
        """get standing orders"""
        logger.debug("Wrapper.get_standing_orders()\n")

        so_url = (
            self.base_url
            + "/ssohl/banking/finanzstatus/dauerauftraege?$event=infoStandingOrder"
        )
        self.dkb_br.open(so_url)

        so_list = []
        soup = self.dkb_br.get_current_page()
        table = soup.find("table", attrs={"class": "expandableTable"})
        if table:
            tbody = table.find("tbody")
            rows = tbody.find_all("tr")
            for row in rows:
                tmp_dic = {}
                cols = row.find_all("td")
                tmp_dic["recipient"] = cols[0].text.strip()
                amount = cols[1].text.strip()
                amount = amount.replace("\n", "")
                amount = string2float(amount.replace("EUR", ""))
                tmp_dic["amount"] = amount

                interval = cols[2]
                for brt in interval.find_all("br"):
                    brt.unwrap()

                interval = re.sub("\t+", " ", interval.text.strip())
                interval = interval.replace("\n", "")
                interval = re.sub(" +", " ", interval)
                tmp_dic["interval"] = interval
                tmp_dic["purpose"] = cols[3].text.strip()

                # store dict in list
                so_list.append(tmp_dic)

        logger.debug("Wrapper.get_standing_orders() ended\n")
        return so_list

    def get_transactions(
        self,
        transaction_url: str,
        atype: str,
        date_from: str,
        date_to: str,
        transaction_type: str = "booked",
    ) -> List[str]:
        """get transactions for a certain amount of time"""
        logger.debug(
            "Wrapper.get_transactions(%s/%s: %s/%s, %s)\n",
            transaction_url,
            atype,
            date_from,
            date_to,
            transaction_type,
        )

        transaction_list = []
        if atype == "account":
            transaction_list = self._get_account_transactions(
                transaction_url, date_from, date_to, transaction_type
            )
        elif atype == "creditcard":
            transaction_list = self._get_creditcard_transactions(
                transaction_url, date_from, date_to, transaction_type
            )
        elif atype == "depot":
            transaction_list = self._get_depot_status(
                transaction_url, date_from, date_to, transaction_type
            )

        logger.debug("Wrapper.get_transactions() ended\n")
        return transaction_list

    def login(self) -> Tuple[Dict[str, str], str]:
        """login into DKB banking area via the legacy frontend"""
        logger.debug("Wrapper.login()\n")

        # login url
        login_url = self.base_url + "/ssohl/" + "banking"

        # create browser and login
        self.dkb_br = self._new_instance()

        last_login = None
        account_dic = {}

        self.dkb_br.open(login_url)
        try:
            self.dkb_br.select_form("#login")
            self.dkb_br["j_username"] = str(self.dkb_user)
            self.dkb_br["j_password"] = str(self.dkb_password)

            # submit form and check response
            self.dkb_br.submit_selected()
            soup = self.dkb_br.get_current_page()

            # catch login error
            if soup.find("div", attrs={"class": "clearfix module text errorMessage"}):
                raise DKBRoboError("Login failed")

            # catch generic notices
            if soup.find("form", attrs={"id": "genericNoticeForm"}):
                self.dkb_br.open(login_url)
                soup = self.dkb_br.get_current_page()

            # filter last login date
            if soup.find("div", attrs={"id": "lastLoginContainer"}):
                last_login = soup.find(
                    "div", attrs={"id": "lastLoginContainer"}
                ).text.strip()
                # remove crlf
                last_login = last_login.replace("\n", "")
                # format string in a way we need it
                last_login = last_login.replace("  ", "")
                last_login = last_login.replace("Letzte Anmeldung:", "")
                if soup.find("h1").text.strip() == "Anmeldung bestätigen":
                    if self.tan_insert:
                        # chiptan input
                        login_confirmed = self._ctan_check(soup)
                    else:
                        # app confirmation needed to continue
                        login_confirmed = self._login_confirm()
                    if login_confirmed:
                        # login got confirmed get overview and parse data
                        soup_new = self._get_financial_statement()
                        account_dic = self._parse_overview(soup_new)
        except mechanicalsoup.utils.LinkNotFoundError as err:
            raise DKBRoboError("Login failed: LinkNotFoundError") from err

        logger.debug("Wrapper.login() ended\n")
        return account_dic, last_login

    def logout(self):
        """logout from DKB banking area"""
        logger.debug("Wrapper.logout()\n")

        logout_url = (
            self.base_url
            + "/ssohl/"
            + "DkbTransactionBanking/banner.xhtml?$event=logout"
        )
        if self.dkb_br:
            self.dkb_br.open(logout_url)
        logger.debug("Wrapper.logout() ended\n")

    def scan_postbox(
        self,
        path: str = None,
        download_all: bool = False,
        archive: bool = False,
        prepend_date: bool = False,
    ):
        """scans the DKB postbox and creates a dictionary"""
        logger.debug(
            "Wrapper.san_postbox() path: %s, download_all: %s, archive: %s, prepend_date: %s\n",
            path,
            download_all,
            archive,
            prepend_date,
        )

        if archive:
            pb_url = (
                self.base_url
                + "/ssohl/banking/postfach/ordner?$event=gotoFolder&folderNameOrId=archiv"
            )
        else:
            pb_url = self.base_url + "/ssohl/banking/postfach"
        self.dkb_br.open(pb_url)
        soup = self.dkb_br.get_current_page()
        if archive:
            table = soup.find("table", attrs={"id": re.compile("mbo-message-list*")})
        else:
            table = soup.find("table", attrs={"id": "welcomeMboTable"})
        if table is None:
            raise DKBRoboError("Expected table not found in old postbox")
        tbody = table.find("tbody")

        if archive:
            select_all = True
        else:
            select_all = download_all

        pb_dic = {}
        for row in tbody.find_all("tr"):
            link = row.find("a")
            link_name = link.contents[0]
            pb_dic[link_name] = {}
            pb_dic[link_name]["name"] = link_name
            pb_dic[link_name]["details"] = self.base_url + link["href"]
            if path:
                pb_dic[link_name]["documents"] = self._get_document_links(
                    pb_dic[link_name]["details"],
                    path,
                    link_name,
                    select_all,
                    prepend_date,
                )
            else:
                pb_dic[link_name]["documents"] = self._get_document_links(
                    pb_dic[link_name]["details"],
                    select_all=select_all,
                    prepend_date=prepend_date,
                )

        logger.debug("Wrapper.scan_postbox() ended\n")
        return pb_dic
