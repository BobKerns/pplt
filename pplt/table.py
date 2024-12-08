'''
Terminal table printer
'''

from collections.abc import Collection
from datetime import datetime
from itertools import tee

from pplt.time import parse_end, unparse_month
from pplt.timeline import TimelineSeries
from pplt.utils import dict_split


def table(timeline: TimelineSeries,
          include: Collection[str]=(),
          exclude: Collection[str]=(),
          end: int|str|datetime=12,
          ):
    """
    Print a table of values.

    PARAMETERS
    ----------
    timeline: Iterator[dict[str, float]]
        A timeline of values.
    include: Collection[str]
        The labels to include.
    exclude: Collection[str]
        The labels to exclude.
    end: int|str|datetime
        The ending date, or the number of months to print.
    """
    timeline, body = tee(timeline, 2)
    values = dict_split(timeline)
    time = values.pop('TIME')
    start = next(values.pop('START'))
    del values['ACCOUNTS']
    end = parse_end(start, end)
    labels = values.keys()
    cols = list(labels)

    # Calculate the column widths.
    widths = {c: len(c) for c in labels}
    if not include:
        include = labels
    for row in range(end):
        for  col, v in values.items():
            if col in include and col not in exclude:
                v = next(v)
                widths[col] = max(widths[col], len(f'{int(v):,d}'))

    # Print the header.
    print('Month', end=' ')
    last = cols[-1]
    for col in cols:
        sep = '\n' if col == last else ' '
        w = widths[col]+1
        print(f'{col:^{w}}', end=sep)
    print('-----', end=' ')
    for col in cols:
        sep = '\n' if col == last else ' '
        widths[col]+1
        print('-' * w, end=sep)

    # Go through the rows and print the values.
    values = dict_split(body)
    time = values.pop('TIME')
    for row in range(end):
        print(unparse_month(next(time)), end=' ')
        for col in cols:
            v = int(next(values[col]))
            sep = '\n' if col == last else ' '
            print(f'${v:>{widths[col]},d}', end=sep)
    return None
