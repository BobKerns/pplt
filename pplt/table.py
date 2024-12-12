'''
Terminal table printer
'''


from calendar import formatstring
from collections.abc import Collection, Iterable
from contextlib import suppress
from datetime import date
from itertools import chain, count, repeat, tee, islice

from pplt.dates import next_month, parse_end
from pplt.timeline import Timeline, TimelineSeries
from pplt.utils import take, attr_split, dict_split


def table(series: TimelineSeries|Timeline,
          include: Collection[str]=(),
          exclude: Collection[str]=(),
          end: int|str|date=12,
          ):
    """
    Print a table of values.

    PARAMETERS
    ----------
    timeline: Timeline|TimelineSeries
        A timeline of values.
    include: Collection[str]
        The labels to include.
    exclude: Collection[str]
        The labels to exclude.
    end: int|str|datetime
        The ending date, or the number of months to print.
    """
    match series:
        case Timeline():
            series = iter(series)
        case TimelineSeries():
            pass
    peek, header, body = tee(series, 3)
    date_, values = attr_split(header, 'date', 'values')
    start = next_month()
    with suppress(StopIteration):
        peek = next(peek)
        start = peek.date
    end = parse_end(start, end)
    values = dict_split(values)
    include = include or values.keys()
    to_show = {
        k:v
        for k, v in values.items()
        if k in include and k not in exclude
    }
    labels = to_show.keys()
    # Limit the date range in case the series has no other
    # values to show.
    series_table(islice(date_, 0, end), *to_show.values(),
                labels=('Months', *to_show.keys()),
                formats=('%y/%m',),
                prefixes=('',),
                end=end,
            )

def series_table(*series: Iterable[float],
                labels: Collection[str]=(),
                formats: Iterable[str] = (),
                prefixes: Iterable[str] = (),
                end: int=12,
                 ):
    '''
    Print a table of values from multiple series.
    '''
    return tuple_table(zip(*series),
                    labels=labels,
                    formats=formats,
                    prefixes=prefixes,
                    end=end,
                    )

def tuple_table(values: Iterable[tuple[float, ...]], /,
                    end: int=12,
                    labels: Collection[str]=(),
                    formats: Iterable[str] = (),
                    prefixes: Iterable[str] = (),
                    ):
    '''
    Print a table of values from multiple series packaged as an iterable of tuples.

    PARAMETERS
    ----------
    values: Iterable[tuple[float, ...]]
        An iterable of tuples of values.
    end: int
        The number of months to print.
    labels: Collection[str]
        The labels for the columns. Defaults to 'Series-1', 'Series-2', etc.
    '''

    # extend the sequence of labels if needed.
    labels = chain(labels, repeat(''))
    labels = (lbl if lbl else f'Series-{i+1}' for i, lbl in enumerate(labels))
    labels = (lbl.capitalize() if lbl.islower() else lbl for lbl in labels)

    formats = chain(formats, repeat('>{width}.2f'))
    prefixes = chain(prefixes, repeat('$'))

    # Limit the number of rows
    values = islice(values, 0, end)

    # Copy the various iterators to allow multiple passes.
    peek, head, body = tee(iter(values), 3)

    # Get the first row to determine the number of columns.
    first = next(peek)
    ncols = len(first)
    labels = take(ncols, labels)
    formats = take(ncols, formats)
    prefixes = take(ncols, prefixes)

    # Calculate the column widths, starting with the labels in the header.
    widths = [len(c) for c in labels]
    for r, row in enumerate(head):
        for i, (v, fmt, prefix) in enumerate(zip(row, formats, prefixes)):
            fmt = fmt.format(width='')
            widths[i] = max(widths[i], len(f'{prefix}{v:{fmt}}'))

    # Print the header.
    last = len(labels) - 1
    for i, lbl in enumerate(labels):
        sep = '\n' if i == last else ' '
        w = widths[i]
        print(f'{lbl:^{w}}', end=sep)

    for i, w in enumerate(widths):
        sep = '\n' if i == last else ' '
        print('-' * w, end=sep)

    # Go through the rows and print the values.
    for row in body:
        for i, (v, fmt, prefix) in enumerate(zip(row, formats, prefixes)):
            sep = '\n' if i == last else ' '
            fmt = fmt.format(width=widths[i])
            print(f'{prefix}{v:{fmt}}', end=sep)
    return None
