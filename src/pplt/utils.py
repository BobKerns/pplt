"""
Utilities for special iterators, etc, etc.
"""

from itertools import islice, tee
from collections.abc import Hashable, Iterable, Iterator
from typing import Any, cast, overload

from rich.console import Console

console = Console()

def take[T](n: int, x: Iterator[T]) -> list[T]:
    """
    Take n from an iterator.

    PARAMETERS
    ----------
    n: int
        The number of items to take.
    x: Iterator[T]
        The iterator.

    RETURNS
    -------
    list[T]
        List wil be [] if the iterator is empty.
    """
    return list(islice(x, 0, n))

def skip[T](n: int, x: Iterator[T]) -> Iterator[T]:
    """
    Skip n from an iterator.

    PARAMETERS
    ----------
    n: int
        The number of items to skip.
    x: Iterator[T]
        The iterator.

    RETURNS
    -------
    Iterator[T]
    """
    for _ in range(n):
        next(x)
    return x

def dict_join[K: Hashable, T](d: dict[K, Iterable[T]]|Any) -> Iterator[dict[K, T]]:
    """
    Iterate over a dictionary's iterable values in parallel,
    returning an iterator of dictionaries.
    """
    state = {k: iter(cast(Iterable[T], v)) if isinstance(v, Iterable) else v
             for k, v in d.items()}
    try:
        while True:
            yield {k: next(cast(Iterator[T], v)) if isinstance(v, Iterator) else v
                for k, v in state.items()}
    except StopIteration:
        pass


def dict_split[K: Hashable, T](joined: Iterator[dict[K, T]]) -> dict[K, Iterator[T]]:
    """
    Split an iterator of dictionaries into a dictionary of iterators.
    """
    peek, main = tee(joined)
    first = next(peek)
    keys = first.keys()
    def split(key: K, d: Iterator[dict[K, T]]) -> Iterator[T]:
        try:
            while True:
                n = next(d)
                yield n[key]
        except StopIteration:
            pass
    return {key: split(key, d) for key, d in zip(keys, tee(main, len(keys)))}


def attr_split(joined: Iterator[Any], *attrs: str):
    """
    Split an iterator of objects into subiterators.
    """
    def split(key: str, d: Any):
        try:
            while True:
                n = next(d)
                yield getattr(n, key)
        except StopIteration:
            pass
    return [split(key, d) for key, d in zip(attrs, tee(joined, len(attrs)))]


@overload
def unzip[T1, T2, T3, T4, T5, T6, T7, T8](x: Iterable[tuple[T1, T2, T3, T4,
                                                            T5, T6, T7, T8]],
                                             n: int|None=None,
                                             ) -> tuple[Iterator[T1],
                                                        Iterator[T2],
                                                        Iterator[T3],
                                                        Iterator[T4],
                                                        Iterator[T5],
                                                        Iterator[T6],
                                                        Iterator[T7],
                                                        Iterator[T8]]:
     ...
@overload
def unzip[T1, T2, T3, T4, T5, T6, T7](x: Iterable[tuple[T1, T2, T3, T4, T5, T6, T7]],
                                        n: int|None=None,
                                        ) -> tuple[Iterator[T1],
                                                      Iterator[T2],
                                                      Iterator[T3],
                                                      Iterator[T4],
                                                      Iterator[T5],
                                                      Iterator[T6],
                                                      Iterator[T7]]:
     ...
@overload
def unzip[T1, T2, T3, T4, T5, T6](x: Iterable[tuple[T1, T2, T3, T4, T5, T6]],
                                    n: int|None=None,
                                    ) -> tuple[Iterator[T1],
                                                 Iterator[T2],
                                                 Iterator[T3],
                                                 Iterator[T4],
                                                 Iterator[T5],
                                                 Iterator[T6]]:
        ...
@overload
def unzip[T1, T2, T3, T4, T5](x: Iterable[tuple[T1, T2, T3, T4, T5]],
                            n: int|None=None,
    ) -> tuple[Iterator[T1],
                Iterator[T2],
                Iterator[T3],
                Iterator[T4],
                Iterator[T5]]:
     ...
@overload
def unzip[T1, T2, T3, T4](x: Iterable[tuple[T1, T2, T3, T4]],
                        n: int|None=None,
    ) -> tuple[Iterator[T1],
                Iterator[T2],
                Iterator[T3],
                Iterator[T4]]:
    ...
@overload
def unzip[T1, T2, T3](x: Iterable[tuple[T1, T2, T3]],
                    n: int|None=None,
    ) -> tuple[Iterator[T1],
               Iterator[T2],
               Iterator[T3]]:
    ...
@overload
def unzip[T1, T2](x: Iterable[tuple[T1, T2]],
                n: int|None=None,
    ) -> tuple[Iterator[T1],
               Iterator[T2]]:
    ...
@overload
def unzip[T1](x: Iterable[tuple[T1]],
            n: int|None=None,
    ) -> tuple[Iterator[T1]]:
    ...
@overload
def unzip[T](x: Iterable[tuple[T, ...]],
            n: int|None=None,
    ) -> tuple[Iterator[T], ...]:
    ...
def unzip[T](x: Iterable[tuple[T, ...]],
            n: int|None=None,
    ) -> tuple[Iterator[T], ...]:
    """
    Unzip an iterator of tuples into a tuple of iterators. This is the inverse of
    the `zip` function. The number of items in the tuples is determined by the first
    tuple in the iterator, unless _n_ is specified. In this case, the number of
    iterators is _n_, regardless of the number of items in the tuples. If a tuple is
    shorter than the number of iterators, the extra iterators will raise `IndexError`.
    If a tuple is longer, the extra items will be ignored.

    If _n_ is unspecified, and a zero-length `Iterable` is passed for _x_,
    the function will raise a `ValueError`. If specified, it will return
    _n_ zero-length iterators in this case.

    PARAMETERS
    ----------
    x: Iterable[tuple[T, ...]]
        The iterator of tuples.
    n: Optional[int]
        The number of items in each tuple.
    """
    if n is None:
        peek, main = tee(x, 2)
        try:
            first = next(peek)
        except StopIteration:
            raise ValueError(
                "Cannot unzip zero-length iterable without specifying n."
                ) from None
        n = len(first)
    else:
        main = x
    iters = tee(main, n)
    def split(it: Iterator[tuple[T, ...]], i: int) -> Iterator[T]:
        try:
            while True:
                t = next(it)
                yield t[i]
        except StopIteration:
            pass
    return tuple(split(iters[i], i) for i in range(n))
