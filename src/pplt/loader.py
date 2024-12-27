'''
Load data from YAML files.
'''

from pathlib import Path
from collections.abc import Iterator
from typing import Any

import yaml

from pplt.account import Account
from pplt.currency import CURRENCIES
from pplt.schedule import TimelineUpdateHandler
from pplt.events import interest
from pplt.dates import next_month, parse_month

def load_data(path: Path) -> list[Account|TimelineUpdateHandler]:
    now = next_month()
    with path.open() as f:
        entries: Iterator[dict[str, Any]] = yaml.safe_load_all(f)
        def load_item(entry: dict[str, Any]):
            name = entry['name']
            match entry['type']:
                case 'account':
                    balance = entry['balance']
                    status = entry.get('status', 'open')
                    currency = CURRENCIES[entry.get('currency', 'USD')]
                    account = Account(name, balance, status, currency)
                    print(f"{account=}")
                    return account
                case 'interest':
                    account_name = entry['account']
                    rate: float = entry['rate']
                    period = entry['period']
                    start = parse_month(entry.get('start', now))
                    i = interest(account_name, start, rate=rate, period=period)
                    period = entry['period']
                    print(f'interest={i}, period={i.period}') # type: ignore
                    return i
                case _:
                    raise ValueError(f"Unsupported entry type: {entry['type']}")
        return [load_item(entry) for entry in entries]

if __name__ == '__main__':
    load_data(Path(__file__).parent / 'data.yml')