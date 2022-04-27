import csv
import datetime
import re

from . import accounts


class StGeorgeFile:
    """
    Working with the csv output from St George Bank.
    """
    # number of chars in the first column
    FIRST_COL = 30
    SECOND_COL = 35

    # time is in this format '00:00 '
    TIME_REGEX = r'\d\d:\d\d\s\S'

    # the descriptions that need work
    DESCRIPTION_TYPES = [
        "Eftpos Purchase",
        "Visa Purchase",
        "Visa Purchase O/Seas",
        "Visa Cash Advance",
        "Visa Credit",
        "Internet Withdrawal",
        "Atm Withdrawal",
        "Atm Withdrawal -Wbc",
        "Tfr Wdl BPAY Internet",
        "Eftpos Refund",
        "Eftpos Debit",
        "Osko Withdrawal",
    ]

    def __init__(self, filename):
        self.filename = filename
        self.fileobj = None

    def __enter__(self):
        """open the file and read the headers"""
        self.fileobj = open(self.filename, 'r')
        # sniff for the type of file
        temp_lines = self.fileobj.readline() + '\n' + self.fileobj.readline()
        self.dialect = csv.Sniffer().sniff(temp_lines, delimiters=',')
        self.fileobj.seek(0)
        # sniff for the header and discard it
        self.has_header = csv.Sniffer().has_header(temp_lines)
        if self.has_header:
            self.fileobj.readline()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fileobj.close()

    def __iter__(self):
        lines = [l for l in csv.reader(self.fileobj, self.dialect)]
        for row in reversed(lines):
            # skip blank rows
            if not len(row):
                continue
            yield self._parsed(row)

    def _parsed(self, row):
        """Break down the description to it's stg components and stick them and the end.
        @param row: a list of csv fields
        """
        date, description, credit, debit, balance, *categories = row

        transaction_type = description[:30]

        # leave direct transactions alone
        if transaction_type.strip() not in self.DESCRIPTION_TYPES:
            return row + [''] * 4

        effective_date = description[30:35]

        time_candidate = description[35:]
        if not re.match(self.TIME_REGEX, time_candidate):
            # no time
            effective_time = ''
            merchant = description[36:56].strip()
            location = description[57:]
        else:
            # has time
            effective_time = description[35:40]
            merchant = " ".join(description[41:].split())
            location = ''

        return [
            date,
            merchant,
            credit,
            debit,
            balance,
            transaction_type.strip(),
            effective_date,
            effective_time,
            location
        ]


def balance_entry(effective_date_str, bank_account, balance):
    return "%s balance %s      %s AUD\n\n" % (effective_date_str, bank_account, balance)


def to_beancount(csv_file, yaml_file, bank_account):
    """Generate beancount records from the the csv and yaml files.

    :param csv_file: <string> the filename of the csv transaction data.
    :param yaml_file: <string> the filename of the yaml account->merchant mappings.
    :param bank_account: <string> the bank account which the transactions apply to.
    :returns: <string> beancount formatted transaction records.
    """
    merchant_accounts = accounts.AccountFile(yaml_file)
    this_month, last_balance = None, None
    with StGeorgeFile(csv_file) as transactions:
        for (str_date, merchant, debit, credit, balance, transaction, act_date, act_time, location,
             *other) in transactions:
            # Parse for the effective date
            effective_date = datetime.datetime.strptime(str_date, "%d/%m/%Y")
            effective_date_str = effective_date.strftime('%Y-%m-%d')

            # Balance every month
            if this_month != effective_date.month:
                this_month = effective_date.month
                yield balance_entry(effective_date_str, bank_account, last_balance)
            last_balance = balance

            description = ("%s %s %s %s %s" % (merchant, location, transaction, act_date, act_time)).strip()
            result = "%s * \"%s\"\n" % (effective_date_str, description)
            account = merchant_accounts.match(merchant) or "Expenses:TODO"
            if len(debit):
                result += "    %s\n" % bank_account
                result += "    %-46s %10.2f AUD\n" % (account, float(debit))
            else:
                result += "    %-46s %10.2f AUD\n" % (bank_account, float(credit))
                result += "    %s\n" % account
            yield result + "\n"
        else:
            yield balance_entry(effective_date_str, bank_account, balance)
