'''
A `Timeline` represents a financial future, with a series of `AccountState` objects
for each account, on a monthly basis.
'''

from collections.abc import Iterable, Callable, Generator
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING, ClassVar, NoReturn, Optional
from weakref import WeakKeyDictionary

from pplt.account import Account, AccountState
from pplt.dates import days_per_month, parse_month
if TYPE_CHECKING:
    import pplt.schedule as sch

type TimelineAccountState = Generator[AccountState, None, NoReturn]
'''
A generator of `AccountState` objects, representing the state of an account.
The generator accepts updates to the account, and yields the updated state.
'''

type TimelineAccountStates = dict[str, TimelineAccountState]
'''
The state of the accounts in the timeline.

The keys are the account names, and the values are generators of `AccountState`.
The generators accept send() calls with updates to the accounts, while next()
returns the updated state.
'''

type CurrentAccountStates = dict[str, AccountState]
'''
The current state of the accounts in the timeline.
'''

@dataclass
class TimelineStep:
    '''
    A step in the timeline, with the date, account iterators, current schedule,
    and the values of the accounts.
    '''
    date: date
    schedule: 'sch.Schedule'
    accounts: TimelineAccountStates
    values: CurrentAccountStates

class TimelineSeries(Generator[TimelineStep, None, NoReturn]):
    '''
    A series of `TimelineStep` objects, representing the values of the accounts.

    This is a generator of `TimelineStep` objects, with the date, account values.

    The generator itself has a `timeline` attribute, which is the metadata for the
    entire timeline.
    '''
    timeline: 'Timeline'

type TimelineUpdateHandler = Callable[[TimelineStep], None]
'''
A function that updates the accounts in the timeline. These are pulled from the
schedule once per month. They may re-add themselves if they are recurring.

They are responsible for updating the accounts in the timeline, and may also
modify the schedule.
'''

if TYPE_CHECKING:
    import pplt.schedule as sch

@dataclass
class Timeline:
    '''
    Metadata for a `TimelineSeries`. The `TimelineSeries` itself is an
    `Iterator` of dictionaries, where each dictionary has a `'TIME'` key
    for the date, a 'SCHEDULE' key for scheduled events, and a
    `'TIMELINE'` key for this metadata, and other keys for
    iterators producing the values of the accounts as `AccountState` objects.

    The `Timeline` is constant over the entire timeline.

    As there is no end to a timeline, the end date is not stored.
    '''
    schedule: 'sch.Schedule'
    '''
    The schedule of events that affect the accounts.
    '''

    start: date
    '''
    The starting date of the timeline.
    '''

    accounts: dict[str, Account]
    '''
    The accounts in the timeline. The keys are the account names, and the values
    are the `Account` objects describing the accounts, including their initial
    values.
    '''

    _series: ClassVar[WeakKeyDictionary[TimelineSeries, 'Timeline']] = \
        WeakKeyDictionary()

    def __iter__(self) -> TimelineSeries:
        def TimelineSeries_():
            '''
            Iterate over the values of the timeline.
            '''
            date_ = self.start
            # Start the account iterators.
            accounts: TimelineAccountStates = {
                k: iter(v)
                for k, v in self.accounts.items()
            }
            # Start with the initial schedule, which will be modified by the events.
            schedule = self.schedule.copy()
            while True:
                states =  {k: next(v) for k, v in accounts.items()}
                step = TimelineStep(date_, schedule, accounts, states)
                yield step
                date_ = date_ + timedelta(days=days_per_month(date_))
                # Note that we don't update the account states after each event.
                # Updating the states would introduce order-dependence, and also
                # deviate from how the real world usually works, with a reconciliation
                # step, usually daily rather than monthly, applying all the updates
                # at once.
                for step_date, event in self.schedule.run(date_):
                    assert step_date <= date_
                    assert step_date >= step_date
                    if step_date > step.date:
                        step = TimelineStep(step_date, schedule, accounts, states)
                    event(step)
        # Make it a bit easier to recognize series generator.
        # We can't override the __class__ or add attributes.
        TimelineSeries_.__name__ = 'TimelineSeries'
        TimelineSeries_.__qualname__ = 'TimelineSeries'
        it = TimelineSeries_()
        # Since we can't add attributes, we use a weak reference to the metadata.
        # This allows it to be GC'd when the series is no longer referenced, but
        # still allows the timeline to be accessed from the series to allow restarts.
        Timeline._series[it] = self
        return it


def timeline(schedule: Optional['sch.Schedule']=None,
             start: Optional[date|str]=None, /,
             **kwargs: Iterable[float]) -> Timeline:
    """
    Create a timeline of values. Iterating over it produces a
    `TimelineSeries`.

    The `TimelineSeries` is an iterator of `TimelineStep` objects,
    each with the date, account values, and current schedule.

    PARAMETERS
    ----------

    start: `Optional[date|str]`
        Starting date. Defaults to the start of the next month.
    **kwargs: `Iterable[Account|float]`
        Accounts, or their initial values for quick tests.

    RETURNS
    -------
    timeline: `TimelineSeries`
        A monthly series of account values encapsulated in a `TimelineStep`.
    """
    if schedule is None:
        from pplt.schedule import Schedule
        schedule = Schedule()
    start = parse_month(start)
    accounts: dict[str, Account] = {
        k: v if isinstance(v, Account) else Account(k, v)
        for k, v in kwargs.items()
    }
    return Timeline(schedule, start, accounts=accounts)


def restart(series: TimelineSeries) -> TimelineSeries:
    '''
    Restart a timeline series. This is the same as calling `iter()` on
    on the original `Timeline`, but avoids the need to find and keep
    a reference, which can be a pain interactively.

    PARAMETERS
    ----------
    series: TimelineSeries
        A series of values.

    RETURNS
    -------
    series: TimelineSeries
        A series of values, with the date reset to the start.
    '''
    return iter(Timeline._series[series])