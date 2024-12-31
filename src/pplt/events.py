'''
Financial events
'''

from datetime import date
from typing import Any

from pplt.account import AccountValue
from pplt.interest_utils import monthly_rate
from pplt.decorators import event

@event(description='{rate:0.2f}% APR')
def interest(date_: date, state: AccountValue, /,
            rate: float,
            **kwargs: Any):
    """
    Calculate interest on an account. e.g.:

    schedule.add(interest('MyAccount', '25/1', rate=0.01))
    """
    return state * monthly_rate(rate)