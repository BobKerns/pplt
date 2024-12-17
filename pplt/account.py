'''
Accounts
'''

from typing import ClassVar, Literal
from functools import total_ordering

from rich.table import Table as RichTable
from rich.console import Console, ConsoleOptions, RenderResult
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

    __match_args__: ClassVar[tuple[str, ...]] = ('balance', 'status')

    __balance: float
    @property
    def balance(self) -> float:
        return self.__balance


    __currency: Currency
    @property
    def currency(self) -> Currency:
        return self.__currency


    __status: str = 'open'
    @property
    def status(self) -> str:
        return self.__status


    def __init__(self,
                 balance: float=0.0,
                 status: AccountStatus = 'open',
                 currency: Currency = DEFAULT_CURRENCY):
        if status not in ('open', 'closed', 'future'):
            raise ValueError(f'Invalid status: {status}')
        self.__status = status
        self.__balance = float(balance)
        self.__currency = currency


    def __format__(self, format_spec):
        match self.status:
            case 'open':
                if COLOR:
                    with console.capture() as capture_:  # type: ignore
                        fmt = self.currency.format
                        sym = self.currency.symbol
                        console.print(f'{sym} {self.balance:{fmt}}', style='green')
                    return capture_.get()
            case _:
                return '--'

    def __bool__(self):
        return self.status == 'open' and self.balance != 0.0

    def __float__(self):
        if self.status != 'open':
            return 0.0
        return float(self.balance)

    def __int__(self):
        return int(self.balance)

    def __complex__(self):
        return complex(self.balance)

    def __eq__(self, value):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(balance) | int(balance) | AccountValue(balance, 'open'):
                return self.balance == balance
            case _:
                return NotImplemented

    def __hash__(self):
        return hash((self.account, self.balance, self.status))

    def __lt__(self, value):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(balance) | int(balance) | AccountValue(balance, 'open'):
                return self.balance < balance
            case _:
                return NotImplemented

    def __add__(self, value):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(balance) | int(balance) | AccountValue(balance, 'open'):
                return AccountValue(self.balance + float(balance), 'open', self.currency)
            case _:
                return NotImplemented

    def __radd__(self, value):
        return self + value

    def __sub__(self, value):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(balance) | int(balance) | AccountValue(balance, 'open'):
                return AccountValue(self.balance - float(balance), 'open', self.currency)
            case _:
                return NotImplemented

    def __rsub__(self, value):
        return -self + value

    def __mul__(self, value):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(balance) | int(balance):
                return AccountValue(self.balance * float(balance), 'open', self.currency)
            case _:
                return NotImplemented

    def __rmul__(self, value):
        return self * value

    def __neg__(self):  # -self
        if self.status != 'open':
            return NotImplemented
        return -self.balance

    def __truediv__(self, value):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(balance) | int(balance):
                return AccountValue(self.balance / float(balance), 'open', self.currency)
            case _:
                return NotImplemented

    def __pow__(self, value):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(balance) | int(balance):
                return self.balance ** float(balance)
            case _:
                return NotImplemented

    def __repr__(self):
        match self.status:
            case 'open':
                return f'<value {self.currency.symbol} {self.balance} {self.currency}>'
            case _:
                return f'<value {self.status}>'

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        def balance(style: str):
            fmt = self.currency.format
            sym = self.currency.symbol
            grid = RichTable.grid(expand=False)
            grid.add_column(max_width=1)
            balance = f'{self.balance:{fmt}}'
            grid.add_column(justify='right', max_width=len(balance))
            grid.add_row(f'[{style}]{sym}[/]', f'[{style}]{balance}[/]')
            return grid
        match self.status:
            case 'open' if self.balance >= 0:
                yield balance('blue')
            case 'open':
                yield balance('red')
            case _:
                return '[grey]--[/]'

    def __rich_measure__(self, console: Console, options: ConsoleOptions):
        match self.status:
            case 'open':
                fmt = self.currency.format
                sym = self.currency.symbol
                vlen = len(f'{self.balance:{fmt}}') + len(sym)
            case '_':
                vlen = 2
        return Measurement(vlen, vlen)

class Account(AccountValue):
    '''
    Abstract Account. An account is just a pool of money with a name and a status.

    The account is iterable, yielding `AccountState` objects. The `AccountState` object
    contains the account, the balance, and the status, and can usually be treated as a
    `float`.
    '''
    name: str

    def __init__(self,
                 name: str,
                 balance: float=0.0,
                 status: AccountStatus='open'
                 ):
        super().__init__(balance, status)
        self.name = name

    def __iter__(self):
        balance = self.balance
        status = self.status
        while True:
            update = yield AccountValue(balance, status)
            match update:
                case AccountValue(balance, status):
                    balance = balance
                    status = status
                case float(amount):
                    match status:
                        case 'open':
                            balance += amount
                        case 'future':
                            balance = amount
                            status = 'open'
                        case _:
                            raise ValueError(f'Invalid update: {update}')
                    balance += amount
                case str(new_status):
                    status = new_status
                case None:
                    pass
                case _:
                    raise ValueError(f'Invalid update: {update}')

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
                grid.add_row('<acct ', self.name,  ': ', *super().__rich_console__(console, options),
                             code, '>')
            case _:
                grid.add_row('<acct ', self.name,  ': ', self.status, code, '>')
        yield grid

    def __repr__(self):
        match self.status:
            case 'open':
                return f'<acct {self.name}: {self.currency.symbol}{self.balance}, {self.currency}>'
            case _:
                return f'<acct {self.name}: {self.status}, {self.currency}>'

    def __str__(self):
        return self.__repr()
