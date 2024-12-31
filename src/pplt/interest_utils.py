'''
Utilities for working with compound interest rates.

Compound interest is a bit trickier than its seems. You cannot just divide the
annual rate by 12 to get the monthly rate. Instead, you need to raise 1 + the
annual rate to the 1/12th power. This is because the interest is compounded
each month, so the interest is added to the principal each month, and you pay or
earn interest on the interest.
'''

from contextlib import suppress
from datetime import datetime, date

from pplt.dates import parse_month
from pplt.period import PeriodUnit

def apr(rate: float, period: PeriodUnit):
    match period:
        case 'day':
            exp = 365.25
        case 'week':
            exp = 365.25 / 7
        case 'month':
            exp = 12
        case 'quarter':
            exp = 4
        case 'year':
            return rate
        case _: # type: ignore
            raise ValueError(f"Invalid period unit: {period}")
    return (1 + rate) ** exp - 1

def monthly_rate(annual: float):
    """
    Convert annual rate to monthly. This is NOT the same as dividing by 12.
    NOTE: not as percentage!
    """
    rate = (1 + annual) ** (1/12.0)
    return (rate - 1)


def monthly_pct(annual: float):
    """
    Convert annual pecentage rate to monthly. This is NOT the same
    as dividing by 12.
    """
    return 100 * monthly_rate(annual / 100)


def daily_rate(annual: float):
    """
    Convert annual rate to daily. This is NOT the same as dividing by 365.25
    NOTE: not as percentage!
    """
    rate = (1 + annual) ** (1/365.25)
    return (rate - 1)


def daily_pct(annual: float):
    """
    Convert annual pecentage rate to daily. This is NOT the same
    as dividing by 365.25
    """
    return 100 * daily_rate(annual / 100)


def quarterly_rate(annual: float):
    """
    Convert annual rate to quarterly. This is NOT the same as dividing by 4.
    NOTE: not as percentage!
    """
    rate = (1 + annual) ** 0.25
    return (rate - 1)


def quarterly_pct(annual: float):
    """
    Convert annual pecentage rate to quarterly. This is NOT the same
    as dividing by 4.
    """
    return 100 * quarterly_rate(annual / 100)


def rate_of_return(start_date: date|str, start_value: float,
                   end_date: date|str, end_value: float):
    '''
    Given a start date and value, and an end date and value, calculate the
    annual rate of return.

    PARAMETERS
    ----------
    start_date: date|str
        Starting date.
    start_value: float
        Starting value.
    end_date: date|str
        Ending date.
    end_value: float
        Ending value.

    RETURNS
    -------
    rate: float
        The annual rate of return, as a fraction.
    '''
    def parse(date_: date|str) -> date:
        match date_:
            case date():
                return date_
            case str():
                with suppress(ValueError):
                    return datetime.strptime(date_, "%Y-%m-%d")
                return parse_month(date_)
            case _: # type: ignore
                raise ValueError(f"Invalid date: {date_}")
    start_date = parse(start_date)
    end_date = parse(end_date)
    change = end_value - start_value
    frac = change / start_value
    days = (end_date - start_date).days
    daily = (1 + frac) ** (1.0 / days)
    annual = daily ** 365.25
    return annual - 1

def pct_return(start_date: date|str, start_value: float,
               end_date: date|str, end_value: float):
    '''
    Given a start date and value, and an end date and value, calculate the
    annual rate of return as a percentage.

    PARAMETERS
    ----------
    start_date: date|str
        Starting date.
    start_value: float
        Starting value.
    end_date: date|str
        Ending date.
    end_value: float
        Ending value.

    RETURNS
    -------
    rate: float
        The annual rate of return, as a percentage.
    '''
    return 100 * rate_of_return(start_date, start_value, end_date, end_value)
