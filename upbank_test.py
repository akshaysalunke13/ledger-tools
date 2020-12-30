import json
import pprint
import unittest.mock

import upbank


# TODO: Convert their transactions to my transactions.
# TODO: Map their categories to my categories.

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
    mock_get.return_value = json.load(open('up_categories.json'))
    data = upbank.categories()
    categories = {c['id']:c for c in data}
    top_level = [c for c in data if c['relationships']['parent']['data'] is None]
    for category in top_level:
        for child in category['relationships']['children']['data']:
            pprint.pp(f"{category['id']} -> {child['id']} {categories[child['id']]['relationships']['children']['data']}")


def test_transaction_data():
    """Play with transaction data."""
    raw_data = json.load(open('up_transactions.json'))
    data = raw_data['data']
    for item in data:
        description = f"{item['attributes']['description']} \"{item['attributes']['rawText']}\""
        value = item['attributes']['amount']['value']
        category = None
        if (data := item['relationships']['category']['data']) is not None:
            category = data['id']
        # parent_category = None
        # if (data := item['relationships']['parentCategory']['data']) is not None:
        #     parent_category = data['id']
        print(f"{description} {value} {category}")
