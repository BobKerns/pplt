'''
Utilities for working with units of time and time series.
'''

from collections.abc import Iterable
from datetime import datetime, timedelta
from itertools import islice
from typing import Optional


DAYS_PER_MONTH = (31,28,31,30,31,30,31,31,30,31,30,31)
def days_per_month(date: datetime|int):
    """
    The number of days in a month.

    PARAMETERS
    ----------
    date: datetime|int
        A date or month number.

    RETURNS
    -------
    days: int
        The number of days in the month.
    """
    month = date if isinstance(date, int) else date.month
    days = DAYS_PER_MONTH[(month-1)%12]
    if month == 2 and (date.year % 4) == 0:
        days += 1
    return days


def next_month():
    """
    RETURNS
    -------
    date: datetime
        The date at the start of the next month.
    """
    today = datetime.today()
    today - today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return today + timedelta(days=days_per_month(today))


def months(start: datetime=next_month()) -> Iterable[datetime]:
    '''
    Yields a series of dates 1 month apart.

    PARAMETERS
    ----------
    start: datetime.date
        Starting date. Default=next_month()
    '''
    date = start
    while True:
        yield date
        date = date + timedelta(days=days_per_month(date))


def months_str(start: datetime=next_month(),
               end: Optional[int]=None,
               stride: int=1):
    """
    Returns a list of month strings for the pltext library.

    These can be used in `plt.xticks()` or as x-values in `plt.plot()`.
    """
    series = (t.strftime('%y/%m') for t in months(start=start))
    if end is None:
        return series
    return islice(series, 0, end, stride)


def parse_month(date: str|datetime):
    '''
    Parse a date string or datetime object into a month.

    Strings should be in the form 'yy/mm'.
    '''
    match date:
        case str():
            return datetime.strptime(date, "%y/%m")
        case datetime():
            return date.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)
        case _:
            raise ValueError(f'Invalid date: {date}.')


def unparse_month(date: datetime):
    '''
    The inverse of `parse_month()`.

    RETURNS
    -------
    date: str
        A string in the form 'yy/mm'.
    '''
    return date.strftime('%y/%m')


def parse_end(start: datetime|str, end: int|str|datetime) -> int:
    """
    Parse the end date.

    PARAMETERS
    ----------
    start: datetime|str
        Starting date.
    end: int|str|datetime
        The ending date, or the number of months to print.

    RETURNS
    -------
    end: int
        The number of months to show.
    """
    start = parse_month(start)
    match end:
        case int():
            return end
        case datetime()|str():
            return (parse_month(end) - start).days
        case _:
            raise ValueError('Invalid end value.')
