'''
Decorators for the pplt package.
'''

from abc import abstractmethod
from collections.abc import Callable, Iterator, Sequence
from datetime import date
import re
from typing import Any, Protocol, TYPE_CHECKING, cast

from rich.console import ConsoleRenderable, RenderableType, RichCast

from pplt.dates import next_month, parse_month, unparse_month
from pplt.period import Period, Periodic, PeriodUnit, valid_period_unit
import pplt.timeline_series as tl
from pplt.account import AccountValue, AccountUpdate
if TYPE_CHECKING:
    from pplt.timeline_series import (
        TimelineStep,
        UpdateHandler,
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

    __name__: str
    __doc__: str|None

class EventSpecifier(Protocol):
    '''
    The signature for the user-defined event functions, after applying
    the decorator but before being configured onto the schedule.
    '''
    @abstractmethod
    def __call__(self, name: str, start: date|None=None, /,
                 **kwargs: Any) -> 'UpdateHandler':
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


class Wrapper(tl.UpdateHandler):
    '''
    A wrapper for the user-supplied function that adds metadata, including
    scheduling information, and adapts it to the TimelineUpdateHandler protocol.
    '''

    start: date
    period: Periodic|None
    dates: Iterator[date]
    fn: Callable[..., Any]
    func: Callable[..., Any]
    accounts: RenderableType|list[RenderableType]
    description: RenderableType|list[RenderableType]
    __doc__: str|None
    __name__: str
    __qualname__: str
    __module__: str

    def __init__(self, func: Callable[..., Any],
                 fn: Callable[..., Any],
                 start: date,
                 period: Periodic|None,
                 accounts: str|list[str],
                 description: str|list[str],
                 /,
                 *args: Any,
                 **kwargs: Any,
                 ) -> None:
        self.func = func
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__
        self.__qualname__ = func.__qualname__
        self.__module__ = func.__module__
        self.fn = fn
        self.start = start
        self.period = period
        self.accounts = format_cell(accounts, *args, **kwargs)
        self.description = format_cell(description, *args, **kwargs)

    # The wrapper's signature is determined by the Schedule.
    # It calls the decorated function and updates the account states.
    @abstractmethod
    def __call__(self, step: 'TimelineStep', /) -> None:
        '''
        Call the user-supplied function and update the account state.
        '''
        ...

    def __repr__(self) -> str:
        return f'<{self.__name__} {unparse_month(self.start)} {self.accounts} {self.description}>'

class EventWrapper(Wrapper):
    '''
    A wrapper for the user-supplied event function that adds metadata, including
    scheduling information, and adapts it to the TimelineUpdateHandler protocol.
    '''

    account_name: str
    args: dict[str, Any]

    def __init__(self, func: Callable[..., Any],
                    fn: Callable[..., Any],
                    start: date,
                    period: Periodic|None,
                    description: str|list[str],
                    account_name: str,
                    /,
                    **kwargs: dict[str, Any]) -> None:
            super().__init__(func, fn, start, period, account_name, description,
                             account_name, **kwargs)
            self.account_name = account_name
            self.args = kwargs

    def __call__(self, step: 'TimelineStep', /) -> None:
        '''
        Call the user-supplied event function and update the account state.
        '''
        date_ = step.date
        if date_ < self.start:
            # Too soon.
            return None
        account = step.states[self.account_name]
        value = step.values[self.account_name]
        update = self.func(date_, value, **self.args)
        match update:
            case None:
                pass
            case str():
                raise ValueError(f'Invalid update: {update} for event')
            case _:
                nbalence= account.send(float(update))
                step.transactions.append((self.account_name, self, update, nbalence))

RE_VAR_REF = re.compile(r'^\{(\w+)\}$')
def format_cell(spec: str|list[str], /, *args: Any, **kwargs: Any,) -> RenderableType|list[RenderableType]:
    '''
    Format a cell in a table, replacing variables with values from the args.

    Handle rich text specially; it is not converted to a string if the spec is of the form `'{var}'`.
    '''
    if isinstance(spec, list):
        return [cast(RenderableType, format_cell(s, *args, **kwargs)) for s in spec]
    match RE_VAR_REF.match(spec):
        case None:
            return spec.format(*args, **kwargs)
        case m:
            var = m.group(1)
            if var not in kwargs:
                raise ValueError(f'Value not supplied: {var}. Variables: {", ".join(kwargs.keys()) or "None"}')
            val = kwargs[var]
            match val:
                case ConsoleRenderable() | RichCast() | str():
                    return val
                case _:
                    return str(val)

def event(period: tuple[int, PeriodUnit]|None=None,
          description: str|list[str] = ''):
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

        def for_account(name: str, start: date|str|None=None, /, *,
                        period: tuple[int, PeriodUnit]|None = outer_period,
                        **kwargs: Any) -> 'UpdateHandler':
            start = parse_month(start) if start else next_month()
            return EventWrapper(func, for_account, start,
                                parse_periodic(period or outer_period, start),
                                      description,
                                      name,
                                      **kwargs)
        for_account.__name__ = func.__name__
        for_account.__doc__ = func.__doc__
        return for_account
    return decorator


class TransactionHandler[V: float|AccountValue](Protocol):
    '''
    The signature for the user-defined transaction functions, before applying
    the decorator.
    '''
    @abstractmethod
    def __call__(self, date_: date,
                 from_state: 'AccountValue',
                 to_state: 'AccountValue',
                 /,
                 amount: V) -> V:
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
    __name__: str
    __doc__: str|None

class TransactionSpecifier(Protocol):
    '''
    The signature for the user-defined transaction functions, after applying
    the decorator but before being configured onto the schedule.
    '''
    @abstractmethod
    def __call__(self, from_: str, to_: str, start: date|None=None, /,
                 **kwargs: Any) -> 'UpdateHandler':
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


class TransactionWrapper(Wrapper):
    '''
    A wrapper for the user-supplied transaction function that adds metadata, including
    scheduling information, and adapts it to the TimelineUpdateHandler protocol.
    '''

    from_account: str
    to_account: str
    args: Any
    kwargs: dict[str, Any]

    def __init__(self, func: Callable[..., Any],
                    fn: Callable[..., Any],
                    start: date,
                    period: Periodic|None,
                    description: str|list[str],
                    from_account: str,
                    to_account: str,
                    /,
                    *args: Any,
                    amount: AccountValue|float = 0.0,
                    **kwargs: Any) -> None:
        accounts = [from_account, '→ ', to_account]
        amount = AccountValue(amount) if isinstance(amount, (float, int)) else amount
        super().__init__(func, fn, start, period, accounts, description,
                         from_account, to_account, amount=amount, **kwargs)
        self.from_account = from_account
        self.to_account = to_account
        self.args = args
        self.kwargs = dict(amount=amount, **kwargs)

    def __call__(self, step: 'TimelineStep', /) -> None:
        '''
        Call the user-supplied transaction function and update the account state.
        '''
        date_ = step.date
        if date_ < self.start:
            # Too soon.
            return None
        from_account = step.states[self.from_account]
        from_value = step.values[self.from_account]
        to_account = step.states[self.to_account]
        to_value = step.values[self.to_account]
        update = self.func(date_, from_value, to_value, **self.kwargs)
        nbalence = from_account.send(-update)
        step.transactions.append((self.from_account, self, -update, nbalence))
        nbalence = to_account.send(update)
        step.transactions.append((self.to_account, self, update, nbalence))


def parse_periodic(period: Period|Sequence[int|PeriodUnit]|str|None, start: date) -> Periodic|None:
    '''
    Create a periodic event.

    PARAMETERS
    ----------
    period: tuple[int, PeriodUnit]
        The period of the event.
    start: date
        The start date of the event.

    RETURNS
    -------
    Periodic
        The periodic event.
    '''
    match period:
        case Period():
            return Periodic(start, period.n, period.unit)
        case None:
            return None
        case str():
            return Periodic(start, 1, valid_period_unit(period))
        case tuple()|list(): # type: ignore
            n, unit = period
            assert isinstance(unit, str)
            assert isinstance(n, int)
            return Periodic(start, n, valid_period_unit(unit))
        case _: # type: ignore
            raise ValueError(f'Invalid period: {period} {type(period)}')


def transaction(period: tuple[int, PeriodUnit]|None=None,
                description: str|list[str] = ''):
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

    def decorator[V: float|AccountValue](func: TransactionHandler[V]) -> TransactionSpecifier:
        outer_period = period
        # This is what you call to create the event handler to add to the schedule.
        def for_accounts(from_: str, to_: str, start: date|str|None=None, /, *,
                        amount: float|AccountValue = 0.0,
                        period: Sequence[int|PeriodUnit]|str|Period|None = None,
                        **kwargs: Any) -> 'UpdateHandler':
            start = parse_month(start) if start else next_month()
            if isinstance(amount, float):
                amount = AccountValue(amount)
            return TransactionWrapper(func, for_accounts, start,
                                      parse_periodic(period or outer_period, start),
                                      description, from_, to_,
                                      amount=amount,
                                      **kwargs)
        for_accounts.__name__ = func.__name__
        for_accounts.__doc__ = func.__doc__
        return for_accounts
    return decorator
