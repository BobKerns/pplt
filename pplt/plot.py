'''
Terminal plotting utilities for pplt
'''

import sys
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from itertools import chain, count, islice, tee
from math import ceil, floor
from typing import Iterator, Literal, Optional

import plotext as plt

from pplt.time import months, next_month, parse_month, unparse_month
from pplt.utils import dict_split, parse_end, take


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
