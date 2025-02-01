<!-- markdownlint-disable  MD013 -->
# Object Structure for unfiltered mode

The "unfiltered mode" is a feature that affects how data is processed and accessed within dkb_robo. When enabled, this mode allows the application to work directly with the raw attributes of objects, providing a more detailed and unprocessed view of the data. The unfiltered mode can be useful for advanced users who need access to the underlying data structures without any additional formatting or filtering.

## Key features of unfiltered mode

*Direct Attribute Access*: When unfiltered mode is enabled, the application accesses data directly from the attributes of objects. This means that you get the raw data as it is stored in the system, without any modifications or transformations.
Example: Accessing an account's ID directly from the object attribute (account.id) instead of through a dictionary key (account['id']).

*Detailed Data View*: Unfiltered mode provides a more detailed view of the data, including all available attributes. This can be particularly useful for debugging or for users who need to see all the information associated with an object.

*No Additional Formatting*: In unfiltered mode, the data is returned as-is, without any additional formatting or processing. This ensures that users receive the data in its original form, which can be important for certain use cases where data integrity is crucial.

## Enabling Unfiltered Mode

### when using the library

pass the option `unfiltered=True` when creating a DKBRobo context handler

```python
with DKBRobo(dkb_user=DKB_USER, dkb_password=DKB_PASSWORD, unfiltered=True) as dkb:
    pprint(dkb.account_dic)
```

### when using CLI

pass the `--unfiltered` flag to your cli command to enable this mode.

```bash
dkb  -u DKB_USER -p DKB_PASSWORD -m 1 accounts
```

## Example output

### Porfolio Overview

#### Account

```python
AccountItem(availableBalance=Amount(value=2000.00,
                                    currencyCode='EUR',
                                    conversionRate=None,
                                    date=None,
                                    unit=None),
            balance=Amount(value=-1000.00,
                            currencyCode='EUR',
                            conversionRate=None,
                            date=None,
                            unit=None),
            currencyCode='EUR',
            displayName='Girokonto',
            holderName='Firstname Lastname',
            id='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx',
            iban='DE75XXXXXXXXXXXXXXXXXXX',
            interestRate='0.000',
            interests=[InterestsItem(details=[DetailsItem(condition=Condition(currency='EUR',
                                                                                maximumAmount=None,
                                                                                minimumAmount=3000.01),
                                                            interestRate='8.000')],
                                        method='individual-rate',
                                        type='overdraft'),
                        InterestsItem(details=[DetailsItem(condition=Condition(currency='EUR',
                                                                                maximumAmount=None,
                                                                                minimumAmount=0.0),
                                                            interestRate='0.000')],
                                        method='individual-rate',
                                        type='credit'),
                        InterestsItem(details=[DetailsItem(condition=Condition(currency='EUR',
                                                                                maximumAmount=None,
                                                                                minimumAmount=0.0),
                                                            interestRate='8.680')],
                                        method='individual-rate',
                                        type='debit')],
            lastAccountStatementDate='2024-01-01',
            nearTimeBalance=Amount(value=-1000.03,
                                    currencyCode='EUR',
                                    conversionRate=None,
                                    date=None,
                                    unit=None),
            openingDate='2003-01-01',
            overdraftLimit=2500.0,
            permissions=['transactions-read',
                            'non-sepa-credit-transfer-create',
                            ....
                            'scheduled-payment-update'],
            product=Product(id='PG_Giro_1',
                            type='checking-account-private',
                            displayName='Girokonto 1'),
            productGroup='Meine Konten',
            state='active',
            type='account',
            unauthorizedOverdraftInterestRate='8.680',
            updatedAt='2024-01-21',
            transactions='https://banking.dkb.de/api/accounts/accounts/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx/transactions')
```

#### Card

```python
CardItem(activationDate='2018-01-91',
            authorizedAmount=Amount(value=12.34,
                                    currencyCode='EUR',
                                    conversionRate=None,
                                    date=None,
                                    unit=None),
            availableLimit=Amount(value=2000.00,
                                currencyCode='EUR',
                                conversionRate=None,
                                date=None,
                                unit=None),
            balance=Amount(value=12.34,
                        currencyCode='EUR',
                        conversionRate=None,
                        date='2025-01-26',
                        unit=None),
            billingDetails=BillingDetails(days=[22],
                                        calendarType='calendar',
                                        cycle='monthly'),
            blockedSince=None,
            creationDate=None,
            engravedLine1='Firstname Lastname',
            engravedLine2='',
            expiryDate='2030-01-01',
            failedPinAttempts=None,
            followUpCardId=None,
            holder=Holder(person=Person(firstName='Firstname',
                                        lastName='Lastname',
                                        title=None,
                                        salutation=None,
                                        dateOfBirth=None,
                                        taxId=None)),
            id='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx',
            limit=Limit(value=2000.0,
                        currencyCode='EUR',
                        identifier=None,
                        categories=None),
            maskedPan='1234XXXXXXXX4321',
            network='visa',
            owner=Person(firstName='Firstname',
                        lastName='Lastname',
                        title='',
                        salutation='frau',
                        dateOfBirth=None,
                        taxId=None),
            product=Product(superProductId='0012345',
                            displayName='Visa Kreditkarte',
                            institute='DKB',
                            productType='CASH-BLACK',
                            ownerType='PRIVATE',
                            id='0054321',
                            type='CASH-BLACK'),
            referenceAccount=Account(iban='DE75XXXXXXXXXXXXXXXXXX',
                                    bic='BYLADEM1001'),
            state='active',
            status=Status(category='active',
                        since=None,
                        reason=None,
                        final=None,
                        limitationsFor=[]),
            type='creditCard',
            transactions='https://banking.dkb.de/api/credit-card/cards/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx/transactions')
```

#### Depot

```python
DepotItem(brokerageAccountPerformance=BrokerageAccountPerformance(currentValue=Amount(value=1234.567,
                                                                                        currencyCode='EUR',
                                                                                        conversionRate=None,
                                                                                        date=None,
                                                                                        unit='currency'),
                                                                    averagePrice=Amount(value=0.0,
                                                                                        currencyCode='EUR',
                                                                                        conversionRate=None,
                                                                                        date=None,
                                                                                        unit='currency'),
                                                                    overallAbsolute=Amount(value=0.0,
                                                                                            currencyCode='EUR',
                                                                                            conversionRate=None,
                                                                                            date=None,
                                                                                            unit='currency'),
                                                                    overallRelative='0',
                                                                    isOutdated=True),
            depositAccountId='987654321',
            holder=Person(firstName='Firstname',
                        lastName='Lastname',
                        title=None,
                        salutation=None,
                        dateOfBirth=None,
                        taxId=None),
            holderName='Firstname Lastname',
            id='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx',
            referenceAccounts=[ReferenceAccountItem(internalReferenceAccounts=True,
                                                    accountType='accounting',
                                                    accountNumber='1234567',
                                                    bankCode='12030000',
                                                    holderName='Lstname, Firstname'),
                                ReferenceAccountItem(internalReferenceAccounts=True,
                                                    accountType='returns',
                                                    accountNumber='1234567',
                                                    bankCode='12030000',
                                                    holderName='Lastname, Firstname')],
            riskClasses=[],
            tradingEnabled=True,
            type='brokerageAccount',
            transactions='https://banking.dkb.de/api/broker/brokerage-accounts/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx/positions?include=instrument%2Cquote')
```

### Transactions

#### Account Transaction

```python
AccountTransactionItem(status='booked',
                    bookingDate='2024-01-01',
                    valueDate='2024-01-01',
                    description='VISA Debitkartenumsatz',
                    mandateId=None,
                    endToEndId='1234567890123',
                    transactionType='KARTENZAHLUNG',
                    purposeCode='DCRD',
                    businessTransactionCode='BUTC+105+123+456',
                    amount=Amount(value=-19.99,
                                    currencyCode='EUR',
                                    conversionRate=None,
                                    date=None,
                                    unit=None),
                    creditor=Account(accountNr='9876543210',
                                        accountId=None,
                                        bic='BYLADEM1001',
                                        blz='12030000',
                                        iban='DE912340056789012',
                                        id=None,
                                        intermediaryName='DEUTSCHE KREDITBANK '
                                                        'AG',
                                        name='Name'),
                    debtor=Account(accountNr='0001234567',
                                    accountId=None,
                                    bic='BYLADEM1001',
                                    blz='12030000',
                                    iban='DE751230300001234567',
                                    id=None,
                                    intermediaryName=None,
                                    name='ISSUER'),
                    isRevocable=False)
```

#### Card Transaction

```python
CreditCardTransactionItem(amount=Amount(value=0.47,
                                        currencyCode='EUR',
                                        conversionRate=4.266,
                                        date=None,
                                        unit=None),
                        id='12345678-1234-1234-1234-123456789011223',
                        authorizationDate='2024-01-01T12:34:56Z',
                        bonuses=[],
                        bookingDate='2024-01-01',
                        cardId='98765432-4321-4321-4321-09876543211122',
                        description='ROSSMANN 03',
                        merchantAmount=Amount(value=1.99,
                                                currencyCode='PLN',
                                                conversionRate=None,
                                                date=None,
                                                unit=None),
                        merchantCategory=MerchantCategory(code='5977'),
                        status='booked',
                        transactionType='retail-store'),
```

### Depot Transaction

```python
DepotTransactionItem(id='98765432-4321-4321-4321-09876543211122',
                    availableQuantity=Quantity(unit='pieces',
                                                value=55.0),
                    custody=Custody(block=Block(blockType='noBlock'),
                                    certificateType='normalPieces',
                                    characteristic=Characteristic(characteristicType='noCharacteristic'),
                                    custodyType='Collective Custody '
                                                'Namensaktie mit masch. '
                                                'Aktienbuch',
                                    custodyTypeId='collective-custody-registered-share-with-match-share-register'),
                    instrument=Instrument(id='12345678-1234-1234-1234-1345678901122',
                                        identifiers=[IdentifierItem(identifier='isin',
                                                                    value='DE0005557508'),
                                                        IdentifierItem(identifier='wkn',
                                                                    value='555750')],
                                        name=Name(long='DEUTSCHE TELEKOM '
                                                        'AG NAMENS-AKTIEN '
                                                        'O.N.',
                                                    short='DT.TELEKOM AG NA'),
                                        unit='pieces'),
                    lastOrderDate='2015-01-01',
                    performance=Performance(currentValue=PerformanceValue(currencyCode='EUR',
                                                                        value=12345.4,
                                                                        unit='currency'),
                                            isOutdated=True),
                    quantity=Quantity(unit='pieces',
                                    value=55.0),
                    quote=Quote(id='18273645-1423-1423-1423-10293847561122',
                                market='Tradegate',
                                price=PerformanceValue(currencyCode='EUR',
                                                        value=33.44,
                                                        unit='currency'),
                                timestamp='2024-01-01T11:25:00Z'))
```

### Postbox Item

```python
PostboxItem(id='12345678-1234-1234-1234-12345678901122',
        document=Document(creationDate='2023-01-01T01:02:03.4567890Z',
                        expirationDate='2025-06-30',
                        retentionPeriod='P3Y',
                        contentType='application/pdf',
                        checksum='1234567890abcdef',
                        fileName='Kreditkarte_4930XXXXXXXX0123_Abrechnung_20230101.pdf',
                        metadata={'cardId': '12345678-1234-1234-1234-123456789011223',
                                    'portfolio': 'dkb',
                                    'statementAmount': '105044.98',
                                    'statementCurrency': 'EUR',
                                    'statementDate': '2023-01-01',
                                    'statementID': '_G_123456',
                                    'subject': 'Kreditkartenabrechnung vom 01.Januar 2023'},
                        owner='service-documentexchange-api',
                        link='https://banking.dkb.de/api/documentstorage/documents/12345678-1234-1234-1234-12345678901122',
                        rcode=None),
        message=Message(archived=False,
                        read=True,
                        subject='Kreditkartenabrechnung vom 01.Januar 2023',
                        documentType='creditCardStatement',
                        creationDate='2023-01-01T01:02:03.4567890Z',
                        link='https://banking.dkb.de/api/documentstorage/messages/12345678-1234-1234-1234-12345678901122'))
```

### Standing-Order Item

```python
StandingOrderItem(amount=Amount(value=10.0,
                                currencyCode='EUR',
                                conversionRate=None,
                                date=None,
                                unit=None),
                creditor=Account(accountNr=None,
                                accountId=None,
                                bic='BYLADWHATEVER',
                                blz=None,
                                iban='DE12123405120391293',
                                id=None,
                                intermediaryName=None,
                                name='NAME'),
                debtor=Account(accountNr=None,
                                accountId='12345678-1234-1234-1234-12345678901122',
                                bic=None,
                                blz=None,
                                iban='DE712345678901122',
                                id=None,
                                intermediaryName=None,
                                name=None),
                description='any decription',
                messages=[],
                recurrence=Recurrence(frm='2024-01-01',
                                        frequency='monthly',
                                        holidayExecutionStrategy='following',
                                        nextExecutionAt='2024-02-01',
                                        until=None),
                status='accepted')
```

### ExeMption-Order Item

```python
ExemptionOrderItem(exemptionAmount=Amount(value=2000.0,
                                           currencyCode='EUR',
                                           conversionRate=None,
                                           date=None,
                                           unit=None),
                    exemptionOrderType='joint',
                    partner=Person(firstName='Firstname',
                                   lastName='Lastname',
                                   title=None,
                                   salutation='salutation',
                                   dateOfBirth='1980-01-01',
                                   taxId='1234567890'),
                    receivedAt='2021-01-01',
                    utilizedAmount=Amount(value=12.34,
                                          currencyCode='EUR',
                                          conversionRate=None,
                                          date=None,
                                          unit=None),
                    remainingAmount=Amount(value=1987.65,
                                           currencyCode='EUR',
                                           conversionRate=None,
                                           date=None,
                                           unit=None),
                    validFrom='2024-01-01',
                    validUntil='9999-12-31')
```
