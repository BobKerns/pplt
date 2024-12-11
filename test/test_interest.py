'''
Tests for the interest module.
'''

from pytest import approx

from pplt.interest import (
    daily_pct, daily_rate, monthly_pct,
    monthly_rate, quarterly_pct, quarterly_rate,
)

def test_monthly_rate():
    assert 1_000*(1+monthly_rate(0.10))**12 == approx(1_100.0)

def test_monthly_pct():
    assert 1_000*(1+monthly_pct(10)/100)**12 == approx(1_100.0)

def test_monthly_rate_zero():
    assert monthly_rate(0) == approx(0)

def test_daily_rate():
    assert 1_000*(1+daily_rate(0.10))**365.25 == approx(1_100.0)

def test_daily_pct():
    assert 1_000*(1+daily_pct(10)/100)**365.25 == approx(1_100.0)

def test_quarterly_rate():
    assert 1_000*(1+quarterly_rate(0.10))**4 == approx(1_100.0)

def test_quarterly_pct():
    assert 1_000*(1+quarterly_pct(10)/100)**4 == approx(1_100.0)
