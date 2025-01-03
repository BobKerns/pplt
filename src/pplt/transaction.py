'''
Transaction definitions. Similar to event definitions, but for transactions,
with two accounts and an amount.
'''


from datetime import date
from typing import cast

from pplt.account import AccountValue
from pplt.decorators import transaction


@transaction(description=['{amount}'])
def transfer[V: float|AccountValue](
    date_: date, from_state: AccountValue, to_state: AccountValue, /,
    amount: V,
    from_min: V = 0, to_max: V = float('inf'),
    ) -> V:
    """
    Transfer a fixed amount of money between accounts.

    PARAMETERS
    ----------
    date_: datetime
        The date of the transaction.
    from_state: AccountState
        The state of the account to transfer from.
    to_state: AccountState
        The state of the account to transfer to.
    amount: float
        The amount to transfer.

    RETURNS
    -------
    amount: float
        The amount transferred.
    """
    if from_state < from_min:
        raise ValueError(f'Amount {from_state} less than minimum {from_min}')
    to = to_state + amount
    if to > to_max:
        return cast(V, -to_state or 0.0)
    return amount
