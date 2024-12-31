'''
Load data from YAML files.
'''

from datetime import date
from pathlib import Path
from typing import NotRequired, Protocol, TypedDict, cast

import yaml

from pplt.account import Account, AccountValue, valid_account_status
from pplt.currency import get_currency
from pplt.interest_utils import apr
from pplt.schedule import Schedule, UpdateHandler
from pplt.events import interest
from pplt.dates import next_month, parse_month, Month
from pplt.period import Period, PeriodUnit, Periodic, valid_period_unit
from pplt.timeline_series import timeline, Timeline
from pplt.transaction import transfer

class LoaderEntry(TypedDict):
    '''
    A loader entry. That is, a YAML document in a loader file.

    Note that YAML files can contain multiple documents.
    '''
    uid: NotRequired[str]
    '''
    A unique identifier for the entry. This will be used to identify entries
    that may be overridden by scenarios that include the loader file.
    '''
    type: str
    '''
    The type of entry. This will determine how the entry is loaded.
    It must be the name of a loader function in the `LOADERS` dictionary.
    '''

type Loadable = Account|UpdateHandler
'''
A type alias for the types that can be loaded by a loader.
'''


class Loader[E: LoaderEntry, T: Loadable](Protocol):
    def __call__(self, entry: E) -> T:
        ...

LOADERS: dict[str, Loader[LoaderEntry, Loadable]] = {}


def add_loader[E: LoaderEntry](type_: str, loader: Loader[E, Account]|Loader[E, UpdateHandler]):
    '''
    Add a loader to the `LOADERS` dictionary.
    '''
    LOADERS[type_] = cast(Loader[LoaderEntry, Loadable], loader)

class LoaderValue(TypedDict):
    '''
    This corresponds to the `AccountValue` type.
    '''
    balance: float
    status: NotRequired[str]
    currency: NotRequired[str]

def load_value(entry: LoaderValue) -> AccountValue:
    '''
    Load an `AccountValue` object from a loader entry.
    '''
    status = valid_account_status(entry.get('status', 'open'))
    currency = get_currency(entry.get('currency', 'USD'))
    return AccountValue(entry['balance'], status, currency)

class LoaderPeriod(TypedDict):
    n: int
    unit: PeriodUnit

class LoaderPeriodic(LoaderPeriod):
    start: Month

def load_period(entry: LoaderPeriod) -> Period:
    unit =  entry['unit']
    return Period(unit, entry['n'])

def load_periodic(entry: LoaderPeriod) -> Periodic:
    start = entry.get('start', None)
    start_ = next_month() if start is None else parse_month(start)
    return Periodic(start_, entry['n'], entry['unit'])

class LoaderRate(TypedDict):
    percent: float
    period: NotRequired[PeriodUnit]

def load_rate(entry: LoaderRate) -> float:
    percent = entry['percent']
    period = valid_period_unit(entry.get('period', 'year'))
    return apr(percent / 100.0, period)

class LoaderAccount(LoaderEntry, LoaderValue):
    name: str

def load_account(entry: LoaderAccount) -> Account:
    value = load_value(entry)
    return Account(entry['name'], value)

add_loader('account', load_account)

class LoaderStart(TypedDict):
    start: NotRequired[Month]

def load_start(entry: LoaderStart) -> date:
    start = entry.get('start', None)
    return next_month() if start is None else parse_month(start)

class LoaderInterest(LoaderEntry):
    account: str
    rate: LoaderRate
    start: NotRequired[Month]


def load_interest(entry: LoaderInterest) -> UpdateHandler:
    rate = load_rate(entry['rate'])
    start = load_start(entry)
    return interest(entry['account'], start, rate=rate*100)

add_loader('interest', load_interest)

LoaderFrom = TypedDict('LoaderFrom', {'from': str})
'''
A type alias for entries that have a `from` field,
since this can't be a field name in a TypedDict.
'''

class TransferLoader(LoaderEntry, LoaderFrom, LoaderStart):
    to: str
    amount: LoaderValue
    period: LoaderPeriod

def load_transfer(entry: TransferLoader) -> UpdateHandler:
    '''
    Load a transfer from a loader entry.
    '''
    start = load_start(entry)
    amount = load_value(entry['amount'])
    period = load_period(entry['period'])
    return transfer(entry['from'], entry['to'], start, amount=amount, period=period)

def load_scenario(path: Path|str) -> Timeline:
    '''
    Load a scenario from a YAML file.
    '''
    path = Path(path)
    with path.open() as f:
        entries = cast(list[LoaderEntry], yaml.safe_load_all(f))
        def load_item(entry: LoaderEntry):
            type_ = entry['type']
            loader = LOADERS.get(type_)
            if loader is None:
                raise ValueError(f'Unknown loader type: {type_}')
            return loader(entry)
        items = [load_item(entry) for entry in entries]
        accounts = {item.name: item for item in items if isinstance(item, Account)}
        schedule = Schedule([item for item in items if isinstance(item, UpdateHandler)])
        return timeline(schedule, **accounts)


if __name__ == '__main__':
    load_scenario(Path(__file__).parent / 'data.yml')