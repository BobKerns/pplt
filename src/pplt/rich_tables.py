'''
Terminal table printer
'''

import sys
from collections.abc import Collection, Iterable, Iterator, Callable
from contextlib import suppress
from datetime import date
from itertools import chain, count, repeat, tee, islice
from typing import Any, cast, overload, TYPE_CHECKING

import pandas as pd

from rich.console import RenderableType
from rich.table import Table as RichTable
from rich.pretty import install as install_rich
from rich.protocol import is_renderable

from pplt.dates import next_month, parse_end, parse_month
from pplt.utils import skip, take, attr_split, dict_split
import pplt.timeline_series as tl
if TYPE_CHECKING:
    from pplt.timeline_series import Timeline, TimelineSeries

RICH_TABLE=True
'''
Use Rich to print tables.
'''

if RICH_TABLE:
    if sys.displayhook.__name__ == 'wrap_displayhook':
        # Already installed
        pass
    else:
        old_hook = sys.displayhook
        install_rich()
        rich_hook = sys.displayhook

        def wrap_displayhook(val: Any):
            if type(val).__module__ == 'xonsh.procs.pipelines':
                return old_hook(val)
            import pplt.plot as pplot
            if isinstance(val, pplot.Figure):
                val.show()
                return
            return rich_hook(val)
        sys.displayhook = wrap_displayhook

type TableContinuation = Callable[[], 'RenderableType|str']|Iterator['RenderableType|str']

next_=next

def table(series: 'TimelineSeries|Timeline',
          include: Collection[str]=(),
          exclude: Collection[str]=(),
          start: int=0,
          end: int|str|date=12,
          formats: Iterable[str]=(),
          next: TableContinuation|None=None, # type: ignore
          ):
    """
    Print a `Table` of values.

    A `Table` is a collection of values, with rows and columns,
    with labels and formats for each column.

    A `Table` can be indexed by row, or by row and column.

    EXAMPLES:
    ---------
    >>> tbl[0]
    (1.0, 2.0, 3.0)
    >>> tbl[0, 1]
    2.0
    >>> tbl[0, 1:3]
    (2.0, 3.0)
    >>> tbl[0:2, 1:3]
    Table of Series-2, Series-3 2 rows
    >>> tbl[0:2, 'Series-2']
    (2.0, 3.0)
    >>> tbl[0:2, 'Series-2':]
    Table of Series-2, Series-3 2 rows
    >>> tbl[(0, 4),]
    Table of rows 0 and 4, all columns. Note that the second comma is required.
    >>> tbl[(0, 4), ('Series-2', 'Series-3)
    Table of Series-2, Series-3 2 rows]

    As a special case, if the first column is an ascending series of dates, the
    row index may be a date or a string in the format 'yy/mm'.

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
    start: int
        The number of months to skip
    next: TableContinuation|None
        A function or `Iterable` giving the next `Table`
    """
    match series:
        case tl.Timeline():
            series = iter(series)
        case tl.TimelineSeries():
            pass
    peek, header = tee(series, 2)
    date_, values = attr_split(header, 'date', 'values')
    start_month = next_month()
    with suppress(StopIteration):
        peek = next_(peek)
        start_month = peek.date
    end = parse_end(start_month, end)
    values = dict_split(values)
    include = include or values.keys()
    to_show = {
        k:v
        for k, v in values.items()
        if k in include and k not in exclude
    }
    labels= ('Month', *to_show.keys())
    formats = chain(('%y/%m',), formats)
    if next is None:
        def next():
            return series_table(islice(date_, 0, end), *to_show.values(),
                                labels=labels,
                                formats=formats,
                                end=end,
                                next=next)

    # Limit the date range in case the series has no other
    # values to show.
    return series_table(islice(date_, start, end), *to_show.values(),
                labels=labels,
                formats=formats,
                end=end,
                next=next,
            )

def series_table(*series: Iterable[float],
                labels: Collection[str]=(),
                formats: Iterable[str] = (),
                start: int=0,
                end: int=12,
                next: TableContinuation|None=None,
            ):
    '''
    Print a table of values from multiple series.
    '''
    return tuple_table(zip(*series),
                    labels=labels,
                    formats=formats,
                    start=start,
                    end=end,
                    next=next,
                )

def dataframe_table(df: pd.DataFrame,
                    start: int=0,
                    end: int=12,
                    labels: Collection[str]=(),
                    formats: Iterable[str] = (),
                    next: TableContinuation|None=None,
                ):
    '''
    Print a table of values from a DataFrame.
    '''
    return tuple_table(df.itertuples(index=False, name=None),
                    labels=labels or df.columns,
                    formats=formats,
                    start=start,
                    end=end,
                    next=next,
                )

type SingleRowIndex = int|str|date
type RowSlice = slice[int|None,int|None,int|None]\
    |slice[str|None,str|None,int|None]\
    |slice[date|None,date|None,int|None]
type MultiRowIndex = tuple[SingleRowIndex|RowSlice, ...]|RowSlice|list[bool]
type MultiRowOnlyIndex = RowSlice|tuple[tuple[SingleRowIndex|RowSlice,...]]|list[bool]
type RowOnlyIndex = SingleRowIndex|RowSlice|tuple[tuple[SingleRowIndex,...]]
type SingleColIndex = int|str
type ColSlice = slice[int|None,int|None,int|None]\
    |slice[str|None,str|None,int|None]
type MultiColIndex = tuple[int|str|ColSlice, ...]|ColSlice|list[bool]
type ColumnIndex = SingleColIndex|MultiColIndex
type TableIndex = RowOnlyIndex\
    |MultiRowOnlyIndex\
    |tuple[SingleRowIndex, SingleColIndex]\
    |tuple[MultiRowIndex, SingleColIndex]\
    |tuple[SingleRowIndex, MultiColIndex]\
    |tuple[MultiRowIndex, MultiColIndex]

def flatten_cols(labels: list[str], cols: ColumnIndex) -> tuple[int, ...]:
    '''
    Flatten a column index into a tuple of integers.
    '''
    match cols:
        case int():
            return (cols,)
        case str():
            return (labels.index(cols),)
        case slice():
                start = labels.index(cols.start) if isinstance(cols.start, str) else (cols.start or 0)
                stop = labels.index(cols.stop) if isinstance(cols.stop, str) else (cols.stop or len(labels))
                step = cols.step or 1
                return tuple(range(start, stop, step))
        case tuple():
            return tuple(c1
                            for i in cols
                            for c1 in flatten_cols(labels, i)
                        )
        case list():
            return tuple(i for i in range(len(labels)) if cols[i])
        case _: # type: ignore
            raise ValueError(f'Invalid column index: {cols}')


def find_row(labels: list[str], values: list[tuple[Any, ...]], rowid: str|date) -> int:
    month = labels.index('Month')
    match rowid:
        case str():
            rowid = parse_month(rowid)
            return next(i for i, d in enumerate(values) if d[month] == rowid)
        case date():
            return next(i for i, d in enumerate(values) if d[month] == rowid)


def extract_rows(labels: list[str],
                 values: list[tuple[Any]],
                 rows: MultiRowIndex|SingleRowIndex|list[bool],
                 ) -> list[tuple[Any]]:
    '''
    Extract rows using row indices.
    '''
    match rows:
        case int():
            return [values[rows]]
        case str()|date():
            return [values[find_row(labels, values, rows)]]
        case slice():
                start = (
                    find_row(labels, values, rows.start)
                    if isinstance(rows.start, (str, date))
                    else (rows.start or 0)
                )
                stop = (
                    find_row(labels, values, rows.stop)
                    if isinstance(rows.stop, (str, date))
                    else len(values)
                )
                step = rows.step or 1
                return [values[i] for i in range(start, stop, step)]
        case tuple():
            return [
                    c1
                    for i in rows
                    for c1 in extract_rows(labels, values, i)
                ]
        case list():
            return [
                row
                for i, row in enumerate(values)
                if rows[i]
            ]

        case _: # type: ignore
            raise ValueError(f'Invalid row index: {rows}')

def next_table(next_: TableContinuation|None) -> TableContinuation|None:
    match next_:
        case Iterator():
            return lambda: next(next_)
        case Callable():
            return next_
        case None:
            return None

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
            def cell(value: Any, fmt: str) -> RenderableType:
                match value:
                    case date():
                        return f'{value:%y/%m}'
                    case _ if is_renderable(value):
                        return cast(RenderableType, value)
                    case float():
                        return f'{value:{fmt}}'
                    case None:
                        return '--'''
                    case _:
                        return str(value)

            for row in self.values:
                cells = (
                    cell(v, fmt)
                    for v, fmt in zip(row, self.formats)
                )
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
    def labels(self, value: list[str]):
        self.__labels = value

    __formats: list[str]
    @property
    def formats(self):
        return self.__formats

    @formats.setter
    def formats(self, fmts: list[str]):
        self.__rich_table = None
        self.__formats = fmts

    values: list[tuple[Any, ...]]

    __next: TableContinuation|None
    @property
    def next(self):
        match self.__next:
            case None:
                return 'No more'
            case Callable():
                return self.__next()
            case Iterator():
                return next(self.__next)

    def __init__(self,
                 /, *,
                labels: list[str],
                formats: list[str],
                ncols: int,
                values: list[tuple[Any, ...]],
                end: int|str|date,
                next: TableContinuation|None=None,
            ):
        self.ncols = ncols
        self.values = values
        self.end = end
        series = (f'Series-{i}' for i in count(len(labels)+1))
        self.labels = list(islice(chain(labels, series), 0, ncols))
        self.formats = list(islice(chain(formats, repeat('>,.2f')), 0, ncols))
        self.__next = next_table(next)

    def __eq__(self, other: Any):
        if not isinstance(other, Table):
            return NotImplemented
        return self.labels == other.labels and self.values == other.values and self.formats == other.formats

    @overload
    def __getitem__(self, i: SingleRowIndex) -> tuple[Any]:...
    @overload
    def __getitem__(self, i: MultiRowOnlyIndex) -> 'Table':...
    @overload
    def __getitem__(self, i: tuple[SingleRowIndex, SingleColIndex]) -> Any:...
    @overload
    def __getitem__(self, i: tuple[MultiRowIndex, SingleColIndex]) -> 'Table':...
    @overload
    def __getitem__(self, i: tuple[SingleRowIndex, MultiColIndex]) -> tuple[Any, ...]:...
    @overload
    def __getitem__(self, i: tuple[MultiRowIndex, MultiColIndex]) -> 'Table':...
    def __getitem__(self, i: TableIndex) -> Any:
        def extract_columns(c: ColumnIndex) -> tuple[Any, list[str], list[str]]:
            cols = flatten_cols(self.labels, c)
            def extract(row: tuple[Any]):
                return tuple(row[i] for i in cols)
            return extract, [self.labels[i] for i in cols], [self.formats[i] for i in cols]
        match i:
            case int():
                return self.values[i]
            case str()|date():
                return self.values[find_row(self.labels, self.values, i)]
            case slice():
                return Table(
                    labels=self.labels,
                    formats=self.formats,
                    ncols=self.ncols,
                    values=self.values[i],
                    end=self.end)
            case (tuple(i_),):
                return Table(
                    labels=self.labels,
                    formats=self.formats,
                    ncols=self.ncols,
                    values=extract_rows(self.labels, self.values, i_),
                    end=self.end)
            case (slice(),
                  int()|slice()|str()|tuple()):
                rowid, colid = i
                rows = self.__getitem__(rowid)
                extract, labels, formats = extract_columns(colid)
                new_rows = [extract(row) for row in rows]
                return Table(
                    labels=labels,
                    formats=formats,
                    ncols=len(labels),
                    values=new_rows,
                    end=self.end)
            case (tuple(),
                  int()|slice()|str()|tuple()):
                rowid, colid = i
                rows = [
                    r for s in rowid
                    for g in extract_rows(self.labels, self.values, s)
                    for r in g
                ]
                extract, labels, formats = extract_columns(colid)
                new_rows = [extract(row) for row in rows]
                return Table(
                    labels=labels,
                    formats=formats,
                    ncols=len(labels),
                    values=new_rows,
                    end=self.end)
            case (int(), int()|slice()|str()|tuple()):
                rowid, colid = i
                row = self.__getitem__(rowid)
                extract, *_ = extract_columns(colid)
                return extract(row)
            case (str()|date(), int()|slice()|str()|tuple()):
                rowid, colid = i
                rowid = find_row(self.labels, self.values, rowid)
                row = self.__getitem__(rowid)
                extract, *_ = extract_columns(colid)
                return extract(row)
            case _: # type: ignore
                return NotImplemented

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def __repr__(self):
        return f'<Table of {','.join(self.labels)} {len(self)} rows>'

def tuple_table(values: Iterable[tuple[Any, ...]], /, *,
                start: int=0,
                end: int=12,
                labels: Collection[str]=(),
                formats: Iterable[str] = (),
                ncols: int|None = None,
                next: TableContinuation|None=None, # type: ignore
            ) -> Table:
    '''
    Print a table of values from multiple series packaged as an iterable of tuples.

    PARAMETERS
    ----------
    values: Iterable[tuple[Any, ...]]
        An iterable of tuples of values.
    end: int
        The number of months to print.
    labels: Collection[str]
        The labels for the columns. Defaults to 'Series-1', 'Series-2', etc.
    formats: Iterable[str]
        The format strings for the columns. Defaults to '>,.2f'.
    prefixes: Iterable[str]
        The prefixes for the columns. Defaults to '$'.
    ncols: int|None
        The number of columns. If None, the number of columns is determined by the first row (which requires non-zero rows).
    next: TableContinuation|None
        Function or `Iterator` giving the next table of values.
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
    skip(start, values_)
    # Limit the number of rows
    tbl_values = take(end, values_)

    if ncols is None:
        # Get the first row to determine the number of columns.
        first = tbl_values[0]
        ncols = len(first)

    labels_ = take(ncols, labels_)
    formats = take(ncols, formats_)
    if next is None:
        def next():
            return tuple_table(values_, end=end, labels=labels, formats=formats)
    return Table(
        labels=labels_,
        formats=formats,
        ncols=ncols,
        values=tbl_values,
        end=end,
        next=next)
