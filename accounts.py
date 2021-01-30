import yaml
from yaml import SafeLoader
import re

# YAML file which maps descriptions into accounts.
ACCOUNTS_YAML = '../john-fiona/accounts.yaml'


class AccountFile:
    """A yaml file mapping accounts to merchant regexes."""

    def __init__(self, filename):
        """:param yaml_file: a yaml formatted file of mappings from accounts to merchants"""
        self.filename = filename
        with open(filename, 'r') as fh:
            self.raw = yaml.load(fh, SafeLoader)

        # a dictionary of merchant patterns
        self.merchant_accounts = self._merchant_accounts()

    @staticmethod
    def _walk(names, merchants):
        if isinstance(merchants, list):
            yield ":".join(names), merchants
        elif isinstance(merchants, dict):
            for key, value in merchants.items():
                for account in AccountFile._walk(names + [key], value):
                    yield account

    @property
    def account_merchants(self):
        # return a dictionary of accounts
        result = dict()
        for account, merchants in AccountFile._walk([], self.raw):
            result[account] = merchants
        return result

    def _merchant_accounts(self):
        # return a dictionary of merchants
        result = dict()
        for account, merchants in AccountFile._walk([], self.raw):
            for merchant in merchants:
                result[str(merchant)] = account
        return result

    def match(self, description):
        """Return the account matching the description"""
        for pattern in self.merchant_accounts.keys():
            if re.match(pattern, description, re.IGNORECASE):
                return self.merchant_accounts[pattern]
        return None


account_file = AccountFile(ACCOUNTS_YAML)


def is_known(description: str) -> str:
    """True if the description maps to an Account.

    Args:
        description: a merchant name or transaction description.

    Returns:
        The account string that matched.
    """
    return account_file.match(description)


def unknowns(descriptions: list) -> list:
    """Returns a sublist with the descriptions which are unknown.

    Args:
        descriptions: list of str: transaction descriptions.

    Returns:
        List of unique descriptions which do not match to an account.
        Sorted by most common occurences to least.
    """
    unknowns = [d for d in descriptions if not is_known(d)]
    sorted(unknowns, key=lambda x: [unknowns.count(x), x])  # Frequency sort.
    return list(dict.fromkeys(unknowns))                    # Remove duplicates.
