import click
import json
import yaml
from yaml import SafeLoader
import re


class AccountFile:
    """A yaml file which matches merchant regexes with account names.
    """
    def __init__(self, filename):
        """param filename: a yaml formatted file of mappings from accounts to merchants"""
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
        if description is not None:
            for pattern in self.merchant_accounts.keys():
                if re.match(pattern, description, re.IGNORECASE):
                    return self.merchant_accounts[pattern]
        return None


def find_unknown_merchants(rawfile, accountfile):
    """From the download, list the most unknown transactions.

    * load the download file and the accounts yaml
    * list the transactions without an account in frequency order.
    """
    print()
    accounts = AccountFile(accountfile)
    raw_data = json.load(open(rawfile))

    unknowns, knowns = dict(), set()
    for item in raw_data:
        raw_text = item['attributes']['rawText']
        description = item['attributes']['description']
        full_description = f"{item['attributes']['description']} \"{item['attributes']['rawText']}\""
        account = accounts.match(description) or accounts.match(raw_text)
        if account is None:
            unknowns.setdefault(full_description, list()).append(item)
        else:
            knowns.add("%-50s -> %s" % (full_description, account))

    unknowns_list = sorted(unknowns.keys(), key=lambda key: len(unknowns[key]), reverse=True)
    for description in unknowns_list:
        values = [trans['attributes']['amount']['value'] for trans in unknowns[description]]
        values_str = ", ".join(values)
        print(f"{len(unknowns[description])} {description} -> {values_str}")

    print()
    for known in sorted(knowns):
        print(known)


@click.group()
def cli():
    pass


unknown_str = '    ACCOUNT_UNKNOWN'


@cli.command()
@click.argument("beanfile", type=click.Path(exists=True))
def unknowns(beanfile):
    """Resolve the unknown transactions.
    """
    # Find the unknown transactions
    lines = open(beanfile)
    buffer = []
    for line in lines:
        line = line.strip('\n')
        if line != '':
            buffer.append(line)
        else:
            if len(buffer) > 1 and re.search(unknown_str, buffer[2]):
                click.echo('\n'.join(buffer))
                description = re.search('\".*\"', buffer[0])
                bracketed_description = re.search("\[.*\]", description.group())
                click.echo(description.group())
                click.echo(bracketed_description.group())
            click.echo('\n')
            buffer.clear()

# ok now I got the description
# i need to match that with something in a file of matchables?
#                                     or a beancount file, and copy that account name over.


if __name__ == "__main__":
    cli()


# account_file = AccountFile(ACCOUNTS_YAML)
#
# def is_known(description: str) -> str:
#     """True if the description maps to an Account.
#
#     Args:
#         description: a merchant name or transaction description.
#
#     Returns:
#         The account string that matched.
#     """
#     return account_file.match(description)
#
#
# def unknowns(descriptions: list) -> list:
#     """Returns a sublist with the descriptions which are unknown.
#
#     Args:
#         descriptions: list of str: transaction descriptions.
#
#     Returns:
#         List of unique descriptions which do not match to an account.
#         Sorted by most common occurences to least.
#     """
#     unknowns = [d for d in descriptions if not is_known(d)]
#     sorted(unknowns, key=lambda x: [unknowns.count(x), x])  # Frequency sort.
#     return list(dict.fromkeys(unknowns))                    # Remove duplicates.
