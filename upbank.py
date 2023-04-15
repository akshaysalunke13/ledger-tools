import click
import json
import os
import pprint
from zoneinfo import ZoneInfo
from ledgertools.upclient import UpbankClient, SETTLED

if (UPBANK_TOKEN := os.getenv('UP_TOKEN')) is None:
    print('Please put a valid upbank token into an environment variable UP_TOKEN')
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


@cli.command()
@click.argument("fromdate", type=click.DateTime(formats=["%d/%m/%Y"]))
@click.argument("todate", type=click.DateTime(formats=["%d/%m/%Y"]))
def gettxns(fromdate, todate):
    """Get all transactions for given date range

    Args:
        fromdate (datetime): from date in dd/mm/yyyy
        todate (datetime): to dat in dd/mm/yyyy
    """
    local_tz = ZoneInfo("Australia/Melbourne")
    # local_tz = ZoneInfo("UTC")
    fromdate = fromdate.replace(tzinfo=local_tz)
    todate = todate.replace(tzinfo=local_tz)
    
    client = UpbankClient(UPBANK_TOKEN)
    txns = client.transactions(fromdate, todate)
    # print(txns[0])
    # print('\n')
    # print(txns[-1])
    for t in txns:
        print(t)

if __name__ == "__main__":
    cli()
    # gettxns("01/12/2022", "31/12/2022")
