'''
Transaction definitions. Similar to event definitions, but for transactions,
with two accounts and an amount.
'''


from datetime import datetime, timedelta
from typing import Callable, Optional, TYPE_CHECKING

from pplt.account import Account, AccountState
from pplt.time import next_month
from pplt.timeline import Timeline, TimelineItem
if TYPE_CHECKING:
    import pplt.schedule as sch


def transaction(period: Optional[tuple[str, int]|timedelta]=None):
    '''
    A decorator for financial events.

    The result is a function that takes the name of an account,
    and keyword arguments, and returns a function that takes
    a date, a `Timeline`, and a `TimelineItem` and produces an
    update to the account (either an amount to add or a new state).

    EXAMPLE
    -------
    @event(period=('months', 1))
    def interest(date: datetime, account: account.Account, state: AccountState, /,
                rate: float):
        """
        Calculate interest on an account.
        """
        return state * monthly_rate(rate)
    '''
    if isinstance(period, tuple):
        interval, amount = period
        period = timedelta(**{interval: amount})
    def decorator(func: Callable[..., AccountState]):
        # This is what you call to create the event handler to add to the schedule.
        def for_accounts(from_: str, to_: str, start: datetime=next_month(), /, **kwargs):
            # The wrapper's signature is determined by the Schedule.
            # It calls the decorated function and updates the account states.
            def wrapper(schedule: 'sch.Schedule',
                        date: datetime,
                        timeline: Timeline,
                        states: TimelineItem):
                from_account = timeline.accounts[from_]
                from_state = states[from_]
                to_account = timeline.accounts[to_]
                to_state = states[to_]
                update = func(date, from_state, to_state,
                              **kwargs)
                if not isinstance(update, float):
                    raise ValueError('Transaction update must be a float.')
                from_account.send(-update)
                to_account.send(update)
                # Re-add the event if it is recurring.
                if period:
                    schedule.add(date + period, wrapper)
            return wrapper
        return for_accounts
    return decorator

@transaction()
def transfer(date: datetime, from_state: AccountState, to_state: AccountState, /,
            amount: float):
    """
    Transfer a fixed amount of money between accounts.

    PARAMETERS
    ----------
    date: datetime
        The date of the transaction.
    from_: Account
        The account to transfer from.
    from_state: AccountState
        The state of the account to transfer from.
    to_: Account
        The account to transfer to.
    to_state: AccountState
        The state of the account to transfer to.
    amount: float
        The amount to transfer.

    RETURNS
    -------
    amount: float
        The amount transferred.
    """
    return amount

