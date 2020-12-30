import unittest

from accounts import AccountFile


YAML_TESTFILE = '../john-fiona/accounts.yaml'


class TestAccountMerchants(unittest.TestCase):
    """Read the list of accounts."""

    def test_read_accounts(self):
        """Load the list of accounts."""
        accounts = AccountFile(YAML_TESTFILE)
        print(accounts.raw)

    def test_read_merchant_accounts(self):
        """Determine the merchants for each account."""
        accounts = AccountFile(YAML_TESTFILE)

        print("Accounts")
        for account, merchants in accounts.account_merchants.items():
            print(account, merchants)
        print()

        print("Merchants")
        for merchant, account in accounts.merchant_accounts.items():
            print(merchant, ' => ', account)

    def test_merchant_matcher(self):
        accounts = AccountFile(YAML_TESTFILE)
        print(accounts.match('Aldi 104'))
        self.assertEqual("Expenses:Food:Groceries", accounts.match('Aldi 104'))
        self.assertIsNone(accounts.match('ALDI 104'))   # ensure case sensitive
        self.assertEqual("Expenses:Food:Groceries", accounts.match('Coles 929023912 asdf Nsa'))
        self.assertEqual("Expenses:Household:Consumables", accounts.match('Bunnings 2019'))

    def test_accounts_list(self):
        """Spit out all the accounts"""
        accounts = AccountFile(YAML_TESTFILE)
        for account in sorted(accounts.account_merchants.keys()):
            print('2016-06-25 open %s' % account)
