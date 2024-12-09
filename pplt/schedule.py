'''
Schedule module for the pplt package.

This maintains a schedule of events and transactions, one-time and recurring,
that affect the accounts.
'''

from collections.abc import Iterable
from datetime import date
from heapq import heappop, heappush, heapify
from typing import Callable, Optional, TYPE_CHECKING

from pplt.account import AccountState
from pplt.timeline import TimelineUpdateHandler

class Schedule:
    '''
    A schedule of events and transactions.

    The schedule is a priority queue of events, ordered by date.
    '''

    __events: list['TimelineUpdateHandler']
    @property
    def events(self) -> list['TimelineUpdateHandler']:
        return self.__events

    def __init__(self, events: Optional[list['TimelineUpdateHandler']]=None):
        self._events = heapify(events) if events else []

    def copy(self):
        '''
        Return a copy of the schedule.
        '''
        return Schedule(self.events)

    def add(self,
            date_: date,
            event: Callable[[date, dict[str, AccountState]], None],
            ):
        '''
        Add an event to the schedule.

        PARAMETERS
        ----------
        date: datetime
            The date of the event.
        event: Callable[[datetime, dict[str, AccountState]], None]
            The event function.
        '''
        heappush(self.events, (date_, event))

    def run(self, date_: date) -> Iterable[TimelineUpdateHandler]:
        '''
        Run through the events up to a given date.

        PARAMETERS
        ----------
        date: datetime
            The date to run up to.
        '''
        while self.events and self.events[0][0] <= date_:
            _, event = heappop(self.events)
            yield event
