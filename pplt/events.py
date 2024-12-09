'''
Financial events
'''

from datetime import date

from pplt.account import Account, AccountState
from pplt.interest import monthly_rate
from pplt.decorators import event

@event()
def interest(date_: date, account: Account, state: AccountState, /,
            rate: float):
    """
    Calculate interest on an account. e.g.:

    schedule.add
    """
    return state * monthly_rate(rate)