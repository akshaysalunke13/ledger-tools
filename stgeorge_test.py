import unittest

import stgeorge

CSV_TESTFILE = '/home/john/Downloads/trans020720.csv'


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
