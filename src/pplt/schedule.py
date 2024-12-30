'''
Schedule module for the pplt package.

This maintains a schedule of events and transactions, one-time and recurring,
that affect the accounts.
'''

from datetime import date
from heapq import heappop, heappush, heapify
from typing import  Any
from itertools import count
from collections.abc import Iterable, Iterator, Sequence

from rich.console import RenderableType
from rich.table import Table as RichTable

from pplt.rich_tables import Table
from pplt.timeline_series import TimelineUpdateHandler

_counter = iter(count())

class ScheduleEntry:
    '''
    A handler entry in the schedule.
    '''
    handler: TimelineUpdateHandler
    dates: Iterator[date]
    id: int
    '''
    A sequential ID, to allow for ordering of handler entries.
    This is needed to support use as a heap entry in a deterministic way.
    '''

    def __init__(self, handler: TimelineUpdateHandler, id: int|None=None):
        self.handler = handler
        if handler.period:
            self.dates = iter(handler.period)
        else:
            self.dates = iter([handler.start])
        self.id = next(_counter) if id is None else id

    def __eq__(self, other: Any):
        match other:
            case ScheduleEntry():
                return self.id == other.id
            case _:
                return False

    def __lt__(self, other: Any):
        match other:
            case ScheduleEntry():
                return self.id < other.id
            case _:
                return NotImplemented

    def copy(self):
        return ScheduleEntry(self.handler, self.id)

    def __repr__(self):
        return f'HandlerEntry({self.handler}, {self.id})'

class Schedule:
    '''
    A schedule of events and transactions.

    The schedule is a priority queue of events, ordered by date.
    '''

    __last_run: date|None

    __events: list[tuple[date, ScheduleEntry]]
    @property
    def events(self) -> list[tuple[date, ScheduleEntry]]:
        return  self.__events

    def __init__(self, events: list[tuple[date, ScheduleEntry]]|None=None):
        _events = events or []
        heapify(_events)
        self.__events = _events
        self.__last_run = None

    def copy(self):
        '''
        Return a copy of the schedule.
        '''
        events = [(date_, entry.copy()) for date_, entry in self.events]
        return Schedule(events)

    def add(self,
            handler: TimelineUpdateHandler,
            /,
            ):
        '''
        Add an event to the schedule.

        PARAMETERS
        ----------
        handler: TimelineUpdateHandler
            The handler for the event.
        '''
        entry = ScheduleEntry(handler)
        date_ = next(entry.dates)
        if self.__last_run and date_ <= self.__last_run:
            raise ValueError('Can only add future dates. '
                             f'date={date_}, last_run={self.__last_run}')
        heappush(self.events, (date_, entry))

    def run(self, until: date) -> 'Iterable[tuple[date, TimelineUpdateHandler]]':
        '''
        Run through the events up to a given date.

        PARAMETERS
        ----------
        date: datetime
            The date to run up to.
        '''
        if self.__last_run and until <= self.__last_run:
            raise ValueError('Can only run to future dates. '
                             f'date={until}, last_run={self.__last_run}')
        self.__last_run = until
        while self.__events and self.__events[0][0] <= until:
            date_, h = heappop(self.__events)
            yield date_, h.handler
            # Add the next date for the handler.
            try:
                date_ = next(h.dates)
                heappush(self.__events, (date_, h))
            except StopIteration:
                pass

    @property
    def table(self):
        '''
        Return a table of the events in the schedule.
        '''
        def cell(value: RenderableType|Sequence[RenderableType]):
            match value:
                case str():
                    return value
                case Sequence():
                    grid = RichTable.grid(expand=True)
                    for i in range(len(value)):
                        match i:
                            case 0:
                                grid.add_column(justify='left')
                            case _ if i == len(value) - 1:
                                grid.add_column(justify='right')
                            case _:
                                grid.add_column(justify='center')
                    grid.add_row(*value)
                    return grid
                case _: # type: ignore
                    raise ValueError(f'Invalid value: {value}')
        def extract(event: tuple[date, ScheduleEntry]):
            date_, entry = event
            handler = entry.handler
            period = handler.period
            end = period.end if period else None
            n = period.n if period else None
            unit = period.unit if period else None
            accounts = cell(handler.accounts)
            description = cell(handler.description)
            period_ = cell((f'{n: 3}', str(unit))) if period else None
            return date_, period_, end, accounts, handler.__name__, description

        events = sorted(self.events)
        return Table(values=list(map(extract, events)),
                    labels=['Month', ' Period  ', ' End ', 'Accounts', 'Handler', 'Details'],
                    ncols=6,
                    formats=['%y/%m'],
                    end=len(events))

    def __repr__(self):
        return f'Schedule({sorted(self.events)}, last_run={self.__last_run})'
