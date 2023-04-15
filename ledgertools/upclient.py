#!/usr/bin/python

"""Up Bank API.

Use the Up Bank API to retrieve transactions.

That is really all I am interested in because I use my own pattern matching,
against the transaction description, to sort them into accounts (aka categories).
"""
import datetime
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
