'''
Load data from YAML files.

This module provides a way to load data from YAML files. The data is loaded
into a `Timeline` object, which can be used to simulate the data.

The module provides a way to load accounts, and updates such as interest and
transfers. The data is loaded from a YAML file, which can contain multiple
YAML documents (separated by `---`, as is standard with YAML).

Each type of entry in the YAML file is loaded by a loader function, which is
registered in the `LOADERS` dictionary. The loader functions are added to the
dictionary using the `add_loader` function.

The loader functions receive a dictionary that corresponds to the YAML document,
and return an object that can be used in the simulation. The type of the dictionary
for each loader is defined in a `TypedDict` subclass. This documents what fields
are required and optional for each loader, and enables type checkers to verify
that the loader functions are implemented correctly.

Some of the dictionaries have sub-dictionaries with their own `TypedDict` subclasses.
These are defined here and are reusable wherever that type needs to be used.

Some scalar values have type aliases defined for them, such as `Month` and `PeriodUnit`.
These are used in the `TypedDict` subclasses to ensure that the values are of the correct
type. The modules that define these types define `valid_xxx` functions that can be used
to validate the values, and convert if necessary. For example,
'''

from collections.abc import Iterable
from datetime import date
from itertools import count
from pathlib import Path
from typing import Literal, NotRequired, Protocol, TypedDict, cast
import sys
from inspect import signature

import yaml

from pplt.account import Account, AccountValue, valid_account_status
from pplt.currency import valid_currency
from pplt.interest_utils import apr
from pplt.schedule import Schedule, UpdateHandler
from pplt.events import interest
from pplt.dates import next_month, valid_month, Month
from pplt.period import Period, PeriodUnit, Periodic, valid_period_unit
from pplt.timeline_series import timeline, Timeline
from pplt.transaction import transfer

class LoaderEntry[T: str](TypedDict):
    '''
    A loader entry. That is, a YAML document in a loader file.

    Note that YAML files can contain multiple documents.
    '''
    id: NotRequired[str|int]
    '''
    A unique identifier for the entry. This will be used to identify entries
    that may be overridden by scenarios that include the loader file.
    '''
    type: T
    '''
    The type of entry. This will determine how the entry is loaded.
    It must be the name of a loader function in the `LOADERS` dictionary,
    or the special type `import`.
    '''
    categories: NotRequired[list[str]]

class LoaderImportEntry(LoaderEntry[Literal['import']]):
    '''
    A loader entry that imports another scenario.
    '''
    type: Literal['import']
    file: str

type Loadable = Account|UpdateHandler
'''
A type alias for the types that can be loaded by a loader.
'''


class Loader[T: str, L: Loadable](Protocol):
    '''
    A loader function for a specific type of entry and loadable object in
    the YAML files.
    '''
    def __call__(self, entry: LoaderEntry[T]) -> L:
        ...

LOADERS: dict[str, Loader[str, Loadable]] = {}


def add_loader[T: str, L: Loadable](type_name: T, loader: Loader[T, L]):
    '''
    Add a loader to the `LOADERS` dictionary.
    '''
    # Complains if we cast as unnecessary (as is proper) but complains if we don't cast.
    LOADERS[type_name] = loader # type: ignore


class LoaderValue_(TypedDict):
    '''
    This corresponds to the `AccountValue` type.
    '''
    amount: float
    status: NotRequired[str]
    currency: NotRequired[str]

type LoaderValue = LoaderValue_|float|int

def load_value(entry: LoaderValue|float|int) -> AccountValue:
    '''
    Load an `AccountValue` object from a loader entry.
    '''
    match entry:
        case float()|int():
            return AccountValue(entry)
        case _:
            status = valid_account_status(entry.get('status', 'open'))
            currency = valid_currency(entry.get('currency', 'USD'))
            return AccountValue(entry['amount'], status, currency)

class LoaderPeriod(TypedDict):
    n: int
    unit: PeriodUnit

class LoaderPeriodic(LoaderPeriod):
    start: Month

def load_period(entry: LoaderPeriod|None) -> Period|None:
    if entry is None:
        # Not periodic.
        return None
    unit =  entry['unit']
    return Period(unit, entry['n'])

def load_periodic(entry: LoaderPeriod) -> Periodic:
    start = entry.get('start', None)
    start_ = next_month() if start is None else valid_month(start)
    return Periodic(start_, entry['n'], entry['unit'])

class LoaderRate(TypedDict):
    percent: float
    period: NotRequired[PeriodUnit]

def load_rate(entry: LoaderRate) -> float:
    '''
    Load a rate (as a percentage) from a loader entry.
    '''
    percent = entry['percent']
    period = valid_period_unit(entry.get('period', 'year'))
    return apr(percent / 100.0, period)

class LoaderAccount(LoaderEntry[Literal['account']], LoaderValue_):
    name: str

def categories[T: str](entry: LoaderEntry[T]) -> list[str]:
    return cast(list[str], entry.get('keys', None) or [])

def load_account(entry: LoaderAccount) -> Account:
    value = load_value(entry)
    cat = categories(entry)
    return Account(entry['name'],
                   value,
                   categories=cat)

# Fails to recognize the LoaderValue_ in the inheritance
add_loader('account', load_account) # type: ignore

class LoaderStart(TypedDict):
    start: NotRequired[Month]

def load_start(entry: LoaderStart) -> date:
    start = entry.get('start', None)
    return next_month() if start is None else valid_month(start)

class LoaderInterest(LoaderEntry[Literal['interest']]):
    '''
    A loader entry for interest. Interest is give as an annual percentage rate (APR)
    unless a period is specified.
    '''
    account: str
    rate: LoaderRate
    start: NotRequired[Month]


def load_interest(entry: LoaderInterest) -> UpdateHandler:
    rate = load_rate(entry['rate'])
    start = load_start(entry)
    return interest(entry['account'], start, rate=rate*100, keys=categories(entry))

add_loader('interest', load_interest) # type: ignore

LoaderFrom = TypedDict('LoaderFrom', {'from': str})
'''
A type alias for entries that have a `from` field,
since this can't be a field name in a TypedDict.
'''

class LoaderTransfer(LoaderEntry[Literal['transfer']], LoaderFrom, LoaderStart):
    to: str
    amount: LoaderValue
    period: LoaderPeriod
    from_min: NotRequired[LoaderValue]
    to_max: NotRequired[LoaderValue]

def load_transfer(entry: LoaderTransfer) -> UpdateHandler:
    '''
    Load a transfer from a loader entry.
    '''
    start = load_start(entry)
    amount = load_value(entry['amount'])
    period = load_period(entry.get('period', None))
    from_min = load_value(entry.get('from_min', 0))
    to_max = load_value(entry.get('to_max', 100000000000000.0))
    return transfer(entry['from'], entry['to'], start,
                    amount=amount,
                    period=period,
                    from_min=from_min,
                    to_max=to_max,
                    keys=categories(entry))

add_loader('transfer', load_transfer) # type: ignore

class LoaderImport(LoaderEntry[Literal['import']]):
    file: str

def genid():
    '''
    Generate a unique ID for an entry.
    '''
    _counter = count()
    return f'__{next(_counter)}'

def entry_id(entry: LoaderEntry[str]) -> str|int:
    '''
    Get the ID for an entry.
    '''
    return entry.get('id', None) or entry.get('name', None) or genid()

def valid_loader_entry(entry: LoaderEntry[str]|None) -> LoaderEntry[str]|None:
    '''
    Validate a loader entry. Validation is not complete: It does not check subfields, nor that
    the fields are the right type. but its should catch most typos.
    '''
    if entry is None:
        return None
    id_ = entry_id(entry)
    entry['id'] = id_
    type_ = entry['type']
    match type_:
        # Handle 'import' specially, as it is not a real loader type,
        # but a directive to import another file.
        case 'import':
            if 'file' not in entry:
                raise ValueError('Import entry must have a file field')
            return entry
        # Verify that it's a valid loader type
        case _:
            if not type_ in LOADERS:
                print(f'Unknown loader type: {type_}', file=sys.stderr)
                return None
    loader = LOADERS[type_]
    # Get the type of the first parameter of the loader function
    sig = signature(loader)
    p0_name = list(sig.parameters)[0]
    p0 = cast(type, sig.parameters[p0_name].annotation)
    # Check that the required keys are present
    for k in p0.__required_keys__: # type: ignore
        if k not in entry:
            print(f'Missing required key {k} for {type_}', file=sys.stderr)
            return None
    # Check that there are no unknown keys
    for k in entry:
        if k not in p0.__required_keys__ and k not in p0.__optional_keys__: # type: ignore
            print(f'Unknown key {k} for {type_}', file=sys.stderr)
            return None
    return entry

def load_scenario_yaml(path: Path|str) -> dict[str|int, LoaderEntry[str]]:
    '''
    Load the `LoaderEntry` objects from a YAML file, to be merged with
    imports of other scenarios.


    '''
    path = Path(path)
    with path.open() as f:
        by_id: dict[str|int, LoaderEntry[str]] = {}
        # Load the entries from the YAML file
        entries = cast(Iterable[LoaderEntry[str]], yaml.safe_load_all(f))

        entries = sorted((e for e in entries if e),
                         key=lambda entry: entry_id(entry))
        for entry in entries:
            match entry.get('type', None):
                case 'import':
                    entry_ = cast(LoaderImport, entry)
                    file = entry_['file']
                    imported = load_scenario_yaml(path.parent / file)
                    for id_, entry_ in imported.items():
                        if id_ in by_id:
                            # An import overriding an entry from a prior import
                            entry_.update(by_id[id_])
                        by_id[id_] = entry_
                case _:
                    pass
        for entry in entries:
            match entry.get('type', None):
                case 'import':
                    pass
                case _:
                    id_ = entry_id(entry)
                    if id_ in by_id:
                        # Overriding an imported entry
                        by_id[id_].update(entry)
                    else:
                        by_id[id_] = entry
        return by_id

def load_scenario(path: Path|str) -> Timeline:
    '''
    Load a scenario from a YAML file.
    '''
    by_id = load_scenario_yaml(path)
    def load_item(entry: LoaderEntry[str]):
        type_ = entry['type']
        loader = LOADERS.get(type_)
        if loader is None:
            raise ValueError(f'Unknown loader type: {type_}')
        return loader(entry)
    items = [
        load_item(entry)
        for entry in by_id.values()
        if entry['type'] != 'import'
    ]
    accounts = {
        item.name: item
        for item in items
        if isinstance(item, Account)
    }
    handlers = [
        item
        for item in items
        if isinstance(item, UpdateHandler)
    ]
    schedule = Schedule(handlers)
    return timeline(schedule, **accounts)


if __name__ == '__main__':
    load_scenario(Path(__file__).parent / 'data.yml')
