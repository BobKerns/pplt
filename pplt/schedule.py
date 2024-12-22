'''
Schedule module for the pplt package.

This maintains a schedule of events and transactions, one-time and recurring,
that affect the accounts.
'''

from datetime import date
from heapq import heappop, heappush, heapify
from typing import TYPE_CHECKING, Any, cast
from itertools import count
if TYPE_CHECKING:
    from collections.abc import Iterable

from pplt.table import Table
from pplt.timeline import TimelineUpdateHandler
from pplt.dates import parse_month

_counter = iter(count())

class HandlerEntry:
    '''
    A handler entry in the schedule.
    '''
    handler: TimelineUpdateHandler
    id: int

    def __init__(self, handler: TimelineUpdateHandler):
        self.handler = handler
        self.id = next(_counter)

    def __eq__(self, other: Any):
        match other:
            case HandlerEntry():
                return self.id == other.id
            case _:
                return False

    def __lt__(self, other: Any):
        match other:
            case HandlerEntry():
                return self.id < other.id
            case _:
                return NotImplemented


class Schedule:
    '''
    A schedule of events and transactions.

    The schedule is a priority queue of events, ordered by date.
    '''

    __last_run: date|None

    __events: list[tuple[date, HandlerEntry]]
    @property
    def events(self) -> list[tuple[date, HandlerEntry]]:
        return  self.__events

    def __init__(self, events: list[tuple[date, HandlerEntry]]|None=None):
        _events = events or []
        heapify(_events)
        self.__events = _events
        self.__last_run = None

    def copy(self):
        '''
        Return a copy of the schedule.
        '''
        return Schedule(self.events)

    def add(self,
            date_: date|str,
            handler: TimelineUpdateHandler,
            ):
        '''
        Add an event to the schedule.

        PARAMETERS
        ----------
        date: date|str
            The date of the event.
        event: Callable[[datetime, dict[str, AccountState]], None]
            The event function.
        '''
        date_ = parse_month(date_)
        if self.__last_run and date_ <= self.__last_run:
            raise ValueError('Can only add future dates. '
                             f'date={date_}, last_run={self.__last_run}')
        heappush(self.events, (date_, HandlerEntry(handler)))

    def run(self, date_: date) -> 'Iterable[tuple[date, TimelineUpdateHandler]]':
        '''
        Run through the events up to a given date.

        PARAMETERS
        ----------
        date: datetime
            The date to run up to.
        '''
        if self.__last_run and date_ <= self.__last_run:
            raise ValueError('Can only run to future dates. '
                             f'date={date_}, last_run={self.__last_run}')
        self.__last_run = date_
        while self.__events and self.__events[0][0] <= date_:
            date_, h = heappop(self.__events)
            yield date_, h.handler

    @property
    def table(self):
        '''
        Return a table of the events in the schedule.
        '''
        def extract(event: tuple[date, HandlerEntry]):
            date_, handler = event
            period = cast(Any, handler.handler).period if hasattr(handler.handler, 'period') else None
            start = period.start if period else None
            end = period.end if period else None
            n = period.n if period else None
            unit = period.unit if period else None
            return date_, handler.handler.__name__, start, end, n, unit

        events = sorted(self.events)
        return Table(values=list(map(extract, events)),
                    labels=['Month', 'Handler', 'Start', 'End', 'N', 'Unit'],
                    ncols=6,
                    formats=['%y/%m'],
                    end=len(events))

    def __repr__(self):
        return f'Schedule({sorted(self.events)}, last_run={self.__last_run})'
