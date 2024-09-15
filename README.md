<!-- markdownlint-disable  MD013 -->
# dkb-robo

![GitHub release](https://img.shields.io/github/release/grindsa/dkb-robo.svg)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/grindsa/dkb-robo/master.svg?label=last%20commit%20into%20master)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/grindsa/dkb-robo/devel.svg?label=last%20commit%20into%20devel)

[![Codecov main](https://img.shields.io/codecov/c/gh/grindsa/dkb-robo/branch/master?label=test%20coverage%20master)](https://app.codecov.io/gh/grindsa/dkb-robo/branch/master)
[![Codecov devel](https://img.shields.io/codecov/c/gh/grindsa/dkb-robo/branch/devel?label=test%20coverage%20devel)](https://app.codecov.io/gh/grindsa/dkb-robo/branch/devel)

[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=grindsa_dkb-robo&metric=security_rating)](https://sonarcloud.io/summary/overall?id=grindsa_dkb-robo)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=grindsa_dkb-robo&metric=sqale_rating)](https://sonarcloud.io/summary/overall?id=grindsa_dkb-robo)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=grindsa_dkb-robo&metric=reliability_rating)](https://sonarcloud.io/summary/overall?id=grindsa_dkb-robo)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=grindsa_dkb-robo&metric=alert_status)](https://sonarcloud.io/summary/overall?id=grindsa_dkb-robo)

dkb-robo is a python library to access the internet banking area of ["Deutsche Kreditbank"](https://banking.dkb.de) to fetch

- account information and current balances
- transactions from creditcards and checking accounts (Girokonten)
- query the content of "DKB Postbox"
- get standing orders (Dauerauftrag)
- get information about credit limits and exemption orders (Freistellungsauftrag)

Starting from version 0.9 dkb-robo can handle the 2nd factor DKB introduced to fulfill the [PSD2 obligations](https://en.wikipedia.org/wiki/Payment_Services_Directive). Starting from September 2019 logins must be confirmed by either

- the blue [DKB-Banking app](https://play.google.com/store/apps/details?id=com.dkbcodefactory.banking)
- Insertion of a TAN created by the [DKB TAN2Go app](https://play.google.com/store/apps/details?id=com.starfinanz.mobile.android.dkbpushtan)

The introduction of a 2nd factor does limit the usage of dkb-robo for automation purposes. DKB is unfortunately ~~not willing/ not able~~ not allowed to open their PSD2-API for non-Fintechs. I discussed this with them for weeks at some point they stopped responding to my emails so I gave up.

DKB introduced a new web-frontend in July 2023 which is using a REST-API as backend. The migration to the new REST endpoints started with v0.22, will take a certain amount of time and gets spread across different releases. We are trying to keep backwards compatibility as much as we can. However, there are certain breaking changes you need to be aware when upgrading from a release prior to v0.22. [Migration status and a list of breaking changes](https://github.com/grindsa/dkb-robo/issues/42) can be found in the [issue section](https://github.com/grindsa/dkb-robo/issues) of this repo.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

To run dkb-robo on your system you need

- [Python](https://www.python.org)
- [mechanicalsoup](https://github.com/MechanicalSoup/MechanicalSoup) - Stateful programmatic web browsing library
- [cookielib](https://docs.python.org/2/library/cookielib.html) - library for Cookie handling for HTTP clients
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - a Python library for pulling data out of HTML and XML files.

Please make sure python and all the above modules had been installed successfully before you start any kind of testing.

### Installing

#### via Pypi

```bash
> pip install dkb_robo
```

#### manually for all users

1. download the archive and unpack it
2. enter the directory and run the setup script

```bash
> python setup.py install
```

#### manually for a single user

1. download the archive and unpack it
2. move the "dkb_robo" subfolder into the directory your script is located

#### SBOM

[A bill of material](https://www.linuxfoundation.org/blog/blog/what-is-an-sbom) of the packages coming along wiht `dkb-robo` will be automatically created during build process and stored in [my SBOM respository](https://github.com/grindsa/sbom/tree/main/sbom/dkb-robo)

### Usage

you need to import dkb-robo into your script

```python
> from dkb_robo import DKBRobo
```

create a new DKBRobo context handler and login to DKB portal

```python
> with DKBRobo(dkb_user=<login username>, dkb_password=<password>, chip_tan=True|False|qr, mfa_device=<m|int>, debug=True|False) as dkb:
```

- dbk_user: username to access the dkb portal
- dkb_password: corresponding login password
- chip_tan: (True/**False**/qr) TAN usage - when not "False" dbk-robo will ask for a TAN during login. So far this library only supports ["chipTAN manuell" and "chipTAN QR](https://www.dkb.de/fragen-antworten/was-ist-das-chiptan-verfahren). "qr" foces the usage of "chipTAN QR" all other values will trigger the usage of "chipTAN Manuell"
- mfa_device: ('m'/Integer) optional - preselect MFA device to be used for 2nd factor - 'm' - main device, otherwise number from device-list
- debug: (True/**False**) Debug mode

After login you can return a dictionary containing a list of your accounts, the actual balance and a link to fetch the transactions

```python
from pprint import pprint
pprint(dkb.account_dic)
{0: {
     'amount': '1458.00',
     'currencycode': 'EUR',
     'date': '22.01.2023',
     'holdername': 'Firstname Lastname',
     'iban': 'DEXXXXXXXXXXXXXXXXXXXXX',
     'id': 'xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
     'limit': '2500.00',
     'name': 'Girokonto',
     'productgroup': 'Meine Konten',
     'transactions': 'https://banking.dkb.de/api/accounts/accounts/xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/transactions',
     'type': 'account'},
 1: {
     'amount': -1000.23,
     'currencycode': 'EUR',
     'date': '22.01.2023',
     'holdername': 'Firstname Lastname',
     'id': 'xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
     'limit': '2000.00',
     'maskedpan': '1234XXXXXXXX5678',
     'name': 'Visa CC',
     'productgroup': 'Meine Konten',
     'transactions': 'https://banking.dkb.de/api/credit-card/cards/xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/transactions',
     'type': 'creditcard'},
 2: {
     'amount': 100000.23,
     'currencycode': 'EUR',
     'date': '22.01.2023',
     'holdername': 'Firstname lastname',
     'id': 'xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
     'limit': '0.00',
     'maskedpan': '5678XXXXXXXX1234',
     'name': 'Another Visa',
     'productgroup': 'Meine Konten',
     'transactions': 'https://banking.dkb.de/api/credit-card/xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/transactions',
     'type': 'creditcard'},
 3: {
     'amount': '123456,79',
     'currencycode': 'EUR',
     'holdername': 'Firstname Lastname',
     'id': 'xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
     'name': 'Mein Depot',
     'productgroup': 'Meine Konten',
     'transactions': 'https://banking.dkb.de/api/broker/brokerage-accounts/xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx(positions?include=instrument%2Cquote',
     'type': 'depot'}}
```

to get the list of transactions for a certain checking account or a credit card use the following method

```python
tlist = dkb.get_transactions(link, type, date_from, date_to)
```

- link - link to get transactions for a specific account - see former step if you do not know how to get it
- type - account type (either "account" or "creditcard") - see former step if you do not know how to get it
- date_from - start date in European notation (DD.MM.YYYY)
- date_to - end date in European notation (DD.MM.YYYY)
- transaction_type - optional: "booked" (default if not specified) or "pending" ("vorgemerkt")

this method returns a list of transactions.

A list of transactions for a regular checking account follows the below format.

```python
from pprint import pprint
pprint(tlist)
[{'amount': -44.98,
  'bdate': '2023-01-22',
  'currencycode': 'EUR',
  'customerreferenz': 'XXXXXX',
  'peer': 'PayPal Europe S.a.r.l. et Cie S.C.A',
  'peeraccount': 'XXXXXXXXX',
  'peerbic': 'XXXXXXXXX',
  'peerid': 'XXXXXXXXXXX',
  'postingtext': 'FOLGELASTSCHRIFT',
  'reasonforpayment': 'XXXXXX PP.XXXXX.PP . Foo-bar AG, Ihr Einkauf bei '
                      'Foo-bar AG',
  'vdate': '2023-01-22'},
 {'amount': -70.05,
  'bdate': '2023-01-22',
  'currencycode': 'EUR',
  'customerreferenz': '68251782022947180823144926',
  'peer': 'FEFASE GmbH',
  'peeraccount': 'XXXXXXXXX',
  'peerbic': 'XXXXXXXXX',
  'peerid': 'XXXXXXXXX',
  'postingtext': 'SEPA-ELV-LASTSCHRIFT',
  'reasonforpayment': 'ELV68251782 18.08 14.49 MEFAS ',
  'vdate': '2023-01-22'},
 {'amount': -7.49,
  'bdate': '2023-01-22',
  'currencycode': 'EUR',
  'customerreferenz': '3REFeSERENC',
  'peer': 'PEER',
  'peeraccount': 'XXXXXXXXX',
  'peerbic': 'XXXXXXXXX',
  'peerid': 'XXXXXXXXX',
  'postingtext': 'FOLGELASTSCHRIFT',
  'reasonforpayment': 'VIELEN DANK VON BAR-FOO GMBH',
  'vdate': '2023-01-22'}]
```

The list of transactions from a creditcard will look as below:

```python
[{'amount': 500.0,
  'bdate': '2023-08-18',
  'currencycode': 'EUR',
  'text': 'Berliner Sparkasse',
  'vdate': '2023-08-18'},
 {'amount': 125.95,
  'bdate': '2023-08-14',
  'currencycode': 'EUR',
  'text': 'Zara Deutschland 3742',
  'vdate': '2023-08-14'},
 {'amount': 500.0,
  'bdate': '2023-08-14',
  'currencycode': 'EUR',
  'text': 'Commerzbank Berlin',
  'vdate': '2023-08-14'}]
```

A brokerage account (depot) will not show the list of transactions but rather a list of positions:

```python
[{'currencycode': 'EUR',
  'isin_wkn': 'DE0005140008',
  'lastorderdate': '2017-01-01',
  'market': 'Frankfurt',
  'price': 9.872,
  'price_euro': '39488.00',
  'quantity': 4000.0,
  'shares_unit': 'pieces',
  'text': 'DEUTSCHE BANK AG NA O.N.'},
 {'currencycode': 'EUR',
  'isin_wkn': 'DE0005557508',
  'lastorderdate': '2017-10-01',
  'market': 'Frankfurt',
  'price': 19.108,
  'price_euro': '28.662.00',
  'quantity': 1500.0,
  'shares_unit': 'pieces',
  'text': 'DT.TELEKOM AG NA'}]
```

to get the credit limits per account or credit-card the method get_credit_limits() must be used

```python
> c_list = dkb.get_credit_limits()
```

This method returns a dictionary of all identified accounts including the credit limit per account

```python
{u'XXXX********XXXX': 100.00,
 u'4748********XXXX': 10000.00,
 u'XXXX********XXXX': 10000.00,
 u'DEXX XXXX XXXX XXXX XXXX XX': 200.00,
 u'DEXX XXXX XXXX XXXX XXXX XX': 2000.00}
```

A list of standing orders (Daueraufträge) can be obtained by calling get_standing_orders() method

```python
> so = dkb.get_standing_orders(account_id)
```

- account_id - 'id' field from account dictionary (`dkb.account_dic[x]['id']`)

A list of standing orders will be returned containing a dictionary per standing order

```python
> pprint(so)
[{'amount': 30.0,
  'creditoraccount': {'bic': 'BIC-1', 'iban': 'IBAN-1'},
  'currencycode': 'EUR',
  'interval': {'frequency': 'monthly',
               'from': '2019-01-05',
               'holidayExecutionStrategy': 'following',
               'nextExecutionAt': '2023-10-01',
               'until': '2025-12-01'},
  'purpose': 'Purpose-1',
  'recpipient': 'Recipient-1'},
 {'amount': 58.0,
  'creditoraccount': {'bic': 'BIC-2', 'iban': 'IBAN-2'},
  'currencycode': 'EUR',
  'interval': {'frequency': 'monthly',
               'from': '2022-12-30',
               'holidayExecutionStrategy': 'following',
               'nextExecutionAt': '2023-12-01'},
  'purpose': 'Purpose-2',
  'recpipient': 'Recipient-2'},]
```

The method get_exemption_order() can be used to get the exemption orders (Freistellungsaufträge)

```python
> exo = dkb.get_exemption_order()
```

A dictionary similar to the one below will be returned

```python
> pprint(exo)
{1: {'amount': 1602.0,
     'available': 1602.0,
     'description': u'Gemeinsam mit XXXX XXXX',
     'used': 0.0,
     'validity': u'01.01.2017  unbefristet'}}
```

To get the amount of dkb points the below method can be used

```python
> points_dic = dkb.get_points()
```

A dictionary similar to the below will be returned

```python
> pprint(points_dic)
{u'DKB-Punkte': 99999,
 u'davon verfallen zum  31.12.2018': 999}
```

To scan the DKB postbox for documents  the below method can be used

```python
> document_dic = dkb.scan_postbox(path, download_all, archive, prepend_date)
```

- path - optional argument. If specified, documents will be downloaded and stored
- dowload_all (True/**False**) - optional argument. By default only unread documents from DKB postbox will get downloaded and marked as "read". By setting this parameter all documents will be downloaded
- archive (True/**False**) - optional argument. When set to `True` the "Archiv" folder in the Postbox will be scanned and documents will be downloaded if a `path` variable is specificed. *Handle this parameter with care as the amount of documents to be downloaded can be huge*.
- prepend_date (True/**False**) - optional argument. Prepend document date in `YYYY-MM-DD_` format to each document to allow easy sorting of downloaded files

The method will return a dictionary containing the different postbox folders and links to download the corresponding documents

Check the scripts [dkb_example.py](doc/dkb_example.py) and [dkb_docdownload.py](doc/dkb_docdownload.py) for further examples.

## dkb_robo command line interface (CLI)

Starting with v0.20 dkb_robo comes with a CLI tool

```bash
$ dkb --help
Usage: dkb [OPTIONS] COMMAND [ARGS]...

Options:
  -d, --debug                     Show additional debugging
  -t, --chip-tan TEXT             use [ChipTan](https://www.dkb.de/fragen-antworten/was-ist-das-chiptan-verfahren) for login ("qr" for chipTan-QR "manual" for chipTan-manuell)
  -u, --username TEXT             username to access the dkb portal
                                  [required]
  -p, --password TEXT             corresponding login password
  --format [pprint|table|csv|json]
                                  output format to use
  --help                          Show this message and exit.

Commands:
  accounts
  credit-limits
  last-login
  standing-orders
  transactions
```

### Example command to fetch account list

```bash
py dkb -u <user> -p <password> accounts
```

### Example commands to fetch transactions via CLI tool

```bash
py dkb -u <user> -p <password> transactions --name Girokonto
py dkb -u <user> -p <password> transactions --account "DE75xxxxxxxxxxxxxxxxxxx"
py dkb -u <user> -p <password> transactions --account "DE75xxxxxxxxxxxxxxxxxxx" --date-from 2023-08-01  --date-to 2023-08-15"
```

## Further documentation

please check the [doc](https://github.com/grindsa/dkb-robo/tree/master/doc) folder of the project. You will find further documentation and an example scripts of all dkb-robo methods there.

## Contributing

Please read [CONTRIBUTING.md](https://github.com/grindsa/dkb-robo/blob/master/CONTRIBUTING.md) for details on my code of conduct, and the process for submitting pull requests.
Please note that I have a life besides programming. Thus, expect a delay in answering.

## Versioning

I use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/grindsa/dkb-robo/tags).

## License

This project is licensed under the GPLv3 - see the [LICENSE.md](https://github.com/grindsa/dkb-robo/blob/master/LICENSE) file for details
