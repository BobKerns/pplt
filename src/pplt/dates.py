'''
Utilities for working with units of time and time series.
'''

from collections.abc import Iterator
from datetime import date, timedelta
from itertools import islice
from types import NoneType

from pplt.utils import skip

type Month = str
'''
A month string in the form 'yy/mm'.
'''

DAYS_PER_MONTH = (31,28,31,30,31,30,31,31,30,31,30,31)
def days_per_month(date_: date|int):
    """
    The number of days in a month.

    PARAMETERS
    ----------
    date_: date|int
        A date or month number.

    RETURNS
    -------
    days: int
        The number of days in the month.
    """
    match date_:
        case int():
            month, year = date_, date.today().year
        case date():
            month, year = date_.month, date_.year
        case _: # type: ignore
            raise ValueError(f'Invalid date: {date_}.')
    days = DAYS_PER_MONTH[(month-1)%12]
    if month == 2 and (year % 4) == 0:
        # Leap year
        days += 1
    return days


def next_month(from_date: date|str|None=None) -> date:
    """
    The start of the next month from the given date, or today.
    RETURNS
    -------
    date: date|datetime|str
        The date at the start of the next month.
    """
    from_date = date.today() if from_date is None else parse_month(from_date)
    from_date = from_date.replace(day=1)
    return from_date + timedelta(days=days_per_month(from_date))


def months(start: date|str|None=None) -> Iterator[date]:
    '''
    Yields a series of dates 1 month apart.

    PARAMETERS
    ----------
    start: date|str
        Starting date. Default=next_month()

    YIELDS
    ------
    date: date
        The next date in the series.
    '''
    if start is None:  # noqa: SIM108
        date_ = next_month()
    else:
        date_ = parse_month(start)
    while True:
        yield date_
        date_ = date_ + timedelta(days=days_per_month(date_))


def months_str(start: date|str|NoneType=None,
               end: int|date|str|None=None,
               stride: int=1):
    """
    Returns a list of month strings for the pltext library.

    These can be used in `plt.xticks()` or as x-values in `plt.plot()`.

    PARAMETERS
    ----------
    start: date|str
        Starting date. Default=next_month()
    end: Optional[int|date|str]
        Number of months to print.
    stride: int
        Number of months to step ahead each time.

    RETURNS
    -------
    series: Iterable[str]
        A series of month strings.
    """
    if start is None:
        start = next_month()
    series = (
        t.strftime('%y/%m')
        for t in months(start=start)
    )
    match end:
        case None:
            return series
        case int():
            return islice(series, 0, end, stride)
        case date()|str():
            end = parse_end(start, end)
            return islice(series, 0, end, stride)
        case _: # type: ignore
            raise ValueError('Invalid end value.')


def parse_month(date_: str|date|None=None) -> date:
    '''
    Parse a date string or date object into a month.

    Strings should be in the form 'yy/mm'.
    '''
    match date_:
        case None:
            return next_month()
        case str():
            date_ = date_.replace('-', '/').replace('.', '/')
            year, month = date_.split('/')
            year, month = int(year), int(month)
            if month < 1 or month > 12:
                raise ValueError(f'Invalid month: {month}.')
            if year < 1900:
                year += 2000
            if year > 2200:
                raise ValueError(f'Invalid year: {year}.')
            return date(year, month, 1)
        case date():
            return date_.replace(day=1)
        case _: # type: ignore
            raise ValueError(f'Invalid date: {date_}.')


def valid_month(date_: str) -> date:
    '''
    Validate a month string  of the form 'yy/mm'. (Leading zeroes are not required).

    This exists for consistency with other validation functions in the loader module,
    but just calls `parse_month()`.
    RETURNS
    -------
    date: date
        The date object.
    '''
    return parse_month(date_)


def unparse_month(date: date):
    '''
    The inverse of `parse_month()`.

    RETURNS
    -------
    date: str
        A string in the form 'yy/mm'.
    '''
    return date.strftime('%y/%m')


def parse_end(start: date|str, end: int|str|date) -> int:
    """
    Parse the end date as the number of months to show.

    NOTE: This results in end-exclusive ranges.

    PARAMETERS
    ----------
    start: date|str
        Starting date.
    end: int|str|date
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
        case date()|str():
            end = parse_month(end)
            years = end.year - start.year
            months = end.month - start.month
            return years * 12 + months
        case _: # type: ignore
            raise ValueError('Invalid end value.')


def month_plus(month: str|date, n: int) -> date:
    '''
    Return the month n months after the given month.
    '''
    series = months(month)
    skip(n, series)
    return next(series)
