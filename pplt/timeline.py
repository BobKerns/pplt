'''
A `Timeline` represents a financial future, with a series of `AccountState` objects
for each account, on a monthly basis.
'''

from collections.abc import Iterable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import tee
from typing import Iterator, TYPE_CHECKING, Optional

from pplt.account import Account, AccountState, AccountStatus
from pplt.utils import days_per_month, dict_join, months, next_month, parse_month
if TYPE_CHECKING:
    import pplt.schedule as sch

type TimelineStep = dict[str, Iterator[float|datetime]|Timeline]
type TimelineSeries = Iterator[TimelineStep]

type AccountUpdate = AccountState|float|AccountStatus
type TimelineEventHandler = Callable[[datetime, Account, AccountState, TimelineStep],
                                     AccountUpdate]

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
    start: datetime
    accounts: dict[str, Account]

    def __iter__(self) -> TimelineSeries:
        def iterator():
            '''
            Iterate over the values of the timeline.
            '''
            date = self.start
            # Start the account iterators.
            accounts = {k: iter(v) for k, v in self.accounts.items()}
            schedule = self.schedule.copy()
            while True:
                yield {
                    'TIME': date,
                    'TIMELINE': self,
                    'SCHEDULE': schedule,
                    **{k: next(v) for k, v in accounts.items()}
                }
                date = date + timedelta(days=days_per_month(date))
                self.schedule.run(date)
        it = iterator()
        it.timeline = self
        return it


def timeline(schedule: Optional['sch.Schedule']=None,
             start: datetime=next_month(), /,
             **kwargs: Iterable[float]):
    """
    Create a timeline of values.

    The special entry `'METADATA'` holds metadata, including the original
    start of the timeline, allowing for restarts.

    PARAMETERS
    ----------

    start: Optional[datetime]
        Starting date.
    **kwargs: Iterable[float]
        A series of values to plot.

    RETURNS
    -------
    timeline: Iterator[dict[str, float]]
        A series of values, one for each key, plus:
        * `'TIME'`, the date of the values.
        * `'SCHEDULE'`, the active schedule of events.
        * `'TIMELINE'`, the metadata (the `Timeline` object).
    """
    if schedule is None:
        from pplt.schedule import Schedule
        schedule = Schedule()
    start = parse_month(start)
    accounts = {k: v if isinstance(v, Account) else Account(k, v)
                for k, v in kwargs.items()}
    return Timeline(schedule, start, accounts=accounts)

def restart(series: TimelineSeries) -> TimelineSeries:
    '''
    Restart a timeline series.

    PARAMETERS
    ----------
    series: TimelineSeries
        A series of values.

    RETURNS
    -------
    series: TimelineSeries
        A series of values, with the date reset to the start.
    '''
    return iter(series.timeline)