import yaml
from yaml import SafeLoader
import re


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

    def match(self, merchant):
        """Return the account matching the merchant pattern"""
        for pattern in self.merchant_accounts.keys():
            if re.fullmatch(pattern, merchant):
                return self.merchant_accounts[pattern]
        return None
