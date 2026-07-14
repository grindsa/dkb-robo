# pylint: disable=c3001, e1101, r0913, w0108, w0622
"""dkb_robo cli"""

from datetime import date
from pathlib import Path
import pathlib
from pprint import pprint
from contextlib import contextmanager
import shlex
import os
import sys
import csv
import json
import dataclasses
import tabulate
import click
import dkb_robo
from dkb_robo.utilities import object2dictionary

sys.path.append("..")

DATE_FORMAT = "%d.%m.%Y"
DATE_FORMAT_ALTERNATE = "%Y-%m-%d"


def _store_proxy(ctx, _param, value):
    """store proxy option in click context"""
    if ctx.obj is None:
        ctx.obj = {}
    if value is not None:
        ctx.obj["PROXY"] = value
    return value


def _store_http1_only(ctx, _param, value):
    """store HTTP/1.1 option in click context"""
    if ctx.obj is None:
        ctx.obj = {}
    if value is not None:
        ctx.obj["HTTP1_ONLY"] = value
    return value


def _store_session_backend(ctx, _param, value):
    """store session backend option in click context"""
    if ctx.obj is None:
        ctx.obj = {}
    if value is not None:
        ctx.obj["SESSION_BACKEND"] = value
    return value


def _store_password_env_var(ctx, _param, value):
    """store password env var name in click context"""
    if ctx.obj is None:
        ctx.obj = {}
    if value is not None:
        ctx.obj["PASSWORD_ENV_VAR"] = value
    return value


def _resolve_password(ctx, password, password_env_var):
    """Resolve password from CLI/env and prompt as fallback."""
    password_source = None
    if hasattr(ctx, "get_parameter_source"):
        try:
            password_source = ctx.get_parameter_source("password")
        except Exception:
            password_source = None

    password_from_cli = (
        hasattr(click.core, "ParameterSource")
        and password_source == click.core.ParameterSource.COMMANDLINE
    )
    if password_from_cli:
        return password

    if password_env_var:
        password_from_env = os.getenv(password_env_var)
        if password_from_env:
            return password_from_env

    if password:
        return password

    return click.prompt("Password", hide_input=True, type=str)


def _read_env_flag(env_name, default=False):
    """Read a boolean flag from an environment variable."""
    value = os.getenv(env_name)
    if value is None:
        return default
    normalized = value.strip().lower()
    return normalized in ("1", "true", "yes", "on")


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
    "--headless",
    default=False,
    is_flag=True,
    help="Run captcha browser in headless mode",
    envvar="DKB_HEADLESS",
)
@click.option(
    "--xvfb",
    default=False,
    is_flag=True,
    help="Use Xvfb virtual display for captcha solving (for headless servers)",
    envvar="DKB_XVFB",
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
    prompt=False,
    hide_input=True,
    type=str,
    help="corresponding login password",
    envvar="DKB_PASSWORD",
)
@click.option(
    "--password-env-var",
    default="DKB_PASSWORD",
    type=str,
    show_default=True,
    help="Environment variable name that contains the login password",
    envvar="DKB_PASSWORD_ENV_VAR",
    callback=_store_password_env_var,
    expose_value=False,
)
@click.option(
    "--format",
    default="pprint",
    type=click.Choice(["pprint", "table", "csv", "json"]),
    help="output format to use",
    envvar="DKB_FORMAT",
)
@click.option(
    "--session-backend",
    default="curl-cffi",
    type=click.Choice(["requests", "curl-cffi"]),
    help="HTTP client backend to create login session",
    envvar="DKB_SESSION_BACKEND",
    callback=_store_session_backend,
    expose_value=False,
)
@click.option(
    "--http1-only",
    default=False,
    is_flag=True,
    help="Force HTTP/1.1 for curl-cffi sessions",
    envvar="DKB_HTTP1_ONLY",
)
@click.option(
    "--proxy",
    default=None,
    type=str,
    help="Proxy address to use for both HTTP and HTTPS requests",
    envvar="DKB_PROXY",
    callback=_store_proxy,
    expose_value=False,
)
@click.pass_context
def main(
    ctx,
    debug,
    unfiltered,
    mfa_device,
    headless,
    xvfb,
    use_tan,
    chip_tan,
    username,
    password,
    format,
    http1_only,
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
    ctx.obj["HEADLESS"] = headless
    ctx.obj["XVFB"] = xvfb
    ctx.obj["USERNAME"] = username
    ctx.obj["PASSWORD"] = _resolve_password(
        ctx,
        password,
        ctx.obj.get("PASSWORD_ENV_VAR", "DKB_PASSWORD"),
    )
    ctx.obj["FORMAT"] = _load_format(format)
    ctx.obj["SESSION_BACKEND"] = ctx.obj.get("SESSION_BACKEND", "curl-cffi")
    ctx.obj["HTTP1_ONLY"] = http1_only
    ctx.obj["LOGIN_VIA_BROWSER"] = _read_env_flag("DKB_LOGIN_VIA_BROWSER")


@main.command()
@click.pass_context
def accounts(ctx):
    """get list of account"""
    try:
        with _session_scope(ctx) as dkb:
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
        with _session_scope(ctx) as dkb:
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
        with _session_scope(ctx) as dkb:
            ctx.obj["FORMAT"]([{"last_login": dkb.last_login}])
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)


@main.command()
@click.pass_context
def credit_limits(ctx):
    """get limits"""
    try:
        with _session_scope(ctx) as dkb:
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
        with _session_scope(ctx) as dkb:
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
        with _session_scope(ctx) as dkb:
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
        with _session_scope(ctx) as dkb:
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


def _invoke_shell_command(ctx, args):
    """Invoke one existing subcommand using the current click context."""
    command_name = args[0]
    if command_name == "interactive":
        click.echo("interactive cannot be called from interactive mode", err=True)
        return

    if "--proxy" in args or "--http1-only" in args:
        click.echo(
            "--proxy and --http1-only must be passed when starting the CLI session",
            err=True,
        )
        return

    command = main.get_command(ctx, command_name)
    if command is None:
        click.echo(f"Unknown command: {command_name}", err=True)
        return

    cmd_ctx = command.make_context(command_name, args[1:], parent=ctx, obj=ctx.obj)
    with cmd_ctx:
        command.invoke(cmd_ctx)


@main.command()
@click.pass_context
def interactive(ctx):
    """Start an interactive shell with a single login session."""
    session = _login(ctx)
    try:
        with session as dkb:
            ctx.obj["ACTIVE_SESSION"] = dkb
            click.echo('Interactive mode started. Type "help" for commands and "logout" to exit.')
            while True:
                try:
                    line = input("dkb> ").strip()
                except EOFError:
                    click.echo()
                    break
                except KeyboardInterrupt:
                    click.echo()
                    break

                if not line:
                    continue

                if line in ("logout", "quit", "exit"):
                    break

                if line in ("help", "?"):
                    commands = sorted(name for name in main.commands if name != "interactive")
                    click.echo("Commands: " + ", ".join(commands))
                    continue

                try:
                    _invoke_shell_command(ctx, shlex.split(line))
                except click.ClickException as err:
                    err.show()
                except click.Abort:
                    click.echo("Aborted", err=True)
    except dkb_robo.DKBRoboError as _err:
        click.echo(_err.args[0], err=True)
    finally:
        ctx.obj.pop("ACTIVE_SESSION", None)


@contextmanager
def _session_scope(ctx):
    """Use active interactive session when present, otherwise login per command."""
    active_session = None
    if ctx.obj:
        if hasattr(ctx.obj, "get"):
            active_session = ctx.obj.get("ACTIVE_SESSION")
        else:
            active_session = getattr(ctx.obj, "ACTIVE_SESSION", None)
    if active_session is not None:
        yield active_session
        return

    with _login(ctx) as dkb:
        yield dkb


class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


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

        return lambda data: click.echo(
            json.dumps(data, indent=2, cls=DataclassJSONEncoder)
        )

    raise ValueError(f"Unknown format: {output_format}")


def _login(ctx):
    proxy = ctx.obj.get("PROXY", None)
    proxies = {"http": proxy, "https": proxy} if proxy else None

    return dkb_robo.DKBRobo(
        dkb_user=ctx.obj["USERNAME"],
        dkb_password=ctx.obj["PASSWORD"],
        chip_tan=ctx.obj["CHIP_TAN"],
        debug=ctx.obj["DEBUG"],
        unfiltered=ctx.obj["UNFILTERED"],
        mfa_device=ctx.obj["MFA_DEVICE"],
        headless=ctx.obj.get("HEADLESS", False),
        xvfb=ctx.obj["XVFB"],
        session_backend=ctx.obj.get("SESSION_BACKEND", "requests"),
        http1_only=ctx.obj.get("HTTP1_ONLY", False),
        login_via_browser=ctx.obj.get("LOGIN_VIA_BROWSER", False),
        proxies=proxies,
    )
