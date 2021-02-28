import datetime
import json
import pprint
import unittest.mock
import sys

import accounts as acc
import upbank

YEAR, MONTH = 2020, 12

RAW_FILE = f'../john-fiona/raw/upbank/{YEAR}-{MONTH}-trans.json'
YAML_TESTFILE = '../john-fiona/accounts.yaml'


def test_download_transactions():
    """Download a sequence of transactions.

      * connect to the Upbank API.
      * save the period of transactions to file.
    """
    local_tz = datetime.datetime.utcnow().astimezone().tzinfo
    since = datetime.datetime(year=YEAR, month=MONTH, day=1, tzinfo=local_tz)
    until = datetime.datetime(year=YEAR, month=MONTH+1, day=1, tzinfo=local_tz)
    transactions = upbank.transactions(since, until, upbank.SETTLED)
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
            knowns.add("%-30s -> %s" % (account, full_description))

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


def test_ping():
    """Verify the token still works."""
    response = upbank.ping()
    pprint.pp(response.text)
    assert response.status_code == 200


def test_accounts():
    """Fetch a list of accounts."""
    data = upbank.accounts()
    pprint.pp(data)


def test_transactions():
    data = upbank.transactions()
    pprint.pp(data)


def test_categories():
    """Show me a list of categories."""
    data = upbank.categories()
    pprint.pp(data)


@unittest.mock.patch.object(upbank, 'get')
def test_categories_processing(mock_get):
    """Show me a list of categories."""
    mock_get.return_value = json.load(open('test_data/up_categories.json'))
    data = upbank.categories()
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

