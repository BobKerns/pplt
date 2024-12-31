'''
Time periods for periodic events.
'''

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from pplt.dates import parse_month

type PeriodUnit = Literal['day', 'week', 'month', 'quarter', 'year']

def valid_period_unit(unit: str) -> PeriodUnit:
    '''
    Validate a period unit.
    '''
    if unit not in ('day', 'week', 'month', 'quarter', 'year'):
        raise ValueError(f'Invalid period unit: {unit}')
    return unit

@dataclass
class Period:
    '''
    A period of time, with a unit and a number of units.
    '''
    unit: PeriodUnit
    n: int

    def __str__(self):
        return f'{self.n} {self.unit}'

class Periodic:
    '''
    A periodic event.
    '''
    period: Period
    start: date
    end: date|None
    next: date

    @property
    def n(self):
        return self.period.n

    @property
    def unit(self):
        return self.period.unit

    def __init__(self, start: date, n: int, unit: PeriodUnit, end: date|None=None):
        self.period = Period(unit, n)
        self.start = parse_month(start)
        self.next = self.start
        self.end = parse_month(end) if end else None

    def __iter__(self):
        next: date = self.start
        while True:
            if self.end and next > self.end:
                break
            # For display, we record the next date before yielding it.
            self.next = next
            yield next
            match self.period.unit:
                case 'day':
                    next = next + timedelta(days=self.period.n)
                case 'week':
                    next = next + timedelta(weeks=self.period.n)
                case 'month':
                    next = next.replace(month=((next.month - 1) + self.period.n) % 12 + 1,
                                        year=next.year + ((next.month - 1) + self.period.n) // 12)
                case 'quarter':
                    next = next.replace(month=((next.month - 1) + self.period.n * 3) % 12 + 1,
                                        year=next.year + ((next.month - 1) + self.period.n * 3) // 12)
                case 'year':
                    next = next.replace(year=next.year + self.period.n)

    def __str__(self):
        return f'{self.period}'
