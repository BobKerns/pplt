'''
Tests for the table module.
'''

from datetime import date
from typing import Any

import pytest

from pplt.dates import parse_month
from pplt.rich_tables import Table

def r(month:str, *v: float) -> tuple[date, *tuple[float, ...]]:
    '''
    Create a row.
    '''
    return (parse_month(month), *v)

default_labels = ['Month', 'Income', 'Expenses']
default_formats = ['%yy/%mm', '>,.2f', '>,.2f']

def t(*values: tuple[Any, ...],
      labels: list[str]=default_labels,
      formats: list[str] = default_formats,
      ncols: int|None=None, ) -> Table:
    '''
    Build a test table.
    '''
    if ncols is None:
        ncols = len(values[0])
    return Table(labels=labels,
                 formats=formats,
                 ncols=ncols,
                 end=len(values),
                 values=list(values))

base_data = [
        r('21/01', 1000.00, 500.00, 1500.00),
        r('21/02', 2000.00, 500.00, 1500.00),
        r('21/03', 3000.00, 500.00, 1500.00),
        r('21/04', 4000.00, 500.00, 1500.00),
        r('21/05', 5000.00, 500.00, 1500.00),
        r('21/06', 6000.00, 500.00, 1500.00),
        r('21/07', 7000.00, 500.00, 1500.00),
        r('21/08', 8000.00, 500.00, 1500.00),
        r('21/09', 9000.00, 500.00, 1500.00),
        r('21/10', 10000.00, 500.00, 1500.00),
        r('21/11', 11000.00, 500.00, 1500.00),
        r('21/12', 12000.00, 500.00, 1500.00),
]

def c(values: list[tuple[Any, ...]],
      slice_: slice) -> list[tuple[Any, ...]]:
    '''
    Slice by columns
    '''
    return list(map(lambda r: r[slice_], values))

base_table = t(
        *base_data,
        labels=['Month', 'Income', 'Expenses',], formats=['%yy/%mm'], ncols=4,
    )

@pytest.fixture(scope='module')
def simple_table()  -> Table:
    return base_table

def test_table(simple_table: Table):
    t = simple_table
    assert t.labels == ['Month', 'Income', 'Expenses', 'Series-4']
    assert t.formats == ['%yy/%mm', '>,.2f', '>,.2f', '>,.2f']
    assert t.ncols == 4
    assert t.end == 12

@pytest.mark.parametrize('i,v', [
    (0,     r('21/01', 1000.00, 500.00, 1500.00)),
    (1,     r('21/02', 2000.00, 500.00, 1500.00)),
    (2,     r('21/03', 3000.00, 500.00, 1500.00)),
    (3,     r('21/04', 4000.00, 500.00, 1500.00)),
    (4,     r('21/05', 5000.00, 500.00, 1500.00)),
    (5,     r('21/06', 6000.00, 500.00, 1500.00)),
    (6,     r('21/07', 7000.00, 500.00, 1500.00)),
    (7,     r('21/08', 8000.00, 500.00, 1500.00)),
    (8,     r('21/09', 9000.00, 500.00, 1500.00)),
    (9,     r('21/10', 10000.00, 500.00, 1500.00)),
    (10,    r('21/11', 11000.00, 500.00, 1500.00)),
    (11,    r('21/12', 12000.00, 500.00, 1500.00)),
    (slice(None), base_table),
    (slice(0, 3), t(*base_data[:3])),
    ((slice(0, 3), slice(0, 2)), t(*c(base_data[:3], slice(0, 2)))),
])
def test_table_subscription(i: Any, v: Any, simple_table: Table):
    t = simple_table
    assert t[i] == v