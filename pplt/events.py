'''
Financial events
'''

from datetime import date
from typing import Any

from pplt.account import AccountValue
from pplt.interest import monthly_rate
from pplt.decorators import event

@event()
def interest(date_: date, state: AccountValue, /,
            rate: float,
            **kwargs: Any):
    """
    Calculate interest on an account. e.g.:

    schedule.add('21/1', interest, rate=0.01)
    """
    return state * monthly_rate(rate)