import datetime
import json
import os
import pprint
import unittest.mock
import sys

from . import accounts as acc
from . import upbank

YEAR, MONTH = 2021, 3
ACCOUNT = 'fiona'

RAW_FILE = '../john-fiona/raw/upbank/%i-%02.i-trans-fiona.json' % (YEAR, MONTH)
YAML_TESTFILE = '../john-fiona/accounts.yaml'

if (UPBANK_TOKEN := os.getenv('UPBANK_TOKEN')) is None:
    print('Please put a valid upbank token into an environment variable UPBANK_TOKEN')
    exit(1)


def test_download_transactions():
    """Download a sequence of transactions.

      * connect to the Upbank API.
      * save the period of transactions to file.
    """
    client = upbank.UpbankClient(UPBANK_TOKEN)
    transactions = client.get_month(YEAR, MONTH)
    with open(RAW_FILE, "w") as fh:
        json.dump(transactions, fh, indent=3)
    print()
    for transaction in transactions:
        print("%-32s %8s %s %s" % (
            transaction['attributes']['rawText'],
            transaction['attributes']['amount']['value'],
            transaction['attributes']['status'],
            transaction['attributes']['createdAt'],
        ))


def test_find_unknown_merchants():
    """From the download, list the most unknown transactions.

    * load the download file and the accounts yaml
    * list the transactions without an account in frequency order.
    """
    print()
    accounts = acc.AccountFile(YAML_TESTFILE)
    raw_data = json.load(open(RAW_FILE))

    unknowns, knowns = dict(), set()
    for item in raw_data:
        raw_text = item['attributes']['rawText']
        description = item['attributes']['description']
        full_description = f"{item['attributes']['description']} \"{item['attributes']['rawText']}\""
        account = accounts.match(description) or accounts.match(raw_text)
        if account is None:
            unknowns.setdefault(full_description, list()).append(item)
        else:
            knowns.add("%-50s -> %s" % (full_description, account))

    unknowns_list = sorted(unknowns.keys(), key=lambda key: len(unknowns[key]), reverse=True)
    for description in unknowns_list:
        print(f"{len(unknowns[description])} {description}")
        values = [trans['attributes']['amount']['value'] for trans in unknowns[description]]
        print(", ".join(values))

    print()
    for known in sorted(knowns):
        print(known)


def test_generate_beans():
    """Convert the given file to beancount transactions, using the accounts yaml.
    """
    accounts = acc.AccountFile(YAML_TESTFILE)
    transactions = json.load(open(RAW_FILE))

    fh = open("generated.beancount", "w")
    sys.stdout.write("\n")
    for trans in reversed(transactions):
        date_str = trans['attributes']['createdAt'][:10]
        raw_text = trans['attributes']['rawText']
        description = trans['attributes']['description']
        value = - float(trans['attributes']['amount']['value'])
        account = (accounts.match(description) or
                   accounts.match(raw_text) or
                   "Expenses:TODO")

        entry = f'{date_str} * "{raw_text} [{description}]"\n'
        entry += "    Assets:Bank:John-Upbank\n"
        entry += "    %-46s %10.2f AUD\n\n" % (account, float(value))

        sys.stdout.write(entry)
        fh.write(entry)
    fh.close()


def test_transactions():
    local_tz = datetime.datetime.utcnow().astimezone().tzinfo
    since = datetime.datetime(year=2020, month=11, day=1, tzinfo=local_tz)
    until = datetime.datetime(year=2020, month=11, day=3, tzinfo=local_tz)
    client = upbank.UpbankClient(UPBANK_TOKEN)
    data = client.transactions(since, until, upbank.SETTLED)
    pprint.pp(data)
    assert len(data) == 9


def test_ping():
    """Verify the token still works."""
    client = upbank.UpbankClient(UPBANK_TOKEN)
    response = client.ping()
    pprint.pp(response.text)
    assert response.status_code == 200


def test_accounts():
    """Fetch a list of accounts."""
    client = upbank.UpbankClient(UPBANK_TOKEN)
    data = client.accounts()
    pprint.pp(data)


def test_categories():
    """Show me a list of categories."""
    client = upbank.UpbankClient(UPBANK_TOKEN)
    data = client.categories()
    pprint.pp(data)


@unittest.mock.patch.object(upbank.UpbankClient, 'get')
def test_categories_processing(mock_get):
    """Show me a list of categories."""
    mock_get.return_value = json.load(open('test_data/up_categories.json'))
    client = upbank.UpbankClient(UPBANK_TOKEN)
    data = client.categories()
    categories = {c['id']:c for c in data}
    top_level = [c for c in data if c['relationships']['parent']['data'] is None]
    for category in top_level:
        for child in category['relationships']['children']['data']:
            pprint.pp(f"{category['id']} -> {child['id']} {categories[child['id']]['relationships']['children']['data']}")


foo = """
2020-01-02 * "Increase 50 Per Month  Internet Withdrawal 01Jan 06:03"
    Assets:Bank:Joint-CompleteFreedom
    Assets:Bank:IncentiveSaver                          50.00 AUD

2020-01-02 * "Hoyts Corp Pty Ltd Modbury Visa Purchase 30Dec"       #adelaide2019
    Assets:Bank:Joint-CompleteFreedom
    Expenses:Holiday:Activities                         38.00 AUD
"""

