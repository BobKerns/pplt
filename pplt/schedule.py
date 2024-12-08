'''
Schedule module for the pplt package.

This maintains a schedule of events and transactions, one-time and recurring,
that affect the accounts.
'''

from datetime import datetime
from heapq import heappop, heappush, heapify
from typing import Callable

from pplt.account import AccountState
from pplt.timeline import Timeline, TimelineUpdateHandler

class Schedule:
    '''
    A schedule of events and transactions.

    The schedule is a priority queue of events, ordered by date.
    '''

    __events: list[TimelineUpdateHandler]
    @property
    def events(self) -> list[TimelineUpdateHandler]:
        return self.__events

    def __init__(self, events: list[TimelineUpdateHandler]=None):
        self.events = heapify(events) if events else []

    def copy(self):
        '''
        Return a copy of the schedule.
        '''
        return Schedule(self.events)

    def add(self, date: datetime, event: Callable[[datetime, dict[str, AccountState]], None]):
        '''
        Add an event to the schedule.

        PARAMETERS
        ----------
        date: datetime
            The date of the event.
        event: Callable[[datetime, dict[str, AccountState]], None]
            The event function.
        '''
        heappush(self.events, (date, event))

    def run(self, date: datetime,
            timeline: Timeline,
            states: dict[str, AccountState]):
        '''
        Run the events up to a given date.

        PARAMETERS
        ----------
        date: datetime
            The date to run up to.
        timeline: Timeline
            The timeline of the accounts.
        states: dict[str, AccountState]
            The current states of the accounts.
        '''
        while self.events and self.events[0][0] <= date:
            _, event = heappop(self.events)
            event(self, date, timeline, states)

