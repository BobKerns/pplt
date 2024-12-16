'''
Terminal table printer
'''

import sys
from collections.abc import Collection, Iterable
from contextlib import suppress
from datetime import date
from itertools import chain, count, repeat, tee, islice

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
    __labels: list[str]
    @property
    def labels(self):
        return self.__labels
    @labels.setter
    def labels(self, value):
        self.__labels = value
        self.__formatted_header = ''
        self.__widths = []

    __proto_formats: list[str]
    __formats: list[str]
    @property
    def formats(self):
        if not self.__formats:
            self.__formats = [
                fmt.format(width=w)
                for fmt, w in zip(self.__proto_formats, self.widths)
            ]
        return self.__formats
    @formats.setter
    def formats(self, value):
        self.__proto_formats = value
        self.__formats = []
    values: list[tuple[float, ...]]

    __widths: list[int]
    @property
    def widths(self):
        if not self.__widths:
            # Calculate the column widths, starting with the labels in the header.
            widths = widths = [len(c) for c in self.labels]
            tmp_fmts =[fmt.format(width='') for fmt in self.__proto_formats]
            # Calculate the column widths
            for row in self:
                for col, w, fmt, val in zip(count(), widths, tmp_fmts, row):
                    widths[col] = max(w, len(f'{val:{fmt}}'))
            self.__widths = widths
        return self.__widths

    @widths.setter
    def widths(self, value):
        self.__widths = value
        # Clear out dependent values.
        self.__formatted_header = ''
        self.__formats = []

    __formatted_header: str = ''
    @property
    def formatted_header(self):
        if not self.__formatted_header:
            header = ' '.join(f'{lbl:^{w}}' for lbl, w in zip(self.labels, self.widths))
            sep = ' '.join('-' * w for w in self.widths)
            self.__formatted_header = f'{header}\n{sep}'
        return self.__formatted_header

    values: list[tuple[float, ...]]

    def __init__(self, labels, formats, ncols, values, end):
        self.labels = labels
        self.ncols = ncols
        self.values = values
        self.end = end
        self.formats = formats
        self.__widths = []
        self.formats = [fmt.format(width=w)
                        for fmt, w in zip(self.formats, self.widths)]

    def __getitem__(self, i: int):
        def extract_columns(row, c):
            match c:
                case int()|slice():
                    return row[c]
                case tuple():
                    return tuple(row[i] for i in c)
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
            case (int(rowid), int(colid)|slice(colid)|str(colid)|tuple(colid)):
                row = self.__getitem__(rowid)
                return extract_columns(row, colid)
            case (slice(rowspec)|tuple(rowspec),
                  int(colid)|slice(colid)|str(colid)|tuple(colid)):
                rows = self.__getitem__(rowspec)
                return [extract_columns(row, colid) for row in rows]
            case _:
                return NotImplemented

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def format_row(self, row):
        return ' '.join(f'{v:{fmt}}'
                        for v, fmt in zip(row, self.formats)
                        )

    def __repr__(self):
        return self.formatted_header + '\n' + '\n'.join(self.format_row(row)
                                                        for row in self)

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

    formats_ = chain(formats, repeat('>{width}.2f'))
    values_ = iter(values)
    tbl_values = take(end, values_)

    # Limit the number of rows
    # Get the first row to determine the number of columns.
    first = tbl_values[0]
    ncols = len(first)

    labels_ = take(ncols, labels_)
    formats = take(ncols, formats_)

    if RICH_TABLE:
        # We wish we could let Rich handle the width calculations.
        # But we can't. So we have to do it ourselves.
        our_table = Table(labels_, formats, ncols, tbl_values, end)
        widths = our_table.widths
        formats = [fmt.format(width='') for fmt in formats]
        table = RichTable(expand=False)
        for lbl, width in zip(labels_, widths):
            table.add_column(lbl, justify='center', style='bold', header_style='bold',)
        for row in tbl_values:
            cells = (v if is_renderable(v) else f'{v:{fmt}}'
                     for v, fmt in zip(row, formats))
            table.add_row(*cells)
        return table
    return Table(labels_, formats, ncols, tbl_values, end)
