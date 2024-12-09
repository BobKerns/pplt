'''
Decorators for the pplt package.
'''

from abc import abstractmethod
from collections.abc import Callable
from datetime import date, timedelta
from typing import Optional, Protocol, TYPE_CHECKING

from pplt.dates import next_month
if TYPE_CHECKING:
    from pplt.account import AccountState
    from pplt.timeline import (
        TimelineStep, TimelineAccountState, AccountUpdate,
        TimelineUpdateHandler,
    )

class EventHandler(Protocol):
    @abstractmethod
    def __call__(self, date_: date,
                 account: 'TimelineAccountState',
                 state: 'AccountState', /,
                 **kwargs) -> 'AccountUpdate':
        ...

class EventSpecifier(Protocol):
    @abstractmethod
    def __call__(self, name: str, start: Optional[date]=None, /,
                 **kwargs) -> 'TimelineUpdateHandler':
        ...

def event(period: Optional[tuple[str, int]|timedelta]=None):
    '''
    A decorator for financial events.

    This is applied to functions with signatures like this:
    ```
    def func(date: datetime, account: account.Account, state: AccountState, /,
            **kwargs) -> AccountState:
        ...
    ```

    The `kwargs` can be whatever constant parameters you need to calculate
    the update.

    This returns a function that takes a `TimelineStep` and produces an update
    (a float or a new `AccountState`) to the account.

    If the decorator was called with the `period` argument, the event will be
    added to the schedule to recur at that interval.

    EXAMPLE
    -------
    @event(period=('months', 1))
    def interest(date: datetime, account: account.Account, state: AccountState, /,
                rate: float):
        """
        Calculate interest on an account.
        """
        return state * monthly_rate(rate)

    sch = Schedule()
    sch.add(next_month(), interest('SAVINGS', rate=0.01))
    '''

    if isinstance(period, tuple):
        interval, amount = period
        period = timedelta(**{interval: amount})
    def decorator(func: EventHandler) -> EventSpecifier:
        # This is what you call to create the event handler to add to the schedule.
        def for_account(name: str, start: Optional[date]=None, /,
                        **kwargs) -> 'TimelineUpdateHandler':
            # The wrapper's signature is determined by the Timeline.
            # It calls the decorated function and updates the account state.
            start = start or next_month()
            def wrapper(step: 'TimelineStep'):
                date_ = step.date
                account = step.accounts[name]
                state = step.states[name]
                update = func(date_, account, state, **kwargs)
                account.send(update)
                # Re-add the event if it is recurring.
                if period:
                    step.schedule.add(date_ + period, wrapper)
            return wrapper
        return for_account
    return decorator


class TransactionHandler(Protocol):
    @abstractmethod
    def __call__(self, date_: date,
                 from_account: 'TimelineAccountState',
                 from_state: 'AccountState',
                 to_account: 'TimelineAccountState',
                 to_state: 'AccountState',
                 /,
                 **kwargs) -> 'AccountUpdate':
        ...

class TransactionSpecifier(Protocol):
    @abstractmethod
    def __call__(self, from_: str, to_: str, start: Optional[date]=None, /,
                 **kwargs) -> 'TimelineUpdateHandler':
        ...

def transaction(period: Optional[tuple[str, int]|timedelta]=None):
    '''
    A decorator for financial transaction functions.

    ```
    def transfer(date: datetime, from_state: AccountState, to_state: AccountState, /,
            **kwargs) -> AccountUpdate:
        ...
    ```

    The `kwargs` can be whatever constant parameters you need to calculate
    the update.

    This returns a function that takes a `TimelineStep` and produces an update
    (a float or a new `AccountState`) to the account.

    If the decorator was called with the `period` argument, the transaction will be
    added to the schedule to recur at that interval.

    EXAMPLE
    -------
    @transaction(period=('months', 1))
    def transfer(date: datetime, account: account.Account, state: AccountState, /,
                amount: float):
        """
        Make a fixed transfer between accounts, such as a loan payment.
        """
        return amount

    schedule = Schedule()
    schedule.add(date=next_month(), handler=transfer('checking', 'savings',
                amount=100.00))
    '''

    if isinstance(period, tuple):
        interval, amount = period
        period = timedelta(**{interval: amount})
    def decorator(func: TransactionHandler) -> TransactionSpecifier:
        # This is what you call to create the event handler to add to the schedule.
        def for_accounts(from_: str, to_: str, start: date=next_month(), /,
                         **kwargs) -> 'TimelineUpdateHandler':
            # The wrapper's signature is determined by the Schedule.
            # It calls the decorated function and updates the account states.
            def wrapper(step: 'TimelineStep'):
                date_ = step.date
                if date_ < start:
                    # Too soon.
                    return None
                from_account = step.accounts[from_]
                from_state = step.states[from_]
                to_account = step.accounts[to_]
                to_state = step.states[to_]
                update = func(date, from_state, to_state,
                              **kwargs)
                if not isinstance(update, float):
                    raise ValueError('Transaction update must be a float.')
                if update is not None:
                    from_account.send(-update)
                    to_account.send(update)
                # Re-add the event if it is recurring.
                if period:
                    step.schedule.add(date + period, wrapper)
            return wrapper
        return for_accounts
    return decorator
