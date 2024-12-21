'''
Test cases for schedule.py
'''

from collections import Counter
from datetime import date
from typing import Literal

import pytest

from pplt.timeline import (
    TimelineStep, TimelineAccountStates, CurrentAccountValues,
)
from pplt.schedule import Schedule
from pplt.dates import parse_month

type ScheduleTestStep = tuple[Literal['run'], date|str, dict[date|str, int]] \
    | Literal['reset'] \
    | tuple[Literal['add'], date|str] \
    | tuple[Literal['fail'], Literal['add', 'run'], date|str]

type ScheduleTest = tuple[ScheduleTestStep, ...]

class CallHandler:
    counts: Counter[date]
    __name__ = 'CallHandler'
    def __init__(self):
        self.counts = Counter()
    def __call__(self, step: TimelineStep):
        assert isinstance(step, TimelineStep)
        date_ = step.date
        assert isinstance(date_, date)
        assert date_.day == 1
        self.counts[date_] += 1


tests: list[ScheduleTest] = [
    (("run", '22/01', {}),),
    (("add", '22/01'),
     ("run", '22/01', {"22/01": 1}),),
    (("add", '22/01'),
     ("add", '22/01'),
     ("run", '22/01', {"22/01": 2}),),
    (('run', '22/01', {}),
     ('fail', 'add', '22/01'),),
    (('run', '22/01', {}),
    ('fail', 'run', '21/01'),),
    (('add', '22/01'),
     ('add', '22/03'),
     ('add', '22/04'),
     ('run', '22/01', {"22/01": 1}),
     ('run', '22/02', {"22/01": 1}),
     ('run', '22/03', {"22/01": 1, '22/03': 1})),
    (('add', '22/01'),
     ('add', '22/03'),
     ('run', '22/01', {"22/01": 1}),
     ('add', '22/04'),
     ('run', '22/02', {"22/01": 1}),
     ('run', '22/03', {"22/01": 1, '22/03': 1})),
    (('add', '22/01'),
     ('add', '22/04'),
     ('run', '22/01', {"22/01": 1}),
     ('add', '22/03'),
     ('run', '22/02', {"22/01": 1}),
     ('run', '22/03', {"22/01": 1, '22/03': 1})),
    (('add', '22/01'),
     ('run', '22/01', {"22/01": 1}),
     ('add', '22/04'),
     ('add', '22/03'),
     ('run', '22/02', {"22/01": 1}),
     ('run', '22/03', {"22/01": 1, '22/03': 1})),
]
@pytest.mark.parametrize('sequence', tests)
def test_schedule(sequence: ScheduleTest):
    sch = Schedule()
    count = CallHandler()
    counts: Counter[date] = count.counts
    states: TimelineAccountStates = {}
    values: CurrentAccountValues = {}
    for entry in sequence:
        match entry:
            case ('run', date_, expected):
                date_ = parse_month(date_)
                expected = {
                    parse_month(d): c
                    for d, c in expected.items()
                }
                step = TimelineStep(date_, sch, states, values)
                for step_date, f in sch.run(date_):
                    assert step_date == date_
                    f(step)
                assert count.counts == expected
            case 'reset':
                counts.clear()
            case ('add', str(date_)):
                sch.add(date_, count)
            case ('fail', 'add', str(date_)):
                with pytest.raises(ValueError):
                    sch.add(date_, count)
            case ('fail', 'run', str(date_)):
                with pytest.raises(ValueError):
                    for _, _ in sch.run(parse_month(date_)):
                        pass
            case _: # pragma: no cover # type: ignore
                raise ValueError(f'Invalid test step: {entry}')
