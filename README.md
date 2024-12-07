## Setting up to explore

# Install direnv

Not essential, but it will save ou trouble.

```bash
port install direnv
```

# Create a github repo

* Create it on the github web UI
* Copy the URL

```bash
git clone <url>
cd <project_name>
```

# Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

`.envrc`:
```bash
if [ -d .venv ]; do
  source .venv/bin/activate
fi
```

`requirements.txt`:
```
pltext
pltext[completions]

```

# Create a `tests/` subdirectory.
```bash
mkdir tests/
touch tests/.gitignore
```

# Set up your python package

* Choose a name, perhaps `mortgage`.
* Create a subdirectory with that name.
* Add an `__init__.py` file (it can be empty).
* Add `utils.py`

`utils.py`:
```python
"""
Utilities for plotting, etc.
"""

from datetime import datetime,timedelta
from plotext import plot
from itertools import islice
from math import ceil

import plotext as plt

DAYS_PER_MONTH = (31,28,31,30,31,30,31,31,30,31,30,31)

def days_per_month(date: datetime):
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

def months(start=next_month()):
    '''
    Yields a series of dates 1 month apart.

    PARAMETERS
    ----------
    start: datetime.datetime
        Starting date. Default=next_month()
    '''
    date = start
    while True:
        yield date
        date = date + timedelta(days=days_per_month(date))

def plt_months(start=next_month(), end=12, stride=1):
    """
    Returns a list of month strings for the pltext library.

    These can be used in `plt.xticks()` or as x-values in `plt.plot()`.
    """
    series = islice(months(start=start), 0, end, stride)
    return [t.strftime('%m/%y') for t in series]

def myplot(*series, start=next_month(), months=12):
    """
    Plot a graph by month
    """
    plt.clear_figure()
    plt.theme('pro')
    plt.date_form('m/y')
    plt.xticks(plt_months(start=start, end=months, stride=ceil(months / 12)))
    for s in series:
        x = list(islice(plt_months(start=start), 0, months))
        y = list(islice(s, 0, months))
        plt.plot(x, y)
    plt.ylim(0, max(y))
    plt.show()
    return plt
```
