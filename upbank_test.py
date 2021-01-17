import datetime
import json
import pprint
import unittest.mock
import sys

import accounts as acc
import upbank

RAW_FILE = '../john-fiona/raw/upbank/latest.json'
YAML_TESTFILE = '../john-fiona/accounts.yaml'


def test_unknowns():
    """From the download, list the most unknown transactions.

    * load the download file and the accounts yaml
    * list the transactions without an account in frequency order.
    """
    # TODO
    pass


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
    """From the download, generate a beancount file for Upbank."""
    # TODO
    pass


def test_convert_file():
    """Convert the given file to beancount transactions, using the accounts yaml.
    """
    accounts = acc.AccountFile(YAML_TESTFILE)
    transactions = json.load(open('test_data/up_transactions.json'))['data']

    fh = open("generated.beancount", "w")
    sys.stdout.write("\n")
    for trans in transactions:
        date_str = trans['attributes']['createdAt'][:10]
        description = f"{trans['attributes']['rawText']} ({trans['attributes']['description']})"
        value = trans['attributes']['amount']['value']
        account = accounts.match(description)
        if account is None:
            account = "Expenses:TODO"
        sys.stdout.write(f"{date_str} * \"{description}\"\n")
        sys.stdout.write(f"    Assets:Bank:Upbank\n")
        sys.stdout.write("    %-46s %10.2f AUD\n" % (account, float(value)))
        sys.stdout.write("\n")
    fh.close()


def test_transaction_data():
    """Play with transaction data."""
    print()
    accounts = acc.AccountFile(YAML_TESTFILE)
    raw_data = json.load(open('test_data/up_transactions.json'))
    data = raw_data['data']
    for item in data:
        date_str = item['attributes']['createdAt'][:10]
        description = f"{item['attributes']['rawText']} ({item['attributes']['description']})"
        value = item['attributes']['amount']['value']
        account = accounts.match(description)
        if account is None:
            account = "Expenses:TODO"

        print(f"{date_str} * \"{description}\"")
        print(f"    Assets:Bank:Upbank")
        print("    %-46s %10.2f AUD\n" % (account, float(value)))


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


def test_find_unknown_merchants():
    """Print a list of merchants not matched to accounts"""
    print()
    accounts = acc.AccountFile(YAML_TESTFILE)
    raw_data = json.load(open('test_data/up_transactions.json'))

    unknowns = set()
    for item in raw_data['data']:
        description = f"{item['attributes']['description']} \"{item['attributes']['rawText']}\""
        account = accounts.match(description)
        if account is None:
            unknowns.add(description)
        else:
            print(f"Known: {description} -> {account}")

    for description in unknowns:
        print(f"Unknown: {description}")

    # TODO: sort unknowns by frequency.
    #     # print them in order of most to least frequently occuring
    #     for records in sorted(unknowns.values(), key=lambda x: len(x), reverse=True):
    #         for record in records:
    #             print(record)


foo = """
2020-01-02 * "Increase 50 Per Month  Internet Withdrawal 01Jan 06:03"
    Assets:Bank:Joint-CompleteFreedom
    Assets:Bank:IncentiveSaver                          50.00 AUD

2020-01-02 * "Hoyts Corp Pty Ltd Modbury Visa Purchase 30Dec"       #adelaide2019
    Assets:Bank:Joint-CompleteFreedom
    Expenses:Holiday:Activities                         38.00 AUD
"""

