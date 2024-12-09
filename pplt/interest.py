'''
Utilities for working with compound interest rates.

Compound interest is a bit trickier than its seems. You cannot just divide the
annual rate by 12 to get the monthly rate. Instead, you need to raise 1 + the
annual rate to the 1/12th power. This is because the interest is compounded
each month, so the interest is added to the principal each month, and you pay or
earn interest on the interest.
'''

from datetime import datetime


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


def rate_of_return(start_date: datetime|str, start_value: float,
                   end_date: datetime|str, end_value: float):
    '''
    Given a start date and value, and an end date and value, calculate the
    annual rate of return.

    PARAMETERS
    ----------
    start_date: datetime|str
        Starting date.
    start_value: float
        Starting value.
    end_date: datetime|str
        Ending date.
    end_value: float
        Ending value.

    RETURNS
    -------
    rate: float
        The annual rate of return, as a fraction.
    '''
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    change = end_value - start_value
    frac = change / start_value
    days = (end_date - start_date).days
    daily = (1 + frac) ** (1.0 / days)
    annual = daily ** 365.25
    return annual - 1


def pct_return(start_date: datetime|str, start_value: float,
               end_date: datetime|str, end_value: float):
    '''
    Given a start date and value, and an end date and value, calculate the
    annual rate of return as a percentage.

    PARAMETERS
    ----------
    start_date: datetime|str
        Starting date.
    start_value: float
        Starting value.
    end_date: datetime|str
        Ending date.
    end_value: float
        Ending value.

    RETURNS
    -------
    rate: float
        The annual rate of return, as a percentage.
    '''
    return 100 * rate_of_return(start_date, start_value, end_date, end_value)