"""
Utilities for plotting, etc.
"""

from datetime import datetime,timedelta
from plotext import plot
from itertools import islice, count, chain
from math import floor, ceil
from collections.abc import Iterable, Iterator, Sequence
from typing import Optional, Literal, cast
import sys
from dataclasses import dataclass, field

import plotext as plt

MORTGATE_RATE=3.875

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

def rate_of_return(start_date: datetime|str, start_value: float, end_date: datetime|str, end_value: float):
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

def pct_return(start_date: datetime|str, start_value: float, end_date: datetime|str, end_value: float):
    return 100 * rate_of_return(start_date, start_value, end_date, end_value)

DAYS_PER_MONTH = (31,28,31,30,31,30,31,31,30,31,30,31)
def days_per_month(date: datetime):
    """
    The number of days in a month.
    """
    days = DAYS_PER_MONTH[(date.month-1)%12]
    if date.month == 2 and (date.year % 4) == 0:
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

def plt_months(start: datetime=next_month(),
               end: Optional[int]=None,
               stride: int=1):
    """
    Returns a list of month strings for the pltext library.

    These can be used in `plt.xticks()` or as x-values in `plt.plot()`.
    """
    series = (t.strftime('%m/%y') for t in months(start=start))
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
type Color = int|tuple[int, int, int]|ColorCode

def color_series():
    "Codes for a nice-looking series of colors."
    return (c % 256 for c in count(112, 13))

@dataclass
class SubPlot:
    x: int
    y: int
    series: Sequence[Iterable[float]]
    start: datetime = field(default_factory=next_month)
    months: int=0
    title: Optional[str] = None
    labels: Iterable[str] = ()
    colors: Iterable[Color] = ()
    ylim: tuple[float|None,...] = ()

def subplot(x: int, # Position of plot
            y: int,
            *series: Sequence[Iterable[float]],
            start: Optional[datetime]=None,
            title: Optional[str]=None,
            labels: Iterable[str]=(),
            colors: Iterable[Color] = (),
            ylim: tuple[float|None,...]=(),
            ):
    return SubPlot(
        x=x, y=y,
        start=start,
        title=title,
        labels=labels,
        colors=colors,
        ylim=ylim,
        series=series,
    )

def take(n: int, x: Iterator[str]) -> list[str]:
    "Take n from an infinite iterator."
    return [next(x) for i in range(n)]

def multiplot(*subplots: SubPlot,
              title: Optional[str]=None,
              start: datetime=next_month(),
              months: int=12,
              colors: Iterable[Color] = (),
              figure=plt,
              show: bool=True,
              wait: bool=True,
              ):
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
        myplot(*sp.series,
               months=sp.months or months,
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
            input('--continue--')


def myplot(*series: Iterable[float],
           start: datetime=next_month(),
           months: int=12,
           title: Optional[str]=None,
           labels: Iterable[str]=(),
           colors: Iterable[Color]=(),
           ylim: tuple[float|None,...]=(),
           figure=plt,
           show: bool=True,
           wait: bool=True):
    """
    Plot a graph by month
    """
    labels = chain(labels, (f'Series-{i}' for i in count(len(labels)+1)))
    colors = chain(colors, color_series())
    if figure is plt:
        figure.clear_figure()
    figure.theme('pro')
    figure.date_form('m/y')
    xticks = list(islice(plt_months(start=start), 0, months+1, ceil(months / 12)))
    figure.xticks(xticks, xticks)
    _ymin=sys.maxsize; _ymax=0
    for s, l, c in zip(series, labels, colors):
        x = list(islice(plt_months(start=start), 0, months))
        y = list(islice(s, 0, months))
        _ymin = min(_ymin, min(y))
        _ymax = max(_ymax, max(y))
        figure.plot(x, y, label=l, color=c, marker='hd')
    ymin, ymax = (*ylim, None, None)[:2]
    ymin = _ymin if ymin is None else ymin
    ymax = _ymax if ymax is None else ymax
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
            input('--contine--')
    return figure
