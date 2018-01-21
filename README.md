# dkb-robo

dkb-robo is a python library to access the internet banking area of  "Deutsche Kreditbank" to fetch 
- account information and current balances
- transactions from creditcards and checking accounts (Girokonten)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

To run dkb-robo on your system you need

* [Python] - (https://www.python.org)
* [mechanize] - (https://pypi.python.org/pypi/mechanize/) - Stateful programmatic web browsing library
* [cookielib] - (https://docs.python.org/2/library/cookielib.html) - library for Cookie handling for HTTP clients¶
* [Beautiful Soup]  - (https://www.crummy.com/software/BeautifulSoup/) - a Python library for pulling data out of HTML and XML files.

Please make sure python and all the above modules had been installed successfully before you start any kind of testing.

### Installing

1. download the archive and unpack it
2. move the "lib" folder into the directory your script is located

### Usage

you need to import dkb-robo into your script
```
> from lib.dkb_robo import DKBRobo
``` 

create a new instance of DKBRobo and assing this object to a local variable
```
> DKB = DKBRobo()
```

login to https://www.dkb.de

```
> (dkb_br, last, overview) = DKB.login(<your-username>, <your-password>)
```
this method will return 
1. a reference to a mechanize browser object you need for later queries
```
> print(dkb_br)
<Browser visiting https://www.dkb.de/banking/finanzstatus?$event=init>
```    
2. the last login date
```
> print(last)
14.03.2017, 13:19 Uhr
```
3. a dictionary containing a list of your accounts, the actual balance and a link to fetch the transactions 
```
> from pprint import pprint
> pprint(overview)
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

to get the list of transaction for a checking account or a saving account use the follwing method
```
tlist = DKB.get_transactions(dkb_br, link, type, date_from, date_to)
```
* dkb_br - the reference to the formerly created mechanize object
* link - link to get transactions for a specific account - see former step if you do not know how to get it
* type - account type (either "account" or "creditcard") - see former step if you do not know how to get it
* date_from - start date in European notation (DD.MM.YYYY)
* date_to   - end date in European notation (DD.MM.YYYY)

this method returns a list of transactions in the below form
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

## Further documentation
please check the doc folder of the project. You will documentation of all dkb-robo methods there.

* [dkb-robo.html] (https://github.com/grindsa/dkb-robo/blob/master/doc/dkb_robo.html)

## Contributing

Please read [CONTRIBUTING.md](https://github.com/grindsa/dkb-robo/blob/master/CONTRIBUTING.md) for details on my code of conduct, and the process for submitting pull requests.
Please note that I have a life besides programming. Thus, expect a delay in answering.

## Versioning

I use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/grindsa/dkb-robo/tags). 

## License

This project is licensed under the GPLv3 - see the [LICENSE.md](https://github.com/grindsa/dkb-robo/blob/master/LICENSE) file for details