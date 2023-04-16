# Ledger Tools

Import tools for using the accounting package [Beancount](https://github.com/beancount/beancount/) (a variant of [Ledger](https://www.ledger-cli.org/)).

  * Import CSV files from [St George Bank](https://www.stgeorge.com.au)
  * Download transactions using the [Up Bank](https://up.com.au/) API
  * Match the descriptions of each transaction to an account
  * Generate ledger entries

## Usages

- Create/activate venv
- add UP API token to env using `export UP_TOKEN=${token}`
- Run like `python upbank [OPTIONS] COMMAND [ARGS]`

### UpBank  

```
$ upbank
Usage: upbank [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  balance     Fetch the current balance of the account.
  brewfiona   Generate beans from fionas upbank transaction file.
  categories  Get a list of transaction categories.
  month       Download a sequence of transactions.
  ping        Send a ping to Upbank, to verify your token and their API...
  gettxns     Download all transactions for date range
```

### Resolving unknown transactions  

```
$ accounts
Usage: accounts [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  unknowns  Resolve the unknown transactions.
```

To import St George  
To generate the ledger file  


## TODO

* what does what, right now?
* TUI for entering/choosing/confirming the account for unknown transactions
* fuzzy matcher, based on previous transactions, for predicting unknown transactions
* How to inject, then tweak, more complex (ie income) transactions from history?
* Work out a way to handle the token. Specify an env var? How?
