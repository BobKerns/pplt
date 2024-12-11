'''
Decorators for the pplt package.
'''

from abc import abstractmethod
from collections.abc import Callable
from functools import wraps
from datetime import date, timedelta
from typing import Optional, Protocol, TYPE_CHECKING

from pplt.dates import next_month, parse_month
if TYPE_CHECKING:
    from pplt.account import AccountValue, AccountStatus
    from pplt.timeline import (
        TimelineStep, TimelineAccountState,
        TimelineUpdateHandler,
    )


type AccountUpdate = 'AccountState|float|AccountStatus|None'''
'''
    Return value from handlers to indicate how accounts should be updated.
'''

class EventHandler(Protocol):
    '''
    The signature for the user-defined event functions, before applying
    the decorator.
    '''
    @abstractmethod
    def __call__(self, date_: date,
                 account: 'TimelineAccountState',
                 state: 'AccountValue', /,
                 **kwargs) -> 'AccountUpdate':
        '''
        The signature for the user-defined event functions, before applying
        the decorator.

        PARAMETERS
        ----------
        date_: date
            The date of the event.
        account: TimelineAccountState
            The account state generator for the account, which can be updated.
        state: AccountState
            The current state of the account.
        kwargs: dict
            Any constant parameters needed to calculate the update,
            such as interest rates or amounts. Supplied by the user
            when adding the event to the schedule.
        '''
        ...

class EventSpecifier(Protocol):
    '''
    The signature for the user-defined event functions, after applying
    the decorator but before being configured onto the schedule.
    '''
    @abstractmethod
    def __call__(self, name: str, start: Optional[date]=None, /,
                 **kwargs) -> 'TimelineUpdateHandler':
        '''
        The signature for the user-defined event functions, after applying
        the decorator but before being configured onto the schedule.

        This is the signature that the user calls to add the event to the
        schedule.

        PARAMETERS
        ----------
        name: str
            The name of the account to update.
        start: date
            The date to start the event.
        kwargs: dict
            Any constant parameters needed to calculate the update,
            such as interest rates or amounts. Supplied by the user
            when adding the event to the schedule.
        '''
        ...

def mywrap(func):
    '''
    Wrap a function without setting the signature.
    '''
    def decorate(wrapper: Callable):
        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__
        wrapper.__qualname__ = func.__qualname__
        wrapper.__module__ = func.__module__
        return wrapper
    return decorate

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
        @mywrap(func)
        def for_account(name: str, start: Optional[date|str]=None, /,
                        **kwargs) -> 'TimelineUpdateHandler':
            start = parse_month(start) if start else next_month()
            # The wrapper's signature is determined by the Timeline.
            # It calls the decorated function and updates the account state.
            @mywrap(func)
            def wrapper(step: 'TimelineStep', /):
                date_ = step.date
                if date_ < start:
                    # Too soon.
                    return None
                account = step.states[name]
                value = step.values[name]
                update = func(date_, account, value, **kwargs)
                account.send(update)
                # Re-add the event if it is recurring.
                if period:
                    step.schedule.add(date_ + period, wrapper)
            return wrapper
        return for_account
    return decorator


class TransactionHandler(Protocol):
    '''
    The signature for the user-defined transaction functions, before applying
    the decorator.
    '''
    @abstractmethod
    def __call__(self, date_: date,
                 from_account: 'TimelineAccountState',
                 from_state: 'AccountValue',
                 to_account: 'TimelineAccountState',
                 to_state: 'AccountValue',
                 /,
                 **kwargs) -> 'AccountUpdate':
        '''
        The signature for the user-defined transaction functions, before applying
        the decorator.

        date_: date
            The date of the transaction.
        from_account: TimelineAccountState
            The account state generator for the 'from' account, which can be updated.
        from_state: AccountState
            The current state of the 'from' account.
        to_account: TimelineAccountState
            The account state generator for the 'to' account, which can be updated.
        to_state: AccountState
            The current state of the 'to' account.
        kwargs: dict
            Any constant parameters needed to calculate the update,
            such as interest rates or amounts. Supplied by the user
            when adding the event to the schedule.
        '''
        ...

class TransactionSpecifier(Protocol):
    '''
    The signature for the user-defined transaction functions, after applying
    the decorator but before being configured onto the schedule.
    '''
    @abstractmethod
    def __call__(self, from_: str, to_: str, start: Optional[date]=None, /,
                 **kwargs) -> 'TimelineUpdateHandler':
        '''
        The signature for the user-defined transaction functions, after applying
        the decorator but before being configured onto the schedule.

        This is the signature that the user calls to add the event to the
        schedule.

        PARAMETERS
        ----------
        name: str
            The name of the account to update.
        start: date
            The date to start the event.
        from_account: str
            The name of the account to transfer from.
        to_account: str
            The name of the account to transfer to.
        kwargs: dict
            Any constant parameters needed to calculate the update,
            such as interest rates or amounts. Supplied by the user
            when adding the event to the schedule.
        '''
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
        @mywrap(func)
        def for_accounts(from_: str, to_: str, start: Optional[date|str]=None, /,
                         **kwargs) -> 'TimelineUpdateHandler':
            start = parse_month(start) if start else next_month()
            # The wrapper's signature is determined by the Schedule.
            # It calls the decorated function and updates the account states.
            @mywrap(func)
            def wrapper(step: 'TimelineStep', /):
                date_ = step.date
                if date_ < start:
                    # Too soon.
                    return None
                from_account = step.states[from_]
                from_value = step.values[from_]
                to_account = step.states[to_]
                to_value = step.values[to_]
                update = func(date, from_value, to_value,
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
