"""
Utilities for special iterators, etc, etc.
"""

from itertools import tee
from collections.abc import Iterable, Iterator
from typing import Any

def take(n: int, x: Iterator[str]) -> list[str]:
    "Take n from an infinite iterator."
    return [next(x) for i in range(n)]


def dict_join(d: dict[str, Iterable[Any]]):
    """
    Iterate over a dictionary's iterable values in parallel,
    returning an iterator of dictionaries.
    """
    state = {k: iter(v) if isinstance(v, Iterable) else v
             for k, v in d.items()}
    try:
        while True:
            yield {k: next(v) if isinstance(v, Iterator) else v
                for k, v in state.items()}
            print('here')
    except StopIteration:
        pass


def dict_split(joined: Iterator[dict[str, Any]]):
    """
    Split an iterator of dictionaries into a dictionary of iterators.
    """
    peek, main = tee(joined)
    first = next(peek)
    keys = first.keys()
    def split(key: str, d: Any):
        try:
            while True:
                n = next(d)
                yield n[key]
        except StopIteration:
            pass
    return {key: split(key, d) for key, d in zip(keys, tee(main, len(keys)))}
