'''
Financial events
'''

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Callable, Optional

from pplt import account
from pplt.account import AccountState
from pplt.interest import monthly_rate
from pplt.time import next_month
from pplt.timeline import Timeline, TimelineItem
if TYPE_CHECKING:
    import pplt.schedule as sch


def event(period: Optional[tuple[str, int]|timedelta]=None):
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
        def for_account(name: str, start: datetime=next_month(), /, **kwargs):
            # The wrapper's signature is determined by the Schedule.
            # It calls the decorated function and updates the account state.
            def wrapper(schedule: 'sch.Schedule',
                        date: datetime,
                        timeline: Timeline,
                        states: TimelineItem):
                account = timeline.accounts[name]
                state = states[name]
                update = func(date, account, state, **kwargs)
                account.send(update)
                # Re-add the event if it is recurring.
                if period:
                    schedule.add(date + period, wrapper)
            return wrapper
        return for_account
    return decorator


@event()
def interest(date: datetime, account: account.Account, state: AccountState, /,
            rate: float):
    """
    Calculate interest on an account. e.g.:

    schedule.add
    """
    return state * monthly_rate(rate)