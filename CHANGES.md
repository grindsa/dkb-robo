<!-- markdownlint-disable  MD013 -->
# dkb-robo changelog

This is a high-level summary of the most important changes. For a full list of changes, see the [git commit log](https://github.com/grindsa/dkb-robo/commits) and pick the appropriate release branch.

# Changes in 0.24.1

**Bugfixes**:

- [#49](https://github.com/grindsa/dkb-robo/issues/49) - adding Mandatsreferenz to transcation dictionary

# Changes in 0.24

**Bugfixes**:

- #47 - refactor `DKBRobo._build_account_dic()` to reflect changes in rest-responses
- do not show transactoin link for debitcards
- several fixes to keep ordering as shown in UI
- [fix](https://github.com/grindsa/dkb-robo/issues/47#issuecomment-1751807028) to allow future transaction dates in new API

**Improvements**:

- show accounts which are not assigned to a group
- show debitcards in DKBRobo.account_dic
- extend credit/debitcard information by status (blocked/active) and expiry date

# Changes in 0.23.2

**Bugfixes**:

- #46 - full fix for `tan_insert` option

# Changes in 0.23.1

**Improvements**:

- #45 - CLI support of the new API
- CLI option `-l` to use the old frontend
- support date input in `%Y-%m-%d` format
- all dates will be returned in `%Y-%m-%d` format when using the new API

**Bufixes**:

- #46 - `tan_insert` option enforces the useage of old frontend
- CLI option `-l` enforces the useage of old frontend

# Changes in 0.23

**Improvements**:

- get_transactions() and get_overview() methods are using the new API

# Changes in 0.22

**Bugfixes**:

- [41] - link changes at DKB portal

# Changes in 0.21 - beta

**Improvements**:

- suppport for the new DKB frontend (experimental). To use the new frontent create dkb context manager as shown below.

```python
with DKBRobo(DKB_USER, DKB_PASSWORD, TAN, legacy_login=False) as dkb:
  ...
```

# Chagens in 0.21

**Features**:

- [[#39](https://github.com/grindsa/dkb-robo/issues/39) support new DKB frontend]

# Changes in 0.20.1

**Bugfixes**:

- #38 `long_description` field in PyPI

## Changes in 0.20

**Features**:

- [#36](https://github.com/grindsa/dkb-robo/pull/36) dkb_robo CLI tool

## Changes in 0.19.1

**Bugfixes**:

- addressing code smells reported by [sonarcloud.io](https://sonarcloud.io/summary/overall?id=grindsa_dkb-robo)

## Changes in 0.19

**Features**:

- [#34](https://github.com/grindsa/dkb-robo/pull/34) Add date into filename when scanning postbox

## Changes in 0.18.2

**Bugfixes**:

- addressing code smells reported by [sonarcloud.io](https://sonarcloud.io/summary/overall?id=grindsa_dkb-robo)

## Changes in 0.18.1

**Bugfixes**:

- [sonarcloud.io](https://sonarcloud.io/summary/overall?id=grindsa_dkb-robo) badges in Readme.md
- security issues reported by sonarcube

## Changes in 0.18

**Bugfixes**:

- [#32](https://github.com/grindsa/dkb-robo/issues/32) German Umlaut in filename

## Changes in 0.17

**Bugfixes**:

- #30 - handle attribute errors in case of empty documentlist
- #31 - avoid overrides in case of duplicate document names

## Changes in 0.16

**Features**:

- #29 - add method to retrieve depot status

**Improvements**:

- convert numbers to float wherever possible

## Changes in 0.15

- obsolete version.py to address [#28](https://github.com/grindsa/dkb-robo/pull/28)

## Changes in 0.14

**Features**:

- [reserved transactions ("vorgemerke Buchungen") support](https://github.com/grindsa/dkb-robo/pull/26/files)

## Changes in 0.13.1

**Improvements**:

- [date_from/date_to validation against minimal date](https://github.com/grindsa/dkb-robo/issues/25)

## Changes in 0.13

**Features**:

- add amount `amount_original` ("ursprünglicher Betrag") field to creditcard transaction list

**Improvements**:

- adding code-review badge from [lgtm.com](https://lgtm.com/projects/g/grindsa/dkb-robo/?mode=list)
- some smaller fixes to address [lgtm code-review comments](https://lgtm.com/projects/g/grindsa/dkb-robo/alerts/?mode=list)

## Changes in 0.12

**Features**:

- support of the new [DKB-app](https://play.google.com/store/apps/details?id=com.dkbcodefactory.banking)

**Improvements**:

- underscore-prefixed Class-local references

## Changes in 0.11

**Improvements**:

- scan_postbox() is able to scan and download the Archiv-Folder
- removed python2 support
- better error handling (raise Exceptions instead of sys.exit)
- use of `logging` module for debug messages
- [date_from/date_to validation](https://github.com/grindsa/dkb-robo/issues/22)
- additional unittests
- pep8 conformance validation
- unittest coverage measurement via [codecov.io](https://app.codecov.io/gh/grindsa/dkb-robo)

**Bugfixes**:

- ExemptionOrder Link corrected

## Changes in 0.10.7

**Improvements**:

- output of scan_postbox() contains path and filename of the downloaded file

## Changes in 0.10.5

**Improvements**:

- fix release summing-up smaller improvements from last few months

  - harmonized workflows
  - code-scanning via CodeQL and OSSAR
  - modifications due to pylint error messages

## Changes in 0.10.4

**Improvements**:

- pypi packaging added to create_release workflow

## Changes in 0.10.3

**Bugfixes***:

- daf35c9 improved checking account detection (DKB removed the "Cash im Shop" link)
- d40200e0 fix for faulty TAN handling reported in #18

## Changes in 0.10.2

**Bugfixes***:

- 14ba22c7 fix for "Kontoauszugsdownload"

## Changes in 0.10

**Features**:

- Ability do download documents from DKB Postbox
- Tan2go support

## Changes in 0.9

**Features**:

- MFA support limited to confirmation via DKB-app and TANs generated by ChipTan method
- Debug mode

## Changes in 0.8.3

**Bugfixes**:

- Some smaller bug-fixes in dkb_robo and unittests

## Changes in 0.8.2

**Bugfixes**:

- fix typos - thanks to tbm

## Changes in 0.8.1

**Features**:

- Transactions for checking accounts and credit cares are based on CSV file downloadable from website
- Support of non dkb-accounts in account overview and transaction list
