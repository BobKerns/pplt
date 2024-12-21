'''
Decorators for the pplt package.
'''

from abc import abstractmethod
from collections.abc import Callable
from datetime import date
from types import NoneType
from typing import Any, Protocol, TYPE_CHECKING

from pplt.dates import next_month, parse_month
from pplt.period import Periodic, PeriodUnit
if TYPE_CHECKING:
    from pplt.account import AccountValue, AccountUpdate
    from pplt.timeline import (
        TimelineStep,
        TimelineUpdateHandler,
    )

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
                 state: 'AccountValue', /,
                 **kwargs: Any) -> 'AccountUpdate':
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
    def __call__(self, name: str, start: date|None=None, /,
                 **kwargs: Any) -> 'TimelineUpdateHandler':
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
    __name__: str


def mywrap(func:  Callable[..., Any]) -> Callable[..., Any]:
    '''
    Wrap a function without setting the signature.
    '''
    def decorate[T: Callable[..., Any]](wrapper: T) -> T:
        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__
        wrapper.__qualname__ = func.__qualname__
        wrapper.__module__ = func.__module__
        return wrapper
    return decorate

def event(period: tuple[int, PeriodUnit]|None=None):
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

    def decorator(func: EventHandler) -> EventSpecifier:
        # This is what you call to create the event handler to add to the schedule.
        outer_period = period
        @mywrap(func)
        def for_account(name: str, start: date|str|None=None, /,
                        period: tuple[int, PeriodUnit]|None = outer_period,
                        **kwargs: Any) -> 'TimelineUpdateHandler':
            start = parse_month(start) if start else next_month()

            if isinstance(period, tuple):
                n, units = period
                periodic: Periodic|NoneType = Periodic(start, n, units)
            else:
                periodic: Periodic|None = None
            dates = iter(periodic) if periodic else iter([start])
            # The wrapper's signature is determined by the Timeline.
            # It calls the decorated function and updates the account state.
            @mywrap(func)
            def wrapper(step: 'TimelineStep', /) -> None:
                date_ = step.date
                if date_ < start:
                    # Too soon.
                    return None
                account = step.states[name]
                value = step.values[name]
                update = func(date_, value, **kwargs)
                match update:
                    case None:
                        pass
                    case str():
                        raise ValueError(f'Invalid update: {update} for event')
                    case _:
                        account.send(float(update))
                # Re-add the event if it is recurring.
                if period:
                    step.schedule.add(next(dates), wrapper)
            wrapper.period = periodic
            wrapper.fn = for_account
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
                 from_state: 'AccountValue',
                 to_state: 'AccountValue',
                 /,
                 amount: float) -> float:
        '''
        The signature for the user-defined transaction functions, before applying
        the decorator.

        date_: date
            The date of the transaction.
        from_state: AccountState
            The current state of the 'from' account.
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
    def __call__(self, from_: str, to_: str, start: date|None=None, /,
                 **kwargs: Any) -> 'TimelineUpdateHandler':
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

def transaction(period: tuple[int, PeriodUnit]|None=None):
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

    def decorator(func: TransactionHandler) -> TransactionSpecifier:
        # This is what you call to create the event handler to add to the schedule.
        @mywrap(func)
        def for_accounts(from_: str, to_: str, start: date|str|None=None, /,
                         **kwargs: Any) -> 'TimelineUpdateHandler':
            start = parse_month(start) if start else next_month()
            if isinstance(period, tuple):
                n, units = period
                periodic: Periodic|NoneType = Periodic(start, n, units)
            else:
                periodic: Periodic|None = None
            dates = iter(periodic) if periodic else iter([start])
            # The wrapper's signature is determined by the Schedule.
            # It calls the decorated function and updates the account states.
            @mywrap(func)
            def wrapper(step: 'TimelineStep', /) -> None:
                date_ = step.date
                if date_ < start:
                    # Too soon.
                    return None
                from_account = step.states[from_]
                from_value = step.values[from_]
                to_account = step.states[to_]
                to_value = step.values[to_]
                update = func(date_, from_value, to_value,
                              **kwargs)
                from_account.send(-update)
                to_account.send(update)
                # Re-add the event if it is recurring.
                if periodic:
                    step.schedule.add(next(dates), wrapper)
            return wrapper
            wrapper.period = period
            wrapper.fn = for_account
        return for_accounts
    return decorator
