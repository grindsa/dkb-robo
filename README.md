# dkb-robo
![GitHub release](https://img.shields.io/github/release/grindsa/dkb-robo.svg) 
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/grindsa/dkb-robo/master.svg?label=last%20commit%20into%20master)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/grindsa/dkb-robo/devel.svg?label=last%20commit%20into%20devel)

dkb-robo is a python library to access the internet banking area of  "Deutsche Kreditbank" to fetch 
- account information and current balances
- transactions from creditcards and checking accounts (Girokonten)
- query the content of "DKB Postbox"
- get standing orders (Dauerauftrag)
- get information about credit limits and exemption orders (Freistellungsauftrag)


## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

To run dkb-robo on your system you need

* [Python](https://www.python.org)
* [mechanicalsoup](https://github.com/MechanicalSoup/MechanicalSoup) - Stateful programmatic web browsing library
* [cookielib](https://docs.python.org/2/library/cookielib.html) - library for Cookie handling for HTTP clients
* [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - a Python library for pulling data out of HTML and XML files.

Please make sure python and all the above modules had been installed successfully before you start any kind of testing.

### Installing

#### via Pypi
```
> pip install dkb_robo
```

#### manually for all users
1. download the archive and unpack it
2. enter the directory and run the setup script
```
> python setup.py install
```

#### manually for a single user
1. download the archive and unpack it
2. move the "dkb_robo" subfolder into the directory your script is located

### Usage

you need to import dkb-robo into your script
```
> from dkb_robo import DKBRobo
``` 

create a new DKBRobo context handler and login to DKB portal
```
> with DKBRobo(dkb_user, dkb_password) as dkb:
```

After login you can return the 
* the last login date
```
> print(dkb.last_login)
14.03.2017, 13:19 Uhr
```
* a dictionary containing a list of your accounts, the actual balance and a link to fetch the transactions 
```
> from pprint import pprint
> pprint(dkb.account_dic)
{0: {'account': u'DExx xxx xxxx xxxx xxx xx',
     'amount': -9999.99,
     'date': u'15.03.2017',
     'details': u'https://www.dkb.de/banking/finanzstatus?$event=details&row=0&group=0',
     'name': u'checking account',
     'transactions': u'https://www.dkb.de/banking/finanzstatus?$event=paymentTransaction&row=0&group=0',
     'type': 'account'},
 1: {'account': u'DExx xxx xxxx xxxx xxx xx',
     'amount': 999999.99,
     'date': u'15.03.2017',
     'details': u'https://www.dkb.de/banking/finanzstatus?$event=details&row=1&group=0',
     'name': u'savings account',
     'transactions': u'https://www.dkb.de/banking/finanzstatus?$event=paymentTransaction&row=1&group=0',
     'type': 'account'},
 2: {'account': u'XXXX********XXXX',
     'amount': 0.0,
     'date': u'15.03.2017',
     'details': u'https://www.dkb.de/banking/finanzstatus?$event=details&row=2&group=0',
     'name': u'first creditcard',
     'transactions': u'https://www.dkb.de/banking/finanzstatus?$event=paymentTransaction&row=2&group=0',
     'type': 'creditcard'},
 3: {'account': u'XXXX********XXXX',
     'amount': -9999.99,
     'date': u'15.03.2017',
     'details': u'https://www.dkb.de/banking/finanzstatus?$event=details&row=3&group=0',
     'name': u'second creditcard',
     'transactions': u'https://www.dkb.de/banking/finanzstatus?$event=paymentTransaction&row=3&group=0',
     'type': 'creditcard'}}
```

to get the list of transactions for a certain checking account or a credit card use the following method
```
tlist = dkb.get_transactions(link, type, date_from, date_to)
```
* link - link to get transactions for a specific account - see former step if you do not know how to get it
* type - account type (either "account" or "creditcard") - see former step if you do not know how to get it
* date_from - start date in European notation (DD.MM.YYYY)
* date_to   - end date in European notation (DD.MM.YYYY)

this method returns a list of transactions in the below format
```
> from pprint import pprint
> pprint(tlist)
[{'amount': u'0.16',
  'date': u'13.03.2017',
  'text': u'Umbuchung DEUTSCHE KREDITBANK AGERSTATTUNG AUSLANDSEINSATZENTGELT'},
 {'amount': u'-12.50',
  'date': u'12.03.2017',
  'text': u'Lastschrift PREBIFIX GmbH K111631 Anz 10'},
 {'amount': u'-7.97',
  'date': u'11.03.2017',
  'text': u'some text'}]
```

to get the credit limits per account or credit-card the method get_credit_limits() must be used
```
> c_list = dkb.get_credit_limits()
```
This method returns a dictionary of all identified accounts including the credit limit per account
```
{u'XXXX********XXXX': u'100.00',
 u'4748********XXXX': u'10000.00',
 u'XXXX********XXXX': u'10000.00',
 u'DEXX XXXX XXXX XXXX XXXX XX': u'200.00',
 u'DEXX XXXX XXXX XXXX XXXX XX': u'2000.00'}
```

A list of standing orders (Daueraufträge) can be obtained by calling get_standing_orders() method
```
> so = dkb.get_standing_orders()
```
A list of standing orders will be returned containing a dictionary per standing order
```
> pprint(so)
[{'amount': 900.0,
  'interval': u'1. monatlich 01.03.2017',
  'purpose': u'Rate FKB 1234567890',
  'recipient': u'FOO BANK'},
 {'amount': 100.0,
  'interval': u'1. monatlich gel\xf6scht',
  'purpose': u'TRANSACTION',
  'recipient': u'ANY RECIEVER'}]
```

The method get_exemption_order() can be used to get the exemption orders (Freistellungsaufträge)
```
> exo = dkb.get_exemption_order()
```
A dictionary similar to the one below will be returned
```
> pprint(exo)
{1: {'amount': 1602.0,
     'available': 1602.0,
     'description': u'Gemeinsam mit XXXX XXXX',
     'used': 0.0,
     'validity': u'01.01.2017  unbefristet'}}
```

To get the amount of dkb points the below method can be used
```
> points_dic = dkb.get_get_points()
```

A dictionary similar to the below will be returned
```
> pprint(points_dic)
{u'DKB-Punkte': 99999, 
 u'davon verfallen zum  31.12.2018': 999}
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
