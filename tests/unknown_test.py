"""
 Looks like I was in the middle of converting accounts.py to a cli.

 I think I want to load the test file (unknown.beancount) and
  a) pass through the file noting beans for their details: description, value -> account
  b) pass for all the unknowns
         ask the user what to do:
            * use the suggestion, or
            * leave it alone

All in order  to run `accounts unknowns master.beancount`, or something like that, for
a dialog that works through the unknowns.
"""
import sys
import pprint
from beancount import loader

beanfile = open('tests/test_data/unknown.beancount')


def test_this():
    for line in beanfile.readlines():
        sys.stdout.write(line)


def test_that():
    entries, errors, options_map = loader.load_file('tests/test_data/unknown.beancount')
    for entry in entries:
        pprint.pp(str(entry))
