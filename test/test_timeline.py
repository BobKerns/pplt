'''
Tests of the timeline module.
'''

from pplt.dates import next_month
from pplt.timeline import timeline

def test_timeline_basic():
    tl = timeline()
    sch = tl.schedule
    assert tl is not None
    assert sch.events == []
    assert tl.start == next_month()
    series = iter(tl)
    step = next(series)
    assert step.date == tl.start
    assert step.schedule != sch
    assert step.schedule.events == []
    assert step.states == {}
    assert step.values == {}
