#!/usr/bin/python

"""Up Bank API.

Use the Up Bank API to retrieve transactions.

That is really all I am interested in because I use my own pattern matching,
against the transaction description, to sort them into accounts (aka categories).
"""
import datetime
import click
import json
import os
import pprint
import requests


URL = "https://api.up.com.au/api/v1"

# Maximum number of transactions upbank return per 'page'.
PAGE_SIZE = 100

# Constants
HELD = "HELD"
SETTLED = "SETTLED"


class LocalTZ(datetime.tzinfo):
    """Your time zone with an arbitrary, constant offset."""

    def utcoffset(self, dt):
        return datetime.timedelta(hours=+11, minutes=0)


class UpbankClient:
    def __init__(self, token: str):
        """
        token: str: upbank "personal access token" from https://api.up.com.au/getting_started
        """
        self.token = token

    def get_month(self, year: int, month: int) -> []:
        """Get settled transactions for the given month.

        year: int: year to download eg: 2021
        month: int: month to download eg: 3

        Returns:
              A list of settled transactions as a dict.
        """
        local_tz = datetime.datetime.utcnow().astimezone().tzinfo
        since = datetime.datetime(year=year, month=month, day=1, tzinfo=local_tz)
        if month == 12:
            month = 0
            year += 1
        until = datetime.datetime(year=year, month=month + 1, day=1, tzinfo=local_tz)
        return self.transactions(since, until, SETTLED)

    def transactions(
        self, since: datetime.datetime, until: datetime.date = None, status: str = None
    ) -> list:
        """Fetch a list of transactions.

        Args:
            since: tzaware datetime to start from
            until: tzaware datetime to stop at; or None for all.
            status: "HELD" or "SETTLED"

        Returns:
            list of "SETTLED" transactions in dict format.
        """
        params = dict()

        # Upbank only return PAGE_SIZE transactions per request, so we need to
        params.update({"page[size]": PAGE_SIZE})
        params.update({"filter[since]": since})
        if until is not None:
            params.update({"filter[until]": until})
        if status is not None:
            params.update({"filter[status]": status})
        response = self.get("/transactions", params=params)
        return response

    def get(self, path, params: dict = None) -> list:
        """Send a GET request to Up.

        Args:
            path: includes the preceding slash.
            params: request parameters.

        Returns:
            list of data; probably dicts.
        """
        result = []
        uri = f"{URL}{path}"
        while uri is not None:
            response = requests.get(uri, headers=self._headers(), params=params)
            data = response.json()
            result.extend(data["data"])
            try:
                uri = data["links"]["next"]
            except KeyError:
                break
        return result

    def ping(self):
        """Verify the access token is working.

        Returns:
            requests.Response
        """
        return requests.get(f"{URL}/util/ping", headers=self._headers())

    def accounts(self):
        """Fetch a list of accounts."""
        return self.get("/accounts")

    def categories(self):
        """Fetch a list of categories."""
        return self.get("/categories")

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}


if (UPBANK_TOKEN := os.getenv('FIONA_UPBANK_TOKEN')) is None:
    print('Please put a valid upbank token into an environment variable JOHN_UPBANK_TOKEN')
    exit(1)


@click.group()
def cli():
    pass


@cli.command()
def ping():
    """Send a ping to Upbank, to verify your token and their API status."""
    client = UpbankClient(UPBANK_TOKEN)
    response = client.ping()
    click.echo("Ping!")
    click.echo(response.text)


@cli.command()
def categories():
    """Get a list of transaction categories."""
    client = UpbankClient(UPBANK_TOKEN)
    response = client.categories()
    click.echo(pprint.pformat(response))


@cli.command()
def balance():
    """Fetch the current balance of the account."""
    client = UpbankClient(UPBANK_TOKEN)
    response = client.accounts()
    print(response)
    click.echo("${0:.2f}".format(float(response[0]['attributes']['balance']['value'])))


@cli.command()
@click.argument("year", type=click.types.INT)
@click.argument("month", type=click.types.INT)
def month(year, month):
    """Download a sequence of transactions.
    """
    client = UpbankClient(UPBANK_TOKEN)
    transactions = client.get_month(year, month)
    click.echo(json.dumps(transactions, indent=3))


@cli.command()
@click.argument("rawfile", type=click.Path(exists=True))
@click.argument("balance", type=click.types.FLOAT)
def brewfiona(rawfile, balance):
    """Generate beans from fionas upbank transaction file.
    """
    transactions = json.load(open(rawfile))
    change = 0.0
    date_str = 'No date'
    tags = '#fiona'
    accountname = "Assets:Bank:Fiona-Upbank"

    for trans in reversed(transactions):
        date_str = trans['attributes']['createdAt'][:10]
        raw_text = trans['attributes']['rawText']
        description = trans['attributes']['description']
        value = - float(trans['attributes']['amount']['value'])
        try:
            category = ':'.join([
                trans['relationships']['parentCategory']['data']['id'],
                trans['relationships']['category']['data']['id'],
            ])
        except TypeError:
            category = ''
        txt_description = f"\"{raw_text} [{description}]\""
        entry = f'{date_str} * {txt_description:66s}  {tags}\n'
        entry += f"    {accountname}\n"
        entry += "    %-46s %10.2f AUD\n" % (
            f'ACCOUNT_UNKNOWN [{category}]', float(value))

        click.echo(entry)
        change += float(value)
    balance = balance - change
    balance_str = f"{date_str} balance {accountname:36s} {balance:.2f} AUD"
    click.echo(balance_str)


if __name__ == "__main__":
    cli()
