"""
Utilities for plotting, etc.
"""

from datetime import datetime, timedelta
from itertools import islice, count, chain, tee, repeat
from math import floor, ceil
from collections.abc import Iterable, Iterator, Sequence, Collection
from typing import Optional, Literal
import sys
from dataclasses import dataclass

import plotext as plt


MORTGAGE_RATE=3.875

def monthly_rate(annual: float):
    """
    Convert annual rate to monthly. This is NOT the same as dividing by 12.
    NOTE: not as percentage!
    """
    rate = (1 + annual) ** (1/12.0)
    return (rate - 1)


def monthly_pct(annual: float):
    """
    Convert annual pecentage rate to monthly. This is NOT the same
    as dividing by 12.
    """
    return 100 * monthly_rate(annual / 100)


def daily_rate(annual: float):
    """
    Convert annual rate to daily. This is NOT the same as dividing by 365.25
    NOTE: not as percentage!
    """
    rate = (1 + annual) ** (1/365.25)
    return (rate - 1)


def daily_pct(annual: float):
    """
    Convert annual pecentage rate to daily. This is NOT the same
    as dividing by 365.25
    """
    return 100 * daily_rate(annual / 100)


def quarterly_rate(annual: float):
    """
    Convert annual rate to quarterly. This is NOT the same as dividing by 4.
    NOTE: not as percentage!
    """
    rate = (1 + annual) ** 0.25
    return (rate - 1)


def quarterly_pct(annual: float):
    """
    Convert annual pecentage rate to quarterly. This is NOT the same
    as dividing by 4.
    """
    return 100 * quarterly_rate(annual / 100)


def rate_of_return(start_date: datetime|str, start_value: float,
                   end_date: datetime|str, end_value: float):
    '''
    Given a start date and value, and an end date and value, calculate the
    annual rate of return.
    
    PARAMETERS
    ----------
    start_date: datetime|str
        Starting date.
    start_value: float
        Starting value.
    end_date: datetime|str
        Ending date.
    end_value: float
        Ending value.
        
    RETURNS
    -------
    rate: float
        The annual rate of return, as a fraction.
    '''
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    change = end_value - start_value
    frac = change / start_value
    days = (end_date - start_date).days
    daily = (1 + frac) ** (1.0 / days)
    annual = daily ** 365.25
    return annual - 1


def pct_return(start_date: datetime|str, start_value: float,
               end_date: datetime|str, end_value: float):
    '''
    Given a start date and value, and an end date and value, calculate the
    annual rate of return as a percentage.
    
    PARAMETERS
    ----------
    start_date: datetime|str
        Starting date.
    start_value: float
        Starting value.
    end_date: datetime|str
        Ending date.
    end_value: float
        Ending value.

    RETURNS
    -------
    rate: float
        The annual rate of return, as a percentage.
    '''
    return 100 * rate_of_return(start_date, start_value, end_date, end_value)

DAYS_PER_MONTH = (31,28,31,30,31,30,31,31,30,31,30,31)
def days_per_month(date: datetime|int):
    """
    The number of days in a month.
    
    PARAMETERS
    ----------
    date: datetime|int
        A date or month number.

    RETURNS
    -------
    days: int
        The number of days in the month.
    """
    month = date if isinstance(date, int) else date.month
    days = DAYS_PER_MONTH[(month-1)%12]
    if month == 2 and (date.year % 4) == 0:
        days += 1
    return days


def next_month():
    """
    RETURNS
    -------
    date: datetime
        The date at the start of the next month.
    """
    today = datetime.today()
    today - today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return today + timedelta(days=days_per_month(today))


def months(start: datetime=next_month()) -> Iterable[datetime]:
    '''
    Yields a series of dates 1 month apart.

    PARAMETERS
    ----------
    start: datetime.date
        Starting date. Default=next_month()
    '''
    date = start
    while True:
        yield date
        date = date + timedelta(days=days_per_month(date))


def months_str(start: datetime=next_month(),
               end: Optional[int]=None,
               stride: int=1):
    """
    Returns a list of month strings for the pltext library.

    These can be used in `plt.xticks()` or as x-values in `plt.plot()`.
    """
    series = (t.strftime('%y/%m') for t in months(start=start))
    if end is None:
        return series
    return islice(series, 0, end, stride)


def choose_stride(ymin: float, ymax: float):
    """
    Choose a good stride size for our Y-value tick marks.
    If ymin is a round number, this tries to keep the ticks rounded.
    It tries to generate an interval that allows for at least 10 ticks,
    but it can be more due to rounding.
    """
    yrange = ymax - ymin
    r = floor(yrange / 10000)*1000
    if r == 0:
        r = floor(yrange / 1000)*100
    if r == 0:
        r = floor(yrange / 100)*10
    if r == 0:
        r = floor(yrange / 10)*1
    if r == 0:
        r = floor(yrange / 1)*0.1
    if r == 0:
        r = floor(yrange / 0.1)*0.01
    if r == 0:
        r = floor(yrange / 0.01)*0.001
    if r == 0:
        r = floor(yrange / 0.001)*0.0001
    if r == 0:
        r = floor(yrange / 0.0001)*0.00001
    if r == 0:
        r = yrange / 10
    return r


type ColorCode = Literal[
    'default',
    'black',     'white',
    'orange',    'orange+',
    'cyan',      'cyan+',
    'gray',      'gray+',
    'magenta',   'magenta+',
    'blue',      'blue+',
    'red',       'red+',
    'green',     'green+',
]
'''
"Color names accepted by the plotext library."
'''
type Color = int|tuple[int, int, int]|ColorCode
'''
"Color type accepted by the plotext library."
'''

def color_series():
    "Codes for a nice-looking series of colors."
    return (c % 256 for c in count(112, 13))


@dataclass
class SubPlot:
    '''
    A subplot for a multiplot.
    '''
    x: int
    y: int
    series: Sequence[Iterable[float]]
    start: datetime|None = None
    end: int|str|datetime = 12
    months: int=0
    title: Optional[str] = None
    labels: Iterable[str] = ()
    colors: Iterable[Color] = ()
    ylim: tuple[float|None,...] = ()


def subplot(x: int, # Position of plot
            y: int,
            *series: Sequence[Iterable[float]],
            start: Optional[datetime]=None,
            end: Optional[int|str|datetime]=None,
            title: Optional[str]=None,
            labels: Iterable[str]=(),
            colors: Iterable[Color] = (),
            ylim: tuple[float|None,...]=(),
            ):
    '''
    Create a subplot for a multiplot.
    
    PARAMETERS
    ----------
    x: int
        Position of plot.
    y: int
        Position of plot.
    series: Sequence[Iterable[float]]
        The data series to plot.
    start: Optional[datetime]
        Starting date. Overrides the default from `multiplot()`.
    end: Optional[int|str|datetime]
        Ending date, or Number of months to plot.
        Overrides the default from `multiplot()`.
    title: Optional[str]
        Title of the subplot.
    labels: Iterable[str]
        Labels for the series.
    colors: Iterable[Color]
        Colors for the series.
    ylim: tuple[float|None,...]
        Y-axis limits.

    RETURNS
    -------
    subplot: SubPlot
        The subplot object to pass to `multiplot()`.
    '''
    return SubPlot(
        x=x, y=y,
        start=start,
        end=end,
        title=title,
        labels=labels,
        colors=colors,
        ylim=ylim,
        series=series,
    )
    

def take(n: int, x: Iterator[str]) -> list[str]:
    "Take n from an infinite iterator."
    return [next(x) for i in range(n)]


def parse_month(date: str|datetime):
    '''
    Parse a date string or datetime object into a month.
    
    Strings should be in the form 'yy/mm'.
    '''
    match date:
        case str():
            return datetime.strptime(date, "%y/%m")
        case datetime():
            return date.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)
        case _:
            raise ValueError(f'Invalid date: {date}.')

    
def unparse_month(date: datetime):
    '''
    The inverse of `parse_month()`.
    
    RETURNS
    -------
    date: str
        A string in the form 'yy/mm'.
    '''
    return date.strftime('%y/%m') 


def dict_join(d: dict[str, Iterable[float]]):
    """
    Iterate over a dictionary's iterable values in parallel,
    returning an iterator of dictionaries.
    """
    state = {k: iter(v) for k, v in d.items()}
    while True:
        yield {k: next(v) for k, v in state.items()}


def dict_split(joined: Iterator[dict[str, float]]):
    """
    Split an iterator of dictionaries into a dictionary of iterators.
    """
    peek, main = tee(joined)
    first = next(peek)
    keys = first.keys()
    def split(key: str, d: Iterator[dict[str, float]]):
        while True:
            yield next(d)[key]
    return {key: split(key, d) for key, d in zip(keys, tee(main, len(keys)))}


def timeline(start: datetime=next_month(), **kwargs: Iterable[float]):
    """
    Create a timeline of values.
    
    The special entry `'ACCOUNTS'` may be used to restart the timeline.
    
    PARAMETERS
    ----------
    start: datetime|
        Starting date.
    **kwargs: Iterable[float]
        A series of values to plot.
        
    RETURNS
    -------
    timeline: Iterator[dict[str, float]]
        A series of values, one for each key, plus:
        * `'TIME'`, the date of the values.
        & `'START'`, the starting date.
        * `'ACCOUNTS`, the original accounts behind the timeline
    """
    start = parse_month(start)
    return dict_join({
        'TIME': months(start),
        'START': repeat(start),
        'ACCOUNTS': repeat(kwargs),
        **kwargs
    })

    
def restart(timeline: Iterator[dict[str, float]]):
    """
    Restart a timeline, keeping the same accounts.
    
    PARAMETERS
    ----------
    timeline: Iterator[dict[str, float]]
        A timeline of values.
    
    RETURNS
    -------
    timeline: Iterator[dict[str, float]]
        A timeline that starts at the original date with the same accounts.
    """
    peek = next(tee(timeline, 1)[0])
    start = peek['START']
    accounts = peek['ACCOUNTS']
    return dict_join({
        'TIME': months(start),
        'START': repeat(start),
        'ACCOUNTS': repeat(accounts),
        **accounts,
    })


def multiplot(*subplots: SubPlot,
              title: Optional[str]=None,
              start: datetime=next_month(),
              end: int|str|datetime=12,
              colors: Iterable[Color] = (),
              figure=plt,
              show: bool=True,
              wait: bool=True,
              ):
    """
    Plot multiple subplots on a single figure.
    
    PARAMETERS
    ----------
    subplots: SubPlot
        The subplots to plot.
    title: Optional[str]
        Title of the figure.
    start: datetime
        Starting date. Applies to all subplots by default.
    end: int|str|datetime
        End date, or Number of months to plot.
        Applies to all subplots by default.
    colors: Iterable[Color]
        Colors for the series.
    figure: plt
        The figure object to plot on.
    """
    colors = chain(colors, color_series())
    labels = (f'Series-{i}' for i in count(1))
    xmax: int = 0
    ymax: int = 0
    for sp in subplots:
        xmax = max(xmax, sp.x)
        ymax = max(ymax, sp.y)
    if title:
        figure.title(title)
    subs = figure.subplots(xmax, ymax)
    for sp in subplots:
        fig = subs.subplot(sp.x, sp.y)
        if sp.title:
            fig.title(sp.title)
        sp_labels = take(len(sp.series), chain(sp.labels, labels))
        sp_colors = take(len(sp.series), chain(sp.colors, colors))
        plt_by_month(*sp.series,
                    start=sp.start or start,
                    end=sp.end or end,
                    title=sp.title,
                    labels=sp_labels,
                    colors=sp_colors,
                    ylim=sp.ylim,
                    figure=fig,
                    show=False,
                    wait=False,
                )
    if show and figure is plt:
        plt.show()
        if wait:
            input()


def parse_end(start: datetime|str, end: int|str|datetime) -> int:
    """
    Parse the end date.

    PARAMETERS
    ----------
    start: datetime|str
        Starting date.
    end: int|str|datetime
        The ending date, or the number of months to print.
        
    RETURNS
    -------
    end: int
        The number of months to show.
    """
    start = parse_month(start)
    match end:
        case int():
            return end
        case datetime()|str():
            return (parse_month(end) - start).days
        case _:
            raise ValueError('Invalid end value.')


def plt_by_month(
        *series: Iterable[float],
        start: datetime|str=next_month(),
        time: Iterable[datetime]=(),
        end: datetime|int|str=12,
        title: Optional[str]=None,
        labels: Iterable[str]=(),
        colors: Iterable[Color]=(),
        ylim: tuple[float|None,...]=(),
        figure=plt,
        show: bool=True,
        wait: bool=True,
    ):
    """
    Plot a graph by month
    
    PARAMETERS
    ----------
    series: Iterable[float]
        The data series to plot.
    start: datetime|str
        Starting date.
    time: Iterable[datetime]
        The time series.
    end: datetime|int|str
        The ending date, or the number of months to print.
    title: Optional[str]
        Title of the plot.
    labels: Iterable[str]
        Labels for the series.
    colors: Iterable[Color]
        Colors for the series.
    ylim: tuple[float|None,...]
        Y-axis limits.
    figure: plt
        The figure object to plot on.
    show: bool
        Whether to show the plot.
    wait: bool
        Whether to wait for user input.
    """
    start = parse_month(start)
    labels = chain(labels, (f'Series-{i}' for i in count(len(labels)+1)))
    colors = chain(colors, color_series())
    if figure is plt:
        figure.clear_figure()
    if not wait and figure is plt:
        plt.plotsize(plt.tw(), plt.th() - 2)
    figure.theme('pro')
    figure.date_form('y/m')
    if not time:
        time = months(start=start)
    time = (unparse_month(t) for t in time)
    end = parse_end(start, end)
    # Copy the time iterator for each usage (series, ticks, labels)
    xticks, *data_x = tee(time, len(series)+1)
    xticks = islice(xticks, 0, end + 1, ceil(end / 10))
    figure.xticks(*tee(xticks, 2))
    _ymin=sys.maxsize
    _ymax=0
    for t, s, lbl, clr in zip(data_x, series, labels, colors):
        x = list(islice(t, 0, end))
        y = list(islice(s, 0, end))
        _ymin = min(_ymin, min(y))
        _ymax = max(_ymax, max(y))
        figure.plot(x, y, label=lbl, color=clr, marker='hd')
    ymin, ymax = (*ylim, None, None)[:2]
    ymin = _ymin if ymin is None else ymin
    ymax = _ymax if ymax is None else ymax
    if ymin * ymax < 0:
        figure.hline(0, color='gray')
    r = choose_stride(ymin, ymax)
    # Expand to include the end-range ticks.
    ymin = floor(ymin / r) * r
    ymax = ceil(1+ymax / r) * r
    figure.ylim(ymin, ymax)
    # Calculate ticks and labels.
    yticks = [ymin + i * r for i in range(0, 20)]
    if r >= 10:
        ylabels = [f'${round(v):,d}' for v in yticks]
    else:
        ylabels = [f'{v:1.4f}' for v in yticks]
    figure.yticks(yticks, ylabels)
    if title:
        figure.title(title)
    if show and figure is plt:
        figure.show()
        if wait:
            input()
    return None


def plt_timeline(timeline: Iterator[dict[str, float]],
                 end: int|str|datetime=12,
                 title: Optional[str]=None,
                 colors: Iterable[Color]=(),
                 ylim: tuple[float|None,...]=(),
                 include: Collection[str]=(),
                 exclude: Collection[str]=(),
                 figure=plt,
                 show: bool=True,
                 wait: bool=True,
                 ):
    """
    Plot a timeline of values.
    
    PARAMETERS
    ----------
    timeline: Iterator[dict[str, float]]
        A timeline of values.
    end: int|str|datetime
        The ending date, or the number of months to print.
    title: Optional[str]
        Title of the plot.
    colors: Iterable[Color]
        Colors for the series.
    ylim: tuple[float|None,...]
        Y-axis limits.
    include: Collection[str]
        The labels to include.
    exclude: Collection[str]
        The labels to exclude.
    figure: plt
        The figure object to plot on.
    show: bool
        Whether to show the plot.
    wait: bool
        Whether to wait for user input.
    
    """
    values = dict_split(timeline)
    time = values.pop('TIME')
    del values['ACCOUNTS']
    del values['START']
    labels = values.keys()
    if not include:
        include = labels
    series = [
        s for k, s in values.items()
        if k in include and k not in exclude
     ]
    plt_by_month(*series,
               time=time,
               end=end,
               title=title,
               labels=labels,
               colors=colors,
               ylim=ylim,
               figure=figure,
               show=show,
               wait=wait,
               )
    

def table(timeline: Iterator[dict[str, float]],
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
