import datetime
import json
import pprint
import unittest.mock
import sys

import accounts as acc
import upbank

RAW_FILE = '../john-fiona/raw/upbank/latest.json'
YAML_TESTFILE = '../john-fiona/accounts.yaml'


def test_find_unknown_merchants():
    """From the download, list the most unknown transactions.

    * load the download file and the accounts yaml
    * list the transactions without an account in frequency order.
    """
    print()
    accounts = acc.AccountFile(YAML_TESTFILE)
    raw_data = json.load(open('test_data/up_transactions.json'))

    unknowns, knowns = dict(), set()
    for item in raw_data['data']:
        description = f"{item['attributes']['description']} \"{item['attributes']['rawText']}\""
        account = accounts.match(description)
        if account is None:
            unknowns.setdefault(description, list()).append(item)
        else:
            knowns.add(f"{description} -> {account}")

    unknowns_list = sorted(unknowns.keys(), key=lambda key: len(unknowns[key]), reverse=True)
    for description in unknowns_list:
        print(f"{len(unknowns[description])} {description}")

    print()
    for known in knowns:
        print(known)


def test_download_transactions():
    """Download a sequence of transactions.

      * connect to the Upbank API.
      * save the period of transactions to file.
    """
    since_day = datetime.date(year=2021, month=1, day=1)
    transactions = upbank.transactions(since=since_day)
    settled = [trans for trans in transactions
               if trans['attributes']['status'] == 'SETTLED']
    with open(RAW_FILE, "w") as fh:
        json.dump(settled, fh, indent=3)
    print(settled)


def test_generate_beans():
    """Convert the given file to beancount transactions, using the accounts yaml.
    """
    accounts = acc.AccountFile(YAML_TESTFILE)
    transactions = json.load(open('test_data/up_transactions.json'))['data']

    fh = open("generated.beancount", "w")
    sys.stdout.write("\n")
    for trans in transactions:
        date_str = trans['attributes']['createdAt'][:10]
        description = f"{trans['attributes']['rawText']} [{trans['attributes']['description']}]"
        value = trans['attributes']['amount']['value']
        account = accounts.match(description) or "Expenses:TODO"

        entry = f"{date_str} * \"{description}\"\n"
        entry += "    Assets:Bank:Upbank\n"
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

