'''
Transaction definitions. Similar to event definitions, but for transactions,
with two accounts and an amount.
'''


from datetime import datetime

from pplt.account import AccountValue
from pplt.decorators import transaction


@transaction()
def transfer(date: datetime, from_state: AccountValue, to_state: AccountValue, /,
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
