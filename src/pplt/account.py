'''
Accounts
'''

from collections.abc import Generator, Iterable
from typing import Any, Literal, NoReturn, cast, overload
from functools import total_ordering

from rich.table import Table as RichTable
from rich.console import Console, ConsoleOptions, RenderResult, RenderableType
from rich.measure import Measurement

from pplt.utils import console
from pplt.currency import Currency, CURRENCIES


DEFAULT_CURRENCY = CURRENCIES['USD']
'''
The default currency for accounts.
'''

COLOR=True
'''
Use color to print account balances.
'''

type AccountStatus = Literal['open', 'closed', 'future']
'''
The status of an account. An account can be open, closed, or future.
A `future` account is an account that will be open in the future.
'''

def valid_account_status(status: str) -> AccountStatus:
    '''
    Cast a string to an `AccountStatus`.
    '''
    if status not in ('open', 'closed', 'future'):
        raise ValueError(f'Invalid account status: {status}')
    return status


@total_ordering
class AccountValue:
    '''
    An `AccountValue` is a number with a status, used both to represent the
    initial state of an account, and subsequent states. It represents what can change
    in an account: the balance and the status.

    `AccountValue` objects can be treated as floats, and can be compared to other
    `AccountValue` objects or floats. They can also be added or subtracted from
    other `AccountValue` objects or floats.

    You can multiply or divide a `AccountValue` object by a float or int, but you
    can't multiply or divide two `AccountValue` objects.
    '''

    __match_args__ = ('amount', 'status')

    __amount: float
    @property
    def amount(self) -> float:
        return self.__amount


    __currency: Currency
    @property
    def currency(self) -> Currency:
        return self.__currency


    __status: AccountStatus = 'open'
    @property
    def status(self) -> AccountStatus:
        return self.__status


    def __init__(self,
                 amount: float=0.0,
                 status: AccountStatus = 'open',
                 currency: Currency = DEFAULT_CURRENCY):
        if status not in ('open', 'closed', 'future'):
            raise ValueError(f'Invalid status: {status}')
        self.__status = status
        self.__amount = float(amount)
        self.__currency = currency


    def __format__(self, format_spec: str):
        match self.status:
            case 'open':
                if COLOR:
                    with console.capture() as capture_:  # type: ignore
                        fmt = self.currency.format
                        sym = self.currency.symbol
                        console.print(f'{sym} {self.amount:{fmt}}', style='green')
                    return capture_.get()
                return f'{self.currency.symbol} {self.amount:{self.currency.format}}'
            case _:
                return '--'

    def __bool__(self):
        return self.status == 'open' and self.amount != 0.0

    def __float__(self):
        if self.status != 'open':
            return 0.0
        return float(self.amount) or 0.0

    def __int__(self):
        return int(self.amount)

    def __complex__(self):
        return complex(self.amount)

    def __eq__(self, value: Any):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(amount) | int(amount) | AccountValue(amount, 'open'):
                return self.amount == amount
            case _:
                # Handle pytest.approx!
                 return value == self.amount

    def __hash__(self):
        return hash((self.amount, self.status))

    def __lt__(self, value: Any):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(amount) | int(amount) | AccountValue(amount, 'open'):
                return self.amount < amount
            case _:
                return NotImplemented

    def __add__(self, value: Any):
        if self.status != 'open':
            return self
        match value:
            case float(amount) | int(amount) | AccountValue(amount, 'open'):
                return AccountValue(self.amount + float(amount) or 0.0,
                                    'open',
                                    self.currency)
            case _:
                return NotImplemented

    def __radd__(self, value: Any):
        return self + value

    def __sub__(self, value: Any):
        if self.status != 'open':
            return self
        match value:
            case float(amount) | int(amount) | AccountValue(amount, 'open'):
                return AccountValue(self.amount - float(amount)  or 0.0,
                                    'open',
                                    self.currency)
            case _:
                return NotImplemented

    def __rsub__(self, value: Any):
        return -self + value

    def __mul__(self, value: Any):
        if self.status != 'open':
            return self
        match value:
            case float(amount) | int(amount):
                ndigits = self.currency.decimal_digits
                amt = self.amount * float(amount) or 0.0
                amt = round(amt, ndigits)
                return AccountValue(amt, 'open', self.currency)
            case _:
                return NotImplemented

    def __rmul__(self, value: Any):
        return self * value

    def __neg__(self) -> 'AccountValue':
        if self.status != 'open':
            return self
        return AccountValue(-self.amount or 0.0, 'open', self.currency)

    def __truediv__(self, value: Any):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(amount) | int(amount):
                ndigits = self.currency.decimal_digits
                amt = self.amount / float(amount)
                amt= round(amt or 0.0, ndigits)
                return AccountValue(amt, 'open', self.currency)
            case _:
                return NotImplemented

    def __repr__(self):
        match self.status:
            case 'open':
                return f'<value {self.currency.symbol} {self.amount} {self.currency}>'
            case _:
                return f'<value {self.status}>'

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        def show_amt(style: str):
            fmt = self.currency.format
            sym = self.currency.symbol
            grid = RichTable.grid(expand=True)
            grid.add_column(max_width=1)
            amount = f'{self.amount:{fmt}}'
            grid.add_column(justify='right', max_width=len(amount))
            grid.add_row(f'[{style}]{sym}[/]', f'[{style}]{amount}[/]')
            return grid
        match self.status:
            case 'open' if self.amount >= 0:
                yield show_amt('blue')
            case 'open':
                yield show_amt('red')
            case _:
                return '[grey]--[/]'

    def __rich_measure__(self, console: Console, options: ConsoleOptions):
        match self.status:
            case 'open':
                fmt = self.currency.format
                sym = self.currency.symbol
                vlen = len(f'{self.amount:{fmt}}') + len(sym)
            case _:
                vlen = 2
        return Measurement(vlen, vlen)


type AccountUpdate = AccountValue|float|AccountStatus|None

class Account(AccountValue):
    '''
    Abstract Account. An account is just a pool of money with a name and a status.

    The account is iterable, yielding `AccountState` objects. The `AccountState` object
    contains the account, the balance, and the status, and can usually be treated as a
    `float`.
    '''
    name: str
    categories: list[str]

    @overload
    def __init__(self,
                 name: str,
                 value: AccountValue,
                 /, *,
                 categories: list[str]|None=None,
                 ) -> None: ...
    @overload
    def __init__(self,
                 name: str,
                 amount: float=0.0,
                 status: AccountStatus='open',
                 currency: Currency=DEFAULT_CURRENCY,
                 /, *,
                 categories: list[str]|None=None,
                 ) -> None: ...
    def __init__(self,
                 name: str,
                 amount: float|AccountValue=0.0,
                 status: AccountStatus='open',
                 currency: Currency=DEFAULT_CURRENCY,
                 /, *,
                 categories: list[str]|None=None,
                 ):
        if isinstance(amount, AccountValue):
            amount, status, currency = amount.amount, amount.status, amount.currency
        super().__init__(amount, status, currency)
        self.name = name
        self.categories = categories or []

    def __iter__(self)  -> Generator[AccountValue, AccountUpdate, NoReturn]:
        amount = self.amount
        status = self.status
        currency = self.currency
        while True:
            update = yield AccountValue(amount, status, currency)
            match update:
                case AccountValue(amount_, status_):
                    amount += amount_
                    status = status_
                case float(amount_):
                    match status:
                        case 'open':
                            amount += amount_
                        case 'future':
                            amount = amount_
                            status = 'open'
                        case _:
                            raise ValueError(f'Invalid update: {update}')
                case str(new_status):
                    status = cast(AccountStatus, new_status)
                case None:
                    pass
                case _:
                    raise ValueError(f'Invalid update: {update}')
            amount = round(amount or 0.0, currency.decimal_digits)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        grid= RichTable.grid(expand=False)
        grid.add_column(justify='left')
        grid.add_column(justify='left', style='bold')
        grid.add_column(justify='left')
        grid.add_column(justify='right')
        grid.add_column(justify='right')
        grid.add_column(justify='right')
        code = f' {self.currency}'
        match self.status:
            case 'open':
                grid.add_row('<acct ', self.name,  ': ', *cast(Iterable[RenderableType], super().__rich_console__(console, options)),
                             code, '>')
            case _:
                grid.add_row('<acct ', self.name,  ': ', self.status, code, '>')
        yield grid

    def __repr__(self):
        match self.status:
            case 'open':
                return f'<acct {self.name}: {self.currency.symbol}{self.amount}, {self.currency}>'
            case _:
                return f'<acct {self.name}: {self.status}, {self.currency}>'

    def __str__(self):
        return self.__repr__()
