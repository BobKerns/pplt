'''
Financial events
'''

from datetime import date

from pplt.account import Account, AccountValue
from pplt.interest import monthly_rate
from pplt.decorators import event

@event()
def interest(date_: date, account: Account, state: AccountValue, /,
            rate: float):
    """
    Calculate interest on an account. e.g.:

    schedule.add
    """
    return state * monthly_rate(rate)