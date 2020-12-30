"""Up Bank API."""

import os
import requests

URL = 'https://api.up.com.au/api/v1'
TOKEN = os.environ['UPTOKEN']


def transactions():
    """Fetch a list of transactions."""
    return get("/transactions")


def accounts():
    """Fetch a list of accounts."""
    return get("/accounts")


def categories():
    """Fetch a list of categories."""
    return get("/categories")


def ping():
    """Verify the access token.

    Returns:
        requests.Response
    """
    return requests.get(f"{URL}/util/ping", headers=headers())


def get(path):
    """Send a GET request to Up.

    Args:
        path: includes the preceding slash.

    Returns:
        list of data; probably dicts.
    """
    url = f"{URL}{path}"
    response = requests.get(url, headers=headers())
    json = response.json()
    data = json['data']
    return data


def headers():
    return {'Authorization': f"Bearer {TOKEN}"}
