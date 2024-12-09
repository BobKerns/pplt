'''
Accounts
'''

from typing import Literal
from functools import total_ordering

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

    __balance: float
    @property
    def balance(self) -> float:
        return self.__balance

    __status: str = 'open'
    @property
    def status(self) -> str:
        return self.__status

    def __init__(self,
                 balance: float=0.0,
                 status: AccountStatus = 'open'):
        if status not in ('open', 'closed', 'future'):
            raise ValueError(f'Invalid status: {status}')
        self.__status = status
        self.__balance = balance

    def __format__(self, format_spec):
        match self.status:
            case 'open':
                return f'{self.balance:{format_spec}}'
            case _:
                return '--'

    def __bool__(self):
        return self.status == 'open' and self.balance != 0.0

    def __float__(self):
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
                return self.balance + float(balance)
            case _:
                return

    def __radd__(self, value):
        return self + value

    def __sub__(self, value):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(balance) | int(balance) | AccountValue(balance, 'open'):
                return self.balance - float(balance)
            case _:
                return NotImplemented

    def __rsub__(self, value):
        return -self + value

    def __mul__(self, value):
        if self.status != 'open':
            return NotImplemented
        match value:
            case float(balance) | int(balance):
                return self.balance * float(balance)
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
                self.balance / float(balance)
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
            update = yield AccountValue(self, balance, status)
            match update:
                case AccountValue(_, balance, status):
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

