'''
Transaction definitions. Similar to event definitions, but for transactions,
with two accounts and an amount.
'''


from datetime import date

from pplt.account import AccountValue
from pplt.decorators import transaction


@transaction()
def transfer(date_: date, from_state: AccountValue, to_state: AccountValue, /,
            amount: float):
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
    return amount
