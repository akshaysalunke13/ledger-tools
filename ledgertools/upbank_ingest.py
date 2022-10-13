import json

from datetime import date

import beancount
from beancount.core import data
from beancount.core import flags
from beancount.core import (account, amount, number)
from beancount.ingest import importer

# Upbank only operates in AUD, afaik.
CURRENCY = "AUD"


class UpbankImporter(importer.ImporterProtocol):
    """Interface that all source importers need to comply with.
    """

    # A flag to use on new transaction. Override this flag in derived classes if
    # you prefer to create your imported transactions with a different flag.
    FLAG = beancount.core.flags.FLAG_OKAY

    def __init__(self, account_name="Assets:Bank:Upbank", tags="#fiona"):
        """

        Args:
            account_name: beancount account name for the upbank account.
                eg:  "Assets:Bank:Upbank"
        """
        self.account_name = account_name
        self.tags = tags

    def name(self):
        """Return a unique id/name for this importer.

        Returns:
          A string which uniquely identifies this importer.
        """
        return "Upbank"

    __str__ = name

    def identify(self, file):
        """Return true if this importer matches the given file.

        Args:
          file: A cache.FileMemo instance.
        Returns:
          A boolean, true if this importer can handle this file.
        """
        # TODO: open file and import json and ensure it has the critical features.
        return True

    def extract(self, file, existing_entries=None):
        """Extract transactions from a file.

        Args:
          file: A cache.FileMemo instance.
          existing_entries: An optional list of existing directives loaded from
            the ledger which is intended to contain the extracted entries. This
            is only provided if the user provides them via a flag in the
            extractor program.
        Returns:
          A list of new, imported directives (usually mostly Transactions)
          extracted from the file.
        """
        # Open the file as json
        transactions = json.loads(file.contents())
        entries = []

        for trans in reversed(transactions):
            trans_id = trans['id']   # Could be used to flag "__duplicate__"s.
            date_ = date.fromisoformat(trans['attributes']['createdAt'][:10])
            raw_text = trans['attributes']['rawText']
            narration = trans['attributes']['description']
            value = amount.Amount(
                beancount.core.number.D(trans['attributes']['amount']['value']),
                CURRENCY
            )
            posting = data.Posting(self.account_name, value, None, None, None, None)
            txn = data.Transaction(
                meta=data.new_metadata(file.name, trans_id),
                date=date_,
                flag=beancount.core.flags.FLAG_OKAY,
                payee=raw_text,
                tags=data.EMPTY_SET,
                links=data.EMPTY_SET,
                narration=narration,
                postings=[posting],
            )
            entries.append(txn)

        # TODO: insert balance line.
        return entries

        #     try:
        #         category = ':'.join([
        #             trans['relationships']['parentCategory']['data']['id'],
        #             trans['relationships']['category']['data']['id'],
        #         ])
        #     except TypeError:
        #         category = ''
        #     txt_description = f"\"{raw_text} [{description}]\""
        #     entry = f'{date_str} * {txt_description:66s}  {tags}\n'
        #     entry += f"    {accountname}\n"
        #     entry += "    %-46s %10.2f AUD\n" % (
        #         f'ACCOUNT_UNKNOWN [{category}]', float(value))
        #
        #     click.echo(entry)
        #     change += float(value)
        # balance = balance - change
        # balance_str = f"{date_str} balance {accountname:36s} {balance:.2f} AUD"
        # click.echo(balance_str)

    def file_account(self, file):
        """Return an account associated with the given file.

        Note: If you don't implement this method you won't be able to move the
        files into its preservation hierarchy; the bean-file command won't
        work.

        Also, normally the returned account is not a function of the input
        file--just of the importer--but it is provided anyhow.

        Args:
          file: A cache.FileMemo instance.
        Returns:
          The name of the account that corresponds to this importer.
        """
        # TODO: it depends... might be john!?
        return self.account_name

    # def file_name(self, file):
    #     """A filter that optionally renames a file before filing.
    #
    #     This is used to make tidy filenames for filed/stored document files. If
    #     you don't implement this and return None, the same filename is used.
    #     Note that if you return a filename, a simple, RELATIVE filename must be
    #     returned, not an absolute filename.
    #
    #     Args:
    #       file: A cache.FileMemo instance.
    #     Returns:
    #       The tidied up, new filename to store it as.
    #     """
    #
    # def file_date(self, file):
    #     """Attempt to obtain a date that corresponds to the given file.
    #
    #     Args:
    #       file: A cache.FileMemo instance.
    #     Returns:
    #       A date object, if successful, or None if a date could not be extracted.
    #       (If no date is returned, the file creation time is used. This is the
    #       default.)
    #     """
    #     # Date of download is not captured inside the file.
    #     return None
