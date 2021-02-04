"""Up Bank API.

Use the Up Bank API to retrieve transactions.

That is really all I am interested in because I use my own pattern matching,
against the transaction description, to sort them into accounts (aka categories).
"""
import datetime
import os
import requests


URL = 'https://api.up.com.au/api/v1'
TOKEN = os.environ['UPTOKEN']

# Maximum number of transactions upbank return per 'page'.
PAGE_SIZE = 10

# Constants
HELD = "HELD"
SETTLED = "SETTLED"


class LocalTZ(datetime.tzinfo):
    """Your time zone with an arbitrary, constant offset."""
    def utcoffset(self, dt):
        return datetime.timedelta(hours=+11, minutes=0)


def transactions(since: datetime.datetime,
                 until: datetime.date = None,
                 status: str = None) -> list:
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
    params.update({'page[size]': PAGE_SIZE})
    params.update({'filter[since]': since})
    if until is not None:
        params.update({'filter[until]': until})
    if status is not None:
        params.update({'filter[status]': status})
    response = get("/transactions", params=params)
    return response


def get(path, params: dict) -> list:
    """Send a GET request to Up.

    Args:
        path: includes the preceding slash.
        params: request parameters.

    Returns:
        list of data; probably dicts.
    """
    result = []
    next = f"{URL}{path}"
    while next is not None:
        response = requests.get(next, headers=_headers(), params=params)
        data = response.json()
        result.extend(data['data'])
        next = data['links']['next']
    return result


def ping():
    """Verify the access token is working.

    Returns:
        requests.Response
    """
    return requests.get(f"{URL}/util/ping", headers=_headers())


def accounts():
    """Fetch a list of accounts."""
    return get("/accounts")


def categories():
    """Fetch a list of categories."""
    return get("/categories")


def _headers():
    return {'Authorization': f"Bearer {TOKEN}"}
