'''
Tests for the time module.
'''

from datetime import datetime, timedelta
from itertools import islice

from pplt.time import days_per_month, next_month, months, months_str

def test__days_per_month():
    assert days_per_month(1) == 31
    assert days_per_month(2) == (28 if datetime.now().year % 4 else 29)
    assert days_per_month(3) == 31
    assert days_per_month(4) == 30
    assert days_per_month(5) == 31
    assert days_per_month(6) == 30
    assert days_per_month(7) == 31
    assert days_per_month(8) == 31
    assert days_per_month(9) == 30
    assert days_per_month(10) == 31
    assert days_per_month(11) == 30
    assert days_per_month(12) == 31
    assert days_per_month(datetime(2021, 2, 1)) == 28
    assert days_per_month(datetime(2020, 2, 1)) == 29

def test__next_month():
    nm =  next_month()
    today = datetime.today()
    assert nm >= today
    assert nm.day == 1
    assert nm.hour == 0
    assert nm.minute == 0
    assert nm.second == 0
    assert nm.microsecond == 0
    assert nm - today <= timedelta(days=days_per_month(today))

def test__months():
    start = datetime(2021, 1, 1)
    previous = datetime(2020, 12, 1)
    ms = months(start)
    for i in range(120):
        m = next(ms)
        assert m.day == 1
        assert m.hour == 0
        assert m.minute == 0
        assert m.second == 0
        assert m.microsecond == 0
        assert m - previous == timedelta(days=days_per_month(previous))
        previous = m

def test_months_str():
    start = datetime(2021, 1, 1)
    ms = months_str(start)
    assert list(islice(ms, 0, 12)) == [
        '21/01', '21/02', '21/03', '21/04', '21/05', '21/06',
        '21/07', '21/08', '21/09', '21/10', '21/11', '21/12'
    ]