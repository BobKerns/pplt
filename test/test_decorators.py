'''
Test cases for decorators.py
'''

from datetime import date
from inspect import signature, Parameter, _empty
from typing import Optional

from pytest import approx

from pplt.dates import parse_month
from pplt.decorators import event, transaction
from pplt.account import Account, AccountValue
from pplt.schedule import Schedule
from pplt.timeline import TimelineStep, TimelineAccountStates

class FakeAccount:
    value: float = 1000.00
    state: str = 'open'
    def __init__(self):
        self.value = 1000.00
        self.state = 'open'

    def __iter__(self):
        value = self.value
        state: open = 'open'
        while True:
            update = (yield AccountValue(value, state))
            match update:
                case AccountValue(_, amount, state_):
                    value = amount
                    state = state_
                case float(amount):
                    value += amount
                case str(state_):
                    state = state_
                case None:
                    pass
            self.value = value
            self.state = state

def make_step(*keys):
    accounts = {k: FakeAccount() for k in keys}
    states: TimelineAccountStates = {
        k: iter(a)
        for k, a in accounts.items()
    }
    values = {k: next(a) for k, a in states.items()}
    step = TimelineStep(parse_month('21/1'),
                        schedule=Schedule(),
                        states=states,
                        values=values)
    return accounts, step


def test_event_signatures():
    @event()
    def interest(date_: date, account: Account, state: AccountValue, /,
                rate: float):
        'Calculate interest on an account.'
        # Not the real monthly calculation!
        return state * rate

    sig1 = signature(interest)
    assert str(sig1.return_annotation) == 'TimelineUpdateHandler'
    assert sig1.parameters['name'].annotation is str
    assert sig1.parameters['name'].kind == Parameter.POSITIONAL_ONLY
    assert sig1.parameters['start'].annotation == Optional[date|str]
    assert sig1.parameters['name'].kind == Parameter.POSITIONAL_ONLY
    assert sig1.parameters['kwargs'].kind == Parameter.VAR_KEYWORD
    assert interest.__doc__ == 'Calculate interest on an account.'
    assert interest.__name__ == 'interest'

    f2 = interest('account', rate=0.01)
    sig2 = signature(f2)
    params = list(sig2.parameters)
    param0 = params[0]
    assert str(sig2.parameters[param0].annotation) == 'TimelineStep'
    assert sig2.parameters[param0].kind == Parameter.POSITIONAL_ONLY
    assert sig2.return_annotation == _empty
    assert f2.__doc__ == 'Calculate interest on an account.'
    assert f2.__name__ == 'interest'

def test_event_invocation():
    @event()
    def interest(date_: date, account: Account, state: AccountValue, /,
                rate: float):
        'Calculate interest on an account.'
        # Not the real monthly calculation!
        return state * rate

    accounts, step = make_step('account')
    f2 = interest('account', '21/1', rate=0.10)
    f2(step)
    assert accounts['account'].value == approx(1100.00)


def test_event_invocation_early():
    '''
    If the event is invoked before the date of the step, it should
    do nothing.
    '''
    @event()
    def interest(date_: date, account: Account, state: AccountValue, /,
                rate: float):
        'Calculate interest on an account.'
        # Not the real monthly calculation!
        return state * rate

    accounts, step = make_step('account')
    f2 = interest('account', '21/2', rate=0.10)
    f2(step)
    assert accounts['account'].value == 1000.00


def test_transaction():
    @transaction()
    def transfer(date: date, from_state: AccountValue, to_state: AccountValue, /,
                amount: float):
        return amount

    sig1 = signature(transfer)
    assert str(sig1.return_annotation) == 'TimelineUpdateHandler'
    params = list(sig1.parameters)
    assert sig1.parameters[params[0]].annotation is str
    assert sig1.parameters[params[0]].kind == Parameter.POSITIONAL_ONLY
    assert sig1.parameters[params[1]].annotation is str
    assert sig1.parameters[params[1]].kind == Parameter.POSITIONAL_ONLY
    assert sig1.parameters[params[2]].annotation == Optional[date|str]
    assert sig1.parameters[params[2]].kind == Parameter.POSITIONAL_ONLY
    assert sig1.parameters[params[3]].annotation == _empty
    assert sig1.parameters[params[3]].kind == Parameter.VAR_KEYWORD

    f2 = transfer('account1', 'account2', amount=0.01)
    sig2 = signature(f2)
    params = list(sig2.parameters)
    param0 = params[0]
    assert str(sig2.parameters[param0].annotation) == 'TimelineStep'
    assert sig2.parameters[param0].kind == Parameter.POSITIONAL_ONLY
    assert sig2.return_annotation == _empty

def test_transaction_invocation():
    @transaction()
    def transfer(date: date, from_state: AccountValue, to_state: AccountValue, /,
                amount: float):
        return amount

    accounts, step = make_step('account1', 'account2')
    f2 = transfer('account1', 'account2', '21/1', amount=100.00)
    f2(step)

    assert accounts['account1'].value == approx(1000.00 - 100.00)
    assert accounts['account2'].value == approx(1000.00 + 100.00)

def test_transaction_invocation_early():
    '''
    If the transaction is invoked before the date of the step, it should
    do nothing.
    '''
    @transaction()
    def transfer(date: date, from_state: AccountValue, to_state: AccountValue, /,
                amount: float):
        return amount

    accounts, step = make_step('account1', 'account2')
    f2 = transfer('account1', 'account2', '21/2', amount=100.00)
    f2(step)
    assert accounts['account1'].value == 1000.00
    assert accounts['account2'].value == 1000.00
