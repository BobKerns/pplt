'''
Terminal table printer
'''

import sys
from collections.abc import Collection, Iterable
from contextlib import suppress
from datetime import date
from itertools import chain, repeat, tee, islice

from rich.table import Table as RichTable
from rich.pretty import install as install_rich
from rich.protocol import is_renderable

from pplt.dates import next_month, parse_end
from pplt.timeline import Timeline, TimelineSeries
from pplt.utils import take, attr_split, dict_split

RICH_TABLE=True
'''
Use Rich to print tables.
'''

if RICH_TABLE:
    if sys.displayhook and sys.displayhook.__name__ == 'wrap_displayhook':
        # Already installed
        pass
    else:
        old_hook = sys.displayhook
        install_rich()
        rich_hook = sys.displayhook

        def wrap_displayhook(val):
            if type(val).__module__ == 'xonsh.procs.pipelines':
                return old_hook(val)
            return rich_hook(val)
        sys.displayhook = wrap_displayhook


def table(series: TimelineSeries|Timeline,
          include: Collection[str]=(),
          exclude: Collection[str]=(),
          end: int|str|date=12,
          formats: Iterable[str]=(),
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
    # Limit the date range in case the series has no other
    # values to show.
    return series_table(islice(date_, 0, end), *to_show.values(),
                labels=('Month', *to_show.keys()),
                formats=chain(('%y/%m',), formats),
                end=end,
            )

def series_table(*series: Iterable[float],
                labels: Collection[str]=(),
                formats: Iterable[str] = (),
                end: int=12,
                 ):
    '''
    Print a table of values from multiple series.
    '''
    return tuple_table(zip(*series),
                    labels=labels,
                    formats=formats,
                    end=end,
                    )


class Table:
    '''
    A table of values, ready to be printed
    '''
    __rich_table: RichTable|None
    @property
    def rich_table(self):
        if self.__rich_table is None:
            table = RichTable(expand=False)
            for lbl in self.labels:
                table.add_column(lbl, justify='center',  header_style='bold',)
            for row in self.values:
                cells = (v if is_renderable(v) else f'{v:{fmt}}'
                         for v, fmt in zip(row, self.formats))
                table.add_row(*cells)
            self.__rich_table = table
        return self.__rich_table

    def __rich__(self):
        return self.rich_table

    __labels: list[str]
    @property
    def labels(self):
        return self.__labels
    @labels.setter
    def labels(self, value):
        self.__labels = value

    __formats: list[str]
    @property
    def formats(self):
        return self.__formats

    @formats.setter
    def formats(self, fmts: list[str]):
        self.__rich_table = None
        self.__formats = fmts

    values: list[tuple[float, ...]]

    values: list[tuple[float, ...]]

    def __init__(self, labels, formats, ncols, values, end):
        self.labels = labels
        self.ncols = ncols
        self.values = values
        self.end = end
        self.formats = formats

    def __getitem__(self, i: int):
        def extract_columns(row, c):
            match c:
                case int()|slice():
                    return row[c]
                case tuple():
                    return tuple(extract_columns(row, i) for i in c)
                case str():
                    return row[self.labels.index(c)]
                case _:
                    return NotImplemented
        match i:
            case int():
                return self.values[i]
            case slice():
                return self.values[i]
            case (tuple(),):
                return [self.values[idx] for idx in i]
            case (int(rowid), int()|slice()|str()|tuple()):
                row = self.__getitem__(rowid)
                return extract_columns(row, i[1])
            case (slice()|tuple(),
                  int()|slice()|str()|tuple()):
                rows = self.__getitem__(i[0])
                return [extract_columns(row, i[1]) for row in rows]
            case _:
                return NotImplemented

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def __repr__(self):
        return f'<Table of {','.join(self.labels)} {len(self)} rows>'

def tuple_table(values: Iterable[tuple[float, ...]], /,
                    end: int=12,
                    labels: Collection[str]=(),
                    formats: Iterable[str] = (),
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
    formats: Iterable[str]
        The format strings for the columns. Defaults to '{width}.2f'.
    prefixes: Iterable[str]
        The prefixes for the columns. Defaults to '$'.
    '''

    # extend the sequence of labels if needed.
    labels_ = chain(labels, repeat(''))
    labels_ = (
        lbl if lbl else f'Series-{i+1}'
        for i, lbl in enumerate(labels_)
    )
    labels_ = (
        lbl.capitalize() if lbl.islower() else lbl
        for lbl in labels_
    )

    formats_ = chain(formats, repeat('>,.2f'))
    values_ = iter(values)
    tbl_values = take(end, values_)

    # Limit the number of rows
    # Get the first row to determine the number of columns.
    first = tbl_values[0]
    ncols = len(first)

    labels_ = take(ncols, labels_)
    formats = take(ncols, formats_)
    return Table(labels_, formats, ncols, tbl_values, end)
