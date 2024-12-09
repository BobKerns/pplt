'''
Tests for the time module.
'''

from datetime import date, timedelta
from itertools import islice

from pplt.time import (
    days_per_month, next_month, months, months_str,
    parse_month, unparse_month, parse_end
)

def test_days_per_month():
    assert days_per_month(1) == 31
    assert days_per_month(2) == (28 if date.today().year % 4 else 29)
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
    assert days_per_month(date(2021, 2, 1)) == 28
    assert days_per_month(date(2020, 2, 1)) == 29

def test_next_month():
    nm =  next_month()
    today = date.today()
    assert nm >= today
    assert nm.day == 1
    assert nm - today <= timedelta(days=days_per_month(today))

def test_months():
    start = date(2021, 1, 1)
    previous = date(2020, 12, 1)
    ms = months(start)
    for _ in range(120):
        m = next(ms)
        assert m.day == 1
        assert m - previous == timedelta(days=days_per_month(previous))
        previous = m

def test_months_str():
    start = date(2021, 1, 1)
    ms = months_str(start)
    assert list(islice(ms, 0, 12)) == [
        '21/01', '21/02', '21/03', '21/04', '21/05', '21/06',
        '21/07', '21/08', '21/09', '21/10', '21/11', '21/12'
    ]
    
def test_parse_month():
    assert parse_month('21/01') == date(2021, 1, 1)
    assert parse_month('21/02') == date(2021, 2, 1)
    assert parse_month('21/03') == date(2021, 3, 1)
    assert parse_month('21/04') == date(2021, 4, 1)
    assert parse_month('21/05') == date(2021, 5, 1)
    assert parse_month('21/06') == date(2021, 6, 1)
    assert parse_month('21/07') == date(2021, 7, 1)
    assert parse_month('21/08') == date(2021, 8, 1)
    assert parse_month('21/09') == date(2021, 9, 1)
    assert parse_month('21/10') == date(2021, 10, 1)
    assert parse_month('21/11') == date(2021, 11, 1)
    assert parse_month('21/12') == date(2021, 12, 1)
    
def test_unparse_month():
    assert unparse_month(date(2021, 1, 1)) == '21/01'
    assert unparse_month(date(2021, 2, 1)) == '21/02'
    assert unparse_month(date(2021, 3, 1)) == '21/03'
    assert unparse_month(date(2021, 4, 1)) == '21/04'
    assert unparse_month(date(2021, 5, 1)) == '21/05'
    assert unparse_month(date(2021, 6, 1)) == '21/06'
    assert unparse_month(date(2021, 7, 1)) == '21/07'
    assert unparse_month(date(2021, 8, 1)) == '21/08'
    assert unparse_month(date(2021, 9, 1)) == '21/09'
    assert unparse_month(date(2021, 10, 1)) == '21/10'
    assert unparse_month(date(2021, 11, 1)) == '21/11'
    assert unparse_month(date(2021, 12, 1)) == '21/12'
    

def test_parse_end():
    assert parse_end('21/01', '21/01') == 0
    assert parse_end('21/01', '21/02') == 1
    assert parse_end('21/01', '21/03') == 2
    assert parse_end('21/01', '22/01') == 12
    assert parse_end('21/01', '22/02') == 13
    assert parse_end('21/12', '22/01') == 1
    