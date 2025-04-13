# pylint: disable=c3001, e1101, r0913, w0108, w0622
""" dkb_robo cli """
from datetime import date
from pathlib import Path
import pathlib
from pprint import pprint
import sys
import csv
import json
import tabulate
import click
import dkb_robo
from dkb_robo.utilities import object2dictionary

sys.path.append("..")

DATE_FORMAT = "%d.%m.%Y"
DATE_FORMAT_ALTERNATE = "%Y-%m-%d"


def _account_lookup(ctx, name, account, account_dic, unfiltered):
    """lookup account"""

    mapping_matrix = {
        "account": "iban",
        "creditCard": "maskedPan",
        "debitCard": "maskedPan",
        "depot": "depositAccountId",
        "brokerageAccount": "depositAccountId",
    }
    if name is not None and account is None:
        if unfiltered:

            def account_filter(acct):
                product = getattr(acct, "product", None)
                return getattr(product, "displayName", None) == name

        else:

            def account_filter(acct):
                return acct["name"] == name

    elif account is not None and name is None:
        if unfiltered:

            def account_filter(acct):
                return getattr(acct, mapping_matrix[acct.type]) == account

        else:

            def account_filter(acct):
                return acct["account"] == account

    else:
        raise click.UsageError("One of --name or --account must be provided.", ctx)

    filtered_accounts = [acct for acct in account_dic.values() if account_filter(acct)]
    if len(filtered_accounts) == 0:
        click.echo(f"No account found matching '{name or account}'", err=True)
        raise click.Abort()

    return filtered_accounts[0]


def _id_lookup(ctx, name, account, account_dic, unfiltered):
    """lookup id"""
    the_account = _account_lookup(ctx, name, account, account_dic, unfiltered)
    if unfiltered:
        uid = getattr(the_account, "id", None)
    else:
        uid = the_account["id"]
    return uid


def _transactionlink_lookup(ctx, name, account, account_dic, unfiltered):
    """lookup id"""
    the_account = _account_lookup(ctx, name, account, account_dic, unfiltered)

    if unfiltered:
        output_dic = {
            "id": getattr(the_account, "id", None),
            "type": getattr(the_account, "type", None),
            "transactions": getattr(the_account, "transactions", None),
        }
    else:
        output_dic = {
            "id": the_account.get("id", None),
            "type": the_account.get("type", None),
            "transactions": the_account.get("transactions", None),
        }
    return output_dic


@click.group()
@click.option(
    "--debug",
    "-d",
    default=False,
    help="Show additional debugging",
    is_flag=True,
    envvar="DKB_DEBUG",
)
@click.option(
    "--unfiltered",
    default=False,
    is_flag=True,
    envvar="DKB_UNFILTERED",
    help="Do not filter output from DKB API",
)
@click.option(
    "--mfa-device",
    "-m",
    default=None,
    help='MFA device used for login ("1", "2" ...)',
    type=int,
    envvar="MFA_DEVICE",
)
@click.option(
    "--use-tan",
    default=False,
    is_flag=True,
    envvar="DKB_USE_TAN",
    hidden=True,
)
@click.option(
    "--chip-tan",
    "-t",
    default=None,
    help='use ChipTAN for login (either "qr" or "manual")',
    type=str,
    envvar="DKB_CHIP_TAN",
)
@click.option(
    "--username",
    "-u",
    required=True,
    type=str,
    help="username to access the dkb portal",
    envvar="DKB_USERNAME",
)
@click.option(
    "--password",
    "-p",
    prompt=True,
    hide_input=True,
    type=str,
    help="corresponding login password",
    envvar="DKB_PASSWORD",
)
@click.option(
    "--format",
    default="pprint",
    type=click.Choice(["pprint", "table", "csv", "json"]),
    help="output format to use",
    envvar="DKB_FORMAT",
)
@click.pass_context
def main(
    ctx, debug, unfiltered, mfa_device, use_tan, chip_tan, username, password, format
):  # pragma: no cover
    """main fuunction"""

    if use_tan:
        click.echo(
            "The --use-tan option is deprecated and will be removed in a future release. Please use the --chip-tan option",
            err=True,
        )
        chip_tan = True
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    ctx.obj["UNFILTERED"] = unfiltered
    ctx.obj["CHIP_TAN"] = chip_tan
    ctx.obj["MFA_DEVICE"] = mfa_device
    ctx.obj["USERNAME"] = username
    ctx.obj["PASSWORD"] = password
    ctx.obj["FORMAT"] = _load_format(format)


@main.command()
@click.pass_context
def accounts(ctx):
    """get list of account"""
    try:
        with _login(ctx) as dkb:
            accounts_dict = dkb.account_dic
            for id, value in accounts_dict.items():
                if ctx.obj["UNFILTERED"]:
                    value = object2dictionary(value)
                    accounts_dict[id] = value
                if "details" in value:
                    del value["details"]
                if "transactions" in value:
                    del value["transactions"]
            ctx.obj["FORMAT"](list(accounts_dict.values()))
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


@main.command()
@click.pass_context
@click.option(
    "--name",
    "-n",
    type=str,
    help="Name of the account to fetch transactions for",
    envvar="DKB_TRANSACTIONS_ACCOUNT_NAME",
)
@click.option(
    "--account",
    "-a",
    type=str,
    help="Account to fetch transactions for",
    envvar="DKB_TRANSACTIONS_ACCOUNT",
)
@click.option(
    "--transaction-type",
    "-t",
    default="booked",
    type=click.Choice(["booked", "reserved"]),
    help="The type of transactions to fetch",
    envvar="DKB_TRANSACTIONS_TYPE",
)
@click.option(
    "--date-from",
    type=click.DateTime(formats=[DATE_FORMAT, DATE_FORMAT_ALTERNATE]),
    default=date.today().strftime(DATE_FORMAT),
)
@click.option(
    "--date-to",
    type=click.DateTime(formats=[DATE_FORMAT, DATE_FORMAT_ALTERNATE]),
    default=date.today().strftime(DATE_FORMAT),
)
def transactions(
    ctx, name, account, transaction_type, date_from, date_to
):  # pragma: no cover
    """get list of transactions"""

    try:
        with _login(ctx) as dkb:
            the_account = _transactionlink_lookup(
                ctx, name, account, dkb.account_dic, ctx.obj["UNFILTERED"]
            )
            transactions_list = dkb.get_transactions(
                the_account["transactions"],
                the_account["type"],
                date_from.strftime(DATE_FORMAT),
                date_to.strftime(DATE_FORMAT),
                transaction_type=transaction_type,
            )
            ctx.obj["FORMAT"](transactions_list)

    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


@main.command()
@click.pass_context
def last_login(ctx):
    """get last login"""
    try:
        with _login(ctx) as dkb:
            ctx.obj["FORMAT"]([{"last_login": dkb.last_login}])
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


@main.command()
@click.pass_context
def credit_limits(ctx):
    """get limits"""
    try:
        with _login(ctx) as dkb:
            limits = dkb.get_credit_limits()
            limits = [{"account": k, "limit": v} for k, v in limits.items()]
            ctx.obj["FORMAT"](limits)
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


@main.command()
@click.pass_context
@click.option(
    "--name",
    "-n",
    type=str,
    help="Name of the account to fetch transactions for",
    envvar="DKB_TRANSACTIONS_ACCOUNT_NAME",
)
@click.option(
    "--account",
    "-a",
    type=str,
    help="Account to fetch transactions for",
    envvar="DKB_TRANSACTIONS_ACCOUNT",
)
def standing_orders(ctx, name, account):  # pragma: no cover
    """get standing orders"""
    try:
        with _login(ctx) as dkb:
            uid = _id_lookup(ctx, name, account, dkb.account_dic, ctx.obj["UNFILTERED"])
            so_list = dkb.get_standing_orders(uid)
            standing_orders_list = []
            for so in so_list:
                if ctx.obj["UNFILTERED"]:
                    standing_orders_list.append(object2dictionary(so))
                else:
                    standing_orders_list.append(so)
            ctx.obj["FORMAT"](standing_orders_list)
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


@main.command()
@click.pass_context
@click.option(
    "--path",
    "-p",
    type=str,
    help="Path to save the documents to",
    envvar="DKB_DOC_PATH",
)
@click.option(
    "--download_all",
    is_flag=True,
    show_default=True,
    default=False,
    help="Download all documents",
    envvar="DKB_DOWNLOAD_ALL",
)
@click.option(
    "--archive",
    is_flag=True,
    show_default=True,
    default=False,
    help="Download archive",
    envvar="DKB_ARCHIVE",
)
@click.option(
    "--prepend_date",
    is_flag=True,
    show_default=True,
    default=False,
    help="Prepend date to filename",
    envvar="DKB_PREPEND_DATE",
)
def scan_postbox(ctx, path, download_all, archive, prepend_date):
    """scan postbox"""
    if not path:
        path = "documents"
    try:
        with _login(ctx) as dkb:
            doc_list = dkb.scan_postbox(
                path=path, download_all=download_all, prepend_date=prepend_date
            )
            if ctx.obj["UNFILTERED"]:
                documents_list = []
                for doc in doc_list.values():
                    documents_list.append(object2dictionary(doc))
            else:
                documents_list = doc_list
            ctx.obj["FORMAT"](documents_list)
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


@main.command()
@click.pass_context
@click.option(
    "--path",
    "-p",
    type=click.Path(writable=True, path_type=pathlib.Path),
    help="Path to save the documents to",
    envvar="DKB_DOC_PATH",
)
@click.option(
    "--all",
    "-A",
    is_flag=True,
    show_default=True,
    default=False,
    help="Download all documents",
    envvar="DKB_DOWNLOAD_ALL",
)
@click.option(
    "--prepend-date",
    is_flag=True,
    show_default=True,
    default=False,
    help="Prepend date to filename",
    envvar="DKB_PREPEND_DATE",
)
@click.option(
    "--mark-read",
    is_flag=True,
    show_default=True,
    default=True,
    help="Mark downloaded files read",
    envvar="DKB_MARK_READ",
)
@click.option(
    "--use-account-folders",
    is_flag=True,
    show_default=True,
    default=False,
    help="Store files in separate folders per account/depot",
    envvar="DKB_ACCOUNT_FOLDERS",
)
@click.option(
    "--list-only",
    is_flag=True,
    show_default=True,
    default=False,
    help="Only list documents, do not download",
    envvar="DKB_LIST_ONLY",
)
def download(
    ctx,
    path: Path,
    all: bool,
    prepend_date: bool,
    mark_read: bool,
    use_account_folders: bool,
    list_only: bool,
):
    """download document"""
    if path is None:
        list_only = True
    try:
        with _login(ctx) as dkb:
            ctx.obj["FORMAT"](
                dkb.download(
                    path=path,
                    download_all=all,
                    prepend_date=prepend_date,
                    mark_read=mark_read,
                    use_account_folders=use_account_folders,
                    list_only=list_only,
                )
            )
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


def _load_format(output_format):
    """select output format based on cli option"""
    if output_format == "pprint":
        return lambda data: pprint(data)

    if output_format == "table":
        return lambda data: click.echo(
            tabulate.tabulate(data, headers="keys", tablefmt="grid")
        )

    if output_format == "csv":

        def formatter(data):  # pragma: no cover
            if len(data) == 0:
                return
            writer = csv.DictWriter(sys.stdout, fieldnames=max(data, key=len).keys())
            writer.writeheader()
            writer.writerows(data)

        return formatter

    if output_format == "json":

        return lambda data: click.echo(json.dumps(data, indent=2))

    raise ValueError(f"Unknown format: {output_format}")


def _login(ctx):
    return dkb_robo.DKBRobo(
        dkb_user=ctx.obj["USERNAME"],
        dkb_password=ctx.obj["PASSWORD"],
        chip_tan=ctx.obj["CHIP_TAN"],
        debug=ctx.obj["DEBUG"],
        unfiltered=ctx.obj["UNFILTERED"],
        mfa_device=ctx.obj["MFA_DEVICE"],
    )
