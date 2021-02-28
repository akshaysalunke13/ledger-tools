import sys
import unittest

import accounts as acc
import stgeorge

CSV_TESTFILE = '/home/john/projects/money/john-fiona/raw/stgeorge/2021-02-11-jointfreedom.csv'
YAML_TESTFILE = '../john-fiona/accounts.yaml'

BANK_ACCOUNT = 'Assets:Bank:Joint-CompleteFreedom'


class TestStGeorgeFile(unittest.TestCase):
    """Read a stgeorge csv of transactions."""

    def test_cleaner(self):
        """Read the CSV file."""
        with stgeorge.StGeorgeFile(CSV_TESTFILE) as thefile:
            for transaction in thefile:
                print(transaction)

    def test_list_merchants(self):
        """List of unique merchants in the CSV file."""
        vendors = set()
        with stgeorge.StGeorgeFile(CSV_TESTFILE) as thefile:
            for record in thefile:
                vendors.add(record[1])

        for vendor in sorted(vendors):
            print("%s" % vendor)


class TestMerchantsMerge(unittest.TestCase):
    """Combine the two files; the transactions and the list of accounts."""

    def test_find_unknown_merchants(self):
        """print out of merchants not matched to accounts"""
        accounts = acc.AccountFile(YAML_TESTFILE)
        with stgeorge.StGeorgeFile(CSV_TESTFILE) as transactions:
            # collect identical unknowns together
            unknowns = {}
            for record in sorted(transactions, key=lambda x: x[1]):
                merchant = record[1]
                if not accounts.match(merchant):
                    if merchant not in unknowns:
                        unknowns[merchant] = []
                    unknowns[merchant].append(record)

            # print them in order of most to least frequently occuring
            for records in sorted(unknowns.values(), key=lambda x: len(x), reverse=True):
                for record in records:
                    print(record)

    def test_convert(self):
        """Convert the transactions and accounts into beancount."""
        fh = open("generated.beancount", "w")
        for record in stgeorge.to_beancount(CSV_TESTFILE, YAML_TESTFILE, BANK_ACCOUNT):
            sys.stdout.write(record)
            fh.write(record)
        fh.close()
