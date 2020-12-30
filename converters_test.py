import sys
from unittest import TestCase
from stgeorge import to_beancount
from stgeorge import StGeorgeFile
from accounts import AccountFile

YAML_TESTFILE = '../john-fiona/accounts.yaml'

CSV_TESTFILE = '/home/john/Downloads/trans020720.csv'

BANK_ACCOUNT = 'Assets:Bank:Joint-CompleteFreedom'
# BANK_ACCOUNT = 'Assets:Bank:John-Freedom'
# BANK_ACCOUNT = 'Assets:Bank:IncentiveSaver'


class TestMerchantsMerge(TestCase):
    """Combine the two files; the transactions and the list of accounts."""

    def test_find_unknown_merchants(self):
        """print out of merchants not matched to accounts"""
        accounts = AccountFile(YAML_TESTFILE)
        with StGeorgeFile(CSV_TESTFILE) as transactions:
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
        for record in to_beancount(CSV_TESTFILE, YAML_TESTFILE, BANK_ACCOUNT):
            sys.stdout.write(record)
            fh.write(record)
        fh.close()
